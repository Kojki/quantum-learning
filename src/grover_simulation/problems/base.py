"""全最適化問題の基底インターフェース。

量子・古典どちらのアルゴリズムからも同じインターフェースで問題を扱えるよう、
抽象基底クラス :class:`OptimizationProblem` を定義する。

各問題クラス（例: :mod:`problems.routing`）はこのクラスを継承し、
すべての抽象メソッドを実装する。

使い方::

    from problems.routing import VehicleRoutingProblem
    from classical.brute_force import solve

    problem = VehicleRoutingProblem(distance_matrix, city_names)
    result = solve(problem)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable


# ---------------------------------------------------------------------------
# 基底クラス
# ---------------------------------------------------------------------------


class OptimizationProblem(ABC):
    """全最適化問題の抽象基底クラス。

    量子・古典どちらのアルゴリズムも、このインターフェース越しに問題を扱う。
    具体的な問題クラスは以下のすべての抽象メソッドを実装する。

    **エンコード規約**

    解は常に「固定長ビット文字列（str）」として扱う。
    ``encode`` / ``decode`` がビット文字列と人間が読める文字列を相互変換し、
    ``cost`` / ``is_feasible`` はビット文字列を直接受け取る。

    こうすることで、アルゴリズム側はビット文字列の意味を知らなくても動作できる。
    """

    # ── エンコード・デコード ──────────────────────────────────────────────

    @abstractmethod
    def encode(self, solution) -> str:
        """人間が読める解 → ビット文字列に変換する。

        Args:
            solution: 問題固有の解（例: 訪問順のリスト）。

        Returns:
            固定長ビット文字列（例: ``"010110"``）。

        Example:
            ::

                vrp.encode([0, 2, 1])  # A→C→B のルート → "001001"
        """
        ...

    @abstractmethod
    def decode(self, bitstring: str):
        """ビット文字列 → 人間が読める解に変換する。

        Args:
            bitstring: :meth:`encode` が返す形式のビット文字列。

        Returns:
            ``encode`` の逆変換。問題固有の解の表現。

        Example:
            ::

                vrp.decode("001001")  # → [0, 2, 1]
        """
        ...

    # ── コスト・実行可能性 ────────────────────────────────────────────────

    @abstractmethod
    def cost(self, bitstring: str) -> float:
        """解のコスト（目的関数値）を返す。

        最適解を知らなくても計算できる。アルゴリズムはこの値を最小化する。
        実行不可能な解には ``float("inf")`` を返すことが望ましいが、
        厳密な判定は :meth:`is_feasible` に任せる。

        Args:
            bitstring: 評価対象のビット文字列。

        Returns:
            コスト値。

        Example:
            ::

                vrp.cost("000110")  # A→B→C→A の総距離
        """
        ...

    @abstractmethod
    def is_feasible(self, bitstring: str) -> bool:
        """解が制約を満たすかどうかを返す。

        コストとは別に「そもそも有効な解か」を確認する。
        アルゴリズムは ``True`` の解だけをコスト計算の対象にする。

        Args:
            bitstring: 判定対象のビット文字列。

        Returns:
            制約を満たす場合 ``True``、そうでなければ ``False``。

        Example:
            ::

                vrp.is_feasible("000110")  # 全都市を1回ずつ訪問 → True
                vrp.is_feasible("000000")  # 都市0を3回訪問    → False
        """
        ...

    # ── 問題のメタ情報 ───────────────────────────────────────────────────

    @abstractmethod
    def n_qubits_required(self) -> int:
        """この問題を量子回路で扱うのに必要な qubit 数を返す。

        問題サイズと量子限界の可視化に使う。
        古典アルゴリズムでは探索空間のサイズ（2^n）を求めるためにも使う。

        Returns:
            必要な qubit 数（正の整数）。
        """
        ...

    @abstractmethod
    def describe(self) -> str:
        """問題の概要を文字列で返す。可視化・README・デバッグ出力に使う。"""
        ...

    # ── 共通ユーティリティ ────────────────────────────────────────────────

    def make_condition(self, threshold: float) -> Callable[[str], bool]:
        """オラクルなどに渡す判定関数を返す。

        ``is_feasible`` と ``cost`` を組み合わせ、
        「制約を満たしかつコストが閾値以下」という条件を関数として返す。

        Args:
            threshold: コストの上限（この値以下の解を受け入れる）。

        Returns:
            ``bitstring`` を受け取り ``bool`` を返す関数。

        Example:
            ::

                condition = problem.make_condition(threshold=120.0)
                condition("000110")  # True / False
        """

        def condition(x: str) -> bool:
            return self.is_feasible(x) and self.cost(x) <= threshold

        return condition

    def is_within_quantum_limit(self, max_qubits: int = 30) -> bool:
        """問題規模が量子シミュレータで扱える範囲かどうかを返す。

        上限を超えているなら古典アルゴリズムに切り替えるといった
        アルゴリズム選択の判断に使う。

        Args:
            max_qubits: 許容する最大 qubit 数（デフォルト: 30）。

        Returns:
            ``n_qubits_required() <= max_qubits`` の結果。
        """
        return self.n_qubits_required() <= max_qubits
