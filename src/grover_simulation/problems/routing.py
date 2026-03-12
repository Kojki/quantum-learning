import itertools
import math
from .base import OptimizationProblem


class VehicleRoutingProblem(OptimizationProblem):
    """
    巡回セールスマン問題（TSP）の実装。

    エンコード方式: 順列エンコーディング
      各都市を「何番目に訪問するか」でビット列に変換する。

    例（3都市 A,B,C）:
      ルート A→B→C → 訪問順[0,1,2] → "000101"
      ルート A→C→B → 訪問順[0,2,1] → "001001"
    """

    def __init__(
        self, distance_matrix: list[list[float]], city_names: list[str] = None
    ):
        self.distances = distance_matrix
        self.n_cities = len(distance_matrix)
        self.city_names = city_names or [str(i) for i in range(self.n_cities)]
        self.bits_per_city = math.ceil(math.log2(self.n_cities))

    # ── エンコード・デコード ──────────────────────────────

    def encode(self, route: list[int]) -> str:
        """
        訪問順のリスト → ビット文字列

        route = [0, 2, 1] （0番目にA, 1番目にC, 2番目にB）
        → 各インデックスを bits_per_city ビットで表現
        → "00" + "10" + "01" = "001001"  （2ビット/都市の場合）
        """
        bitstring = ""
        for city_index in route:
            # 各都市インデックスを固定長ビット列に変換
            bitstring += format(city_index, f"0{self.bits_per_city}b")
        return bitstring

    def decode(self, bitstring: str) -> list[int]:
        """
        ビット文字列 → 訪問順のリスト

        "000110" → ["00", "01", "10"] → [0, 1, 2]
        """
        route = []
        for i in range(self.n_cities):
            # bits_per_city ビットずつ切り出す
            start = i * self.bits_per_city
            end = start + self.bits_per_city
            chunk = bitstring[start:end]
            route.append(int(chunk, 2))
        return route

    # ── コスト計算 ────────────────────────────────────────

    def cost(self, bitstring: str) -> float:
        """
        ビット文字列 → ルートの総距離

        無効なルート（重複訪問など）は is_feasible で弾くが
        念のため無限大を返す
        """
        route = self.decode(bitstring)

        if not self._is_valid_permutation(route):
            return float("inf")

        total = 0.0
        for i in range(self.n_cities):
            frm = route[i]
            to = route[(i + 1) % self.n_cities]  # 最後は出発地に戻る
            total += self.distances[frm][to]
        return total

    # ── 実行可能性チェック ────────────────────────────────

    def is_feasible(self, bitstring: str) -> bool:
        """
        有効なルートかどうかを判定。

        条件:
          1. ビット列の長さが正しい
          2. 各都市インデックスが範囲内
          3. 全都市をちょうど1回ずつ訪問している
        """
        # 条件1: 長さチェック
        expected_length = self.n_cities * self.bits_per_city
        if len(bitstring) != expected_length:
            return False

        route = self.decode(bitstring)

        # 条件2: インデックス範囲チェック
        if any(c >= self.n_cities for c in route):
            return False

        # 条件3: 重複なしチェック
        return self._is_valid_permutation(route)

    def _is_valid_permutation(self, route: list[int]) -> bool:
        """全都市をちょうど1回ずつ訪問しているか"""
        return sorted(route) == list(range(self.n_cities))

    # ── qubit数・限界 ─────────────────────────────────────

    def n_qubits_required(self) -> int:
        """
        順列エンコーディングで必要なqubit数。
        都市数が増えると急激に増加する → 限界の可視化に使う
        """
        return self.n_cities * self.bits_per_city

    @staticmethod
    def qubit_scaling(max_cities: int) -> dict[int, int]:
        """
        都市数 → 必要qubit数の対応表を返す。
        limits.py でグラフを描くために使う。
        """
        result = {}
        for n in range(2, max_cities + 1):
            bits = math.ceil(math.log2(n))
            result[n] = n * bits
        return result

    # ── 説明・デバッグ ─────────────────────────────────────

    def describe(self) -> str:
        return (
            f"{self.n_cities}都市のTSP\n"
            f"都市: {self.city_names}\n"
            f"必要qubit数: {self.n_qubits_required()}"
        )

    def route_to_str(self, bitstring: str) -> str:
        """デバッグ用: ビット列をわかりやすいルート表示に変換"""
        route = self.decode(bitstring)
        names = [self.city_names[i] for i in route]
        return " → ".join(names) + f" → {names[0]}"
