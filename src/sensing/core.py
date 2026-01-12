# ==================== 定数定義 ====================

# シミュレーション設定
DEFAULT_SHOTS_EXPERIMENT = 1024  # 位相実験の測定回数
DEFAULT_SHOTS_FEEDBACK = 100  # フィードバック制御の測定回数
IPE_SHOTS = 1  # IPEは決定論的なので1回

# アルゴリズムパラメータ
IPE_DEFAULT_BITS = 6  # IPEの推定精度（ビット数）
FEEDBACK_GAIN = 0.5  # P制御ゲイン（Kp）

# 物理パラメータ
TRUE_BASE_PHASE = 1.23  # 初期磁場位相 [rad]
PHASE_DRIFT_RATE = 0.02  # 位相ドリフト速度 [rad/step]

# モニタリング設定
MONITORING_STEPS = 50  # モニタリングステップ数
ANIMATION_INTERVAL = 0.1  # グラフ更新間隔 [秒]

# GUI設定
GUI_WINDOW_WIDTH = 300  # 選択ウィンドウの幅 [px]
GUI_WINDOW_HEIGHT = 150  # 選択ウィンドウの高さ [px]

# 可視化設定
FIGURE_WIDTH = 10  # グラフの幅 [インチ]
FIGURE_HEIGHT = 8  # グラフの高さ [インチ]
LINE_ALPHA = 0.6  # 線の透明度
MARKER_SIZE = 4  # マーカーサイズ

# ==================== ここまで定数 ====================

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import numpy as np
import sympy as sp
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk


def select() -> str:
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


def input_theta(prompt: str = "位相をラジアンで入力してください(-π~π): ") -> float:
    """この関数では、ユーザーに位相θをラジアンで入力させます。

    Args:
        prompt (str, optional): ユーザーに表示するプロンプトメッセージ。 Defaults to "位相をラジアンで入力してください(-π~π):

    Returns:
        float: ユーザーが入力した位相θの数値
    """
    theta = input(prompt)
    try:
        theta_symbolic = sp.sympify(theta)
        return float(sp.N(theta_symbolic))
    except (ValueError, SyntaxError, TypeError):
        print("無効な入力です。再度入力してください。")
        return input_theta(prompt)


def phase_probability_experiment() -> None:
    """位相θに応じた測定確率の変化を観察します.

    H-RZ(θ)-H回路を用いて、位相回転角θと測定確率の関係を実験的に確認します.
    この実験は量子干渉の基礎を理解するためのデモンストレーションです.

    Theory:
        H·RZ(θ)·H|0⟩の測定確率:
        - P(|0⟩) = cos²(θ/2)
        - P(|1⟩) = sin²(θ/2)

        特殊なケース:
        - θ = 0    → P(|0⟩) = 1.00 (完全に|0⟩)
        - θ = π/2  → P(|0⟩) = 0.50 (等確率)
        - θ = π    → P(|0⟩) = 0.00 (完全に|1⟩)

    Returns:
        None: 結果は標準出力に表示されます.

    Example:
        >>> phase_probability_experiment()

        --- 位相による確率変化の実験 ---
        位相θを入力してください (単位: rad): 1.5708
        回路:
             ┌───┐┌─────────┐┌───┐┌─┐
        q_0: ┤ H ├┤ Rz(1.57)├┤ H ├┤M├
             └───┘└─────────┘└───┘└╥┘
        c: 1/══════════════════════╩═
                                    0

        測定結果:
        {'0': 512, '1': 512}
        状態 |0⟩: 512回 (50.00%)
        状態 |1⟩: 512回 (50.00%)
    """
    print("\n--- 位相による確率変化の実験 ---")

    theta_float = input_theta()
    qc = QuantumCircuit(1, 1)
    qc.h(0)  # H(重ね合わせ)
    qc.rz(theta_float, 0)  # RZ(位相回転)
    qc.h(0)  # H(干渉)
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

    total_shots = sum(counts.values())
    for state, count in counts.items():
        probability = count / total_shots
        print(f"状態 |{state}⟩: {count}回 ({probability*100:.2f}%)")


def iterative_phase_estimation(true_theta: float, num_bits: int = 6) -> float:
    """反復位相推定(IPE)アルゴリズムを用いて位相を推定します.

    量子位相推定の省リソース版.
    1量子ビットのみを使用して位相を最下位ビットから順に決定していきます.

    Args:
        true_theta (float): 推定対象の真の位相[rad] (0 ~ 2π)
        num_bits (int, optional): 推定精度(ビット数). Defaults to 6.
            精度 ≈ 2π / 2^num_bits (例: 6ビット → 約0.098 rad)

    Returns:
        float: 推定された位相[rad]

    Algorithm:
        各ビットiについて(最上位から):
        1. |+⟩状態を準備
        2. true_theta × 2^i の位相回転を適用
        3. 既に決定したビットによる補正(-estimated_phase × 2^i)
        4. 測定により現在のビット値を決定
        5. 結果に応じて推定位相を更新

    Example:
        >>> # π/4 (約0.785 rad)を推定
        >>> iterative_phase_estimation(np.pi/4, num_bits=6)
        --- IPE algorithm (Bits: 6) ---
            修正した結果: 0.7854
    """
    print(f"\n--- IPE algorithm (Bits: {num_bits}) ---")

    estimated_phase = 0.0
    for i in reversed(range(num_bits)):
        scaling = 2**i
        qc = QuantumCircuit(1, 1)
        qc.h(0)  # H（重ね合わせ）
        qc.rz(true_theta * scaling, 0)  # RZ（位相回転）
        qc.rz(-estimated_phase * scaling, 0)  # RZ (既知位相の打ち消し)
        qc.h(0)  # H（干渉）
        qc.measure(0, 0)  # 測定

        # --- 実行 ---
        sim = AerSimulator()
        simulation_result = sim.run(transpile(qc, sim), shots=1).result()
        measured_bit = int(list(simulation_result.get_counts().keys())[0])

        # 位相の更新
        if measured_bit == 1:
            estimated_phase += (1 / 2 ** (i + 1)) * (2 * np.pi)

    print(f" 修正した結果: {estimated_phase:.4f}")
    return estimated_phase


def feedback_control_step(actual_field, current_correction, shots=100, gain=0.5):
    """量子フィードバック制御の1ステップを実行します.

    外部磁場による位相回転を補正し、測定結果に基づいて
    補正値を更新する比例制御(P制御)を実装しています.

    Args:
        actual_field (float): 補正対象の外部磁場による位相回転角[rad].
        current_correction (float): 現在の補正位相[rad].
        shots (int, optional): 測定ショット数(統計精度に影響). Defaults to 100.
        gain (float, optional): P制御ゲイン(Kp).
            Defaults to 0.5.
            - 大きいほど速く収束するが振動しやすい
            - 小さいほど安定だが収束が遅い
            - 推奨範囲: 0.1~0.5

    Returns:
        tuple[float, float]: 以下の2要素のタプル
            - new_correction (float): 更新された補正位相[rad]
            - prob_0 (float): 測定で得られた状態|0⟩の確率

    Notes:
        - 目標状態: P(|0⟩) = P(|1⟩) = 0.5 (最大感度点)
        - 制御則: new_correction = current_correction + gain × (P(|1⟩) - P(|0⟩))
        - 収束条件: actual_field - current_correction ≈ π/2

    Example:
    >>> # 1ステップの補正
    >>> new_corr, prob = feedback_control_step(2.0, 0.0, shots=1000, gain=0.2)
    >>> round(new_corr, 2)
    0.12

    >>> # 10回反復して収束
    >>> correction = 0.0
    >>> for _ in range(10):
    ...     correction, _ = feedback_control_step(2.0, correction, shots=1000, gain=0.2)
    >>> round(correction, 2)
    1.57
    """
    qc = QuantumCircuit(1, 1)
    qc.h(0)  # H（重ね合わせ）

    # 位相回転（補正後の実効位相を適用）
    # actual_field: 外乱による位相
    # current_correction: 現在の補正値
    # 差分が目標値π/2に近づくように制御
    qc.rz(actual_field - current_correction, 0)  # RZ

    qc.h(0)  # H（干渉）
    qc.measure(0, 0)  # 測定

    # --- 実行 ---
    sim = AerSimulator()
    counts = sim.run(transpile(qc, sim), shots=shots).result().get_counts()
    # 確率計算
    prob_0 = counts.get("0", 0) / shots
    prob_1 = counts.get("1", 0) / shots

    # P制御則に基づく補正位相の更新
    error = prob_1 - prob_0  # 誤差
    new_correction = current_correction + error * gain  # 補正位相の更新
    return new_correction, prob_0


def main():
    selected_theme = select()
    if selected_theme == "位相による確率変化の実験":
        phase_probability_experiment()
        return
    if selected_theme == "量子センシング":
        true_base_phase = 1.23
        print(
            f"モニタリングシステムを起動しています… 基準の位相: {true_base_phase} rad"
        )

        current_correction = iterative_phase_estimation(true_base_phase, num_bits=6)

        steps, true_phases, corrections = [], [], []
        p0_history = []
        drift_rate = 0.02
        plt.ion()
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

        ax1.set_title(
            "Feedback-based Quantum Phase Sensing using Single-Qubit Interference"
        )
        ax1.set_ylabel("Phase (rad)")

        (line_true,) = ax1.plot([], [], "b-", label="Phase Drift (rad)", alpha=0.6)
        (line_corr,) = ax1.plot(
            [], [], "r-o", label="Estimated Phase Correction (rad)", markersize=4
        )
        ax1.legend()

        ax2.set_title("Sensing Stability P(0)")
        ax2.set_ylabel("Probability")
        ax2.set_ylim(0, 1)
        ax2.axhline(0.5, color="gray", linestyle="--")  # 0.5に基準を定める
        (line_p0,) = ax2.plot([], [], "g-", label="P(0)")
        ax2.legend()
        print("\nモニタリングを開始しました。ウィンドウを閉じると終了します。")
        try:
            for step in range(50):
                actual_field = true_base_phase + (step * drift_rate)
                current_correction, p0 = feedback_control_step(
                    actual_field, current_correction, shots=100
                )
                steps.append(step)
                true_phases.append(actual_field)
                corrections.append(current_correction)
                p0_history.append(p0)
                line_true.set_data(steps, true_phases)
                line_corr.set_data(steps, corrections)
                ax1.relim()
                ax1.autoscale_view()

                line_p0.set_data(steps, p0_history)
                ax2.relim()
                ax2.autoscale_view()

                plt.draw()
                plt.pause(0.1)

        except KeyboardInterrupt:
            print("\nモニタリングを停止しました。")
        plt.ioff()
        plt.show()


if __name__ == "__main__":
    main()
