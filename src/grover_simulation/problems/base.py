from abc import ABC, abstractmethod
from typing import Callable


class OptimizationProblem(ABC):
    """
    全最適化問題の基底クラス。
    量子・古典どちらのアルゴリズムも
    このインターフェースを通して問題を扱う。
    """

    # ── メソッド ─────────────────────────────────────

    @abstractmethod
    def encode(self, solution) -> str:
        """
        人間が読める解 → ビット文字列
        例: ["A","C","B"] → "010"
        """
        ...

    @abstractmethod
    def decode(self, bitstring: str):
        """
        ビット文字列 → 人間が読める解
        例: "010" → ["A","C","B"]
        """
        ...

    @abstractmethod
    def cost(self, bitstring: str) -> float:
        """
        解のコストを計算する。
        最適解を知らなくても計算できる。
        例: ルートの総距離、スケジュールの総時間
        """
        ...

    @abstractmethod
    def is_feasible(self, bitstring: str) -> bool:
        """
        解が制約を満たすか（実行可能な解か）。
        コストとは別に「そもそも有効な解か」を判定する。
        例: 全都市を1回ずつ訪問しているか
        """
        ...

    @abstractmethod
    def n_qubits_required(self) -> int:
        """
        この問題を量子回路で扱うのに必要なqubit数。
        問題サイズと限界の可視化に使う。
        """
        ...

    @abstractmethod
    def describe(self) -> str:
        """問題の説明文（可視化・READMEに使う）"""
        ...

    # ── 共通処理 ─────────────────────────────────────

    def make_condition(self, threshold: float) -> Callable[[str], bool]:
        """
        oracle.py に渡す判定関数を生成する。
        cost と is_feasible を組み合わせる。
        """

        def condition(x: str) -> bool:
            return self.is_feasible(x) and self.cost(x) <= threshold

        return condition

    def is_within_quantum_limit(self, max_qubits: int = 30) -> bool:
        """
        現在の量子シミュレータで扱える範囲かどうか。
        limits.py の可視化に使う。
        """
        return self.n_qubits_required() <= max_qubits
