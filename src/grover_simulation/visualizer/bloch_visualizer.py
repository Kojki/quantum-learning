"""ブロッホ球による Grover アルゴリズムの可視化（QuTiP Bloch 版）。

量子ビット数に応じて自動的に可視化モードを切り替える:
  n_qubits <= 4  : 個別 qubit モード
      各量子ビットの reduced state をブロッホ球で表示する。
  n_qubits > 4   : 有効ブロッホ球モード（Effective Bloch Sphere）
      全状態を「ターゲット部分空間 |T>」と「非ターゲット部分空間 |S>」の
      2状態系に射影し、1つのブロッホ球でアルゴリズム全体の回転を表示する。
      Grover の反復が何量子ビットでも球面上の弧として明確に見える。

呼び出しシグネチャは既存と同じ::

    from visualizer.bloch_visualizer import run
    run(problem, threshold=best_cost, save_path="output/bloch.gif",
        target_bitstrings=optimal_bitstrings)

依存: pip install qutip pillow
"""

from __future__ import annotations

import io
import math
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyArrowPatch
from mpl_toolkits.mplot3d.proj3d import proj_transform

if TYPE_CHECKING:
    from problems.base import OptimizationProblem

# ---------------------------------------------------------------------------
# 依存インポート
# ---------------------------------------------------------------------------
try:
    from qiskit.quantum_info import Statevector, DensityMatrix
    from qiskit.quantum_info import partial_trace as qk_partial_trace
    from quantum.oracle import (
        build_oracle,
        make_condition_from_cost,
        _enumerate_targets,
    )
    from quantum.grover import build_grover_circuit, optimal_iterations

    _QISKIT_AVAILABLE = True
except ImportError:
    _QISKIT_AVAILABLE = False

try:
    from qutip import Bloch

    _QUTIP_AVAILABLE = True
except ImportError:
    _QUTIP_AVAILABLE = False

# ---------------------------------------------------------------------------
# しきい値
# ---------------------------------------------------------------------------
_INDIVIDUAL_QUBIT_MAX = 4  # これ以下なら個別 qubit モード

# ---------------------------------------------------------------------------
# カラー
# ---------------------------------------------------------------------------
C_INITIAL = "#378ADD"
C_CURRENT = "#1D9E75"
C_TARGET_VEC = "#D85A30"
C_TRAJ = "#a8dadc"
C_BG = "#f8f9fa"

# ===========================================================================
# Qiskit による量子状態計算
# ===========================================================================


def _get_statevectors(n_qubits: int, oracle, n_iter: int) -> list[Statevector]:
    """k=0..n_iter の Statevector（ancilla 込み）リストを返す。"""
    svs = []
    for k in range(n_iter + 1):
        circ = build_grover_circuit(n_qubits, oracle, n_iterations=k)
        circ_nm = circ.remove_final_measurements(inplace=False)
        svs.append(Statevector.from_instruction(circ_nm))
    return svs


def _bloch_vec_individual(
    sv: Statevector, qubit_idx: int
) -> tuple[float, float, float]:
    """qubit_idx の reduced state のブロッホベクトルを返す。

    ancilla を含む全 qubit のうち qubit_idx 以外をトレースアウトする。
    Qiskit は Little Endian。ancilla = index n_qubits（最上位）。
    """
    n_total = sv.num_qubits
    dm = DensityMatrix(sv)
    trace_out = [q for q in range(n_total) if q != qubit_idx]
    rho = qk_partial_trace(dm, trace_out).data
    x = float(2.0 * np.real(rho[0, 1]))
    y = float(-2.0 * np.imag(rho[0, 1]))
    z = float(np.real(rho[0, 0] - rho[1, 1]))
    return x, y, z


def _effective_bloch_vec(
    sv: Statevector,
    n_qubits: int,
    target_indices: list[int],
) -> tuple[float, float, float]:
    """有効ブロッホ球のベクトルを返す。

    Grover アルゴリズムは全状態ベクトルを
        |psi> = alpha * |S> + beta * |T>
    と書ける2次元平面内で回転させる。ここで
        |T> = 1/sqrt(M) * sum_{x in targets} |x>   (ターゲット)
        |S> = 1/sqrt(N-M) * sum_{x not in targets} |x>  (非ターゲット)

    この2状態を有効 qubit の |0>_eff / |1>_eff と見なしたときの
    ブロッホベクトルを返す。

    ancilla の部分はトレースアウトしてから入力レジスタの振幅を取り出す。
    """
    # ancilla をトレースアウトして入力レジスタの密度行列を取得
    dm = DensityMatrix(sv)
    rho_input = qk_partial_trace(dm, [n_qubits])
    dim = 2**n_qubits
    probs = rho_input.probabilities()[:dim]

    M = len(target_indices)
    N = dim
    if M == 0 or M == N:
        return (0.0, 0.0, 0.0)

    # 振幅を取り出す（密度行列から対角成分は確率 = |amp|^2 だが、
    # 純粋状態として Statevector から直接振幅を引く方が正確）
    # ancilla 込みの sv から入力レジスタ部分の振幅を取り出す
    # Qiskit Little Endian: index = q[0] + 2*q[1] + ... + 2^(n-1)*q[n-1] + 2^n * ancilla
    # ancilla=0 の成分だけを取り出す（ancilla は位相キックバック後 |0> に戻っている）
    sv_data = sv.data
    n_total = sv.num_qubits
    # ancilla bit が 0 の成分を取り出す
    # ancilla は最上位 bit = index の 2^n_qubits ビット
    anc_mask = 1 << n_qubits
    amps = np.zeros(dim, dtype=complex)
    for idx in range(2**n_total):
        if (idx & anc_mask) == 0:
            input_idx = idx & (dim - 1)
            amps[input_idx] += sv_data[idx]

    # 正規化
    norm = np.sqrt(np.sum(np.abs(amps) ** 2))
    if norm < 1e-12:
        return (0.0, 0.0, 0.0)
    amps /= norm

    # |T> と |S> への射影
    sqrt_M = math.sqrt(M)
    sqrt_S = math.sqrt(N - M)

    alpha_T = sum(amps[i] for i in target_indices) / sqrt_M  # <T|psi>
    alpha_S = (
        sum(amps[i] for i in range(dim) if i not in set(target_indices)) / sqrt_S
    )  # <S|psi>

    # 有効 qubit: |0>_eff = |T>, |1>_eff = |S>
    # rho_eff = [[|aT|^2, aT*conj(aS)], [aS*conj(aT), |aS|^2]]
    rho_eff = np.array(
        [
            [alpha_T * np.conj(alpha_T), alpha_T * np.conj(alpha_S)],
            [alpha_S * np.conj(alpha_T), alpha_S * np.conj(alpha_S)],
        ]
    )
    x = float(2.0 * np.real(rho_eff[0, 1]))
    y = float(-2.0 * np.imag(rho_eff[0, 1]))
    z = float(np.real(rho_eff[0, 0] - rho_eff[1, 1]))
    return x, y, z


def _get_input_probs(sv: Statevector, n_qubits: int) -> np.ndarray:
    """ancilla をトレースアウトした入力レジスタの測定確率を返す。"""
    dm = DensityMatrix(sv)
    rho_input = qk_partial_trace(dm, [n_qubits])
    dim = 2**n_qubits
    return rho_input.probabilities()[:dim]


# ===========================================================================
# QuTiP Bloch セットアップ
# ===========================================================================


def _make_bloch(ax: plt.Axes, xlabel=None, ylabel=None, zlabel=None) -> Bloch:
    """ax に紐付けた Bloch インスタンスを生成する。"""
    b = Bloch(axes=ax)

    b.xlabel = xlabel or [r"$|{+}\rangle$", r"$|{-}\rangle$"]
    b.ylabel = ylabel or [r"$|i\rangle$", r"$|-i\rangle$"]
    b.zlabel = zlabel or [r"$|0\rangle$", r"$|1\rangle$"]

    b.sphere_color = "#f0f4f8"
    b.sphere_alpha = 0.10
    b.frame_color = "#b0b8c4"
    b.frame_alpha = 0.35
    b.frame_width = 0.6

    b.vector_color = [C_CURRENT]
    b.vector_width = 4
    b.vector_arrowsize = 0.06

    b.point_color = [C_TRAJ, C_INITIAL]
    b.point_marker = ["o", "o"]
    b.point_size = [8, 40]

    b.font_size = 13
    return b


def _add_traj_and_vector(
    b: Bloch,
    traj: list[tuple[float, float, float]],
    frame: int,
    vec_color: str = C_CURRENT,
) -> None:
    """軌跡・始点・現在ベクトルを Bloch に追加する。"""
    # 始点（青い点）
    x0, y0, z0 = traj[0]
    b.add_points([[x0], [y0], [z0]], meth="s")

    # 軌跡（折れ線）: frame=0 のときは軌跡なし
    if frame > 0:
        xs = [traj[i][0] for i in range(frame + 1)]
        ys = [traj[i][1] for i in range(frame + 1)]
        zs = [traj[i][2] for i in range(frame + 1)]
        b.add_points([xs, ys, zs], meth="l")

    # 現在ベクトル
    cx, cy, cz = traj[frame]
    b.vector_color = [vec_color]
    b.add_vectors([cx, cy, cz])


# ===========================================================================
# 確率棒グラフ
# ===========================================================================


def _draw_prob_bar(
    ax: plt.Axes,
    probs: np.ndarray,
    n_qubits: int,
    target_set: set[int],
    max_bars: int = 32,
) -> None:
    """測定確率の横棒グラフを描画する。状態数が多い場合は上位のみ表示。"""
    dim = len(probs)
    # 確率上位 max_bars 件だけ表示（見やすさのため）
    if dim > max_bars:
        top_idx = np.argsort(probs)[::-1][:max_bars]
        top_idx = np.sort(top_idx)
        p_show = probs[top_idx]
        labels = [format(i, f"0{n_qubits}b") for i in top_idx]
        colors = [C_TARGET_VEC if i in target_set else C_CURRENT for i in top_idx]
        ax.set_title(
            f"measurement probability  (top {max_bars} / {dim} states)",
            fontsize=7,
            pad=2,
            color="#555",
        )
    else:
        p_show = probs
        labels = [format(i, f"0{n_qubits}b") for i in range(dim)]
        colors = [C_TARGET_VEC if i in target_set else C_CURRENT for i in range(dim)]
        ax.set_title("measurement probability", fontsize=7, pad=2, color="#555")

    y = np.arange(len(p_show))
    ax.barh(y, p_show, color=colors, height=0.6, alpha=0.85)
    ax.set_xlim(0, 1.05)
    ax.set_yticks(y)
    ax.set_yticklabels(
        labels, fontsize=max(5, 7 - len(labels) // 16), fontfamily="monospace"
    )
    ax.set_xlabel("probability", fontsize=7)
    ax.tick_params(axis="x", labelsize=7)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_facecolor(C_BG)

    for i, p in enumerate(p_show):
        if p > 0.04:
            ax.text(p + 0.01, i, f"{p:.3f}", va="center", fontsize=5, color="#555")


# ===========================================================================
# フレーム描画：個別 qubit モード
# ===========================================================================


def _render_frame_individual(
    frame: int,
    n_iter: int,
    trajs: list[list[tuple[float, float, float]]],
    svs: list[Statevector],
    n_qubits: int,
    target_set: set[int],
    targets_str: list[str],
    city_names: list[str] | None,
    elev: float,
    azim: float,
) -> bytes:
    max_display = min(n_qubits, 4)
    n_cols = min(max_display, 4)
    n_rows = math.ceil(max_display / n_cols)

    t_prob = sum(_get_input_probs(svs[frame], n_qubits)[i] for i in target_set)

    fig = plt.figure(
        figsize=(3.8 * n_cols, 3.8 * n_rows + 2.2),
        facecolor=C_BG,
        dpi=110,
    )
    outer = gridspec.GridSpec(
        2, 1, figure=fig, height_ratios=[n_rows * 3.6, 2.0], hspace=0.06
    )
    sg = gridspec.GridSpecFromSubplotSpec(
        n_rows, n_cols, subplot_spec=outer[0], hspace=0.04, wspace=0.04
    )

    step_lbl = "initial  H|0>^n" if frame == 0 else f"iteration {frame} / {n_iter}"
    fig.suptitle(
        f"Grover — individual qubit Bloch  [{step_lbl}]   "
        f"target prob = {t_prob:.1%}",
        fontsize=10,
        fontweight="bold",
        y=0.998,
        color="#222",
    )

    for q in range(max_display):
        row, col = divmod(q, n_cols)
        ax = fig.add_subplot(sg[row, col], projection="3d")
        ax.set_facecolor(C_BG)
        ax.view_init(elev=elev, azim=azim)

        label = f"q[{q}]"
        if city_names and q < len(city_names):
            label += f"  ({city_names[q]})"

        b = _make_bloch(ax)
        _add_traj_and_vector(b, trajs[q], frame)
        b.render()
        ax.set_title(label, fontsize=9, pad=2, color="#444")

        cx, cy, cz = trajs[q][frame]
        ax.text2D(
            0.02,
            0.02,
            f"({cx:.2f}, {cy:.2f}, {cz:.2f})",
            transform=ax.transAxes,
            fontsize=6,
            color="#888",
        )

    ax_prob = fig.add_subplot(outer[1])
    probs = _get_input_probs(svs[frame], n_qubits)
    _draw_prob_bar(ax_prob, probs, n_qubits, target_set)

    plt.tight_layout(rect=[0, 0, 1, 0.975])
    return _fig_to_bytes(fig)


# ===========================================================================
# フレーム描画：有効ブロッホ球モード
# ===========================================================================


def _render_frame_effective(
    frame: int,
    n_iter: int,
    eff_traj: list[tuple[float, float, float]],
    svs: list[Statevector],
    n_qubits: int,
    target_set: set[int],
    targets_str: list[str],
    elev: float,
    azim: float,
) -> bytes:
    """有効ブロッホ球（1つ）＋確率棒グラフのフレームを生成する。"""
    probs = _get_input_probs(svs[frame], n_qubits)
    t_prob = sum(probs[i] for i in target_set)

    fig = plt.figure(figsize=(10, 6.5), facecolor=C_BG, dpi=110)
    outer = gridspec.GridSpec(1, 2, figure=fig, width_ratios=[1, 1.1], wspace=0.10)

    step_lbl = "initial  H|0>^n" if frame == 0 else f"iteration {frame} / {n_iter}"
    fig.suptitle(
        f"Grover — effective Bloch sphere  [{step_lbl}]   "
        f"target prob = {t_prob:.1%}",
        fontsize=11,
        fontweight="bold",
        y=1.01,
        color="#222",
    )

    # --- 有効ブロッホ球 ---
    ax_b = fig.add_subplot(outer[0], projection="3d")
    ax_b.set_facecolor(C_BG)
    ax_b.view_init(elev=elev, azim=azim)

    b = _make_bloch(
        ax_b,
        zlabel=[r"$|T\rangle$  (target)", r"$|S\rangle$  (non-target)"],
        xlabel=[r"$|T\rangle+|S\rangle$", r"$|T\rangle-|S\rangle$"],
    )
    _add_traj_and_vector(b, eff_traj, frame, vec_color=C_TARGET_VEC)
    b.render()
    ax_b.set_title(
        f"effective qubit\n"
        f"|T⟩ = target subspace ({len(target_set)} states)\n"
        f"|S⟩ = non-target subspace",
        fontsize=8,
        pad=3,
        color="#333",
    )

    # ブロッホベクトル座標
    cx, cy, cz = eff_traj[frame]
    ax_b.text2D(
        0.02,
        0.02,
        f"({cx:.3f}, {cy:.3f}, {cz:.3f})",
        transform=ax_b.transAxes,
        fontsize=7,
        color="#888",
    )

    # 理論的な theta（回転角）を表示
    # Grover: theta = 2 * arcsin(sqrt(M/N))
    M = len(target_set)
    N = 2**n_qubits
    theta = 2 * math.asin(math.sqrt(M / N))
    expected_z = math.cos(math.pi / 2 - theta * frame)
    ax_b.text2D(
        0.02,
        0.08,
        f"θ = {math.degrees(theta):.1f}°/iter  " f"z_theory = {expected_z:.3f}",
        transform=ax_b.transAxes,
        fontsize=6,
        color="#aaa",
    )

    # --- 確率棒グラフ ---
    ax_p = fig.add_subplot(outer[1])
    _draw_prob_bar(ax_p, probs, n_qubits, target_set)

    plt.tight_layout(rect=[0, 0, 1, 0.97])
    return _fig_to_bytes(fig)


# ===========================================================================
# ユーティリティ
# ===========================================================================


def _fig_to_bytes(fig: plt.Figure) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight", facecolor=C_BG)
    buf.seek(0)
    data = buf.read()
    plt.close(fig)
    return data


# ===========================================================================
# メイン関数
# ===========================================================================


def run(
    problem: "OptimizationProblem",
    threshold: float,
    save_path: str | Path | None = None,
    target_bitstrings: list[str] | None = None,
    elev: float = 22,
    azim: float = -60,
    fps: float = 1.2,
) -> None:
    """Grover 各反復のブロッホ球軌跡アニメーション（GIF）を生成する。

    n_qubits <= 4: 個別 qubit モード（各 qubit の reduced state を表示）
    n_qubits >  4: 有効ブロッホ球モード（ターゲット/非ターゲット 2状態系）
    """
    if not _QISKIT_AVAILABLE:
        print("  [Bloch] Qiskit が見つかりません。pip install qiskit qiskit-aer")
        return
    if not _QUTIP_AVAILABLE:
        print("  [Bloch] QuTiP が見つかりません。pip install qutip")
        return
    try:
        from PIL import Image
    except ImportError:
        print("  [Bloch] Pillow が見つかりません。pip install pillow")
        return

    n_qubits = problem.n_qubits_required()
    mode = "individual" if n_qubits <= _INDIVIDUAL_QUBIT_MAX else "effective"
    print(f"  [Bloch] n_qubits={n_qubits} -> モード: {mode}")

    # オラクル構築
    condition = make_condition_from_cost(
        cost_fn=problem.cost,
        threshold=threshold,
        feasibility_fn=problem.is_feasible,
    )
    oracle = build_oracle(n_qubits, condition)

    if target_bitstrings is None:
        target_bitstrings = _enumerate_targets(n_qubits, condition)
    if not target_bitstrings:
        print("  [Bloch] ターゲット状態が 0 件です。")
        return

    target_indices = [int(t, 2) for t in target_bitstrings]
    target_set = set(target_indices)

    n_iter = optimal_iterations(n_qubits, len(target_bitstrings))
    print(f"  [Bloch] targets={len(target_bitstrings)}, 最適反復数={n_iter}")

    # Statevector 計算
    print(f"  [Bloch] Statevector 計算中 ({n_iter + 1} frames)...")
    svs = _get_statevectors(n_qubits, oracle, n_iter)

    # 軌跡の事前計算
    if mode == "individual":
        print(f"  [Bloch] 個別 qubit ブロッホベクトル計算中...")
        trajs = [[_bloch_vec_individual(sv, q) for sv in svs] for q in range(n_qubits)]
        city_names = getattr(problem, "city_names", None)
    else:
        print(f"  [Bloch] 有効ブロッホベクトル計算中...")
        eff_traj = [_effective_bloch_vec(sv, n_qubits, target_indices) for sv in svs]

    # フレーム生成
    n_frames = n_iter + 1
    print(f"  [Bloch] フレーム生成中 ({n_frames} frames)...")
    pil_frames: list[Image.Image] = []
    for i in range(n_frames):
        print(f"    frame {i + 1}/{n_frames}...", end="\r")
        if mode == "individual":
            png = _render_frame_individual(
                frame=i,
                n_iter=n_iter,
                trajs=trajs,
                svs=svs,
                n_qubits=n_qubits,
                target_set=target_set,
                targets_str=target_bitstrings,
                city_names=city_names,
                elev=elev,
                azim=azim,
            )
        else:
            png = _render_frame_effective(
                frame=i,
                n_iter=n_iter,
                eff_traj=eff_traj,
                svs=svs,
                n_qubits=n_qubits,
                target_set=target_set,
                targets_str=target_bitstrings,
                elev=elev,
                azim=azim,
            )
        pil_frames.append(Image.open(io.BytesIO(png)).convert("RGBA"))
    print()

    # GIF 保存
    if save_path is None:
        save_path = Path("bloch_animation.gif")
    out = Path(save_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    duration_ms = int(1000 / fps)
    pil_frames[0].save(
        str(out),
        save_all=True,
        append_images=pil_frames[1:],
        duration=duration_ms,
        loop=0,
        optimize=False,
    )
    print(f"  [Bloch] 保存完了: {out.resolve()}")
    print(
        f"         {out.stat().st_size // 1024} KB, {n_frames} frames, {duration_ms} ms/frame"
    )
