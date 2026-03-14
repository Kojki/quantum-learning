"""古典的な全探索（ブルートフォース）アルゴリズム。

``2^n`` 通りすべてのビット文字列を生成し、``OptimizationProblem`` の
``is_feasible`` でフィルタしたうえで ``cost`` が最小の解を返す。

**計算量:** O(2^n)。Groverのアルゴリズムとの比較ベースラインとして使う。
``n_qubits_required()`` が 20 を超えると実行に数秒以上かかることがある。

使い方::

    from problems.routing import VehicleRoutingProblem
    from classical.brute_force import solve

    problem = VehicleRoutingProblem(distances, city_names)
    result = solve(problem)

    # result["status"] が "ok" のとき最適解が含まれる
    print(result["best_route"])   # "A → B → C → A"
    print(result["best_cost"])    # 120.0
    print(result["n_evaluated"])  # 評価した実行可能解の個数
    print(result["elapsed_sec"])  # 計算時間（秒）
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from problems.base import OptimizationProblem


# ---------------------------------------------------------------------------
# 内部ユーティリティ
# ---------------------------------------------------------------------------


def _all_bitstrings(n_bits: int):
    """``n_bits`` ビットの全ビット文字列を昇順に生成するジェネレータ。

    リストを作らず逐次生成するのでメモリを節約できる。

    Args:
        n_bits: ビット数（非負整数）。

    Yields:
        ``"0...0"`` から ``"1...1"`` までの固定長ビット文字列（計 ``2**n_bits`` 個）。
    """
    fmt = f"0{n_bits}b"
    for i in range(2**n_bits):
        yield format(i, fmt)


# ---------------------------------------------------------------------------
# 全探索
# ---------------------------------------------------------------------------


def solve(problem: "OptimizationProblem") -> dict:
    """全探索で最適解を求める。

    ``2^n`` 通りすべてのビット文字列を試し、最小コストの解を返す。

    処理の流れ:

    1. ``problem.is_feasible(x)`` が ``False`` の解はスキップ。
    2. ``problem.cost(x)`` を計算し、暫定の最良解を更新。
    3. 全て列挙したのち、結果のディクショナリを返す。

    Args:
        problem: :class:`~problems.base.OptimizationProblem` を実装した
                 問題のインスタンス。

    Returns:
        以下のキーを持つディクショナリ。

        **成功時** (``status == "ok"``)::

            {
                "status":         "ok",
                "best_bitstring": str,    # 最適解のビット文字列
                "best_cost":      float,  # 最小コスト
                "best_route":     str,    # problem.route_to_str() の結果
                "n_evaluated":    int,    # 評価した実行可能解の個数
                "n_total":        int,    # 列挙したビット文字列の総数（2^n）
                "all_costs":      list,   # 実行可能解のコスト一覧（list[float]）
                "elapsed_sec":    float,  # 実行時間（秒）
            }

        **実行可能解なし** (``status == "no_solution"``)::

            {
                "status":      "no_solution",
                "n_evaluated": 0,
                "n_total":     int,
                "elapsed_sec": float,
            }

    Note:
        計算量は O(2^n) なので、``n_qubits_required()`` が大きいと急激に遅くなる。
        Grover 法との速度比較には ``elapsed_sec`` を使うとよい。
    """
    n_bits = problem.n_qubits_required()
    n_total = 2**n_bits

    best_bitstring: str | None = None
    best_cost = float("inf")
    all_costs: list[float] = []
    n_evaluated = 0

    start = time.perf_counter()

    for x in _all_bitstrings(n_bits):

        # 制約に反する解はスキップ
        if not problem.is_feasible(x):
            continue

        cost = problem.cost(x)
        n_evaluated += 1
        all_costs.append(cost)

        # 暫定の最良解を更新
        if cost < best_cost:
            best_cost = cost
            best_bitstring = x

    elapsed = time.perf_counter() - start

    # 実行可能解が1つも見つからなかった場合
    if best_bitstring is None:
        return {
            "status": "no_solution",
            "n_evaluated": 0,
            "n_total": n_total,
            "elapsed_sec": elapsed,
        }

    return {
        "status": "ok",
        "best_bitstring": best_bitstring,
        "best_cost": best_cost,
        "best_route": problem.route_to_str(best_bitstring),
        "n_evaluated": n_evaluated,
        "n_total": n_total,
        "all_costs": all_costs,
        "elapsed_sec": elapsed,
    }
