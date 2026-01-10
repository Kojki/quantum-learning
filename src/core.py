from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import numpy as np
import sympy as sp
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk


def select():
    """この関数では、GUIを用いてユーザーにテーマを選択させます。

    Returns:
        selected_value (str): 選択されたテーマの文字列
    """

    print("このツールでは量子センシングについて扱います。")
    selected_value = {"val": None}

    root = tk.Tk()
    root.title("選択")
    root.geometry("300x150")

    label = tk.Label(root, text="扱いたいテーマを選んでください。")
    label.pack(pady=10)

    values = ["位相による確率変化の実験", "量子センシング", "3"]
    combobox = ttk.Combobox(root, values=values)
    combobox.pack(pady=10)

    def on_select():
        selected_value["val"] = combobox.get()
        root.destroy()

    button = tk.Button(root, text="決定", command=on_select)
    button.pack()
    root.mainloop()
    return selected_value["val"]


def input_theta(prompt="位相をラジアンで入力してください(-π~π): "):
    theta = input(prompt)
    try:
        theta_sympify = sp.sympify(theta)
        return float(sp.N(theta_sympify))
    except:
        print("無効な入力です。再度入力してください。")
        return input_theta(prompt)


def phase_probability_experiment():
    theta_float = input_theta()
    qc = QuantumCircuit(1, 1)
    qc.h(0)  # H（重ね合わせ）
    qc.rz(theta_float, 0)  # RZ
    qc.h(0)  # H（干渉）
    qc.measure(0, 0)  # 測定
    print("回路:")
    print(qc.draw("text"))

    # --- 実行 ---
    sim = AerSimulator()
    qc_compiled = transpile(qc, sim)
    result = sim.run(qc_compiled, shots=1024).result()
    counts = result.get_counts()

    print("\n測定結果:")
    print(counts)

    # 確率
    total_shots = sum(counts.values())
    for state, count in counts.items():
        probability = count / total_shots
        print(f"状態 |{state}⟩: {count}回 ({probability*100:.2f}%)")


def iterative_phase_estimation(true_theta, num_bits=6):
    print(f"\n--- IPE (Bits: {num_bits}) ---")
    estimated_phase = 0.0
    for i in reversed(range(num_bits)):
        scaling = 2**i
        qc = QuantumCircuit(1, 1)
        qc.h(0)
        qc.rz(true_theta * scaling, 0)
        qc.rz(-estimated_phase * scaling, 0)
        qc.h(0)
        qc.measure(0, 0)
        sim = AerSimulator()
        result = sim.run(transpile(qc, sim), shots=1).result()
        measured_bit = int(list(result.get_counts().keys())[0])
        if measured_bit == 1:
            estimated_phase += (1 / 2 ** (i + 1)) * (2 * np.pi)

    print(f" Calibration Result: {estimated_phase:.4f}")
    return estimated_phase


def feedback_control_step(actual_field, current_correction, shots=100, gain=0.5):
    qc = QuantumCircuit(1, 1)
    qc.h(0)
    qc.rz(actual_field - current_correction, 0)
    qc.h(0)
    qc.measure(0, 0)
    sim = AerSimulator()
    counts = sim.run(transpile(qc, sim), shots=shots).result().get_counts()
    prob_0 = counts.get("0", 0) / shots
    prob_1 = counts.get("1", 0) / shots

    # エラーの計算と更新
    error = (0.5 - prob_0) + (prob_1 - 0.5)
    new_correction = current_correction + error * gain
    return new_correction, prob_0


def main():
    if select() == "位相による確率変化の実験":
        phase_probability_experiment()
        return
    if select() == "量子センシング":
        pass

    true_base_phase = 1.23
    print(f"Monitoring System Starting... Base Phase: {true_base_phase}")

    current_correction = iterative_phase_estimation(true_base_phase, num_bits=6)

    steps, true_phases, corrections = [], [], []
    drift_rate = 0.02
    plt.ion()
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title("Quantum Sensing Phase Tracker (Real-time Feedback)")
    ax.set_xlabel("Time Step")
    ax.set_ylabel("Phase (rad)")
    (line_true,) = ax.plot([], [], "b-", label="Env (True)", alpha=0.6)
    (line_corr,) = ax.plot([], [], "r-o", label="Quantum Lock", markersize=4)
    ax.legend()
    print("\nMonitor Active. Close window to exit.")
    try:
        for t in range(50):
            actual_field = true_base_phase + (t * drift_rate)
            current_correction, p0 = feedback_control_step(
                actual_field, current_correction, shots=100
            )
            steps.append(t)
            true_phases.append(actual_field)
            corrections.append(current_correction)
            # 更新
            line_true.set_data(steps, true_phases)
            line_corr.set_data(steps, corrections)
            ax.relim()
            ax.autoscale_view()
            plt.draw()
            plt.pause(0.1)

    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
    plt.ioff()
    plt.show()


if __name__ == "__main__":
    main()
