import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from qiskit import transpile
from qiskit_aer import AerSimulator

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.sensing.core import iterative_phase_estimation, feedback_control_step
from src.sensing.control import PIDController


def main():
    # 1. 初期設定
    true_base_phase = 1.23  # 監視対象の初期値
    drift_rate = 0.02  # 外部環境の変化
    conv = 10.0  # 変換係数(rad -> mm)

    print(f"--- QK-Pulse: Advanced Sensing (PID Mode) ---")
    print(f"基準位相: {true_base_phase} rad")

    current_correction = iterative_phase_estimation(true_base_phase, num_bits=6)

    pid = PIDController(Kp=0.4, Ki=0.08, Kd=0.1)

    # データ保存用
    steps, true_phases, corrections = [], [], []
    p0_history = []

    # グラフ設定
    plt.ion()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    ax1.set_title("Quantum Phase Tracker (PID Control)")
    ax1.set_ylabel("Vibration Amplitude (mm)")
    (line_true,) = ax1.plot([], [], "b-", label="Env (Actual)", alpha=0.4)
    (line_corr,) = ax1.plot([], [], "r-", label="Quantum Lock (PID)", linewidth=2)
    ax1.legend()

    ax2.set_title("Sensing Stability P(0)")
    ax2.set_ylabel("Probability")
    ax2.set_ylim(0, 1)
    ax2.axhline(0.5, color="gray", linestyle="--")
    (line_p0,) = ax2.plot([], [], "g-", label="P(0)")
    ax2.legend()
    print(
        "\n[PID Monitoring Active] 積分項(I)が定常偏差を消し去る様子を観察してください。"
    )
    try:
        for t in range(100):
            actual_field = true_base_phase + (t * drift_rate)

            _, p0 = feedback_control_step(actual_field, current_correction, shots=100)

            # エラーを計算
            error = 0.5 - p0

            control_output = pid.update(error)

            # 補正値を更新
            current_correction += control_output

            # データの保存
            steps.append(t)
            true_phases.append(actual_field * conv)
            corrections.append(current_correction * conv)
            p0_history.append(p0)

            # グラフ更新
            line_true.set_data(steps, true_phases)
            line_corr.set_data(steps, corrections)
            ax1.relim()
            ax1.autoscale_view()

            line_p0.set_data(steps, p0_history)
            ax2.relim()
            ax2.autoscale_view()

            plt.draw()
            plt.pause(0.05)

    except KeyboardInterrupt:
        print("\nStop.")
    plt.ioff()
    plt.show()


if __name__ == "__main__":
    main()
