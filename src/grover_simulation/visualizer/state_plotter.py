"""古典（全探索）と量子（Grover）の探索過程を並べて比較するアニメーション。

左パネルに古典の探索（ランダムに候補を試していく様子）、
右パネルに量子の探索（観測確率が正解に集中していく様子）を並べ、
同じ「ステップ」で進むアニメーションとして表示・保存する。

使い方::

    from problems.routing import VehicleRoutingProblem
    from visualizer.state_plotter import run

    problem = VehicleRoutingProblem(distances, city_names)
    run(problem, threshold=50.0, save_path="race.gif")
"""

from __future__ import annotations

import random
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from matplotlib.patches import Patch

from quantum.oracle import build_oracle, make_condition_from_cost, _enumerate_targets
from quantum.grover import build_grover_circuit, optimal_iterations
from quantum.noise import build_combined_model
from qiskit import transpile
from qiskit_aer import AerSimulator
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


# ---------------------------------------------------------------------------
# 古典探索のシミュレーション：ステップごとの「試した回数」を記録
# ---------------------------------------------------------------------------


def _simulate_classical_search(
    n_qubits: int,
    target_bitstrings: list[str],
    n_steps: int,
    seed: int,
) -> list[dict[str, int]]:
    """古典のランダム探索を模擬し、各ステップで各ビット列が何回試されたかを返す。

    実際の全探索（brute_force）は順番に試すが、
    ここでは「量子との対比」として視覚的にわかりやすいランダム探索を使う。
    ステップ数は Grover の反復回数に合わせる。

    Args:
        n_qubits: 入力レジスタのビット数。
        target_bitstrings: 正解のビット列リスト。
        n_steps: 総ステップ数（Grover の反復回数に合わせる）。
        seed: 乱数シード。

    Returns:
        長さ ``n_steps + 1`` のリスト。
        各要素は ``{ビット列: 累積試行回数}`` の辞書。
    """
    rng = random.Random(seed)
    labels = [format(i, f"0{n_qubits}b") for i in range(2**n_qubits)]
    n_space = 2**n_qubits

    # 1ステップあたりの試行回数：探索空間をステップ数で均等割り
    trials_per_step = max(1, n_space // n_steps)

    cumulative: dict[str, int] = {label: 0 for label in labels}
    history = [dict(cumulative)]

    for _ in range(n_steps):
        for _ in range(trials_per_step):
            candidate = rng.choice(labels)
            cumulative[candidate] += 1
        history.append(dict(cumulative))

    return history


# ---------------------------------------------------------------------------
# アニメーション本体
# ---------------------------------------------------------------------------


def run(
    problem,
    threshold: float,
    shots: int = 2048,
    noise_model=None,
    seed: int = 42,
    save_path: str | Path | None = None,
    fps: int = 2,
    target_bitstrings: list[str] | None = None,
) -> None:
    """古典 vs 量子の探索レースアニメーションを表示・保存する。

    左パネルに古典（ランダム探索の累積試行回数）、
    右パネルに量子（ノイズあり観測確率）を並べる。
    ノイズモデルが省略された場合は eagle_r3 の実機パラメータを使用する。

    Args:
        problem: OptimizationProblem のインスタンス。
        threshold: Grover の条件に使うコストのしきい値。
        shots: ノイズありシミュレーションのショット数。
        noise_model: qiskit_aer のノイズモデル。省略時は eagle_r3 を使用。
        seed: 古典探索の乱数シード。
        save_path: 保存先パス（.gif）。省略時はウィンドウ表示。
        fps: アニメーションのフレームレート（ステップ/秒）。
        target_bitstrings: 正解のビット列リスト。指定時は threshold から計算せずこれを使用。

    Raises:
        ValueError: 条件を満たす解が存在しない場合。
    """
    n_qubits = problem.n_qubits_required()

    # ノイズモデルの決定
    if noise_model is None:
        noise_model = build_combined_model(
            device="eagle_r3",
            gate_time_1q=50e-9,
        )

    # 条件・オラクルの構築
    condition = make_condition_from_cost(
        cost_fn=problem.cost,
        threshold=threshold,
        feasibility_fn=problem.is_feasible,
    )
    oracle = build_oracle(n_qubits, condition)

    # target_bitstrings が外から渡された場合はそれを使う（浮動小数点誤差対策）
    if target_bitstrings is None:
        target_bitstrings = _enumerate_targets(n_qubits, condition)
    else:
        print(
            f"  [state_plotter] target_bitstrings を直接受け取りました: {len(target_bitstrings)} 件"
        )

    n_iterations = optimal_iterations(n_qubits, len(target_bitstrings))

    # 量子：各反復後の観測確率を取得
    print("量子シミュレーション実行中...")
    simulator = AerSimulator()
    labels = make_bar_labels(n_qubits)
    noisy_probs_history = []

    for k in range(n_iterations + 1):
        circuit = build_grover_circuit(n_qubits, oracle, n_iterations=k)
        compiled = transpile(circuit, simulator)
        job = simulator.run(compiled, shots=shots, noise_model=noise_model)
        counts = job.result().get_counts()

        # リトルエンディアン → ビッグエンディアンに変換
        normalized: dict[str, int] = {}
        for bitstring, count in counts.items():
            key = bitstring.replace(" ", "")[::-1]
            normalized[key] = normalized.get(key, 0) + count

        probs = [normalized.get(label, 0) / shots for label in labels]
        noisy_probs_history.append(probs)

    # 古典：ランダム探索の累積試行履歴を生成
    print("古典探索シミュレーション生成中...")
    classical_history = _simulate_classical_search(
        n_qubits, target_bitstrings, n_iterations, seed
    )

    # 最大試行回数（左パネルの y 軸スケール用）
    max_trials = max(max(step.values()) for step in classical_history if step)

    # X軸ラベル（ルート名に変換）
    tick_indices, tick_labels = make_axis_labels(labels, problem)

    # 色の準備
    colors_classical = make_bar_colors(labels, target_bitstrings, "#adb5bd")
    colors_quantum = make_bar_colors(labels, target_bitstrings, COLOR_NOISY)
    x = np.arange(len(labels))

    # ---グラフの初期設定---
    fig, (ax_classical, ax_quantum) = plt.subplots(
        1, 2, figsize=(14, 5), facecolor="#f8f9fa"
    )
    fig.suptitle("古典 vs 量子：探索過程の比較", fontsize=14, fontweight="bold")

    def _setup_ax(ax, title: str, ylabel: str, ylim: float):
        ax.set_facecolor("#f8f9fa")
        ax.set_title(title, fontsize=11)
        ax.set_xlabel("ルート", fontsize=9)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.set_ylim(0, ylim)
        ax.set_xticks(tick_indices)
        ax.set_xticklabels(tick_labels, rotation=45, ha="right", fontsize=7)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    _setup_ax(
        ax_classical,
        "古典（ランダム探索）",
        "累積試行回数",
        max_trials * 1.2,
    )
    _setup_ax(
        ax_quantum,
        "量子（Grover / eagle_r3 ノイズあり）",
        "観測確率",
        1.05,
    )

    # 初期フレームの棒グラフ
    classical_counts_0 = [classical_history[0][label] for label in labels]
    bars_classical = ax_classical.bar(
        x, classical_counts_0, color=colors_classical, width=0.6
    )
    bars_quantum = ax_quantum.bar(
        x, noisy_probs_history[0], color=colors_quantum, width=0.6
    )

    # 凡例
    legend_elements = [
        Patch(facecolor=COLOR_TARGET, label="正解のビット列"),
    ]
    for ax in (ax_classical, ax_quantum):
        ax.legend(handles=legend_elements, fontsize=8, loc="upper right")

    # 正解発見フラグ（古典側）
    found_text = ax_classical.text(
        0.5,
        0.92,
        "",
        transform=ax_classical.transAxes,
        ha="center",
        fontsize=9,
        color=COLOR_TARGET,
        fontweight="bold",
    )

    step_text = fig.text(
        0.5,
        0.01,
        make_frame_title(0, n_iterations),
        ha="center",
        fontsize=10,
        color="#333333",
    )

    plt.tight_layout(rect=[0, 0.04, 1, 1])

    # ---アニメーション更新関数---
    def update(frame: int):
        # 古典側の更新
        classical_counts = [classical_history[frame][label] for label in labels]
        for bar, h in zip(bars_classical, classical_counts):
            bar.set_height(h)

        # 正解ビット列がすでに試されているか確認
        target_found = any(classical_history[frame][t] > 0 for t in target_bitstrings)
        found_text.set_text("✓ 正解を発見済み" if target_found else "")

        # 量子側の更新
        for bar, h in zip(bars_quantum, noisy_probs_history[frame]):
            bar.set_height(h)

        step_text.set_text(make_frame_title(frame, n_iterations))

        return list(bars_classical) + list(bars_quantum) + [found_text, step_text]

    ani = animation.FuncAnimation(
        fig,
        update,
        frames=n_iterations + 1,
        interval=1000 // fps,
        blit=True,
    )

    save_or_show(ani, save_path, fps=fps)
