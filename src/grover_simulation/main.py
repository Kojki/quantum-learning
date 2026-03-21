from __future__ import annotations

from web_app import get_config_from_web

import base64
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
import matplotlib.font_manager as fm


def _setup_fonts():
    candidates = [
        "MS Gothic",
        "Yu Gothic",
        "Meiryo",
        "Hiragino Sans",
        "Hiragino Kaku Gothic Pro",
        "Noto Sans CJK JP",
        "IPAexGothic",
        "IPAGothic",
    ]
    available = {f.name for f in fm.fontManager.ttflist}
    for font in candidates:
        if font in available:
            plt.rcParams["font.family"] = font
            return


_setup_fonts()

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
from visualizer.amplitude_visualizer import run as run_amplitude
from visualizer.animation import run as run_animation
from visualizer.bloch_visualizer import run as run_bloch
from visualizer.circuit_drawer import draw_circuits
from visualizer.state_plotter import run as run_race
from geo.geocoder import geocode_cities
from geo.distance import build_distance_matrix
from geo.map_plotter import plot_route, plot_route_from_matrix


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
# 成功率グラフ
# ---------------------------------------------------------------------------


def _plot_success_rate(
    problem: VehicleRoutingProblem,
    best_cost: float,
    shots: int,
    noise_model,
    noise_label: str,
    save_path: Path | None,
) -> None:
    n = problem.n_cities
    factorial = math.factorial(n - 1)
    r_opt = max(1, round(math.pi / 4 * math.sqrt(factorial)))
    r_max = min(r_opt * 3, 50)

    iterations = list(range(1, r_max + 1))
    success_rates = []

    print(f"  成功率グラフ生成中（1〜{r_max}反復）...")
    for r in iterations:
        eps = max(1.0, best_cost * 1e-6) if best_cost > 0 else 1.0
        result = grover_solve(
            problem=problem,
            n_iterations=r,
            shots=shots,
            threshold=best_cost + eps,
            noise_model=noise_model,
        )
        if result.get("status") == "ok" and result.get("top_k"):
            success_prob = 0.0
            for e in result["top_k"]:
                bs = e.get("bitstring", "")
                if problem.is_feasible(bs):
                    cost = problem.cost(bs)
                    if cost <= best_cost + 1e-6:
                        success_prob += e["probability"]
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
        label=f"Optimal R={r_opt}",
    )
    ax.set_xlabel("Grover Iterations")
    ax.set_ylabel("Success Rate")
    ax.set_title(f"Success Rate vs Iterations ({noise_label})")
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
# ノイズモデル比較可視化
# ---------------------------------------------------------------------------

_NOISE_COLORS = {
    "ideal": "#2563eb",
    "depol": "#d97706",
    "thermal": "#16a34a",
    "readout": "#9333ea",
    "combined": "#dc2626",
}


def _plot_noise_comparison(
    comparison_rows: list[dict],
    bf_best_cost: float,
    output_dir: Path | None,
) -> None:
    valid = [r for r in comparison_rows if r["best_cost"] is not None]
    if not valid:
        print("  ⚠️  比較グラフ: 有効なデータがありません。")
        return

    labels = [r["noise_model"] for r in valid]
    costs = [r["best_cost"] for r in valid]
    times = [r["elapsed_sec"] for r in valid]
    optimals = [r["optimal"] for r in valid]
    colors = [_NOISE_COLORS.get(l, "#888888") for l in labels]

    fig, ax1 = plt.subplots(figsize=(9, 5))
    bars = ax1.bar(labels, costs, color=colors, alpha=0.75, width=0.5, label="Min Cost")
    for bar, ok in zip(bars, optimals):
        mark = "★" if ok else "✗"
        color = "#16a34a" if ok else "#dc2626"
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(costs) * 0.02,
            mark,
            ha="center",
            va="bottom",
            fontsize=14,
            color=color,
            fontweight="bold",
        )
    ax1.axhline(
        bf_best_cost,
        color="#374151",
        linestyle="--",
        linewidth=1.2,
        label=f"Classical Optimal: {bf_best_cost:.1f}",
    )
    ax1.set_ylabel("Min Cost")
    ax1.set_ylim(0, max(costs) * 1.25 if max(costs) > 0 else 1)
    ax1.set_xlabel("Noise Model")
    ax1.set_title("Noise Model Comparison: Min Cost & Elapsed Time")

    ax2 = ax1.twinx()
    ax2.plot(
        labels,
        times,
        color="#6b7280",
        marker="o",
        linewidth=1.5,
        markersize=6,
        linestyle="--",
        label="Elapsed Time",
    )
    ax2.set_ylabel("Elapsed Time (s)")
    ax2.set_ylim(0, max(times) * 1.4 if max(times) > 0 else 1)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=9)
    fig.tight_layout()

    if output_dir:
        save_path = output_dir / "noise_comparison.png"
        fig.savefig(save_path, dpi=150)
        print(f"  比較棒グラフを保存: {save_path.name}")
    else:
        plt.show()
    plt.close(fig)


def _plot_success_rate_comparison(
    problem: VehicleRoutingProblem,
    best_cost: float,
    shots: int,
    cfg: dict,
    output_dir: Path | None,
) -> None:
    n = problem.n_cities
    factorial = math.factorial(n - 1)
    r_opt = max(1, round(math.pi / 4 * math.sqrt(factorial)))
    r_max = min(r_opt * 3, 30)
    iterations = list(range(1, r_max + 1))

    fig, ax = plt.subplots(figsize=(10, 5))

    for noise in ALL_NOISE_MODELS:
        run_cfg = {**cfg, "noise_model": noise}
        try:
            noise_model = _build_noise_model(run_cfg)
        except Exception as e:
            print(f"  ⚠️  [{noise}] ノイズモデル構築失敗: {e}")
            continue

        success_rates = []
        print(f"  [{noise}] 成功率計算中（1〜{r_max}反復）...")
        eps = max(1.0, best_cost * 1e-6) if best_cost > 0 else 1.0
        for r in iterations:
            try:
                result = grover_solve(
                    problem=problem,
                    n_iterations=r,
                    shots=shots,
                    threshold=best_cost + eps,
                    noise_model=noise_model,
                )
                if result.get("status") == "ok" and result.get("top_k"):
                    prob = sum(
                        e["probability"]
                        for e in result["top_k"]
                        if abs(e.get("cost", float("inf")) - best_cost) < 1e-6
                    )
                else:
                    prob = 0.0
            except Exception:
                prob = 0.0
            success_rates.append(prob)

        color = _NOISE_COLORS.get(noise, "#888888")
        ax.plot(
            iterations,
            success_rates,
            marker="o",
            markersize=3,
            linewidth=1.5,
            color=color,
            label=noise,
        )

    ax.axvline(
        x=r_opt,
        color="#374151",
        linestyle="--",
        linewidth=1,
        label=f"Optimal R={r_opt}",
    )
    ax.set_xlabel("Grover Iterations")
    ax.set_ylabel("Success Rate")
    ax.set_title("Success Rate vs Iterations by Noise Model")
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1.0))
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    if output_dir:
        save_path = output_dir / "success_rate_comparison.png"
        fig.savefig(save_path, dpi=150)
        print(f"  成功率比較グラフを保存: {save_path.name}")
    else:
        plt.show()
    plt.close(fig)


# ---------------------------------------------------------------------------
# HTMLレポート生成
# ---------------------------------------------------------------------------


def _img_to_base64(path) -> str | None:
    if path is None or not path.exists():
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _generate_html_report(
    cfg, bf_result, grover_result, comparison_rows, output_dir
) -> None:
    if output_dir is None:
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    mode = "all" if comparison_rows is not None else cfg.get("noise_model", "unknown")

    def img_tag(filename, alt, width="100%"):
        b64 = _img_to_base64(output_dir / filename)
        if b64 is None:
            return f'<p style="color:#888;">({alt} not generated)</p>'
        return f'<img src="data:image/png;base64,{b64}" alt="{alt}" style="width:{width};border-radius:8px;border:1px solid #e0e0e0;">'

    def gif_tag(filename, alt):
        path = output_dir / filename
        if not path.exists():
            return f'<p style="color:#888;">({alt} not generated)</p>'
        b64 = _img_to_base64(path)
        if b64 is None:
            return f'<p style="color:#888;">({alt} not generated)</p>'
        return f'<img src="data:image/gif;base64,{b64}" alt="{alt}" style="width:100%;border-radius:8px;border:1px solid #e0e0e0;">'

    def matrix_table():
        dm = cfg.get("distance_matrix", [])
        names = cfg.get("city_names", [])
        if not dm or not names:
            return "<p>N/A</p>"
        rows = "<tr><th></th>" + "".join(f"<th>{n}</th>" for n in names) + "</tr>"
        for i, row in enumerate(dm):
            cells = "".join(
                (
                    '<td style="background:#f7f7f7;color:#aaa;">0</td>'
                    if i == j
                    else f"<td>{v:.1f}</td>"
                )
                for j, v in enumerate(row)
            )
            rows += f"<tr><th>{names[i]}</th>{cells}</tr>"
        return f'<table class="matrix">{rows}</table>'

    def history_table(result):
        history = result.get("history", [])
        if not history:
            return "<p>No history</p>"
        rows = "<tr><th>Iter</th><th>Cost</th><th>Route</th><th>Improved</th></tr>"
        for h in history:
            mark = "★" if h.get("improved") else "—"
            color = "#16a34a" if h.get("improved") else "#888"
            rows += (
                f"<tr><td>{h['iteration']}</td><td>{h['threshold']:.1f}</td>"
                f"<td>{h.get('route','—')}</td>"
                f'<td style="color:{color};font-weight:bold;">{mark}</td></tr>'
            )
        return f'<table class="data">{rows}</table>'

    def comparison_table(rows):
        header = "<tr><th>Noise Model</th><th>Best Cost</th><th>Optimal</th><th>Time (s)</th><th>Grover Calls</th></tr>"
        body = ""
        for r in rows:
            cost = f"{r['best_cost']:.1f}" if r["best_cost"] is not None else "—"
            opt = (
                '<span style="color:#16a34a;font-weight:bold;">★ YES</span>'
                if r["optimal"]
                else '<span style="color:#dc2626;">✗ NO</span>'
            )
            t = f"{r['elapsed_sec']:.3f}" if r["elapsed_sec"] is not None else "—"
            calls = str(r["n_grover_calls"]) if r["n_grover_calls"] is not None else "—"
            body += f'<tr><td><code>{r["noise_model"]}</code></td><td>{cost}</td><td>{opt}</td><td>{t}</td><td>{calls}</td></tr>'
        return f'<table class="data">{header}{body}</table>'

    bf_ok = bf_result.get("status") == "ok"
    bf_cost = bf_result.get("best_cost", 0) if bf_ok else 0
    bf_route = bf_result.get("best_route", "—") if bf_ok else "—"
    bf_time = f"{bf_result.get('elapsed_sec', 0):.4f} s" if bf_ok else "—"
    bf_eval = (
        f"{bf_result.get('n_evaluated',0):,} / {bf_result.get('n_total',0):,}"
        if bf_ok
        else "—"
    )
    n_cities = len(cfg.get("city_names", []))
    n_routes = 1
    for i in range(2, n_cities):
        n_routes *= i

    quantum_section = ""
    if grover_result and grover_result.get("status") == "ok":
        q_cost = grover_result.get("best_cost", 0)
        q_route = grover_result.get("best_route", "—")
        q_time = f"{grover_result.get('elapsed_sec', 0):.4f} s"
        q_calls = grover_result.get("n_grover_calls", "—")
        match = abs(q_cost - bf_cost) < 1e-6 if bf_ok else False
        match_b = (
            '<span class="badge ok">★ Optimal Match</span>'
            if match
            else '<span class="badge ng">✗ No Match</span>'
        )
        quantum_section = (
            f'<section><h2>Quantum Result (Durr-Hoyer / {cfg.get("noise_model","—")})</h2>'
            f'<div class="kv-grid">'
            f'<div class="kv"><span>Best Route</span><strong>{q_route}</strong></div>'
            f'<div class="kv"><span>Min Cost</span><strong>{q_cost:.1f}</strong></div>'
            f'<div class="kv"><span>Elapsed</span><strong>{q_time}</strong></div>'
            f'<div class="kv"><span>Grover Calls</span><strong>{q_calls}</strong></div>'
            f'<div class="kv"><span>Match Classical</span><strong>{match_b}</strong></div>'
            f"</div><h3>Search History</h3>{history_table(grover_result)}</section>"
            f'<section><h2>Success Rate</h2>{img_tag("success_rate.png","Success Rate Graph","80%")}</section>'
        )

    comparison_section = ""
    if comparison_rows:
        comparison_section = (
            f"<section><h2>Noise Model Comparison</h2>{comparison_table(comparison_rows)}"
            f'<h3>Cost &amp; Time</h3>{img_tag("noise_comparison.png","Noise Comparison")}'
            f'<h3>Success Rate by Noise Model</h3>{img_tag("success_rate_comparison.png","Success Rate Comparison")}</section>'
        )

    mds_note = (
        '<p style="font-size:0.8rem;color:#888;margin-top:0.5rem;">* Layout approximated from distance matrix (MDS).</p>'
        if not cfg.get("use_geo")
        else ""
    )

    css = """
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', system-ui, sans-serif; background: #f4f6f9; color: #1a1a2e; padding: 2rem; }
    .container { max-width: 960px; margin: 0 auto; }
    header { background: linear-gradient(135deg, #1e3a8a, #2563eb); color: white; border-radius: 12px; padding: 2rem; margin-bottom: 2rem; }
    header h1 { font-size: 1.6rem; margin-bottom: 0.4rem; }
    header p  { font-size: 0.9rem; opacity: 0.85; }
    section { background: white; border-radius: 12px; padding: 1.5rem 2rem; margin-bottom: 1.5rem; box-shadow: 0 1px 4px rgba(0,0,0,.06); }
    h2 { font-size: 1.1rem; font-weight: 600; color: #1e3a8a; border-bottom: 2px solid #dbeafe; padding-bottom: 0.5rem; margin-bottom: 1rem; }
    h3 { font-size: 0.95rem; font-weight: 600; color: #374151; margin: 1.2rem 0 0.6rem; }
    .kv-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 0.75rem; }
    .kv { background: #f8fafc; border-radius: 8px; padding: 0.75rem 1rem; }
    .kv span { display: block; font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem; }
    .kv strong { font-size: 0.95rem; color: #1a1a2e; word-break: break-all; }
    table.data { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
    table.data th { background: #f1f5f9; padding: 0.5rem 0.75rem; text-align: left; font-weight: 600; }
    table.data td { padding: 0.5rem 0.75rem; border-bottom: 1px solid #f1f5f9; }
    table.data tr:last-child td { border-bottom: none; }
    table.matrix { border-collapse: collapse; font-size: 0.8rem; }
    table.matrix th, table.matrix td { border: 1px solid #e5e7eb; padding: 4px 8px; text-align: center; }
    table.matrix th { background: #f8fafc; font-weight: 600; }
    code { background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 0.85rem; }
    .badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }
    .badge.ok { background: #dcfce7; color: #15803d; }
    .badge.ng { background: #fee2e2; color: #dc2626; }
    .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
    """

    cities_str = ", ".join(cfg.get("city_names", []))
    gen_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    device_str = cfg.get("device", "—")
    dist_str = "Geocoded" if cfg.get("use_geo") else "Manual"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Grover Simulation Report</title>
<style>{css}</style>
</head>
<body>
<div class="container">
  <header>
    <h1>Grover Simulation Report</h1>
    <p>Generated: {gen_time} | Mode: {mode} | Device: {device_str}</p>
  </header>
  <section>
    <h2>Problem Overview</h2>
    <div class="kv-grid">
      <div class="kv"><span>Cities</span><strong>{cities_str}</strong></div>
      <div class="kv"><span>City Count</span><strong>{n_cities}</strong></div>
      <div class="kv"><span>Valid Routes (n-1)!</span><strong>{n_routes:,}</strong></div>
      <div class="kv"><span>Shots</span><strong>{cfg.get("shots","—")}</strong></div>
      <div class="kv"><span>Max Iterations</span><strong>{cfg.get("max_iterations","—")}</strong></div>
      <div class="kv"><span>Ancilla Mode</span><strong>{cfg.get("ancilla_mode","—")}</strong></div>
      <div class="kv"><span>Seed</span><strong>{cfg.get("seed","—")}</strong></div>
      <div class="kv"><span>Distance Input</span><strong>{dist_str}</strong></div>
    </div>
    <h3>Distance Matrix (km)</h3>
    {matrix_table()}
  </section>
  <section>
    <h2>Classical Result (Brute Force)</h2>
    <div class="kv-grid">
      <div class="kv"><span>Best Route</span><strong>{bf_route}</strong></div>
      <div class="kv"><span>Min Cost</span><strong>{bf_cost:.1f}</strong></div>
      <div class="kv"><span>Elapsed</span><strong>{bf_time}</strong></div>
      <div class="kv"><span>Routes Evaluated</span><strong>{bf_eval}</strong></div>
    </div>
  </section>
  {quantum_section}
  {comparison_section}
  <section>
    <h2>Route Map</h2>
    {img_tag("route_map.png", "Route Map")}
    {mds_note}
  </section>
  <section>
    <h2>Circuit Diagrams</h2>
    <h3>Overview (1 iteration)</h3>
    {img_tag("circuit_overview.png", "Circuit Overview")}
    <div class="two-col" style="margin-top:1rem;">
      <div><h3>Oracle</h3>{img_tag("circuit_oracle.png", "Oracle Circuit")}</div>
      <div><h3>Diffusion</h3>{img_tag("circuit_diffusion.png", "Diffusion Circuit")}</div>
    </div>
  </section>
  <section>
    <h2>Animations</h2>
    <div class="two-col">
      <div><h3>Grover Probability</h3>{gif_tag("grover_animation.gif","Grover Animation")}</div>
      <div><h3>Classical vs Quantum</h3>{gif_tag("classical_vs_quantum.gif","Classical vs Quantum")}</div>
    </div>
    <h3 style="margin-top:1rem;">Amplitude bar chart</h3>
    {gif_tag("amplitude_animation.gif","Amplitude Animation")}
    <h3 style="margin-top:1rem;">Bloch Sphere Trajectories</h3>
    {gif_tag("bloch_animation.gif","Bloch Sphere Animation")}
  </section>
</div>
</body>
</html>"""

    report_path = output_dir / f"report_{timestamp}.html"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  HTMLレポートを保存しました: {report_path.name}")


# ---------------------------------------------------------------------------
# ノイズモデル一括比較
# ---------------------------------------------------------------------------


def _run_noise_comparison(
    problem: VehicleRoutingProblem,
    cfg: dict,
    bf_result: dict,
    output_dir: Path | None,
) -> None:
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

    print(
        f"\n  {'ノイズモデル':<12} {'最小コスト':>10} {'最適解':>6} {'実行時間':>10} {'Grover呼出':>10}"
    )
    print(f"  {'-' * 56}")
    for r in comparison_rows:
        cost_str = f"{r['best_cost']:.1f}" if r["best_cost"] is not None else "失敗"
        optimal_str = (
            "[OK]" if r["optimal"] else ("[NG]" if r["optimal"] is False else "-")
        )
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

    bf_cost = bf_result.get("best_cost", 0) if bf_result.get("status") == "ok" else 0
    print("\n  比較棒グラフを生成中...")
    try:
        _plot_noise_comparison(comparison_rows, bf_cost, output_dir)
    except Exception as e:
        print(f"  ⚠️  比較棒グラフの生成に失敗しました: {e}")

    print("  成功率比較グラフを生成中...")
    try:
        _plot_success_rate_comparison(problem, bf_cost, cfg["shots"], cfg, output_dir)
    except Exception as e:
        print(f"  ⚠️  成功率比較グラフの生成に失敗しました: {e}")

    return comparison_rows


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------


def main() -> None:
    cfg = get_config_from_web()

    random.seed(cfg["seed"])
    np.random.seed(cfg["seed"])

    coords = None
    if cfg["use_geo"]:
        ui_coords = cfg.get("coords")
        if ui_coords and len(ui_coords) >= 2:
            print("\n✅ UIで確認済みの座標を使用します。")
            coords = {name: (c["lat"], c["lng"]) for name, c in ui_coords.items()}
            cfg["city_names"] = list(coords.keys())
        else:
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

    if len(cfg.get("city_names", [])) < 2:
        print("❌ 都市数が不足しています（最低2都市必要です）。")
        sys.exit(1)

    dm = cfg.get("distance_matrix", [])
    DEFAULT_DIST = 10.0
    if dm:
        n = len(dm)
        filled = 0
        for i in range(n):
            for j in range(n):
                if i != j and (not dm[i][j] or dm[i][j] == 0):
                    dm[i][j] = DEFAULT_DIST
                    filled += 1
        if filled > 0:
            print(
                f"\n💡 距離の空欄 {filled // 2} ペアを {DEFAULT_DIST:.0f} km で補完しました。"
            )
            print("   正確な距離を使いたい場合は UI で入力し直してください。\n")
        cfg["distance_matrix"] = dm

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

    output_dir = Path(cfg["output_dir"]) if cfg.get("output_dir") else None
    if output_dir is not None:
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"\n⚠️  出力ディレクトリの作成に失敗しました: {e}")
            output_dir = None

    bf_result = bf_solve(problem)
    _print_result("古典（全探索）", bf_result)

    # ── ノイズモデル一括比較モード ──
    if cfg["noise_model"] == "all":
        comparison_rows = _run_noise_comparison(problem, cfg, bf_result, output_dir)

        if bf_result.get("status") == "ok":
            print("\nルートマップを生成中...")
            try:
                if coords is not None:
                    plot_route(
                        coords=coords,
                        best_route=bf_result["best_route"],
                        title="Classical Optimal Route",
                        save_path=output_dir / "route_map.png" if output_dir else None,
                    )
                else:
                    plot_route_from_matrix(
                        distance_matrix=cfg["distance_matrix"],
                        city_names=cfg["city_names"],
                        best_route=bf_result["best_route"],
                        title="Classical Optimal Route — Approx. Layout",
                        save_path=output_dir / "route_map.png" if output_dir else None,
                    )
            except Exception as e:
                print(f"  ⚠️  地図描画に失敗しました: {e}")

        if output_dir:
            print("\nHTMLレポートを生成中...")
            try:
                _generate_html_report(cfg, bf_result, None, comparison_rows, output_dir)
            except Exception as e:
                print(f"  ⚠️  レポート生成に失敗しました: {e}")

        print("\n回路図を生成中...")
        try:
            draw_circuits(
                problem=problem,
                threshold=bf_result["best_cost"],
                output_dir=output_dir,
            )
        except Exception as e:
            print(f"  ⚠️  回路図の生成に失敗しました: {e}")

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
    if grover_result.get("interrupted"):
        print("\n  ⚠️  途中で中断されました。上記はその時点での最良解です。")

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

    print("\nルートマップを生成中...")
    try:
        if coords is not None:
            plot_route(
                coords=coords,
                best_route=grover_result["best_route"],
                title=f"Grover Optimal Route ({cfg['noise_model']})",
                save_path=output_dir / "route_map.png" if output_dir else None,
            )
        else:
            plot_route_from_matrix(
                distance_matrix=cfg["distance_matrix"],
                city_names=cfg["city_names"],
                best_route=grover_result["best_route"],
                title=f"Grover Optimal Route ({cfg['noise_model']}) — Approx. Layout",
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

    print("\n回路図を生成中...")
    try:
        draw_circuits(
            problem=problem,
            threshold=grover_result["best_cost"],
            output_dir=output_dir,
        )
    except Exception as e:
        print(f"  ⚠️  回路図の生成に失敗しました: {e}")

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

    print("\n振幅バーチャートアニメーションを生成中...")
    try:
        run_amplitude(
            problem=problem,
            threshold=grover_result["best_cost"],
            save_path=output_dir / "amplitude_animation.gif" if output_dir else None,
            target_bitstrings=None,  # threshold から自動計算（全有効解）
            fps=2,
        )
    except Exception as e:
        print(f"  ⚠️  振幅バーチャート生成に失敗しました: {e}")

    print("\nブロッホ球アニメーションを生成中...")
    try:
        run_bloch(
            problem=problem,
            threshold=grover_result["best_cost"],
            save_path=output_dir / "bloch_animation.gif" if output_dir else None,
            target_bitstrings=None,  # threshold から自動計算（全有効解）
            fps=cfg.get("bloch_fps", 1.2),
            elev=cfg.get("bloch_elev", 22),
            azim=cfg.get("bloch_azim", -60),
        )
    except Exception as e:
        print(f"  ⚠️  ブロッホ球アニメーション生成に失敗しました: {e}")

    if output_dir:
        print("\nHTMLレポートを生成中...")
        try:
            _generate_html_report(cfg, bf_result, grover_result, None, output_dir)
        except Exception as e:
            print(f"  ⚠️  レポート生成に失敗しました: {e}")

    print("\nすべての出力が完了しました。")
    if output_dir:
        print(f"保存先: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
