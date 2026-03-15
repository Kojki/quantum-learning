"""巡回セールスマン問題（TSP）の実装。

エンコード方式として 「順列エンコーディング」 を採用する。
各都市の訪問順インデックスを固定長ビット列に変換し、それを連結して1つのビット列とする。

エンコード例（3都市 A, B, C）:

+-------------------+-------------+-------------+
| ルート             | 訪問順リスト | ビット文字列 |
+===================+=============+=============+
| A → B → C → A     | [0, 1, 2]   | "000110"    |
+-------------------+-------------+-------------+
| A → C → B → A     | [0, 2, 1]   | "001001"    |
+-------------------+-------------+-------------+

bits_per_city = ceil(log2(n_cities)) ビットで1都市を表す。
3都市なら ceil(log2(3)) = 2 ビット/都市、計 6 ビット。
"""

from __future__ import annotations

import math

from .base import OptimizationProblem


# ---------------------------------------------------------------------------
# VehicleRoutingProblem（TSP）
# ---------------------------------------------------------------------------


class VehicleRoutingProblem(OptimizationProblem):
    """巡回セールスマン問題（TSP）を表すクラス。

    出発地を固定せず、ビット列の先頭都市から出発して
    全都市を一巡し、出発都市に戻る経路を扱う。

    エンコード方式: 順列エンコーディング
        各都市インデックスを ``bits_per_city`` ビットで表し、
        ``n_cities`` 個を連結したビット列とする。

    Args:
        distance_matrix: ``n×n`` の対称な距離行列（正の実数）。
                         ``distance_matrix[i][j]`` が都市 i → j の距離。
        city_names: 都市の表示名リスト（省略時は ``["0", "1", ...]``）。

    Attributes:
        distances (list[list[float]]): コンストラクタに渡した距離行列。
        n_cities (int): 都市数。
        city_names (list[str]): 都市の表示名。
        bits_per_city (int): 1都市を表すビット数 = ceil(log2(n_cities))。
    """

    def __init__(
        self,
        distance_matrix: list[list[float]],
        city_names: list[str] | None = None,
    ) -> None:
        self.distances = distance_matrix
        self.n_cities = len(distance_matrix)
        self.city_names = city_names or [str(i) for i in range(self.n_cities)]
        # 都市数が2のべき乗でない場合も含め、必要なビット数を切り上げで求める
        self.bits_per_city = math.ceil(math.log2(self.n_cities))

    # ── エンコード・デコード ──────────────────────────────────────────────

    def encode(self, route: list[int]) -> str:
        """訪問順インデックスのリスト → ビット文字列に変換する。

        各都市インデックスを ``bits_per_city`` ビットの固定長で表し、順に連結する。

        Args:
            route: 都市インデックスの訪問順リスト（例: ``[0, 2, 1]``）。

        Returns:
            固定長ビット文字列（例: ``"001001"``、3都市2ビット/都市の場合）。

        Example:
            ::

                vrp.encode([0, 2, 1])
                # → "00" + "10" + "01" = "001001"  (bits_per_city=2)
        """
        return "".join(
            format(city_index, f"0{self.bits_per_city}b") for city_index in route
        )

    def decode(self, bitstring: str) -> list[int]:
        """ビット文字列 → 訪問順インデックスのリストに変換する。

        Args:
            bitstring: :meth:`encode` が返す形式のビット文字列。

        Returns:
            都市インデックスの訪問順リスト（例: ``[0, 2, 1]``）。

        Example:
            ::

                vrp.decode("001001")
                # → ["00","10","01"] → [0, 2, 1]
        """
        return [
            int(bitstring[i * self.bits_per_city : (i + 1) * self.bits_per_city], 2)
            for i in range(self.n_cities)
        ]

    # ── コスト計算 ────────────────────────────────────────────────────────

    def cost(self, bitstring: str) -> float:
        """ルートの総距離を返す。

        出発都市から全都市を一巡し、出発都市に戻るまでの距離の合計。
        無効なルート（重複訪問など）は通常 ``is_feasible`` で弾かれるが、
        念のため ``float("inf")`` を返すようにしている。

        Args:
            bitstring: 評価対象のビット文字列。

        Returns:
            ルートの総距離。無効な順列の場合は ``float("inf")``。
        """
        route = self.decode(bitstring)

        # 念のため無効な順列を弾く（通常は is_feasible が先に除外する）
        if not self._is_valid_permutation(route):
            return float("inf")

        # 各エッジの距離を合算する（最後のエッジは末尾→先頭で出発都市に戻る）
        return sum(
            self.distances[route[i]][route[(i + 1) % self.n_cities]]
            for i in range(self.n_cities)
        )

    # ── 実行可能性チェック ────────────────────────────────────────────────

    def is_feasible(self, bitstring: str) -> bool:
        """ビット文字列が有効なルートかどうかを判定する。

        以下の3条件をすべて満たす場合に ``True`` を返す:

        1. ビット列の長さが ``n_cities × bits_per_city`` と一致する。
        2. 各都市インデックスが ``0`` 以上 ``n_cities`` 未満である。
        3. 全都市をちょうど1回ずつ訪問している（有効な順列）。

        Args:
            bitstring: 判定対象のビット文字列。

        Returns:
            3条件すべてを満たす場合 ``True``。
        """
        # 条件1: ビット長チェック
        expected_length = self.n_cities * self.bits_per_city
        if len(bitstring) != expected_length:
            return False

        route = self.decode(bitstring)

        # 条件2: インデックス範囲チェック
        if any(c >= self.n_cities for c in route):
            return False

        # 条件3: 重複なし（有効な順列）チェック
        return self._is_valid_permutation(route)

    def _is_valid_permutation(self, route: list[int]) -> bool:
        """全都市インデックスが過不足なく1回ずつ現れるかを確認する（内部用）。"""
        return sorted(route) == list(range(self.n_cities))

    # ── qubit 数・スケーリング ────────────────────────────────────────────

    def n_qubits_required(self) -> int:
        """順列エンコーディングに必要な qubit 数を返す。

        ``n_cities × bits_per_city`` で計算され、都市数が増えると急増する。
        量子限界の可視化（limits.py）や探索空間のサイズ（2^n）の確認に使う。

        Returns:
            必要な qubit 数（正の整数）。
        """
        return self.n_cities * self.bits_per_city

    @staticmethod
    def qubit_scaling(max_cities: int) -> dict[int, int]:
        """都市数と必要 qubit 数の対応表を返す。

        limits.py でスケーリンググラフを描く際に使う。

        Args:
            max_cities: 計算する最大都市数。

        Returns:
            ``{都市数: 必要qubit数}`` の辞書（都市数 2 から ``max_cities`` まで）。

        Example:
            ::

                VehicleRoutingProblem.qubit_scaling(5)
                # → {2: 2, 3: 6, 4: 8, 5: 15}
        """
        return {n: n * math.ceil(math.log2(n)) for n in range(2, max_cities + 1)}

    # ── 説明・デバッグ ────────────────────────────────────────────────────

    def describe(self) -> str:
        """問題の概要を文字列で返す。"""
        return (
            f"{self.n_cities} 都市の TSP\n"
            f"  都市        : {self.city_names}\n"
            f"  必要qubit数 : {self.n_qubits_required()}\n"
            f"  探索空間    : 2^{self.n_qubits_required()} = "
            f"{2 ** self.n_qubits_required():,} 通り\n"
            f"  有効ルート  : {math.factorial(self.n_cities):,} 通り"
        )

    def route_to_str(self, bitstring: str) -> str:
        """ビット文字列をルート表示（都市名の連鎖）に変換する。

        Args:
            bitstring: :meth:`encode` が返す形式のビット文字列。

        Returns:
            ``"A → B → C → A"`` 形式の文字列。

        Example:
            ::

                vrp.route_to_str("000110")  # → "A → B → C → A"
        """
        route = self.decode(bitstring)
        names = [self.city_names[i] for i in route]
        return " → ".join(names) + f" → {names[0]}"
