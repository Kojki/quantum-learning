from __future__ import annotations

from web_app import get_config_from_web

import json
import math
import random
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

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

ALL_NOISE_MODELS = ["ideal", "depol", "thermal", "readout", "combined"]


def _build_noise_model(cfg: dict):
    mode = cfg["noise_model"]
    device = cfg.get("device", "eagle_r3")
    preset = DEVICE_PRESETS.get(device, DEVICE_PRESETS["eagle_r3"])

    if mode == "ideal":
        return build_ideal_model()
    if mode == "depol":
        return build_depolarizing_model(
            depol_1q=preset["depol_1q"], depol_2q=preset["depol_2q"]
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
            p_meas1_prep0=preset["p_meas1_prep0"], p_meas0_prep1=preset["p_meas0_prep1"]
        )
    if mode == "combined":
        return build_combined_model(device=device)

    raise ValueError(
        f"不明なノイズモデル設定: {mode!r}。{ALL_NOISE_MODELS} のいずれかを指定してください。"
    )


# ---------------------------------------------------------------------------
# 結果の表示
# ---------------------------------------------------------------------------


def _print_result(label: str, result: dict, top_k: int = 5) -> None:
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
                    f"  {mark} 反復 {entry['iteration']:2d}  コスト: {entry['threshold']:.1f}  ルート: {entry['route']}"
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
                f"  {i}. {entry['bitstring']}  回数={entry['count']}  確率={entry['probability']:.3f}"
            )
    if "ancilla_comparison" in result:
        print("\n  --- ancilla モード比較 ---")
        for mode_name, info in result["ancilla_comparison"].items():
            print(
                f"  [{mode_name}]  補助ビット数={info['n_ancilla']}  総量子ビット数={info['n_qubits_total']}  回路深さ={info['circuit_depth']}"
            )


# ---------------------------------------------------------------------------
# 結果のファイル出力
# ---------------------------------------------------------------------------


def _save_result(
    output_dir: Path, bf_result: dict, grover_result: dict, cfg: dict
) -> None:
    """実行結果を JSON ファイルに保存する。"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    noise = cfg.get("noise_model", "unknown")
    filename = output_dir / f"result_{noise}_{timestamp}.json"
    payload = {
        "timestamp": timestamp,
        "config": {k: v for k, v in cfg.items() if k != "distance_matrix"},
        "classical": bf_result,
        "quantum": {k: v for k, v in grover_result.items()},
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
    print(f"  結果を保存しました: {filename.name}")


# ---------------------------------------------------------------------------
# 成功率グラフ（反復回数 vs 正解確率）
# ---------------------------------------------------------------------------


def _plot_success_rate(
    problem: VehicleRoutingProblem,
    best_cost: float,
    shots: int,
    noise_model,
    noise_label: str,
    save_path: Path | None,
) -> None:
    """反復回数 1〜R_max での正解確率の推移を折れ線グラフで保存する。"""
    n = problem.n_cities
    factorial = math.factorial(n - 1)
    r_opt = max(1, round(math.pi / 4 * math.sqrt(factorial)))
    r_max = min(r_opt * 3, 50)

    iterations = list(range(1, r_max + 1))
    success_rates = []

    print(f"  成功率グラフ生成中（1〜{r_max}反復）...")
    for r in iterations:
        result = grover_solve(
            problem=problem, n_iterations=r, shots=shots, noise_model=noise_model
        )
        if result.get("status") == "ok" and result.get("top_k"):
            success_prob = sum(
                e["probability"]
                for e in result["top_k"]
                if abs(e.get("cost", float("inf")) - best_cost) < 1e-6
            )
        else:
            success_prob = 0.0
        success_rates.append(success_prob)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(
        iterations,
        success_rates,
        marker="o",
        markersize=4,
        linewidth=1.5,
        color="#2563eb",
        label=noise_label,
    )
    ax.axvline(
        x=r_opt,
        color="#dc2626",
        linestyle="--",
        linewidth=1,
        label=f"最適反復回数 R={r_opt}",
    )
    ax.set_xlabel("Grover 反復回数")
    ax.set_ylabel("正解確率")
    ax.set_title(f"反復回数と正解確率の関係（{noise_label}）")
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1.0))
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)
        print(f"  成功率グラフを保存: {save_path.name}")
    else:
        plt.show()
    plt.close(fig)


# ---------------------------------------------------------------------------
# ノイズモデル一括比較
# ---------------------------------------------------------------------------


def _run_noise_comparison(
    problem: VehicleRoutingProblem,
    cfg: dict,
    bf_result: dict,
    output_dir: Path | None,
) -> None:
    """全ノイズモデルを一括実行し、結果を比較表示・保存する。"""
    print(f"\n{'=' * 50}")
    print("  ノイズモデル一括比較")
    print(f"{'=' * 50}")

    comparison_rows = []
    for noise in ALL_NOISE_MODELS:
        run_cfg = {**cfg, "noise_model": noise}
        noise_model = _build_noise_model(run_cfg)
        print(f"\n  [{noise}] 実行中...")
        try:
            result = solve_iterative(
                problem=problem,
                shots=cfg["shots"],
                max_iterations=cfg["max_iterations"],
                top_k=5,
                ancilla_mode=cfg["ancilla_mode"],
                noise_model=noise_model,
                seed=cfg["seed"],
                verbose=False,
            )
        except Exception as e:
            print(f"  ⚠️  [{noise}] 実行中にエラーが発生しました: {e}")
            result = {"status": "error", "error": str(e)}

        if result.get("status") == "ok":
            bf_cost = bf_result.get("best_cost", float("nan"))
            q_cost = result["best_cost"]
            match = (
                abs(q_cost - bf_cost) < 1e-6
                if bf_result.get("status") == "ok"
                else None
            )
            row = {
                "noise_model": noise,
                "best_cost": q_cost,
                "optimal": match,
                "elapsed_sec": result["elapsed_sec"],
                "n_grover_calls": result.get("n_grover_calls"),
            }
        else:
            row = {
                "noise_model": noise,
                "best_cost": None,
                "optimal": False,
                "elapsed_sec": None,
                "n_grover_calls": None,
            }
        comparison_rows.append(row)

    # 比較表を表示
    print(
        f"\n  {'ノイズモデル':<12} {'最小コスト':>10} {'最適解':>6} {'実行時間':>10} {'Grover呼出':>10}"
    )
    print(f"  {'-' * 56}")
    for r in comparison_rows:
        cost_str = f"{r['best_cost']:.1f}" if r["best_cost"] is not None else "失敗"
        optimal_str = "✅" if r["optimal"] else ("❌" if r["optimal"] is False else "-")
        elapsed_str = (
            f"{r['elapsed_sec']:.3f}s" if r["elapsed_sec"] is not None else "-"
        )
        calls_str = str(r["n_grover_calls"]) if r["n_grover_calls"] is not None else "-"
        print(
            f"  {r['noise_model']:<12} {cost_str:>10} {optimal_str:>6} {elapsed_str:>10} {calls_str:>10}"
        )

    if output_dir:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = output_dir / f"noise_comparison_{timestamp}.json"
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(comparison_rows, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n  比較結果を保存しました: {save_path.name}")


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------


def main() -> None:
    cfg = get_config_from_web()

    random.seed(cfg["seed"])
    np.random.seed(cfg["seed"])

    # ── 座標取得 ──
    coords = None
    if cfg["use_geo"]:
        print("\n座標を取得中...")
        try:
            coords = geocode_cities(cfg["city_names"])
        except RuntimeError as e:
            print(f"\n❌ 座標取得エラー: {e}")
            sys.exit(1)
        cfg["city_names"] = list(coords.keys())
        try:
            cfg["distance_matrix"], cfg["city_names"] = build_distance_matrix(coords)
        except Exception as e:
            print(f"\n❌ 距離行列の構築に失敗しました: {e}")
            sys.exit(1)

    # ── 都市数チェック ──
    if len(cfg.get("city_names", [])) < 2:
        print("❌ 都市数が不足しています（最低2都市必要です）。")
        sys.exit(1)

    # ── 問題の生成 ──
    try:
        problem = VehicleRoutingProblem(
            distance_matrix=cfg["distance_matrix"],
            city_names=cfg["city_names"],
        )
    except Exception as e:
        print(f"\n❌ 問題の生成に失敗しました: {e}")
        sys.exit(1)

    print()
    print(problem.describe())
    print(f"\nノイズモデル     : {cfg['noise_model']}")

    # ── 出力ディレクトリの準備 ──
    output_dir = Path(cfg["output_dir"]) if cfg.get("output_dir") else None
    if output_dir is not None:
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"\n⚠️  出力ディレクトリの作成に失敗しました: {e}")
            print("   ウィンドウ表示のみで続行します。")
            output_dir = None

    # ── 古典（全探索） ──
    bf_result = bf_solve(problem)
    _print_result("古典（全探索）", bf_result)

    # ── ノイズモデル一括比較モード ──
    if cfg["noise_model"] == "all":
        _run_noise_comparison(problem, cfg, bf_result, output_dir)
        print("\nすべての出力が完了しました。")
        if output_dir:
            print(f"保存先: {output_dir.resolve()}")
        return

    # ── 通常モード ──
    try:
        noise_model = _build_noise_model(cfg)
    except ValueError as e:
        print(f"\n❌ ノイズモデルのエラー: {e}")
        sys.exit(1)

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

    if output_dir:
        _save_result(output_dir, bf_result, grover_result, cfg)

    if grover_result.get("status") != "ok":
        print("\n⚠️  Grover が解を見つけられなかったため、可視化をスキップします。")
        return

    if coords is not None:
        print("\n最適ルートを地図上に描画中...")
        try:
            plot_route(
                coords=coords,
                best_route=grover_result["best_route"],
                title=f"Grover が見つけた最短ルート（{cfg['noise_model']}）",
                save_path=output_dir / "route_map.png" if output_dir else None,
            )
        except Exception as e:
            print(f"  ⚠️  地図描画に失敗しました: {e}")

    print("\n成功率グラフを生成中...")
    try:
        _plot_success_rate(
            problem=problem,
            best_cost=grover_result["best_cost"],
            shots=cfg["shots"],
            noise_model=noise_model,
            noise_label=cfg["noise_model"],
            save_path=output_dir / "success_rate.png" if output_dir else None,
        )
    except Exception as e:
        print(f"  ⚠️  成功率グラフの生成に失敗しました: {e}")

    print("\n確率変化アニメーションを生成中...")
    try:
        run_animation(
            problem=problem,
            threshold=grover_result["best_cost"],
            shots=cfg["shots"],
            noise_model=noise_model,
            save_path=output_dir / "grover_animation.gif" if output_dir else None,
            fps=2,
        )
    except Exception as e:
        print(f"  ⚠️  アニメーション生成に失敗しました: {e}")

    print("\n古典 量子 比較アニメーションを生成中...")
    try:
        run_race(
            problem=problem,
            threshold=grover_result["best_cost"],
            shots=cfg["shots"],
            noise_model=noise_model,
            seed=cfg["seed"],
            save_path=output_dir / "classical_vs_quantum.gif" if output_dir else None,
            fps=2,
        )
    except Exception as e:
        print(f"  ⚠️  比較アニメーション生成に失敗しました: {e}")

    print("\nすべての出力が完了しました。")
    if output_dir:
        print(f"保存先: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
