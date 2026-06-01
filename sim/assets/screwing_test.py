import mujoco
import mujoco.viewer
import time
import numpy as np

# --- PID 控制器参数 (针对滑动关节) ---
KP_SLIDE = 1000.0  # 比例增益
KI_SLIDE = 50.0   # 积分增益
KD_SLIDE = 5.0    # 微分增益

# 积分误差限制 (防止积分饱和)
INTEGRAL_LIMIT_SLIDE = 0.005

# --- 螺栓运动参数 ---
SCREW_PITCH = 0.004  # 螺距 (米/圈)
NUM_TURNS = 10       # 总螺纹圈数

# --- 初始化 PID 变量 ---
integral_error_slide = 0.0
prev_hinge_angle = 0.0

# --- 加载模型 ---
model = mujoco.MjModel.from_xml_path("i4_7_8_screwing.xml")
data = mujoco.MjData(model)

# --- 获取关节和执行器ID ---
hinge_joint_id = model.joint('bolt_hinge').id
slide_joint_id = model.joint('bolt_slide').id
slide_motor_id = model.actuator('slide_bolt_motor').id

# --- 获取传感器ID ---
hinge_angle_sensor_id = model.sensor('bolt_hinge_angle').id
slide_position_sensor_id = model.sensor('bolt_slide_position').id
slide_velocity_sensor_id = model.sensor('bolt_slide_velocity').id

# --- 获取螺栓质量和重力分量，用于前馈计算 ---
bolt_mass = model.body('bolt_body').mass.item() # *** 确保是标量 ***
gravity_z = model.opt.gravity[2].item()         # *** 确保是标量 ***
# 计算抵消重力的前馈力：质量 * (-重力Z分量)，向上为正
gravity_feedforward_force = bolt_mass * (-gravity_z) # *** 结果会是标量 ***

# --- 创建Viewer ---
viewer = mujoco.viewer.launch_passive(model, data)

print("Simulation started with gravity compensation (feedforward control).")
print(f"Screw Pitch: {SCREW_PITCH * 1000} mm/turn")
print(f"Bolt Mass: {bolt_mass:.3f} kg")
print(f"Gravity Feedforward Force (to counter gravity): {gravity_feedforward_force:.2f} N")


# --- 模拟循环 ---
try:
    while viewer.is_running():
        step_start = time.time()
        dt = model.opt.timestep

        # --- 读取当前关节状态 ---
        current_hinge_angle = data.sensordata[hinge_angle_sensor_id].item() # *** 确保是标量 ***
        current_slide_position = data.sensordata[slide_position_sensor_id].item() # *** 确保是标量 ***
        current_slide_velocity = data.sensordata[slide_velocity_sensor_id].item() # *** 确保是标量 ***

        # 计算期望的滑动位置
        desired_slide_position = (-current_hinge_angle / (2 * np.pi)) * SCREW_PITCH #顺进逆出
        # clip 函数的结果也可能是 0-D 数组，所以也要确保是标量
        desired_slide_position = np.clip(desired_slide_position, model.joint('bolt_slide').range[0], model.joint('bolt_slide').range[1]).item() # *** 确保是标量 ***


        # --- 计算滑动关节的 PID 反馈力 ---
        error_slide = desired_slide_position - current_slide_position # *** 结果会是标量 ***

        integral_error_slide += error_slide * dt
        integral_error_slide = np.clip(integral_error_slide, -INTEGRAL_LIMIT_SLIDE, INTEGRAL_LIMIT_SLIDE)

        derivative_error_slide = -current_slide_velocity # 目标速度为0

        # PID 反馈部分输出的力
        pid_feedback_force = KP_SLIDE * error_slide + KI_SLIDE * integral_error_slide + KD_SLIDE * derivative_error_slide
        # pid_feedback_force 也可能是 0-D 数组，需要 item()

        # --- 总控制力 = PID 反馈力 + 前馈力 ---
        motor_total_force = 0.0 # 声明为 float
        if abs(current_hinge_angle - prev_hinge_angle) < np.radians(0.1) and abs(error_slide) < 1e-4:
            # 螺栓静止或几乎静止，并且已经接近目标，只用前馈力维持高度
            motor_total_force = gravity_feedforward_force # 这是一个标量
            integral_error_slide = 0.0 # 消除静止时的积分累积
        else:
            # 螺栓正在被转动，需要 PID 来驱动到期望位置，并用前馈力抵消重力
            motor_total_force = pid_feedback_force.item() + gravity_feedforward_force # *** 确保 pid_feedback_force 是标量 ***

        data.ctrl[slide_motor_id] = motor_total_force # *** motor_total_force 此时应为标量 ***

        # --- 执行一步仿真 ---
        mujoco.mj_step(model, data)

        # --- 更新前一时刻的铰链角度 ---
        prev_hinge_angle = current_hinge_angle

        # --- 打印状态 (可选) ---
        if data.time % 0.1 < dt: # 每0.1秒打印一次
            print(f"Time: {data.time:.2f}s | " # *** data.time 保持不变 ***
                  f"Hinge Angle: {current_hinge_angle:.2f} rad | "
                  f"Desired Slide Pos: {desired_slide_position:.4f} m | "
                  f"Current Slide Pos: {current_slide_position:.4f} m | "
                  f"Slide Error: {error_slide:.4f} | "
                  f"Total Force: {motor_total_force:.2f} N")

        # --- 更新Viewer ---
        viewer.sync()

        # --- 控制模拟速度 ---
        time_until_next_step = model.opt.timestep - (time.time() - step_start)
        if time_until_next_step > 0: # 修正拼写错误
            time.sleep(time_until_next_step)

except KeyboardInterrupt:
    pass
finally:
    viewer.close()
    print("Simulation finished.")