from typing import Dict

import torch
import numpy as np


def get_mano_joints_dict(joints):
    back_to_numpy = False
    if isinstance(joints, np.ndarray):
        joints = torch.from_numpy(joints)
        back_to_numpy = True

    joints_dim = joints.dim()
    if joints_dim == 2:
        joints = joints.unsqueeze(0)

    joints_dict = {
        'forearm': joints[:, 0],
        'wrist':   joints[:, 1],
        'thumb':   joints[:, 2:6],
        'index':   joints[:, 6:10],
        'middle':  joints[:, 10:14],
        'ring':    joints[:, 14:18],
        'pinky':   joints[:, 18:22],
    }

    if joints_dim == 2:
        joints_dict = {k: v.squeeze(0) for k, v in joints_dict.items()}

    if back_to_numpy:
        joints_dict = {k: v.numpy() for k, v in joints_dict.items()}

    return joints_dict


def get_hand_center_and_rotation(
    thumb_base, index_base, middle_base, ring_base, pinky_base, wrist=None
):
    if torch is not None and isinstance(thumb_base, torch.Tensor):
        norm  = torch.norm
        cross = torch.cross
        stack = lambda arrays: torch.cat([a.reshape(1, 3) for a in arrays], dim=0)
    else:
        norm  = lambda x: np.linalg.norm(x)
        cross = np.cross
        stack = lambda arrays: np.concatenate([a.reshape(1, 3) for a in arrays], axis=0)

    hand_center = (thumb_base + pinky_base) / 2.0
    if wrist is None:
        wrist = hand_center

    y_axis = middle_base - wrist
    y_axis = y_axis / norm(y_axis)

    x_axis = index_base - ring_base
    x_axis -= (x_axis @ y_axis.T) * y_axis
    x_axis = x_axis / norm(x_axis)

    z_axis = cross(x_axis, y_axis)
    z_axis = z_axis / norm(z_axis)

    rot_matrix = stack([x_axis, y_axis, z_axis]).T
    return hand_center, rot_matrix


def normalize_points_to_hands_local(joint_pos):
    joint_dict = get_mano_joints_dict(joint_pos)
    hand_center, hand_rot = get_hand_center_and_rotation(
        thumb_base=joint_dict["thumb"][0],
        index_base=joint_dict["index"][0],
        middle_base=joint_dict["middle"][0],
        ring_base=joint_dict["ring"][0],
        pinky_base=joint_dict["pinky"][0],
        wrist=joint_dict["wrist"],
    )
    joint_pos = joint_pos - hand_center
    joint_pos = joint_pos @ hand_rot
    return joint_pos, (hand_center, hand_rot)


def rotation_matrix_z(angle):
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def rotation_matrix_y(angle):
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rotation_matrix_x(angle):
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
