"""振幅バーチャートによる Grover アルゴリズムの可視化。

理想シミュレーター（ノイズなし）から Statevector を取り出し、
各基底状態の振幅（実部・確率）が反復ごとに変化する様子を
GIF アニメーションとして保存する。

state_plotter.py が「ショット測定の確率分布（ノイズあり）」を見るのに対し、
こちらは「量子状態の振幅そのもの（理想値）」を直接表示する。
これにより Grover の動作原理——平均振幅を軸とした反転——が
棒の動きとして直接見える。

呼び出しシグネチャ::

    from visualizer.amplitude_visualizer import run
    run(problem, threshold=best_cost, save_path="output/amplitude.gif")
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.ticker as ticker
from matplotlib.patches import Patch

from qiskit.quantum_info import Statevector, DensityMatrix
from qiskit.quantum_info import partial_trace as qk_partial_trace
from qiskit import transpile
from qiskit_aer import AerSimulator

from quantum.oracle import build_oracle, make_condition_from_cost, _enumerate_targets
from quantum.grover import build_grover_circuit, optimal_iterations
from visualizer.core import (
    COLOR_TARGET,
    COLOR_IDEAL,
    COLOR_BG,
    _setup_japanese_font,
    make_bar_labels,
    make_frame_title,
    save_or_show,
)

if TYPE_CHECKING:
    from problems.base import OptimizationProblem

_setup_japanese_font()

# ---------------------------------------------------------------------------
# 色の定義
# ---------------------------------------------------------------------------
_C_TARGET = "#D85A30"  # ターゲット状態（橙）
_C_NONTARGET = "#85B7EB"  # 非ターゲット状態（青）
_C_MEAN = "#1D9E75"  # 平均振幅ライン（緑）
_C_NEG = "#AFA9EC"  # 負の振幅（薄紫）
_C_BG = "#f8f9fa"

# 表示する基底状態の上限（これを超えたら有効解のみ表示に切り替え）
_FULL_DISPLAY_MAX = 64

# ---------------------------------------------------------------------------
# Statevector の取得
# ---------------------------------------------------------------------------


def _get_statevectors(
    n_qubits: int,
    oracle,
    n_iter: int,
) -> list[Statevector]:
    """k=0..n_iter の理想 Statevector（ancilla 込み）を返す。

    AerSimulator の statevector モードを使って取得する。
    ancilla を含む (n_qubits+1) 本分の状態ベクトル。
    """
    svs: list[Statevector] = []
    simulator = AerSimulator(method="statevector")

    for k in range(n_iter + 1):
        circ = build_grover_circuit(n_qubits, oracle, n_iterations=k)
        circ_sv = circ.copy()
        circ_sv.remove_final_measurements(inplace=True)
        circ_sv.save_statevector()
        compiled = transpile(circ_sv, simulator)
        result = simulator.run(compiled).result()
        sv = result.get_statevector(compiled)
        svs.append(sv)

    return svs


def _extract_input_amps(sv: Statevector, n_qubits: int) -> np.ndarray:
    """ancilla をトレースアウトして入力レジスタの複素振幅を返す。

    ancilla が |0> に戻っている（理想回路）場合、
    ancilla=0 の成分を取り出すだけで正確な入力レジスタの振幅が得られる。
    ただし一般性のため partial trace 経由で密度行列から対角成分を取る方式は
    振幅の位相情報を失うので、ここでは直接 statevector から取り出す。
    """
    dim = 2**n_qubits
    anc_mask = 1 << n_qubits
    amps = np.zeros(dim, dtype=complex)
    data = np.asarray(sv)

    for idx in range(len(data)):
        if (idx & anc_mask) == 0:
            input_idx = idx & (dim - 1)
            amps[input_idx] += data[idx]

    return amps


# ---------------------------------------------------------------------------
# 表示データの準備
# ---------------------------------------------------------------------------


def _build_display_data(
    amps_list: list[np.ndarray],
    n_qubits: int,
    target_set: set[int],
    feasible_set: set[int],
    city_names: list[str] | None,
    problem,
) -> dict:
    """フレームごとの表示データを事前計算して返す。

    Returns:
        {
          "labels": 表示する基底状態のラベル（ビット文字列 or ルート名）
          "indices": 対応する整数インデックス
          "is_target": ターゲットかどうかのbool配列
          "is_feasible": 有効解かどうかのbool配列
          "amps_real": フレームごとの実部 (n_frames x n_display)
          "amps_imag": フレームごとの虚部
          "probs": フレームごとの確率
          "mean_real": フレームごとの全体平均実部
          "mode": "full" or "valid_only"
        }
    """
    dim = 2**n_qubits
    n_frames = len(amps_list)

    if dim <= _FULL_DISPLAY_MAX:
        # 全状態を表示
        indices = list(range(dim))
        mode = "full"
    else:
        # 有効解 + 代表的な無効解を表示
        # 有効解全部 + 無効解から均等サンプリングして合計 _FULL_DISPLAY_MAX 件
        valid_idx = sorted(feasible_set)
        invalid_idx = sorted(set(range(dim)) - feasible_set)
        n_invalid_show = max(0, _FULL_DISPLAY_MAX - len(valid_idx))
        if n_invalid_show > 0 and invalid_idx:
            step = max(1, len(invalid_idx) // n_invalid_show)
            sampled_invalid = invalid_idx[::step][:n_invalid_show]
        else:
            sampled_invalid = []
        indices = sorted(valid_idx + list(sampled_invalid))
        mode = "valid_only"

    # ラベル生成
    def make_label(i: int) -> str:
        bits = format(i, f"0{n_qubits}b")
        if i in feasible_set and city_names:
            try:
                return (
                    problem.route_to_str(bits).replace(" -> ", "->").rsplit("->", 1)[0]
                )
            except Exception:
                return bits
        return bits

    labels = [make_label(i) for i in indices]
    is_target = np.array([i in target_set for i in indices])
    is_feasible = np.array([i in feasible_set for i in indices])

    amps_real = np.zeros((n_frames, len(indices)))
    amps_imag = np.zeros((n_frames, len(indices)))
    probs = np.zeros((n_frames, len(indices)))
    mean_real = np.zeros(n_frames)

    for f, amps in enumerate(amps_list):
        amps_real[f] = amps[indices].real
        amps_imag[f] = amps[indices].imag
        probs[f] = np.abs(amps[indices]) ** 2
        mean_real[f] = float(np.mean(amps.real))

    return {
        "labels": labels,
        "indices": indices,
        "is_target": is_target,
        "is_feasible": is_feasible,
        "amps_real": amps_real,
        "amps_imag": amps_imag,
        "probs": probs,
        "mean_real": mean_real,
        "mode": mode,
    }


# ---------------------------------------------------------------------------
# 1フレームの描画更新
# ---------------------------------------------------------------------------


def _make_animation(
    data: dict,
    n_qubits: int,
    n_iter: int,
    target_bitstrings: list[str],
    problem,
    fps: int,
) -> animation.FuncAnimation:
    """FuncAnimation を組み立てて返す。"""
    labels = data["labels"]
    is_target = data["is_target"]
    amps_real = data["amps_real"]
    probs = data["probs"]
    mean_real = data["mean_real"]
    mode = data["mode"]
    n_display = len(labels)
    n_frames = amps_real.shape[0]

    # 全フレームでの y 軸範囲を事前決定（ちらつき防止）
    amp_max = float(np.max(np.abs(amps_real))) * 1.25 + 0.01
    amp_min = -amp_max

    # レイアウト: 上段=振幅(実部)、下段=確率
    fig, (ax_amp, ax_prob) = plt.subplots(
        2,
        1,
        figsize=(max(10, n_display * 0.4 + 3), 9),
        facecolor=_C_BG,
        gridspec_kw={"height_ratios": [1.4, 1], "hspace": 0.45},
    )

    x = np.arange(n_display)
    bar_w = max(0.3, min(0.7, 0.6 * 30 / max(n_display, 30)))

    # --- 上段: 振幅（実部）---
    ax_amp.set_facecolor(_C_BG)
    ax_amp.spines[["top", "right"]].set_visible(False)
    ax_amp.set_ylabel("振幅（実部）", fontsize=10)
    ax_amp.set_ylim(amp_min, amp_max)
    ax_amp.set_xlim(-0.5, n_display - 0.5)
    ax_amp.axhline(0, color="#B4B2A9", linewidth=0.8, alpha=0.5)
    ax_amp.set_xticks(x)
    ax_amp.set_xticklabels(
        labels,
        rotation=55,
        ha="right",
        fontsize=max(6, min(9, 200 // n_display)),
    )

    # 参照線: 1/sqrt(N)
    ref = 1.0 / math.sqrt(2**n_qubits)
    ax_amp.axhline(ref, color="#B4B2A9", linewidth=0.8, linestyle="--", alpha=0.6)
    ax_amp.text(
        n_display - 0.3,
        ref + amp_max * 0.03,
        f"1/√N={ref:.4f}",
        fontsize=7,
        color="#888780",
        ha="right",
    )

    # 棒グラフ（振幅）
    colors_amp = [_C_TARGET if t else _C_NONTARGET for t in is_target]
    bars_amp = ax_amp.bar(x, amps_real[0], width=bar_w, color=colors_amp, alpha=0.88)

    # 平均線
    mean_line = ax_amp.axhline(
        mean_real[0], color=_C_MEAN, linewidth=2, linestyle="--", zorder=5
    )
    mean_txt = ax_amp.text(
        -0.4,
        mean_real[0],
        f" 平均={mean_real[0]:.4f}",
        fontsize=8,
        color=_C_MEAN,
        va="bottom",
    )

    ax_amp.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.3f"))

    # --- 下段: 確率 ---
    ax_prob.set_facecolor(_C_BG)
    ax_prob.spines[["top", "right"]].set_visible(False)
    ax_prob.set_ylabel("測定確率", fontsize=10)
    ax_prob.set_ylim(0, 1.05)
    ax_prob.set_xlim(-0.5, n_display - 0.5)
    ax_prob.set_xticks(x)
    ax_prob.set_xticklabels(
        labels,
        rotation=55,
        ha="right",
        fontsize=max(6, min(9, 200 // n_display)),
    )
    ax_prob.axhline(ref**2, color="#B4B2A9", linewidth=0.8, linestyle="--", alpha=0.6)
    ax_prob.text(
        n_display - 0.3,
        ref**2 + 0.01,
        f"1/N={ref**2:.5f}",
        fontsize=7,
        color="#888780",
        ha="right",
    )

    bars_prob = ax_prob.bar(x, probs[0], width=bar_w, color=colors_amp, alpha=0.88)

    # 確率の数値ラベル（有効解のみ）
    val_texts_prob = []
    for i in range(n_display):
        txt = ax_prob.text(
            x[i],
            probs[0][i] + 0.01,
            "",
            ha="center",
            fontsize=max(6, min(8, 150 // n_display)),
            color="#555",
        )
        val_texts_prob.append(txt)

    # タイトル・全体確率
    title_txt = fig.suptitle("", fontsize=12, fontweight="bold", y=0.99)
    target_prob_txt = fig.text(0.5, 0.96, "", ha="center", fontsize=10, color=_C_TARGET)

    # 凡例
    legend_elems = [
        Patch(
            facecolor=_C_TARGET, label=f"ターゲット状態（{len(target_bitstrings)} 個）"
        ),
        Patch(facecolor=_C_NONTARGET, label="非ターゲット状態"),
    ]
    if mode == "valid_only":
        legend_elems.append(
            Patch(
                facecolor="none",
                edgecolor="#888",
                linestyle="--",
                label=f"※ 有効解+非ターゲットの代表 {n_display} 件を表示",
            )
        )
    ax_amp.legend(handles=legend_elems, fontsize=8, loc="upper right")

    # --- 更新関数 ---
    def update(frame: int):
        real = amps_real[frame]
        prob = probs[frame]
        mean = mean_real[frame]

        for bar, h in zip(bars_amp, real):
            bar.set_height(h)
            bar.set_y(min(h, 0))
            bar.set_color(_C_NEG if h < 0 else bar.get_facecolor())

        mean_line.set_ydata([mean, mean])
        mean_txt.set_position((-0.4, mean))
        mean_txt.set_text(f" 平均={mean:.4f}")

        for bar, h in zip(bars_prob, prob):
            bar.set_height(h)

        for i, (txt, h) in enumerate(zip(val_texts_prob, prob)):
            if is_target[i] and h > 0.005:
                txt.set_text(f"{h:.3f}")
                txt.set_position((x[i], h + 0.01))
            else:
                txt.set_text("")

        t_prob = float(np.sum(prob[is_target]))
        title_txt.set_text(make_frame_title(frame, n_iter))
        target_prob_txt.set_text(f"ターゲット合計確率: {t_prob:.1%}")

        return (
            list(bars_amp)
            + list(bars_prob)
            + [mean_line, mean_txt, title_txt, target_prob_txt]
            + val_texts_prob
        )

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    ani = animation.FuncAnimation(
        fig,
        update,
        frames=n_frames,
        interval=1000 // fps,
        blit=True,
    )
    return ani


# ---------------------------------------------------------------------------
# メイン関数
# ---------------------------------------------------------------------------


def run(
    problem: "OptimizationProblem",
    threshold: float,
    save_path: str | Path | None = None,
    target_bitstrings: list[str] | None = None,
    fps: int = 2,
) -> None:
    """Grover 各反復の振幅バーチャートアニメーション（GIF）を生成する。

    上段に振幅の実部、下段に測定確率を表示する。
    有効解（ターゲット）は橙、非ターゲットは青で表示。
    緑の破線が平均振幅——拡散演算子はこれを軸に全振幅を反転する。

    状態数が 64 を超える場合は有効解 + 代表的な非ターゲット状態を表示する。

    Args:
        problem: OptimizationProblem のインスタンス。
        threshold: コストのしきい値。
        save_path: 保存先パス（.gif）。省略時はウィンドウ表示。
        target_bitstrings: 正解のビット列リスト。省略時は threshold から計算。
        fps: アニメーションの fps。
    """
    n_qubits = problem.n_qubits_required()

    # --- オラクル構築 ---
    condition = make_condition_from_cost(
        cost_fn=problem.cost,
        threshold=threshold,
        feasibility_fn=problem.is_feasible,
    )
    oracle = build_oracle(n_qubits, condition)

    if target_bitstrings is None:
        target_bitstrings = _enumerate_targets(n_qubits, condition)
    if not target_bitstrings:
        print("  [Amplitude] ターゲット状態が 0 件です。閾値を確認してください。")
        return

    target_set = {int(t, 2) for t in target_bitstrings}
    feasible_set = {
        i for i in range(2**n_qubits) if problem.is_feasible(format(i, f"0{n_qubits}b"))
    }

    n_iter = optimal_iterations(n_qubits, len(target_bitstrings))
    city_names = getattr(problem, "city_names", None)

    print(
        f"  [Amplitude] n_qubits={n_qubits}, targets={len(target_bitstrings)}, "
        f"最適反復数={n_iter}"
    )

    # --- Statevector 取得 ---
    print(f"  [Amplitude] Statevector 取得中 ({n_iter + 1} フレーム)...")
    svs = _get_statevectors(n_qubits, oracle, n_iter)

    # --- 入力レジスタの振幅を抽出 ---
    print("  [Amplitude] 振幅を抽出中...")
    amps_list = [_extract_input_amps(sv, n_qubits) for sv in svs]

    # --- 表示データ構築 ---
    data = _build_display_data(
        amps_list, n_qubits, target_set, feasible_set, city_names, problem
    )
    if data["mode"] == "valid_only":
        print(
            f"  [Amplitude] 状態数 {2**n_qubits} > {_FULL_DISPLAY_MAX}。"
            f"有効解 {len(list(target_set))} 件 + 代表的な非ターゲットを表示します。"
        )

    # --- アニメーション生成 ---
    print("  [Amplitude] アニメーション生成中...")
    ani = _make_animation(data, n_qubits, n_iter, target_bitstrings, problem, fps)

    # --- 保存 ---
    save_or_show(ani, save_path, fps=fps)
    plt.close("all")
    print("  [Amplitude] 完了。")
