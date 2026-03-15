"""Grover アルゴリズムの確率変化アニメーション。

画面構成：
    上段左  : 理想シミュレーション（確率振幅）の棒グラフ
    上段右  : ノイズありシミュレーション（観測確率）の棒グラフ
    下段    : 反復ごとの正解確率の推移（理想・ノイズあり の折れ線）

各棒グラフ内には現在の正解確率・反復回数を表示する。
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.gridspec as gridspec
import numpy as np

from qiskit import transpile
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

from quantum.oracle import build_oracle, make_condition_from_cost, _enumerate_targets
from quantum.grover import build_grover_circuit, optimal_iterations
from quantum.noise import build_combined_model
from visualizer.core import (
    COLOR_IDEAL,
    COLOR_NOISY,
    COLOR_TARGET,
    make_bar_labels,
    make_bar_colors,
    make_frame_title,
    make_axis_labels,
    save_or_show,
)


def _get_ideal_probs(n_qubits, oracle, n_iterations):
    probs_per_step = []
    for k in range(n_iterations + 1):
        circuit = build_grover_circuit(n_qubits, oracle, n_iterations=k)
        circuit_no_measure = circuit.remove_final_measurements(inplace=False)
        sv = Statevector.from_instruction(circuit_no_measure)
        probs = sv.probabilities(qargs=list(range(n_qubits)))
        probs_per_step.append(probs.tolist())
    return probs_per_step


def _get_noisy_probs(n_qubits, oracle, n_iterations, noise_model, shots):
    simulator = AerSimulator()
    labels = [format(i, f"0{n_qubits}b") for i in range(2**n_qubits)]
    probs_per_step = []
    for k in range(n_iterations + 1):
        circuit = build_grover_circuit(n_qubits, oracle, n_iterations=k)
        compiled = transpile(circuit, simulator)
        job = simulator.run(compiled, shots=shots, noise_model=noise_model)
        counts = job.result().get_counts()
        normalized: dict[str, int] = {}
        for bitstring, count in counts.items():
            key = bitstring.replace(" ", "")[::-1]
            normalized[key] = normalized.get(key, 0) + count
        probs = [normalized.get(label, 0) / shots for label in labels]
        probs_per_step.append(probs)
    return probs_per_step


def run(
    problem,
    threshold: float,
    shots: int = 2048,
    noise_model=None,
    save_path: str | Path | None = None,
    fps: int = 2,
) -> None:
    """Grover の確率変化アニメーションを表示・保存する。

    Args:
        problem: OptimizationProblem のインスタンス。
        threshold: コストのしきい値。
        shots: ノイズありシミュレーションのショット数。
        noise_model: ノイズモデル。省略時は eagle_r3 を使用。
        save_path: 保存先パス（.gif）。省略時はウィンドウ表示。
        fps: アニメーションのフレームレート。
    """
    n_qubits = problem.n_qubits_required()

    if noise_model is None:
        noise_model = build_combined_model(
            device="eagle_r3",
            gate_time_1q=50e-9,
        )

    condition = make_condition_from_cost(
        cost_fn=problem.cost,
        threshold=threshold,
        feasibility_fn=problem.is_feasible,
    )
    oracle = build_oracle(n_qubits, condition)
    target_bitstrings = _enumerate_targets(n_qubits, condition)
    n_iterations = optimal_iterations(n_qubits, len(target_bitstrings))

    print("理想シミュレーション実行中...")
    ideal_probs = _get_ideal_probs(n_qubits, oracle, n_iterations)
    print("ノイズありシミュレーション実行中...")
    noisy_probs = _get_noisy_probs(n_qubits, oracle, n_iterations, noise_model, shots)

    labels = make_bar_labels(n_qubits)
    colors_ideal = make_bar_colors(labels, target_bitstrings, COLOR_IDEAL)
    colors_noisy = make_bar_colors(labels, target_bitstrings, COLOR_NOISY)
    x = np.arange(len(labels))

    # 正解の合計確率を反復ごとに計算
    def _target_prob(probs):
        return sum(probs[labels.index(t)] for t in target_bitstrings if t in labels)

    ideal_target_probs = [_target_prob(p) for p in ideal_probs]
    noisy_target_probs = [_target_prob(p) for p in noisy_probs]

    # X軸ラベルの間引き
    tick_indices, tick_labels = make_axis_labels(labels, problem)

    # ---レイアウト---
    fig = plt.figure(figsize=(14, 8), facecolor="#f8f9fa")
    gs = gridspec.GridSpec(2, 2, height_ratios=[3, 1.5], hspace=0.45, wspace=0.3)

    ax_ideal = fig.add_subplot(gs[0, 0])
    ax_noisy = fig.add_subplot(gs[0, 1])
    ax_line = fig.add_subplot(gs[1, :])

    fig.suptitle("Grover アルゴリズム：確率の変化", fontsize=14, fontweight="bold")

    def _setup_bar_ax(ax, title):
        ax.set_facecolor("#f8f9fa")
        ax.set_title(title, fontsize=11)
        ax.set_xlabel("ルート", fontsize=9)
        ax.set_ylabel("確率", fontsize=9)
        ax.set_ylim(0, 1.05)
        ax.set_xticks(tick_indices)
        ax.set_xticklabels(tick_labels, rotation=45, ha="right", fontsize=7)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    _setup_bar_ax(ax_ideal, "理想（ノイズなし）")
    _setup_bar_ax(ax_noisy, "実機相当ノイズあり（eagle_r3）")

    bars_ideal = ax_ideal.bar(x, ideal_probs[0], color=colors_ideal, width=0.6)
    bars_noisy = ax_noisy.bar(x, noisy_probs[0], color=colors_noisy, width=0.6)

    # 正解確率テキスト
    prob_text_ideal = ax_ideal.text(
        0.03,
        0.95,
        "",
        transform=ax_ideal.transAxes,
        fontsize=9,
        verticalalignment="top",
        color=COLOR_TARGET,
    )
    prob_text_noisy = ax_noisy.text(
        0.03,
        0.95,
        "",
        transform=ax_noisy.transAxes,
        fontsize=9,
        verticalalignment="top",
        color=COLOR_TARGET,
    )

    # 凡例
    from matplotlib.patches import Patch

    legend_elements = [Patch(facecolor=COLOR_TARGET, label="正解のルート")]
    for ax in (ax_ideal, ax_noisy):
        ax.legend(handles=legend_elements, fontsize=8, loc="upper right")

    # ---折れ線グラフ（正解確率の推移）---
    ax_line.set_facecolor("#f8f9fa")
    ax_line.set_title("反復ごとの正解確率の推移", fontsize=10)
    ax_line.set_xlabel("反復回数", fontsize=9)
    ax_line.set_ylabel("正解確率", fontsize=9)
    ax_line.set_xlim(-0.2, n_iterations + 0.2)
    ax_line.set_ylim(0, 1.05)
    ax_line.set_xticks(range(n_iterations + 1))
    ax_line.set_xticklabels(
        ["初期状態"] + [f"反復 {i}" for i in range(1, n_iterations + 1)],
        fontsize=8,
    )
    ax_line.spines["top"].set_visible(False)
    ax_line.spines["right"].set_visible(False)
    ax_line.axhline(
        y=1 / len(labels),
        color="#adb5bd",
        linestyle="--",
        linewidth=1,
        label="初期確率（均一）",
    )
    ax_line.legend(fontsize=8, loc="lower right")

    (line_ideal,) = ax_line.plot(
        [], [], color=COLOR_IDEAL, marker="o", linewidth=2, label="理想"
    )
    (line_noisy,) = ax_line.plot(
        [], [], color=COLOR_NOISY, marker="o", linewidth=2, label="ノイズあり"
    )
    ax_line.legend(fontsize=8, loc="lower right")

    # フレームラベル
    step_text = fig.text(
        0.5,
        0.005,
        make_frame_title(0, n_iterations),
        ha="center",
        fontsize=10,
        color="#333333",
    )

    # ---アニメーション更新---
    def update(frame: int):
        for bar, h in zip(bars_ideal, ideal_probs[frame]):
            bar.set_height(h)
        for bar, h in zip(bars_noisy, noisy_probs[frame]):
            bar.set_height(h)

        ip = ideal_target_probs[frame]
        np_ = noisy_target_probs[frame]
        prob_text_ideal.set_text(f"正解確率：{ip:.3f}")
        prob_text_noisy.set_text(
            f"正解確率：{np_:.3f}  （理想比 {np_/ip:.2f}）"
            if ip > 0
            else f"正解確率：{np_:.3f}"
        )

        line_ideal.set_data(range(frame + 1), ideal_target_probs[: frame + 1])
        line_noisy.set_data(range(frame + 1), noisy_target_probs[: frame + 1])

        step_text.set_text(make_frame_title(frame, n_iterations))

        return (
            list(bars_ideal)
            + list(bars_noisy)
            + [prob_text_ideal, prob_text_noisy, line_ideal, line_noisy, step_text]
        )

    ani = animation.FuncAnimation(
        fig,
        update,
        frames=n_iterations + 1,
        interval=1000 // fps,
        blit=True,
    )

    save_or_show(ani, save_path, fps=fps)
