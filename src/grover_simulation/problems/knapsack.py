"""ナップサック問題 (Knapsack Problem) の定義モジュール。"""

from __future__ import annotations

from typing import Any

from problems.base import OptimizationProblem


class KnapsackProblem(OptimizationProblem):
    """0-1 ナップサック問題。
    
    与えられたアイテム（重さと価値）から、総重量が制限(capacity)を超えないように
    いくつかを選び、選んだアイテムの合計価値を最大化する問題。
    """

    def __init__(
        self,
        weights: list[int],
        values: list[float],
        capacity: int,
    ):
        """
        Args:
            weights: 各アイテムの重さのリスト
            values: 各アイテムの価値のリスト
            capacity: ナップサックの最大容量

        Raises:
            ValueError: weights と values の長さが異なる場合
        """
        if len(weights) != len(values):
            raise ValueError("weights と values の長さは同じである必要があります。")

        self.weights = weights
        self.values = values
        self.capacity = capacity
        self.num_items = len(weights)

    def encode(self, solution: list[int]) -> str:
        """
        アイテムの選択状態(0 or 1のリスト)をビット文字列に変換する。
        例: [1, 0, 1] -> "101"
        """
        return "".join(str(bit) for bit in solution)

    def decode(self, bitstring: str) -> list[int]:
        """
        ビット文字列を元のアイテム選択状態のリストに戻す。
        例: "101" -> [1, 0, 1]
        """
        return [int(char) for char in bitstring]

    def cost(self, bitstring: str) -> float:
        """
        合計価値の「マイナス」を返す（最小化問題として扱うため）。
        Grover等では条件（しきい値以下）として扱うことが多いため。

        実行不可能な場合はペナルティを含めるか、is_feasible側で弾く前提で一旦純粋な価値だけを計算。
        """
        total_value = sum(
            self.values[i] 
            for i, bit in enumerate(bitstring) 
            if bit == "1"
        )
        return -float(total_value)  # 負の価値（＝最小化で元の価値を最大化）

    def is_feasible(self, bitstring: str) -> bool:
        """
        選ばれたアイテムの合計重量が capacity 以下であるか判定する。
        """
        total_weight = sum(
            self.weights[i] 
            for i, bit in enumerate(bitstring) 
            if bit == "1"
        )
        return total_weight <= self.capacity

    def n_qubits_required(self) -> int:
        """アイテム数が量子ビット数に対応する。"""
        return self.num_items

    def describe(self) -> str:
        return (
            f"0-1 Knapsack Problem\n"
            f"- items: {self.num_items}\n"
            f"- capacity: {self.capacity}\n"
            f"- weights: {self.weights}\n"
            f"- values: {self.values}"
        )
