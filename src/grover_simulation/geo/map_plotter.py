"""地図上に都市と最適ルートを描画するモジュール。

contextily で OpenStreetMap のタイル画像を背景として使い、
matplotlib で都市の位置と最適ルートを重ねて描画する。

使い方::

    from geo.map_plotter import plot_route

    plot_route(
        coords={"福岡": (33.59, 130.40), "大阪": (34.69, 135.50)},
        best_route="福岡 → 大阪 → 福岡",
        title="Grover が見つけた最短ルート",
        save_path="output/route_map.png",
    )
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import contextily as ctx
from pyproj import Transformer


# ---------------------------------------------------------------------------
# 座標変換（WGS84 → Web メルカトル）
# ---------------------------------------------------------------------------


def _to_web_mercator(lat: float, lon: float) -> tuple[float, float]:
    """WGS84（緯度経度）を Web メルカトル座標（EPSG:3857）に変換する。

    contextily は Web メルカトル座標系を使うため、
    matplotlib に渡す前に変換が必要。

    Args:
        lat: 緯度（度）。
        lon: 経度（度）。

    Returns:
        (x, y) の Web メルカトル座標（メートル）。
    """
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    x, y = transformer.transform(lon, lat)
    return x, y


# ---------------------------------------------------------------------------
# 地図描画
# ---------------------------------------------------------------------------


def plot_route(
    coords: dict[str, tuple[float, float]],
    best_route: str,
    title: str = "最短ルート",
    save_path: str | Path | None = None,
    zoom: int | None = None,
) -> None:
    """地図上に都市と最適ルートを描画する。

    Args:
        coords: ``{地名: (緯度, 経度)}`` の辞書。
        best_route: ``"福岡 → 大阪 → 東京 → 福岡"`` 形式のルート文字列。
        title: グラフのタイトル。
        save_path: 保存先パス（.png）。省略時はウィンドウ表示。
        zoom: 地図のズームレベル。省略時は自動調整。
    """
    # ルート文字列を都市名リストに変換
    route_names = [r.strip() for r in best_route.split("→")]

    # 座標を Web メルカトルに変換
    mercator: dict[str, tuple[float, float]] = {}
    for name, (lat, lon) in coords.items():
        mercator[name] = _to_web_mercator(lat, lon)

    # 描画範囲の計算（余白つき）
    xs = [x for x, y in mercator.values()]
    ys = [y for x, y in mercator.values()]
    margin_x = (max(xs) - min(xs)) * 0.25 + 50000
    margin_y = (max(ys) - min(ys)) * 0.25 + 50000

    x_min, x_max = min(xs) - margin_x, max(xs) + margin_x
    y_min, y_max = min(ys) - margin_y, max(ys) + margin_y

    # ---描画---
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)

    # 背景地図（OpenStreetMap）
    try:
        ctx.add_basemap(
            ax,
            crs="EPSG:3857",
            source=ctx.providers.OpenStreetMap.Mapnik,
            zoom=zoom,
        )
    except Exception:
        print("  ⚠️  地図タイルの取得に失敗しました。背景なしで描画します。")
        ax.set_facecolor("#e8f4f8")

    # ルートの矢印を描画
    for i in range(len(route_names) - 1):
        from_city = route_names[i]
        to_city = route_names[i + 1]
        if from_city not in mercator or to_city not in mercator:
            continue

        x1, y1 = mercator[from_city]
        x2, y2 = mercator[to_city]

        ax.annotate(
            "",
            xy=(x2, y2),
            xytext=(x1, y1),
            arrowprops=dict(
                arrowstyle="-|>",
                color="#e63946",
                lw=2.5,
                mutation_scale=20,
            ),
        )

    # 都市の点とラベルを描画
    for name, (x, y) in mercator.items():
        is_start = name == route_names[0]
        color = "#e63946" if is_start else "#457b9d"
        size = 120 if is_start else 80

        ax.scatter(
            x, y, s=size, color=color, zorder=5, edgecolors="white", linewidths=1.5
        )
        ax.annotate(
            name,
            xy=(x, y),
            xytext=(8, 8),
            textcoords="offset points",
            fontsize=11,
            fontweight="bold",
            color="#1d3557",
            bbox=dict(
                boxstyle="round,pad=0.3",
                facecolor="white",
                edgecolor="#adb5bd",
                alpha=0.85,
            ),
        )

    # タイトルと凡例
    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    ax.set_axis_off()

    legend_elements = [
        mpatches.Patch(color="#e63946", label="出発地"),
        mpatches.Patch(color="#457b9d", label="経由地"),
        plt.Line2D(
            [0],
            [0],
            color="#e63946",
            linewidth=2,
            marker=">",
            markersize=8,
            label="最適ルート",
        ),
    ]
    ax.legend(
        handles=legend_elements,
        loc="lower right",
        fontsize=9,
        framealpha=0.9,
    )

    plt.tight_layout()

    if save_path is not None:
        path = Path(save_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(str(path), dpi=150, bbox_inches="tight")
        print(f"  地図を保存しました: {path}")
    else:
        plt.show()

    plt.close(fig)
