from __future__ import annotations

import random
from pathlib import Path

import numpy as np

import config
from classical.brute_force import solve as bf_solve
from problems.routing import VehicleRoutingProblem
from quantum.grover import solve as grover_solve
from quantum.noise import (
    build_combined_model,
    build_depolarizing_model,
    build_ideal_model,
    build_thermal_model,
)
from benchmark.metrics import compare
from visualizer.animation import run as run_animation
from visualizer.state_plotter import run as run_race


# ---------------------------------------------------------------------------
# ノイズモデルの選択
# ---------------------------------------------------------------------------


def _build_noise_model():
    """config.NOISE_MODEL に応じてノイズモデルを返す。

    Returns:
        NoiseModel または None（理想の場合）。

    Raises:
        ValueError: config.NOISE_MODEL が不正な値の場合。
    """
    mode = config.NOISE_MODEL

    if mode == "ideal":
        return build_ideal_model()

    if mode == "depol":
        return build_depolarizing_model()

    if mode == "thermal":
        return build_thermal_model(gate_time_1q=config.GATE_TIME_1Q)

    if mode == "combined":
        return build_combined_model(
            device=config.DEVICE,
            gate_time_1q=config.GATE_TIME_1Q,
        )

    raise ValueError(
        f"不明なノイズモデル設定: {mode!r}。"
        "'ideal' / 'depol' / 'thermal' / 'combined' のいずれかを指定してください。"
    )


# ---------------------------------------------------------------------------
# 結果の表示
# ---------------------------------------------------------------------------


def _print_result(label: str, result: dict) -> None:
    """solve() の返り値を整形して表示する。"""
    print(f"\n{'=' * 50}")
    print(f"  {label}")
    print(f"{'=' * 50}")

    status = result.get("status")
    if status != "ok":
        print(f"  ステータス : {status}")
        if "error" in result:
            print(f"  エラー     : {result['error']}")
        return

    print(f"  ステータス       : {status}")
    print(f"  最適ルート       : {result['best_route']}")
    print(f"  最小コスト       : {result['best_cost']}")
    print(f"  実行時間         : {result['elapsed_sec']:.4f} 秒")

    # 古典固有
    if "n_evaluated" in result:
        print(f"  評価した解の数   : {result['n_evaluated']} / {result['n_total']}")

    # 量子固有
    if "n_iterations" in result:
        print(f"  Grover 反復回数  : {result['n_iterations']}")
        print(f"  回路深さ         : {result['circuit_depth']}")
        print(f"  ancilla モード   : {result.get('mode')}")
        print(f"  使用量子ビット数 : {result.get('n_qubits_total')}")

    if "top_k" in result:
        print(f"\n  --- 上位 {config.TOP_K} 件の測定結果 ---")
        for i, entry in enumerate(result["top_k"], 1):
            print(
                f"  {i}. {entry['bitstring']}"
                f"  回数={entry['count']}"
                f"  確率={entry['probability']:.3f}"
            )

    # compare モード固有
    if "ancilla_comparison" in result:
        print("\n  --- ancilla モード比較 ---")
        for mode_name, info in result["ancilla_comparison"].items():
            print(
                f"  [{mode_name}]"
                f"  補助ビット数={info['n_ancilla']}"
                f"  総量子ビット数={info['n_qubits_total']}"
                f"  回路深さ={info['circuit_depth']}"
            )


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------


def main() -> None:
    # --- 乱数シード固定 ---
    random.seed(config.SEED)
    np.random.seed(config.SEED)

    # --- 問題のセットアップ ---
    problem = VehicleRoutingProblem(
        distance_matrix=config.DISTANCE_MATRIX,
        city_names=config.CITY_NAMES,
    )
    print(problem.describe())
    print(f"\nノイズモデル     : {config.NOISE_MODEL}")
    print(f"コストのしきい値 : {config.COST_THRESHOLD}")

    # --- 古典：全探索 ---
    bf_result = bf_solve(problem)
    _print_result("古典（全探索）", bf_result)

    # --- 量子：Grover ---
    noise_model = _build_noise_model()
    grover_result = grover_solve(
        problem=problem,
        shots=config.SHOTS,
        threshold=config.COST_THRESHOLD,
        top_k=config.TOP_K,
        ancilla_mode=config.ANCILLA_MODE,
        noise_model=noise_model,
    )
    _print_result(f"量子（Grover / {config.NOISE_MODEL}）", grover_result)

    # --- ベンチマーク比較 ---
    if bf_result.get("status") == "ok" and grover_result.get("status") == "ok":
        report = compare(
            bf_result=bf_result,
            grover_result=grover_result,
            n_qubits=problem.n_qubits_required(),
        )
        print(f"\n{report['summary']}")

    # --- 可視化 ---
    # 出力先フォルダ
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    print("\n確率変化アニメーションを生成中...")
    run_animation(
        problem=problem,
        threshold=config.COST_THRESHOLD,
        shots=config.SHOTS,
        noise_model=noise_model,
        save_path=output_dir / "grover_animation.gif",
        fps=config.ANIMATION_FPS,
    )

    print("\n古典 vs 量子 レースアニメーションを生成中...")
    run_race(
        problem=problem,
        threshold=config.COST_THRESHOLD,
        shots=config.SHOTS,
        noise_model=noise_model,
        seed=config.SEED,
        save_path=output_dir / "classical_vs_quantum.gif",
        fps=config.ANIMATION_FPS,
    )

    print("\nすべての出力が完了しました。")
    print(f"保存先: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
