"""量子回路図を生成・保存するモジュール。

出力する回路図：
    circuit_overview.png   : Oracle + Diffusion 1反復分の全体回路
    circuit_oracle.png     : Oracle の内部構造（フェーズキックバック）
    circuit_diffusion.png  : Diffusion の内部構造（振幅反転）

使い方::

    from visualizer.circuit_drawer import draw_circuits

    draw_circuits(problem, threshold=40.0, output_dir=Path("output"))
"""

from __future__ import annotations
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec

from qiskit import QuantumCircuit

from quantum.oracle import build_oracle, make_condition_from_cost, _enumerate_targets
from quantum.grover import (
    build_grover_circuit,
    build_diffusion,
    optimal_iterations,
)
from visualizer.core import _setup_japanese_font

_setup_japanese_font()


# ---------------------------------------------------------------------------
# 回路図の描画ヘルパー
# ---------------------------------------------------------------------------


def _draw_to_ax(
    circuit: QuantumCircuit, ax: plt.Axes, title: str, fold: int = 40
) -> None:
    """回路を matplotlib の Axes に描画する。

    Args:
        circuit: 描画する QuantumCircuit。
        ax: 描画先の Axes。
        title: パネルタイトル。
        fold: 1行に並べるゲート数の上限（長い回路を折り返す）。
    """
    fig_circuit = circuit.draw(
        output="mpl",
        fold=fold,
        style={
            "backgroundcolor": "#f8f9fa",
            "linecolor": "#333333",
            "textcolor": "#1a1a2e",
            "gatefacecolor": "#dbeafe",
            "gatetextcolor": "#1e3a8a",
            "barrierfacecolor": "#e0e7ff",
            "creglinecolor": "#6b7280",
            "margin": [0.5, 0.5, 0.5, 0.5],
            "fontsize": 11,
        },
        plot_barriers=True,
        initial_state=True,
    )

    # fig_circuit を Axes に貼り付ける（canvas 経由）
    fig_circuit.canvas.draw()
    img = fig_circuit.canvas.renderer.buffer_rgba()
    import numpy as np

    img_array = np.frombuffer(img, dtype=np.uint8).reshape(
        fig_circuit.canvas.get_width_height()[::-1] + (4,)
    )
    plt.close(fig_circuit)

    ax.imshow(img_array)
    ax.set_title(title, fontsize=12, fontweight="bold", pad=10, color="#1e3a8a")
    ax.axis("off")


def _add_annotation(ax: plt.Axes, text: str) -> None:
    """Axes の下部に説明文を追加する。"""
    ax.text(
        0.5,
        -0.02,
        text,
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=8,
        color="#6b7280",
        wrap=True,
    )


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------


def draw_circuits(
    problem,
    threshold: float,
    output_dir: Path | None = None,
    save: bool = True,
) -> None:
    """3種類の回路図を生成して保存する。

    Args:
        problem: OptimizationProblem のインスタンス。
        threshold: オラクルのコストしきい値。
        output_dir: 保存先ディレクトリ。
        save: True なら PNG 保存、False なら画面表示。
    """
    n_qubits = problem.n_qubits_required()

    condition = make_condition_from_cost(
        cost_fn=problem.cost,
        threshold=threshold,
        feasibility_fn=problem.is_feasible,
    )

    # Oracle・Diffusion を構築
    oracle = build_oracle(n_qubits, condition, verbose=False)
    diffusion = build_diffusion(n_qubits)
    targets = _enumerate_targets(n_qubits, condition)
    n_iter = optimal_iterations(n_qubits, len(targets))

    # ── ① 全体回路（1反復分） ──
    print("  回路図① 全体回路を生成中...")
    circuit_full = build_grover_circuit(n_qubits, oracle, n_iterations=1)
    _save_circuit_figure(
        circuit=circuit_full,
        title=f"Grover 回路（全体 / 1反復）\n"
        f"入力: {n_qubits} qubit  |  最適反復数: {n_iter}  |  正解数: {len(targets)}",
        annotation=(
            "H gates: 入力を均一な重ね合わせ状態に初期化  ｜  "
            "Oracle: 正解の位相を反転  ｜  "
            "Diffusion: 全状態を平均振幅の軸で反射し、正解の確率振幅を増幅"
        ),
        save_path=output_dir / "circuit_overview.png" if output_dir else None,
        fold=25,
    )

    # ── ② Oracle の内部 ──
    print("  回路図② Oracle の内部を生成中...")
    oracle_circuit = QuantumCircuit(n_qubits + 1, name="Oracle 内部")
    oracle_circuit.append(oracle, list(range(n_qubits + 1)))
    oracle_decomposed = oracle_circuit.decompose()
    _save_circuit_figure(
        circuit=oracle_decomposed,
        title="Oracle の内部構造（フェーズキックバック）",
        annotation=(
            "ancilla qubit（最下段）を |−⟩ 状態に初期化し、"
            "正解条件を満たすビット列の位相を −1 倍にする。"
            "CNOT・Toffoli ゲートで条件を評価し、ancilla に書き込む。"
        ),
        save_path=output_dir / "circuit_oracle.png" if output_dir else None,
        fold=30,
    )

    # ── ③ Diffusion の内部 ──
    print("  回路図③ Diffusion の内部を生成中...")
    diff_circuit = QuantumCircuit(n_qubits, name="Diffusion 内部")
    diff_circuit.append(diffusion, list(range(n_qubits)))
    diff_decomposed = diff_circuit.decompose()
    _save_circuit_figure(
        circuit=diff_decomposed,
        title="Diffusion の内部構造（振幅反転）",
        annotation=(
            "H^n → X^n → multi-controlled-Z → X^n → H^n の構成で、"
            "全状態を平均振幅の軸で反射する（振幅増幅）。"
            "これにより正解の確率振幅が反復ごとに増加する。"
        ),
        save_path=output_dir / "circuit_diffusion.png" if output_dir else None,
        fold=30,
    )

    print("  回路図の生成が完了しました。")
    if output_dir:
        print(
            f"  保存先: circuit_overview.png / circuit_oracle.png / circuit_diffusion.png"
        )


def _save_circuit_figure(
    circuit: QuantumCircuit,
    title: str,
    annotation: str,
    save_path: Path | None,
    fold: int = 30,
) -> None:
    """回路を描画してファイルに保存する。"""
    try:
        fig_circuit = circuit.draw(
            output="mpl",
            fold=fold,
            style={
                "backgroundcolor": "#ffffff",
                "gatefacecolor": "#dbeafe",
                "gatetextcolor": "#1e3a8a",
                "textcolor": "#1a1a2e",
                "linecolor": "#374151",
                "fontsize": 10,
                "margin": [1.0, 0.5, 1.0, 0.5],
            },
            plot_barriers=True,
            initial_state=True,
        )

        # タイトルと注釈を追加
        fig_circuit.suptitle(
            title,
            fontsize=11,
            fontweight="bold",
            color="#1e3a8a",
            y=1.01,
        )
        fig_circuit.text(
            0.5,
            -0.01,
            annotation,
            ha="center",
            va="top",
            fontsize=8,
            color="#6b7280",
            transform=fig_circuit.transFigure,
            wrap=True,
        )

        fig_circuit.tight_layout()

        if save_path:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            fig_circuit.savefig(
                str(save_path),
                dpi=150,
                bbox_inches="tight",
                facecolor="#ffffff",
            )
            print(f"    保存: {save_path.name}")
        else:
            plt.show()

        plt.close(fig_circuit)

    except Exception as e:
        print(f"  ⚠️  回路図の生成に失敗しました: {e}")
        import traceback

        traceback.print_exc()
