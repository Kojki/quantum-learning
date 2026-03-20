"""地名から緯度経度を取得するモジュール。

geopy の Nominatim（OpenStreetMap ベース）を使用する。
countrycodes パラメータは geopy バージョンによって非対応のため、
クエリ文字列に国名を付加する方式で検索精度を向上させる。
"""

from __future__ import annotations
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError


# ---------------------------------------------------------------------------
# 国推定・クエリ組み立て
# ---------------------------------------------------------------------------


def _contains_japanese(text: str) -> bool:
    """文字列に日本語（CJK）が含まれるか判定する。"""
    return any("\u3000" <= c <= "\u9fff" or "\uff00" <= c <= "\uffef" for c in text)


# 地名キーワード → 付加する国名サフィックス
_COUNTRY_SUFFIX: dict[str, str] = {
    # 日本語キーワード
    "東京": ", Japan",
    "大阪": ", Japan",
    "名古屋": ", Japan",
    "福岡": ", Japan",
    "札幌": ", Japan",
    "仙台": ", Japan",
    "広島": ", Japan",
    "京都": ", Japan",
    "神戸": ", Japan",
    "横浜": ", Japan",
    "川崎": ", Japan",
    "さいたま": ", Japan",
    "市": ", Japan",
    "区": ", Japan",
    "町": ", Japan",
    "村": ", Japan",
    "県": ", Japan",
    # 欧米の都市
    "London": ", UK",
    "Paris": ", France",
    "Berlin": ", Germany",
    "Rome": ", Italy",
    "Madrid": ", Spain",
    "Vienna": ", Austria",
    "Amsterdam": ", Netherlands",
    "Brussels": ", Belgium",
    "New York": ", USA",
    "Los Angeles": ", USA",
    "Chicago": ", USA",
    "Tokyo": ", Japan",
    "Osaka": ", Japan",
    "Kyoto": ", Japan",
}


def _build_query(name: str) -> str:
    """地名に国名サフィックスを付加して検索精度を向上させる。

    例: 「東京」→「東京, Japan」
    """
    # 日本語を含む場合は Japan を付加
    if _contains_japanese(name):
        # すでに国名が含まれていれば付加しない
        if "Japan" not in name and "日本" not in name:
            return f"{name}, Japan"
        return name

    # キーワードテーブルで検索
    for keyword, suffix in _COUNTRY_SUFFIX.items():
        if keyword in name:
            if suffix.strip(", ") not in name:
                return f"{name}{suffix}"
            return name

    return name


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

    検索クエリに国名を付加して精度を向上させる。
    見つからない場合は元の地名でフォールバック検索する。

    Returns:
        {地名: (緯度, 経度)} の辞書。

    Raises:
        RuntimeError: 取得できた都市が2件未満の場合。
    """
    geolocator = Nominatim(user_agent="grover_simulation_tsp", timeout=timeout)

    coords: dict[str, tuple[float, float]] = {}
    failed: list[str] = []

    for name in city_names:
        query = _build_query(name)
        located = False

        try:
            # 国名付きクエリで検索
            location = geolocator.geocode(query, language=language)

            # 見つからなければ元の地名でフォールバック
            if location is None and query != name:
                print(f"  ↩  '{query}' で見つからず、'{name}' で再検索...")
                location = geolocator.geocode(name, language=language)

            if location is not None:
                coords[name] = (location.latitude, location.longitude)
                addr = location.address
                addr_short = addr[:70] + ("..." if len(addr) > 70 else "")
                print(
                    f"  取得成功: {name} → ({location.latitude:.4f}, {location.longitude:.4f})"
                )
                print(f"           [{addr_short}]")
                located = True

        except GeocoderTimedOut:
            print(f"  ⚠️  タイムアウト: {name}")
        except GeocoderServiceError as e:
            print(f"  ⚠️  サービスエラー: {name} ({e})")
        except Exception as e:
            print(f"  ⚠️  予期しないエラー: {name} ({type(e).__name__}: {e})")

        if not located:
            print(f"  ⚠️  見つかりませんでした: {name}")
            failed.append(name)

        time.sleep(wait_sec)

    if failed:
        print(f"\n  取得できなかった地名: {failed}")

    if len(coords) < 2:
        raise RuntimeError(
            f"座標を取得できた都市が {len(coords)} 件のみです（最低2都市必要）。\n"
            "地名のスペルを確認するか、距離行列を手動で入力してください。"
        )

    if failed:
        print(f"  取得できた {len(coords)} 都市のみで続行します。\n")

    return coords
