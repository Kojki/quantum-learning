"""Grover アルゴリズムの確率変化アニメーション（改善版）。

画面構成：
    上段左  : 有効ルートの確率分布（理想）
    上段右  : 有効ルートの確率分布（ノイズあり）
    下段    : 反復ごとの正解確率の推移（折れ線）

全ビット列ではなく有効ルートのみに絞ることで
X軸がルート名で読めるグラフになる。
"""

from __future__ import annotations
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.gridspec as gridspec
import numpy as np
from matplotlib.patches import Patch

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
    COLOR_BG,
    make_bar_labels,
    make_frame_title,
    save_or_show,
    _setup_japanese_font,
)

_setup_japanese_font()


# ---------------------------------------------------------------------------
# 有効ルートの確率を抽出
# ---------------------------------------------------------------------------


def _feasible_probs(
    all_probs: list[float], feasible_labels: list[str], all_labels: list[str]
) -> list[float]:
    """全ビット列の確率から有効ルートのものだけ取り出す。"""
    label_to_idx = {label: i for i, label in enumerate(all_labels)}
    return [
        all_probs[label_to_idx[label]]
        for label in feasible_labels
        if label in label_to_idx
    ]


def _get_feasible_labels(n_qubits: int, problem) -> list[str]:
    """実行可能なビット列（有効ルート）をすべて列挙する。"""
    all_labels = make_bar_labels(n_qubits)
    return [label for label in all_labels if problem.is_feasible(label)]


def _label_to_route(label: str, problem) -> str:
    """ビット列をルート名に変換する（戻りルートを除く）。"""
    try:
        full = problem.route_to_str(label)
        # 「A → B → C → A」→「A→B→C」
        parts = [p.strip() for p in full.split("→")]
        return "→".join(parts[:-1])
    except Exception:
        return label


# ---------------------------------------------------------------------------
# 理想・ノイズありの確率を取得
# ---------------------------------------------------------------------------


def _get_ideal_probs(n_qubits, oracle, n_iterations, feasible_labels, all_labels):
    """理想シミュレーションで各反復後の有効ルート確率を返す。"""
    probs_per_step = []
    for k in range(n_iterations + 1):
        circuit = build_grover_circuit(n_qubits, oracle, n_iterations=k)
        circuit_no_meas = circuit.remove_final_measurements(inplace=False)
        sv = Statevector.from_instruction(circuit_no_meas)
        all_probs = sv.probabilities(qargs=list(range(n_qubits))).tolist()
        probs_per_step.append(_feasible_probs(all_probs, feasible_labels, all_labels))
    return probs_per_step


def _get_noisy_probs(
    n_qubits, oracle, n_iterations, feasible_labels, all_labels, noise_model, shots
):
    """ノイズありシミュレーションで各反復後の有効ルート確率を返す。"""
    simulator = AerSimulator()
    probs_per_step = []
    for k in range(n_iterations + 1):
        circuit = build_grover_circuit(n_qubits, oracle, n_iterations=k)
        compiled = transpile(circuit, simulator)
        job = simulator.run(compiled, shots=shots, noise_model=noise_model)
        counts = job.result().get_counts()
        normalized: dict[str, float] = {}
        for bitstring, count in counts.items():
            key = bitstring.replace(" ", "")[::-1]
            normalized[key] = normalized.get(key, 0) + count / shots
        all_probs = [normalized.get(label, 0.0) for label in all_labels]
        probs_per_step.append(_feasible_probs(all_probs, feasible_labels, all_labels))
    return probs_per_step


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------


def run(
    problem,
    threshold: float,
    shots: int = 2048,
    noise_model=None,
    save_path: str | Path | None = None,
    fps: int = 2,
) -> None:
    """Grover の確率変化アニメーションを生成する（有効ルート版）。"""
    n_qubits = problem.n_qubits_required()

    if noise_model is None:
        noise_model = build_combined_model(device="eagle_r3")

    condition = make_condition_from_cost(
        cost_fn=problem.cost,
        threshold=threshold,
        feasibility_fn=problem.is_feasible,
    )
    oracle = build_oracle(n_qubits, condition)
    target_bitstrings = set(_enumerate_targets(n_qubits, condition))
    n_iterations = optimal_iterations(n_qubits, len(target_bitstrings))

    all_labels = make_bar_labels(n_qubits)
    feasible_labels = _get_feasible_labels(n_qubits, problem)

    if not feasible_labels:
        print("  ⚠️  有効ルートが見つかりません。アニメーションをスキップします。")
        return

    route_names = [_label_to_route(label, problem) for label in feasible_labels]
    target_mask = [label in target_bitstrings for label in feasible_labels]
    bar_colors_ideal = [COLOR_TARGET if m else COLOR_IDEAL for m in target_mask]
    bar_colors_noisy = [COLOR_TARGET if m else COLOR_NOISY for m in target_mask]

    print("  理想シミュレーション実行中...")
    ideal_probs = _get_ideal_probs(
        n_qubits, oracle, n_iterations, feasible_labels, all_labels
    )
    print("  ノイズありシミュレーション実行中...")
    noisy_probs = _get_noisy_probs(
        n_qubits, oracle, n_iterations, feasible_labels, all_labels, noise_model, shots
    )

    # 正解確率の推移
    def _target_prob(probs):
        return sum(p for p, m in zip(probs, target_mask) if m)

    ideal_target_probs = [_target_prob(p) for p in ideal_probs]
    noisy_target_probs = [_target_prob(p) for p in noisy_probs]

    x = np.arange(len(feasible_labels))

    # ── レイアウト ──
    fig = plt.figure(figsize=(14, 8), facecolor=COLOR_BG)
    gs = gridspec.GridSpec(2, 2, height_ratios=[3, 1.5], hspace=0.5, wspace=0.35)
    ax_ideal = fig.add_subplot(gs[0, 0])
    ax_noisy = fig.add_subplot(gs[0, 1])
    ax_line = fig.add_subplot(gs[1, :])
    fig.suptitle(
        "Grover アルゴリズム：確率の変化（有効ルート）", fontsize=14, fontweight="bold"
    )

    noise_label = (
        getattr(noise_model, "_label", "ノイズあり") if noise_model else "ideal"
    )

    def _setup_bar_ax(ax, title):
        ax.set_facecolor(COLOR_BG)
        ax.set_title(title, fontsize=11)
        ax.set_ylabel("確率", fontsize=9)
        ax.set_ylim(0, 1.05)
        ax.set_xticks(x)
        # 有効ルートが多い場合は間引く
        MAX_LABELS = 12
        if len(route_names) <= MAX_LABELS:
            ax.set_xticklabels(route_names, rotation=60, ha="right", fontsize=8)
        else:
            step = max(1, len(route_names) // MAX_LABELS)
            shown_x = x[::step]
            shown_names = route_names[::step]
            ax.set_xticks(shown_x)
            ax.set_xticklabels(shown_names, rotation=60, ha="right", fontsize=8)
            ax.set_xlabel(
                f"ルート（{len(feasible_labels)}通り中 {len(shown_names)}件表示）",
                fontsize=9,
            )
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    _setup_bar_ax(ax_ideal, "理想（ノイズなし）")
    _setup_bar_ax(ax_noisy, f"ノイズあり（{noise_label}）")

    bars_ideal = ax_ideal.bar(x, ideal_probs[0], color=bar_colors_ideal, width=0.6)
    bars_noisy = ax_noisy.bar(x, noisy_probs[0], color=bar_colors_noisy, width=0.6)

    prob_text_ideal = ax_ideal.text(
        0.03,
        0.95,
        "",
        transform=ax_ideal.transAxes,
        fontsize=9,
        va="top",
        color=COLOR_TARGET,
    )
    prob_text_noisy = ax_noisy.text(
        0.03,
        0.95,
        "",
        transform=ax_noisy.transAxes,
        fontsize=9,
        va="top",
        color=COLOR_TARGET,
    )

    legend_elems = [Patch(facecolor=COLOR_TARGET, label="正解のルート")]
    ax_ideal.legend(handles=legend_elems, fontsize=8, loc="upper right")
    ax_noisy.legend(handles=legend_elems, fontsize=8, loc="upper right")

    # ── 折れ線グラフ ──
    ax_line.set_facecolor(COLOR_BG)
    ax_line.set_title("反復ごとの正解確率の推移", fontsize=10)
    ax_line.set_xlabel("反復回数", fontsize=9)
    ax_line.set_ylabel("正解確率", fontsize=9)
    ax_line.set_xlim(-0.2, n_iterations + 0.2)
    ax_line.set_ylim(0, 1.05)
    ax_line.set_xticks(range(n_iterations + 1))
    ax_line.set_xticklabels(
        ["初期状態"] + [f"反復 {i}" for i in range(1, n_iterations + 1)], fontsize=8
    )
    ax_line.axhline(
        y=1 / len(feasible_labels),
        color="#adb5bd",
        linestyle="--",
        linewidth=1,
        label="初期確率（均一）",
    )
    ax_line.spines["top"].set_visible(False)
    ax_line.spines["right"].set_visible(False)

    (line_ideal,) = ax_line.plot(
        [], [], color=COLOR_IDEAL, marker="o", linewidth=2, label="理想"
    )
    (line_noisy,) = ax_line.plot(
        [], [], color=COLOR_NOISY, marker="o", linewidth=2, label="ノイズあり"
    )
    ax_line.legend(fontsize=8, loc="upper left")

    step_text = fig.text(
        0.5,
        0.005,
        make_frame_title(0, n_iterations),
        ha="center",
        fontsize=10,
        color="#333333",
    )

    def update(frame):
        for bar, h in zip(bars_ideal, ideal_probs[frame]):
            bar.set_height(h)
        for bar, h in zip(bars_noisy, noisy_probs[frame]):
            bar.set_height(h)
        ip = ideal_target_probs[frame]
        np_ = noisy_target_probs[frame]
        prob_text_ideal.set_text(f"正解確率：{ip:.3f}")
        ratio = f"（理想比 {np_/ip:.2f}）" if ip > 1e-9 else ""
        prob_text_noisy.set_text(f"正解確率：{np_:.3f}  {ratio}")
        line_ideal.set_data(range(frame + 1), ideal_target_probs[: frame + 1])
        line_noisy.set_data(range(frame + 1), noisy_target_probs[: frame + 1])
        step_text.set_text(make_frame_title(frame, n_iterations))
        return (
            list(bars_ideal)
            + list(bars_noisy)
            + [prob_text_ideal, prob_text_noisy, line_ideal, line_noisy, step_text]
        )

    ani = animation.FuncAnimation(
        fig, update, frames=n_iterations + 1, interval=1000 // fps, blit=True
    )
    save_or_show(ani, save_path, fps=fps)
