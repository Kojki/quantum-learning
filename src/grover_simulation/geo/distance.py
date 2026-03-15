"""座標間の距離を計算するモジュール。

haversine 公式を使って緯度経度から実距離（km）を計算する。

使い方::

    from geo.distance import build_distance_matrix

    coords = {"福岡": (33.59, 130.40), "大阪": (34.69, 135.50)}
    matrix, names = build_distance_matrix(coords)
"""

from __future__ import annotations

import math

import numpy as np


# ---------------------------------------------------------------------------
# haversine 公式
# ---------------------------------------------------------------------------


def haversine(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """2点間の大圏距離（km）を返す。

    地球を球体と仮定した haversine 公式による計算。
    誤差は実距離の 0.3% 以内。

    Args:
        lat1: 地点1の緯度（度）。
        lon1: 地点1の経度（度）。
        lat2: 地点2の緯度（度）。
        lon2: 地点2の経度（度）。

    Returns:
        2点間の距離（km）。
    """
    R = 6371.0  # 地球の平均半径（km）

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


# ---------------------------------------------------------------------------
# 距離行列の構築
# ---------------------------------------------------------------------------


def build_distance_matrix(
    coords: dict[str, tuple[float, float]],
) -> tuple[list[list[float]], list[str]]:
    """座標辞書から距離行列を構築する。

    Args:
        coords: ``{地名: (緯度, 経度)}`` の辞書。

    Returns:
        以下のタプル：
            - ``list[list[float]]``: n×n の距離行列（km）。対角成分は 0。
            - ``list[str]``: 距離行列の行・列に対応する地名リスト。
    """
    names = list(coords.keys())
    n = len(names)
    matrix = [[0.0] * n for _ in range(n)]

    for i in range(n):
        for j in range(n):
            if i == j:
                matrix[i][j] = 0.0
            elif i < j:
                lat1, lon1 = coords[names[i]]
                lat2, lon2 = coords[names[j]]
                dist = haversine(lat1, lon1, lat2, lon2)
                matrix[i][j] = round(dist, 1)
                matrix[j][i] = round(dist, 1)

    return matrix, names


def suggest_threshold(
    matrix: list[list[float]],
    names: list[str],
) -> float:
    """距離行列から適切なコストのしきい値を提案する。

    全ルートの平均コストを計算し、それより少し低い値を返す。
    ユーザーがしきい値を設定する際の参考値として使う。

    Args:
        matrix: build_distance_matrix() が返す距離行列。
        names: 地名リスト。

    Returns:
        提案するしきい値（km）。
    """
    from itertools import permutations

    n = len(names)
    total = 0.0
    count = 0

    # 全順列のコストを計算（都市数が多い場合はサンプリング）
    perms = list(permutations(range(n)))
    if len(perms) > 1000:
        import random

        perms = random.sample(perms, 1000)

    for perm in perms:
        cost = sum(matrix[perm[i]][perm[(i + 1) % n]] for i in range(n))
        total += cost
        count += 1

    avg = total / count if count > 0 else 0.0
    # 平均の 70% を提案値とする（上位 30% のルートを正解とみなす）
    return round(avg * 0.7, 1)
