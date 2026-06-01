# Copied from faive_system/src/retargeter/retargeter.py
# Changes:
#   - "from .utils import retarget_utils" → "import retarget_utils"
#   - strip_meshes() added so pytorch_kinematics doesn't need mesh files on disk

import time
import xml.etree.ElementTree as ET
import torch
import numpy as np
from torch.nn.functional import normalize
import os
import pytorch_kinematics as pk
import retarget_utils          # flat import — both files live in teleop/
from typing import Union
import yaml
from scipy.spatial.transform import Rotation
from collections import defaultdict


def _strip_meshes(xml_str: str) -> str:
    """
    Prepare MJCF for pytorch_kinematics (which calls mujoco.MjModel.from_xml_string):
      - Remove <asset>  → no mesh file look-ups
      - Remove <default> → no inherited mesh/type defaults
      - Replace every <geom> with a tiny sphere → bodies keep non-zero mass
    """
    root = ET.fromstring(xml_str)
    for tag in ("asset", "default"):
        for el in root.findall(tag):
            root.remove(el)
    for parent in root.iter():
        for geom in parent.findall("geom"):
            geom.attrib.clear()
            geom.set("type", "sphere")
            geom.set("size", "0.001")
            geom.set("mass", "0.001")
            geom.set("contype", "0")
            geom.set("conaffinity", "0")
    return ET.tostring(root, encoding="unicode")


def transform_from_anchor(chain_transforms, target_frame, anchor_frame):
    transform_target = chain_transforms[target_frame]
    if anchor_frame is None:
        return transform_target
    transform_anchor = chain_transforms[anchor_frame]
    return transform_anchor.inverse().compose(transform_target)


class Retargeter:
    """
    Gradient-descent retargeter: maps 22-point MANO hand pose to robot joint angles.

    hand_scheme: path to YAML or dict
    mano_adjustments: path to YAML or dict (optional)
    retargeter_cfg: path to YAML or dict (optional)
    """

    def __init__(
        self,
        urdf_filepath: str = None,
        mjcf_filepath: str = None,
        sdf_filepath: str = None,
        hand_scheme: Union[str, dict] = None,
        mano_adjustments: Union[str, dict] = None,
        retargeter_cfg: Union[str, dict] = None,
        optimizer: str = "RMSprop",
        device: str = None,
    ) -> None:
        assert (
            int(urdf_filepath is not None)
            + int(mjcf_filepath is not None)
            + int(sdf_filepath is not None)
        ) == 1, "Exactly one of urdf_filepath, mjcf_filepath, or sdf_filepath must be provided"

        if hand_scheme is None:
            print("No hand scheme provided. Assuming Franka gripper")
            self.use_franka_gripper = True
        else:
            self.use_franka_gripper = False
            if isinstance(hand_scheme, str):
                with open(hand_scheme) as f:
                    hand_scheme = yaml.safe_load(f)
            elif not isinstance(hand_scheme, dict):
                raise ValueError("hand_scheme must be a str path or dict")

        if mano_adjustments is None:
            self._mano_adjustments = {}
        elif isinstance(mano_adjustments, dict):
            self._mano_adjustments = mano_adjustments
        elif isinstance(mano_adjustments, str):
            with open(mano_adjustments) as f:
                self._mano_adjustments = yaml.safe_load(f)

        self.model_center = None
        self.model_rotation = None

        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        if hand_scheme is not None:
            GC_TENDONS      = hand_scheme["gc_tendons"]
            FINGER_TO_TIP   = hand_scheme["finger_to_tip"]
            FINGER_TO_BASE  = hand_scheme["finger_to_base"]
            GC_LIMITS_LOWER = hand_scheme["gc_limits_lower"]
            GC_LIMITS_UPPER = hand_scheme["gc_limits_upper"]
            self.wrist_name   = hand_scheme["wrist_name"]
            self.anchor_name  = hand_scheme.get("anchor_name", None)
            self.forearm_and_wrist = hand_scheme.get("forearm_and_wrist", None)

            if retargeter_cfg is None:
                self._retargeter_cfg = {"lr": 2.5, "loss_func_cfg": {"keyvector_fingers2palm": 1.0}}
            elif isinstance(retargeter_cfg, dict):
                self._retargeter_cfg = retargeter_cfg
            elif isinstance(retargeter_cfg, str):
                with open(retargeter_cfg) as f:
                    self._retargeter_cfg = yaml.safe_load(f)

            self.lr = self._retargeter_cfg["lr"]
            self.target_angles = None
            self.gc_limits_lower = GC_LIMITS_LOWER
            self.gc_limits_upper = GC_LIMITS_UPPER
            self.finger_to_tip  = FINGER_TO_TIP
            self.finger_to_base = FINGER_TO_BASE

            prev_cwd = os.getcwd()
            model_path = urdf_filepath or mjcf_filepath or sdf_filepath
            os.chdir(os.path.dirname(model_path))
            if urdf_filepath is not None:
                self.chain = pk.build_chain_from_urdf(open(urdf_filepath).read()).to(device=self.device)
            elif mjcf_filepath is not None:
                self.chain = pk.build_chain_from_mjcf(_strip_meshes(open(mjcf_filepath).read())).to(device=self.device)
            else:
                self.chain = pk.build_chain_from_sdf(open(sdf_filepath).read()).to(device=self.device)
            os.chdir(prev_cwd)

            joint_parameter_names = self.chain.get_joint_parameter_names()
            self.n_joints  = self.chain.n_joints
            self.n_tendons = len(GC_TENDONS)
            self.joint_map = torch.zeros(self.n_joints, self.n_tendons).to(self.device)
            self.tendon_names = []
            joint_names_check = []
            for i, (name, tendons) in enumerate(GC_TENDONS.items()):
                vw = 0.5 if name.endswith("_virt") else 1.0
                self.joint_map[joint_parameter_names.index(name), i] = vw
                self.tendon_names.append(name)
                joint_names_check.append(name)
                for tendon, weight in tendons.items():
                    self.joint_map[joint_parameter_names.index(tendon), i] = weight * vw
                    joint_names_check.append(tendon)
            assert set(joint_names_check) == set(joint_parameter_names), \
                "Joint names mismatch — check hand_scheme"

            self.gc_joints = torch.ones(self.n_tendons).to(self.device) * 15.0
            self.gc_joints.requires_grad_()

            if optimizer.lower() == "adam":
                self.opt = torch.optim.Adam([self.gc_joints], lr=self.lr)
            elif optimizer.lower() == "rmsprop":
                self.opt = torch.optim.RMSprop([self.gc_joints], lr=self.lr)
            else:
                raise ValueError(f"Unsupported optimizer: {optimizer}")

            self.root = torch.zeros(1, 3).to(self.device)
            self.frames_we_care_about = None

            self.sanity_check()
            _ct = self.chain.forward_kinematics(
                torch.zeros(self.chain.n_joints, device=self.chain.device)
            )
            self.model_center, self.model_rotation = retarget_utils.get_hand_center_and_rotation(
                thumb_base=transform_from_anchor(_ct, self.finger_to_base["thumb"],  self.anchor_name).transform_points(self.root),
                index_base=transform_from_anchor(_ct, self.finger_to_base["index"],  self.anchor_name).transform_points(self.root),
                middle_base=transform_from_anchor(_ct, self.finger_to_base["middle"], self.anchor_name).transform_points(self.root),
                ring_base=transform_from_anchor(_ct, self.finger_to_base["ring"],   self.anchor_name).transform_points(self.root),
                pinky_base=transform_from_anchor(_ct, self.finger_to_base["pinky"],  self.anchor_name).transform_points(self.root),
                wrist=transform_from_anchor(_ct, self.wrist_name, self.anchor_name).transform_points(self.root),
            )
            self.model_center   = self.model_center.cpu().numpy()
            self.model_rotation = self.model_rotation.cpu().numpy()
            assert np.allclose(self.model_rotation @ self.model_rotation.T, np.eye(3), atol=1e-6)

            self._loss_function = self.build_loss_function(self._retargeter_cfg["loss_func_cfg"])

    # ── Properties ────────────────────────────────────────────────────────────

    def sanity_check(self):
        for finger, tip in self.finger_to_tip.items():
            assert tip in self.chain.get_link_names(), f"Tip {tip} not in chain"
        for finger, base in self.finger_to_base.items():
            assert base in self.chain.get_link_names(), f"Base {base} not in chain"

    @property
    def mano_adjustments(self):
        return self._mano_adjustments

    @mano_adjustments.setter
    def mano_adjustments(self, v):
        self._mano_adjustments = v

    @property
    def retargeter_cfg(self):
        return self._retargeter_cfg

    @retargeter_cfg.setter
    def retargeter_cfg(self, cfg):
        self._retargeter_cfg = cfg
        self.lr = cfg["lr"]
        self._loss_function = self.build_loss_function(cfg["loss_func_cfg"])

    # ── Core retarget API ─────────────────────────────────────────────────────

    def retarget(self, joints, debug_dict=None, opt_steps: int = 2):
        """
        joints: (22, 3) numpy array in MANO layout
          [0]=forearm, [1]=wrist, [2-5]=thumb, [6-9]=index, [10-13]=middle,
          [14-17]=ring, [18-21]=pinky
        Returns: (n_tendons,) joint angles in degrees
        """
        normalized, mano_center_and_rot = retarget_utils.normalize_points_to_hands_local(joints)
        if self.use_franka_gripper:
            self.target_angles = self._retarget_franka(normalized)
        else:
            if debug_dict is not None:
                debug_dict["mano_center_and_rot"] = mano_center_and_rot
                debug_dict["model_center_and_rot"] = (self.model_center, self.model_rotation)
                debug_dict["raw_joint_pos"] = normalized
            normalized = self.adjust_mano_fingers(normalized)
            normalized = normalized @ self.model_rotation.T + self.model_center
            if debug_dict is not None:
                debug_dict["normalized_joint_pos"] = normalized
            self.target_angles = self.retarget_finger_mano_joints(normalized, opt_steps=opt_steps)
        return self.target_angles, debug_dict

    def retarget_finger_mano_joints(self, joints: np.ndarray, warm: bool = True, opt_steps: int = 2):
        if self.frames_we_care_about is None:
            names = [self.finger_to_base["thumb"], self.finger_to_base["pinky"]]
            names += list(self.finger_to_tip.values())
            if self.forearm_and_wrist is not None:
                names += list(self.forearm_and_wrist.values())
            self.frames_we_care_about = self.chain.get_frame_indices(*names)

        if not warm:
            self.gc_joints = torch.ones(self.n_joints).to(self.device) * 15.0
            self.gc_joints.requires_grad_()

        assert joints.shape == (22, 3)
        mano_points = torch.from_numpy(joints).to(self.device)

        for _ in range(opt_steps):
            loss = self._loss_function(self.gc_joints, mano_points)
            self.opt.zero_grad()
            loss.backward()
            self.opt.step()
            with torch.no_grad():
                self.gc_joints[:] = torch.clamp(
                    self.gc_joints,
                    torch.tensor(self.gc_limits_lower).to(self.device),
                    torch.tensor(self.gc_limits_upper).to(self.device),
                )
        return self.gc_joints.detach().cpu().numpy()

    def adjust_mano_fingers(self, joints):
        adj = self._mano_adjustments
        if adj.get("all") is not None:
            translation = adj["all"].get("translation", np.zeros(3))
            rotation_angles = adj["all"].get("rotation", np.zeros(3))
            scale = adj["all"].get("scale", np.ones(3))
            joints = joints * scale + translation
            R = Rotation.from_euler("xyz", rotation_angles).as_matrix()
            joints = joints @ R.T

        jd = retarget_utils.get_mano_joints_dict(joints)
        out = {}
        for finger in ["thumb", "index", "middle", "ring", "pinky"]:
            fj = jd[finger]
            if adj.get(finger) is None:
                out[finger] = fj
                continue
            fa = adj[finger]
            translation = fa.get("translation", np.zeros(3))
            rotation_angles = fa.get("rotation", np.zeros(3))
            scale = fa.get("scale", np.ones(3))
            base = fj[0]
            local = (fj - base) * scale
            R = Rotation.from_euler("xyz", rotation_angles).as_matrix()
            out[finger] = base + local @ R.T + translation
        out["wrist"]   = jd["wrist"]
        out["forearm"] = jd["forearm"]

        return np.concatenate([
            out["forearm"].reshape(1, -1),
            out["wrist"].reshape(1, -1),
            out["thumb"], out["index"], out["middle"], out["ring"], out["pinky"],
        ], axis=0)

    def _retarget_franka(self, joints):
        d = np.linalg.norm(joints[4] - joints[8])
        return np.rad2deg(d)

    # ── Loss functions ────────────────────────────────────────────────────────

    def build_loss_function(self, loss_func_cfg):
        def loss(joints, mano_points):
            l = 0.0
            for name, weight in loss_func_cfg.items():
                fn = getattr(self, f"loss_{name}", None)
                if fn is None:
                    raise ValueError(f"Loss `loss_{name}` not found")
                if isinstance(weight, dict):
                    l += weight["weight"] * fn(joints, mano_points, **weight.get("kwargs", {}))
                else:
                    l += weight * fn(joints, mano_points)
            return l

        r_joints = torch.randn(self.n_tendons, device=self.device)
        r_mano   = torch.randn(22, 3, device=self.device)
        return torch.jit.trace(loss, (r_joints, r_mano))

    def loss_keyvector_fingers2palm(self, robot_joints, mano_points):
        jd = retarget_utils.get_mano_joints_dict(mano_points)
        fingertips = {f: jd[f][[-1], :] for f in ["thumb","index","middle","ring","pinky"]}
        mano_palm = torch.mean(
            torch.cat([jd["thumb"][[0],:], jd["pinky"][[0],:]], dim=0), dim=0, keepdim=True
        )
        kv_mano = torch.stack([fingertips[f] for f in ["thumb","index","middle","ring","pinky"]], dim=0)

        ct = self.chain.forward_kinematics(
            self.joint_map @ (robot_joints / (180 / np.pi)),
            frame_indices=self.frames_we_care_about,
        )
        robot_tips = {
            f: transform_from_anchor(ct, self.finger_to_tip[f], self.anchor_name).transform_points(self.root)
            for f in ["thumb","index","middle","ring","pinky"]
        }
        kv_robot = torch.stack([robot_tips[f] for f in ["thumb","index","middle","ring","pinky"]], dim=0)
        return torch.sum((kv_mano - kv_robot) ** 2)

    def loss_keyvector_fingers2fingers(self, robot_joints, mano_points):
        jd = retarget_utils.get_mano_joints_dict(mano_points)
        tips = {f: jd[f][[-1], :] for f in ["thumb","index","middle","ring","pinky"]}

        def kv(t):
            return torch.stack([
                t["index"] - t["thumb"], t["middle"] - t["thumb"],
                t["ring"] - t["thumb"],  t["pinky"] - t["thumb"],
                t["middle"] - t["index"], t["ring"] - t["index"],
                t["pinky"] - t["index"],  t["ring"] - t["middle"],
                t["pinky"] - t["middle"], t["pinky"] - t["ring"],
            ], dim=0)

        kv_mano = kv(tips)
        ct = self.chain.forward_kinematics(
            self.joint_map @ (robot_joints / (180 / np.pi)),
            frame_indices=self.frames_we_care_about,
        )
        robot_tips = {
            f: transform_from_anchor(ct, self.finger_to_tip[f], self.anchor_name).transform_points(self.root)
            for f in ["thumb","index","middle","ring","pinky"]
        }
        return torch.sum((kv_mano - kv(robot_tips)) ** 2)

    def loss_keyvector_forearm_and_wrist(self, robot_joints, mano_points):
        jd = retarget_utils.get_mano_joints_dict(mano_points)
        kv_mano = jd["forearm"] - jd["wrist"]

        ct = self.chain.forward_kinematics(
            self.joint_map @ (robot_joints / (180 / np.pi)),
            frame_indices=self.frames_we_care_about,
        )
        kp = {
            name: transform_from_anchor(ct, frame_name, self.anchor_name).transform_points(self.root)
            for name, frame_name in self.forearm_and_wrist.items()
        }
        kv_robot = kp["forearm"] - kp["wrist"]
        return torch.sum((kv_mano - kv_robot) ** 2)

    def loss_zero_regularizor(self, robot_joints, mano_points, **joint_regularizers):
        zeros   = torch.zeros(self.n_tendons).to(self.device)
        weights = torch.zeros(self.n_tendons).to(self.device)
        for jname, (zero_val, w) in joint_regularizers.items():
            i = self.tendon_names.index(jname)
            zeros[i]   = zero_val
            weights[i] = w
        rj = robot_joints / (180 / np.pi)
        return torch.sum(weights * (rj - zeros) ** 2)

    def loss_pinch_grasp(self, robot_joints, mano_points):
        jd = retarget_utils.get_mano_joints_dict(mano_points)
        d_mano = torch.norm(jd["index"][[-1], :] - jd["thumb"][[-1], :])
        ct = self.chain.forward_kinematics(
            self.joint_map @ (robot_joints / (180 / np.pi)),
            frame_indices=self.frames_we_care_about,
        )
        tip_i = transform_from_anchor(ct, self.finger_to_tip["index"], self.anchor_name).transform_points(self.root)
        tip_t = transform_from_anchor(ct, self.finger_to_tip["thumb"], self.anchor_name).transform_points(self.root)
        d_robot = torch.norm(tip_i - tip_t)
        return torch.sum((d_mano - d_robot) ** 2) / (d_mano + 1e-2)

    def loss_virtual_coupling(self, robot_joints, mano_points, **couplings):
        loss = torch.tensor(0.0).to(self.device)
        rj = robot_joints / (180 / np.pi)
        for _, (weight, joint_lists) in couplings.items():
            factors = torch.zeros(self.n_tendons).to(self.device)
            for factor, jname in joint_lists:
                factors[self.tendon_names.index(jname)] = factor
            loss += (factors * rj).sum() ** 2 * weight
        return loss
