"""ベンチマーク結果の収集・メトリクス算出モジュール。

古典（brute_force）と量子（Grover）の solve() 結果を受け取り、
比較・評価に使うメトリクスを算出する。

使い方::

    from benchmark.metrics import compare, summarize_noise_sweep

    report = compare(bf_result, grover_result, n_qubits=6)
    print(report["summary"])
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# 1回分の比較レポート
# ---------------------------------------------------------------------------


def compare(
    bf_result: dict,
    grover_result: dict,
    n_qubits: int,
) -> dict:
    """brute_force と Grover の結果を比較したレポートを返す。

    Args:
        bf_result: classical.brute_force.solve() の返り値。
        grover_result: quantum.grover.solve() の返り値。
        n_qubits: 問題の qubit 数（探索空間 2^n の計算に使う）。

    Returns:
        以下のキーを持つ辞書。

        - ``classical``: 古典側のメトリクス
        - ``quantum``: 量子側のメトリクス
        - ``comparison``: 両者の比較値
        - ``summary``: 人間が読める要約文字列
    """
    n_space = 2**n_qubits

    # --- 古典メトリクス ---
    classical = _extract_classical(bf_result, n_space)

    # --- 量子メトリクス ---
    quantum = _extract_quantum(grover_result, n_space)

    # --- 比較メトリクス ---
    comparison = _make_comparison(classical, quantum, bf_result, grover_result)

    # --- サマリー文字列 ---
    summary = _make_summary(classical, quantum, comparison, n_qubits, n_space)

    return {
        "classical": classical,
        "quantum": quantum,
        "comparison": comparison,
        "summary": summary,
    }


def _extract_classical(result: dict, n_space: int) -> dict:
    """古典結果からメトリクスを抽出する。"""
    if result.get("status") != "ok":
        return {
            "status": result.get("status"),
            "elapsed_sec": result.get("elapsed_sec"),
        }

    return {
        "status": "ok",
        "best_cost": result["best_cost"],
        "best_route": result["best_route"],
        "n_evaluated": result["n_evaluated"],
        "n_total": n_space,
        "search_ratio": round(result["n_evaluated"] / n_space, 4),
        "elapsed_sec": result["elapsed_sec"],
    }


def _extract_quantum(result: dict, n_space: int) -> dict:
    """量子結果からメトリクスを抽出する。"""
    if result.get("status") != "ok":
        return {
            "status": result.get("status"),
            "elapsed_sec": result.get("elapsed_sec"),
        }

    # 成功確率：top_k の中で最良解のカウント割合
    success_prob = None
    if "top_k" in result and "best_bitstring" in result:
        best_bs = result["best_bitstring"]
        counts = result.get("counts", {})
        total = sum(counts.values())
        best_count = counts.get(best_bs, 0)
        success_prob = round(best_count / total, 4) if total > 0 else 0.0

    return {
        "status": "ok",
        "best_cost": result["best_cost"],
        "best_route": result["best_route"],
        "n_iterations": result["n_iterations"],
        "circuit_depth": result["circuit_depth"],
        "n_qubits_total": result.get("n_qubits_total"),
        "ancilla_mode": result.get("mode"),
        "success_prob": success_prob,
        "elapsed_sec": result["elapsed_sec"],
    }


def _make_comparison(
    classical: dict,
    quantum: dict,
    bf_result: dict,
    grover_result: dict,
) -> dict:
    """両者の比較値を算出する。"""
    if classical.get("status") != "ok" or quantum.get("status") != "ok":
        return {"optimal_match": False, "note": "どちらかの結果が異常終了しています。"}

    optimal_match = classical["best_cost"] == quantum["best_cost"]

    # 理論上の Grover の優位性: √N vs N
    # 古典の期待探索ステップ数 = N/2（平均）、Grover = π/4 * √N
    import math

    n_space = classical["n_total"]
    classical_expected_steps = n_space / 2
    grover_expected_steps = math.pi / 4 * math.sqrt(n_space)
    speedup_theoretical = round(classical_expected_steps / grover_expected_steps, 2)

    # 実測の speedup（elapsed_sec ベース）
    speedup_actual = None
    if quantum["elapsed_sec"] > 0:
        speedup_actual = round(classical["elapsed_sec"] / quantum["elapsed_sec"], 4)

    return {
        "optimal_match": optimal_match,
        "speedup_theoretical": speedup_theoretical,
        "speedup_actual": speedup_actual,
        "classical_steps": classical["n_evaluated"],
        "grover_iterations": quantum["n_iterations"],
    }


def _make_summary(
    classical: dict,
    quantum: dict,
    comparison: dict,
    n_qubits: int,
    n_space: int,
) -> str:
    """人間が読める要約文字列を返す。"""
    lines = [
        f"{'=' * 55}",
        f"  ベンチマーク結果サマリー",
        f"{'=' * 55}",
        f"  探索空間       : 2^{n_qubits} = {n_space:,} 通り",
        f"",
        f"  【古典（全探索）】",
        f"    最適ルート   : {classical.get('best_route', 'N/A')}",
        f"    最小コスト   : {classical.get('best_cost', 'N/A')}",
        f"    評価した解   : {classical.get('n_evaluated', 'N/A')} 件",
        f"    実行時間     : {classical.get('elapsed_sec', 0):.4f} 秒",
        f"",
        f"  【量子（Grover）】",
        f"    最適ルート   : {quantum.get('best_route', 'N/A')}",
        f"    最小コスト   : {quantum.get('best_cost', 'N/A')}",
        f"    反復回数     : {quantum.get('n_iterations', 'N/A')}",
        f"    回路深さ     : {quantum.get('circuit_depth', 'N/A')}",
        f"    成功確率     : {quantum.get('success_prob', 'N/A')}",
        f"    実行時間     : {quantum.get('elapsed_sec', 0):.4f} 秒",
        f"",
        f"  【比較】",
        f"    最適解一致   : {'✅' if comparison.get('optimal_match') else '❌'}",
        f"    理論加速度   : {comparison.get('speedup_theoretical', 'N/A')} 倍（√N優位）",
        f"    実測加速度   : {comparison.get('speedup_actual', 'N/A')} 倍（シミュレータ時間）",
        f"{'=' * 55}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ノイズスイープ用：複数結果のまとめ
# ---------------------------------------------------------------------------


def summarize_noise_sweep(
    sweep_results: list[dict[str, Any]],
) -> dict:
    """ノイズレベルを変えた複数回の Grover 結果をまとめる。

    visualizer でノイズ vs 成功確率のグラフを描く際に使う。

    Args:
        sweep_results: 各要素が以下のキーを持つリスト。
            - ``noise_label``: ノイズ設定の名前（例: "ideal", "eagle_r3"）
            - ``grover_result``: quantum.grover.solve() の返り値

    Returns:
        以下のキーを持つ辞書。

        - ``labels``: ノイズ設定名のリスト
        - ``success_probs``: 各設定の成功確率リスト
        - ``circuit_depths``: 各設定の回路深さリスト
        - ``elapsed_secs``: 各設定の実行時間リスト
    """
    labels = []
    success_probs = []
    circuit_depths = []
    elapsed_secs = []

    for entry in sweep_results:
        label = entry["noise_label"]
        result = entry["grover_result"]

        labels.append(label)
        circuit_depths.append(result.get("circuit_depth"))
        elapsed_secs.append(result.get("elapsed_sec"))

        # 成功確率の算出
        if result.get("status") == "ok" and "counts" in result:
            best_bs = result.get("best_bitstring", "")
            counts = result["counts"]
            total = sum(counts.values())
            best_count = counts.get(best_bs, 0)
            success_probs.append(round(best_count / total, 4) if total > 0 else 0.0)
        else:
            success_probs.append(0.0)

    return {
        "labels": labels,
        "success_probs": success_probs,
        "circuit_depths": circuit_depths,
        "elapsed_secs": elapsed_secs,
    }
