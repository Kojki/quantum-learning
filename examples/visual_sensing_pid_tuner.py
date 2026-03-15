import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.sensing.ipe_algorithm import iterative_phase_estimation, feedback_control_step
from src.sensing.pid_control import PIDController

SENSITIVITY = 1.0
TARGET_LOCK_BIAS = np.pi / 2
PHYSICAL_UNIT = "rad"


def main():  # 初期設定
    true_base_phase = 1.23
    drift_rate = 0.02

    current_correction = iterative_phase_estimation(true_base_phase, num_bits=6)

    # PIDコントローラー
    pid = PIDController(Kp=0.4, Ki=0.08, Kd=0.1)

    # グラフの構築
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    plt.subplots_adjust(bottom=0.25)

    steps, env_actual, sensor_lock, p0_history = [], [], [], []

    (line_true,) = ax1.plot([], [], "b-", label="Environment Phase (rad)", alpha=0.3)
    (line_corr,) = ax1.plot(
        [], [], "r-", label="Quantum Sensor Output (rad)", linewidth=2
    )
    ax1.set_title("Quantum Phase Real-time Tracker (PID Control)")
    ax1.set_ylabel(f"Value ({PHYSICAL_UNIT})")
    ax1.legend(loc="upper left")

    (line_p0,) = ax2.plot([], [], "g-", label="P(0) Sensor Output")
    ax2.axhline(0.5, color="gray", linestyle="--")
    ax2.set_ylim(0, 1)
    ax2.set_ylabel("Probability")
    ax2.legend(loc="upper left")

    # --- スライダーの設置 ---
    ax_kp = plt.axes([0.15, 0.12, 0.65, 0.03])
    ax_ki = plt.axes([0.15, 0.08, 0.65, 0.03])
    ax_kd = plt.axes([0.15, 0.04, 0.65, 0.03])
    s_kp = Slider(ax_kp, "Kp (Speed)", 0.0, 2.0, valinit=pid.Kp)
    s_ki = Slider(ax_ki, "Ki (Precision)", 0.0, 0.5, valinit=pid.Ki)
    s_kd = Slider(ax_kd, "Kd (Stability)", 0.0, 1.0, valinit=pid.Kd)

    def update_params(val):
        pid.Kp = s_kp.val
        pid.Ki = s_ki.val
        pid.Kd = s_kd.val

    s_kp.on_changed(update_params)
    s_ki.on_changed(update_params)
    s_kd.on_changed(update_params)
    t = 0
    print("\nスライダーを動かしてPIDパラメータを調整してください。")
    try:
        while plt.fignum_exists(fig.number):
            # 外部環境の変化
            ext_drift = true_base_phase + (t * drift_rate)

            _, p0 = feedback_control_step(ext_drift, current_correction, shots=100)

            # PID計算
            error = 0.5 - p0
            output = pid.update(error)
            current_correction += output

            # データの蓄積（直近60ステップを表示）
            steps.append(t)
            env_actual.append(ext_drift * SENSITIVITY)
            sensor_lock.append((current_correction - TARGET_LOCK_BIAS) * SENSITIVITY)
            p0_history.append(p0)

            if len(steps) > 60:
                steps.pop(0)
                env_actual.pop(0)
                sensor_lock.pop(0)
                p0_history.pop(0)

            # 更新
            line_true.set_data(steps, env_actual)
            line_corr.set_data(steps, sensor_lock)
            ax1.set_xlim(min(steps), max(steps) + 1)
            ax1.relim()
            ax1.autoscale_view(scalex=False)

            line_p0.set_data(steps, p0_history)
            ax2.set_xlim(min(steps), max(steps) + 1)

            plt.draw()
            plt.pause(0.01)
            t += 1

    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
