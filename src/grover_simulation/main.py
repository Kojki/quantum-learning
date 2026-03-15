from __future__ import annotations

import random
from pathlib import Path

import numpy as np

from input_handler import select_config_mode
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


def _build_noise_model(cfg: dict):
    """設定辞書に応じてノイズモデルを返す。"""
    mode = cfg["noise_model"]

    if mode == "ideal":
        return build_ideal_model()
    if mode == "depol":
        return build_depolarizing_model()
    if mode == "thermal":
        return build_thermal_model(gate_time_1q=cfg["gate_time_1q"])
    if mode == "combined":
        return build_combined_model(
            device=cfg["device"],
            gate_time_1q=cfg["gate_time_1q"],
        )

    raise ValueError(
        f"不明なノイズモデル設定: {mode!r}。"
        "'ideal' / 'depol' / 'thermal' / 'combined' のいずれかを指定してください。"
    )


# ---------------------------------------------------------------------------
# 結果の表示
# ---------------------------------------------------------------------------


def _print_result(label: str, result: dict, top_k: int = 5) -> None:
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

    if "n_evaluated" in result:
        print(f"  評価した解の数   : {result['n_evaluated']} / {result['n_total']}")

    if "n_iterations" in result:
        print(f"  Grover 反復回数  : {result['n_iterations']}")
        print(f"  回路深さ         : {result['circuit_depth']}")
        print(f"  ancilla モード   : {result.get('mode')}")
        print(f"  使用量子ビット数 : {result.get('n_qubits_total')}")

    if "top_k" in result:
        print(f"\n  --- 上位 {top_k} 件の測定結果 ---")
        for i, entry in enumerate(result["top_k"], 1):
            print(
                f"  {i}. {entry['bitstring']}"
                f"  回数={entry['count']}"
                f"  確率={entry['probability']:.3f}"
            )

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
    # --- 設定の読み込み ---
    cfg = select_config_mode()

    # --- 乱数シード固定 ---
    random.seed(cfg["seed"])
    np.random.seed(cfg["seed"])

    # --- 問題のセットアップ ---
    problem = VehicleRoutingProblem(
        distance_matrix=cfg["distance_matrix"],
        city_names=cfg["city_names"],
    )
    print()
    print(problem.describe())
    print(f"\nノイズモデル     : {cfg['noise_model']}")
    print(f"コストのしきい値 : {cfg['cost_threshold']}")

    # --- 古典：全探索 ---
    bf_result = bf_solve(problem)
    _print_result("古典（全探索）", bf_result)

    # --- 量子：Grover ---
    noise_model = _build_noise_model(cfg)
    grover_result = grover_solve(
        problem=problem,
        shots=cfg["shots"],
        threshold=cfg["cost_threshold"],
        top_k=5,
        ancilla_mode=cfg["ancilla_mode"],
        noise_model=noise_model,
    )
    _print_result(f"量子（Grover / {cfg['noise_model']}）", grover_result)

    # --- ベンチマーク比較 ---
    if bf_result.get("status") == "ok" and grover_result.get("status") == "ok":
        report = compare(
            bf_result=bf_result,
            grover_result=grover_result,
            n_qubits=problem.n_qubits_required(),
        )
        print(f"\n{report['summary']}")

    # --- 可視化 ---
    output_dir = Path(cfg["output_dir"]) if cfg["output_dir"] else None

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)

    print("\n確率変化アニメーションを生成中...")
    run_animation(
        problem=problem,
        threshold=cfg["cost_threshold"],
        shots=cfg["shots"],
        noise_model=noise_model,
        save_path=output_dir / "grover_animation.gif" if output_dir else None,
        fps=2,
    )

    print("\n古典 vs 量子 レースアニメーションを生成中...")
    run_race(
        problem=problem,
        threshold=cfg["cost_threshold"],
        shots=cfg["shots"],
        noise_model=noise_model,
        seed=cfg["seed"],
        save_path=output_dir / "classical_vs_quantum.gif" if output_dir else None,
        fps=2,
    )

    print("\nすべての出力が完了しました。")
    if output_dir:
        print(f"保存先: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
