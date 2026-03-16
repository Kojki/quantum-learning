from __future__ import annotations

from web_app import get_config_from_web

import random
from pathlib import Path

import numpy as np

from classical.brute_force import solve as bf_solve
from problems.routing import VehicleRoutingProblem
from quantum.grover import solve as grover_solve, solve_iterative
from quantum.noise import (
    DEVICE_PRESETS,
    build_combined_model,
    build_depolarizing_model,
    build_ideal_model,
    build_thermal_model,
    build_readout_model,
)
from benchmark.metrics import compare
from visualizer.animation import run as run_animation
from visualizer.state_plotter import run as run_race
from geo.geocoder import geocode_cities
from geo.distance import build_distance_matrix
from geo.map_plotter import plot_route


# ---------------------------------------------------------------------------
# ノイズモデルの選択
# ---------------------------------------------------------------------------


def _build_noise_model(cfg: dict):
    """設定辞書に応じてノイズモデルを返す。

    ノイズモデルの区分:
        ideal    : ノイズなし（理想シミュレーター）
        depol    : 脱分極ノイズのみ
        thermal  : 熱緩和ノイズのみ
        readout  : 読み出しエラーのみ
        combined : 上記3種を合わせた複合ノイズ
    """
    mode = cfg["noise_model"]
    device = cfg.get("device", "eagle_r3")
    preset = DEVICE_PRESETS.get(device, DEVICE_PRESETS["eagle_r3"])

    if mode == "ideal":
        return build_ideal_model()

    if mode == "depol":
        return build_depolarizing_model(
            depol_1q=preset["depol_1q"],
            depol_2q=preset["depol_2q"],
        )

    if mode == "thermal":
        return build_thermal_model(
            t1=preset["t1"],
            t2=preset["t2"],
            gate_time_1q=preset["gate_time_1q"],
            gate_time_2q=preset["gate_time_2q"],
            gate_time_measure=preset["gate_time_measure"],
        )

    if mode == "readout":
        return build_readout_model(
            p_meas1_prep0=preset["p_meas1_prep0"],
            p_meas0_prep1=preset["p_meas0_prep1"],
        )

    if mode == "combined":
        return build_combined_model(device=device)

    raise ValueError(
        f"不明なノイズモデル設定: {mode!r}。"
        "'ideal' / 'depol' / 'thermal' / 'readout' / 'combined' のいずれかを指定してください。"
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

    if "n_grover_calls" in result:
        print(f"  Grover 実行回数  : {result['n_grover_calls']}")
        if "history" in result:
            print(f"\n  --- 探索の履歴 ---")
            for entry in result["history"]:
                mark = "✅" if entry["improved"] else "  "
                print(
                    f"  {mark} 反復 {entry['iteration']:2d}  "
                    f"コスト: {entry['threshold']:.1f}  "
                    f"ルート: {entry['route']}"
                )

    if "n_iterations" in result:
        print(f"  Grover 反復回数  : {result['n_iterations']}")
        print(f"  回路深さ         : {result['circuit_depth']}")
        print(f"  ancilla モード   : {result.get('mode')}")
        print(f"  使用量子ビット数 : {result.get('n_qubits_total')}")

    if "top_k" in result and result["top_k"]:
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
    cfg = get_config_from_web()

    random.seed(cfg["seed"])
    np.random.seed(cfg["seed"])

    coords = None
    if cfg["use_geo"]:
        print("\n座標を取得中...")
        coords = geocode_cities(cfg["city_names"])
        cfg["city_names"] = list(coords.keys())
        cfg["distance_matrix"], cfg["city_names"] = build_distance_matrix(coords)

    problem = VehicleRoutingProblem(
        distance_matrix=cfg["distance_matrix"],
        city_names=cfg["city_names"],
    )
    print()
    print(problem.describe())
    print(f"\nノイズモデル     : {cfg['noise_model']}")

    bf_result = bf_solve(problem)
    _print_result("古典（全探索）", bf_result)

    noise_model = _build_noise_model(cfg)
    print("\nDurr-Hoyer アルゴリズムで探索中...")
    grover_result = solve_iterative(
        problem=problem,
        shots=cfg["shots"],
        max_iterations=cfg["max_iterations"],
        top_k=5,
        ancilla_mode=cfg["ancilla_mode"],
        noise_model=noise_model,
        seed=cfg["seed"],
        verbose=True,
    )
    _print_result(f"量子（Durr-Hoyer / {cfg['noise_model']}）", grover_result)

    if bf_result.get("status") == "ok" and grover_result.get("status") == "ok":
        report = compare(
            bf_result=bf_result,
            grover_result=grover_result,
            n_qubits=problem.n_qubits_required(),
        )
        print(f"\n{report['summary']}")

    output_dir = Path(cfg["output_dir"]) if cfg["output_dir"] else None
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)

    if grover_result.get("status") != "ok":
        print("\n⚠️  Grover が解を見つけられなかったため、可視化をスキップします。")
        return

    if coords is not None:
        print("\n最適ルートを地図上に描画中...")
        plot_route(
            coords=coords,
            best_route=grover_result["best_route"],
            title=f"Grover が見つけた最短ルート（{cfg['noise_model']}）",
            save_path=output_dir / "route_map.png" if output_dir else None,
        )

    print("\n確率変化アニメーションを生成中...")
    run_animation(
        problem=problem,
        threshold=grover_result["best_cost"],
        shots=cfg["shots"],
        noise_model=noise_model,
        save_path=output_dir / "grover_animation.gif" if output_dir else None,
        fps=2,
    )

    print("\n古典 量子 比較アニメーションを生成中...")
    run_race(
        problem=problem,
        threshold=grover_result["best_cost"],
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
