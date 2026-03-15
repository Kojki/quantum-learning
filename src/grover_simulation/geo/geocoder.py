"""地名から緯度経度を取得するモジュール。

geopy の Nominatim（OpenStreetMap ベース）を使用する。
API の利用規約により、連続リクエストの間に待機時間を設ける。

使い方::

    from geo.geocoder import geocode_cities

    coords = geocode_cities(["福岡", "大阪", "東京", "札幌"])
    # → {"福岡": (33.5902, 130.4017), "大阪": (34.6937, 135.5023), ...}
"""

from __future__ import annotations

import time

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError


# ---------------------------------------------------------------------------
# 座標取得
# ---------------------------------------------------------------------------


def geocode_cities(
    city_names: list[str],
    language: str = "ja",
    timeout: int = 10,
    wait_sec: float = 1.1,
) -> dict[str, tuple[float, float]]:
    """都市名のリストから緯度経度を取得する。

    Nominatim の利用規約により、リクエスト間に最低 1 秒の待機を設ける。

    Args:
        city_names: 地名のリスト（日本語・英語どちらでも可）。
        language: 検索に使う言語（デフォルト: 日本語）。
        timeout: タイムアウト秒数。
        wait_sec: リクエスト間の待機時間（秒）。1.0 以上を推奨。

    Returns:
        ``{地名: (緯度, 経度)}`` の辞書。
        取得できなかった地名はスキップされる。

    Raises:
        RuntimeError: 1件も座標が取得できなかった場合。
    """
    geolocator = Nominatim(
        user_agent="grover_simulation_tsp",
        timeout=timeout,
    )

    coords: dict[str, tuple[float, float]] = {}
    failed: list[str] = []

    for name in city_names:
        try:
            location = geolocator.geocode(name, language=language)
            if location is not None:
                coords[name] = (location.latitude, location.longitude)
                print(
                    f"  取得成功: {name} → ({location.latitude:.4f}, {location.longitude:.4f})"
                )
            else:
                print(f"  ⚠️  見つかりませんでした: {name}")
                failed.append(name)
        except GeocoderTimedOut:
            print(f"  ⚠️  タイムアウト: {name}")
            failed.append(name)
        except GeocoderServiceError as e:
            print(f"  ⚠️  サービスエラー: {name} ({e})")
            failed.append(name)

        # リクエスト間の待機
        time.sleep(wait_sec)

    if not coords:
        raise RuntimeError(
            "座標の取得に失敗しました。"
            "地名が正しいか、インターネット接続を確認してください。"
        )

    if failed:
        print(f"\n  以下の地名は取得できませんでした: {failed}")
        print("  取得できた地名のみで続行します。")

    return coords
