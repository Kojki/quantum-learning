import sys
import os
import matplotlib.pyplot as plt
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from src.sensing.core import feedback_control_step, iterative_phase_estimation


def main():
    # --- 設定 ---
    steps = []
    true_phases = []
    corrections = []
    true_base_phase = 1.23
    current_correction = iterative_phase_estimation(true_base_phase, num_bits=6)
    drift_rate = 0.02
    # グラフ
    plt.ion()
    fig, ax = plt.subplots()
    (line_true,) = ax.plot([], [], "b-", label="Environment Phase (rad)", alpha=0.5)
    (line_corr,) = ax.plot([], [], "r-", label="Quantum Sensor Output (rad)")
    ax.legend()
    ax.set_title("Quantum Phase Real-time Tracker")
    ax.set_xlabel("Step")
    ax.set_ylabel("Phase (rad)")
    for t in range(100):
        actual_field = true_base_phase + (t * drift_rate)
        current_correction, p0 = feedback_control_step(
            actual_field, current_correction, shots=100
        )
        steps.append(t)
        true_phases.append(actual_field)
        corrections.append(current_correction)
        # グラフの更新
        line_true.set_data(steps, true_phases)
        line_corr.set_data(steps, corrections)
        ax.relim()
        ax.autoscale_view()
        plt.draw()
        plt.pause(0.05)
    plt.ioff()
    plt.show()


if __name__ == "__main__":
    main()
