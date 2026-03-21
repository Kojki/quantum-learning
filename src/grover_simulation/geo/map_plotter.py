"""地図上に都市と最適ルートを描画するモジュール。

contextily で OpenStreetMap のタイル画像を背景として使い、
matplotlib で都市の位置と最適ルートを重ねて描画する。

座標が不明な場合は距離行列から MDS（多次元尺度法）で
近似座標を生成して描画する。

使い方::

    from geo.map_plotter import plot_route, plot_route_from_matrix

    # 実座標から描画（use_geo=True のとき）
    plot_route(
        coords={"福岡": (33.59, 130.40), "大阪": (34.69, 135.50)},
        best_route="福岡 → 大阪 → 福岡",
        title="Grover が見つけた最短ルート",
        save_path="output/route_map.png",
    )

    # 距離行列から近似座標を生成して描画（use_geo=False のとき）
    plot_route_from_matrix(
        distance_matrix=[[0,10,25],[10,0,15],[25,15,0]],
        city_names=["A","B","C"],
        best_route="A → B → C → A",
        title="Grover が見つけた最短ルート（近似座標）",
        save_path="output/route_map.png",
    )
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker


# ---------------------------------------------------------------------------
# MDS による近似座標生成
# ---------------------------------------------------------------------------


def _mds_coords(
    distance_matrix: list[list[float]],
) -> list[tuple[float, float]]:
    """距離行列から MDS（古典的多次元尺度法）で 2D 近似座標を生成する。

    完全に正確な座標にはならないが、
    「近い都市同士は近くに、遠い都市同士は遠くに」という
    相対的な位置関係を保った座標が得られる。

    Args:
        distance_matrix: n×n の距離行列。

    Returns:
        [(x0, y0), (x1, y1), ...] の座標リスト。
    """
    D = np.array(distance_matrix, dtype=float)
    n = len(D)

    # 距離行列を二乗
    D2 = D**2

    # センタリング行列 H = I - (1/n) * 11^T
    H = np.eye(n) - np.ones((n, n)) / n

    # グラム行列 B = -0.5 * H * D2 * H
    B = -0.5 * H @ D2 @ H

    # 固有値分解（上位2次元を取得）
    eigvals, eigvecs = np.linalg.eigh(B)

    # 固有値を降順にソート
    idx = np.argsort(eigvals)[::-1]
    eigvals = eigvals[idx]
    eigvecs = eigvecs[:, idx]

    # 負の固有値はゼロにクリップ（数値誤差対策）
    eigvals_pos = np.maximum(eigvals[:2], 0)

    # 2D 座標
    coords_2d = eigvecs[:, :2] * np.sqrt(eigvals_pos)

    return [(float(x), float(y)) for x, y in coords_2d]


# ---------------------------------------------------------------------------
# 共通描画ユーティリティ
# ---------------------------------------------------------------------------


def _draw_route(
    ax: plt.Axes,
    coords_2d: dict[str, tuple[float, float]],
    route_names: list[str],
    city_color_default: str = "#457b9d",
    city_color_start: str = "#e63946",
    arrow_color: str = "#e63946",
    label_fontsize: int = 11,
) -> None:
    """都市・ルート矢印・ラベルを Axes に描画する共通処理。"""

    # ルートの矢印
    for i in range(len(route_names) - 1):
        from_city = route_names[i]
        to_city = route_names[i + 1]
        if from_city not in coords_2d or to_city not in coords_2d:
            continue
        x1, y1 = coords_2d[from_city]
        x2, y2 = coords_2d[to_city]
        ax.annotate(
            "",
            xy=(x2, y2),
            xytext=(x1, y1),
            arrowprops=dict(
                arrowstyle="-|>",
                color=arrow_color,
                lw=2.5,
                mutation_scale=20,
            ),
        )

    # 都市の点とラベル
    for name, (x, y) in coords_2d.items():
        is_start = name == route_names[0]
        color = city_color_start if is_start else city_color_default
        size = 120 if is_start else 80
        ax.scatter(
            x, y, s=size, color=color, zorder=5, edgecolors="white", linewidths=1.5
        )
        ax.annotate(
            name,
            xy=(x, y),
            xytext=(8, 8),
            textcoords="offset points",
            fontsize=label_fontsize,
            fontweight="bold",
            color="#1d3557",
            bbox=dict(
                boxstyle="round,pad=0.3",
                facecolor="white",
                edgecolor="#adb5bd",
                alpha=0.85,
            ),
        )


def _add_legend(ax: plt.Axes) -> None:
    legend_elements = [
        mpatches.Patch(color="#e63946", label="Start"),
        mpatches.Patch(color="#457b9d", label="Waypoint"),
        plt.Line2D(
            [0],
            [0],
            color="#e63946",
            linewidth=2,
            marker=">",
            markersize=8,
            label="Optimal Route",
        ),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=9, framealpha=0.9)


def _save_or_show(fig: plt.Figure, save_path: str | Path | None, label: str) -> None:
    plt.tight_layout()
    if save_path is not None:
        path = Path(save_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(str(path), dpi=150, bbox_inches="tight")
        print(f"  {label}を保存しました: {path}")
    else:
        plt.show()
    plt.close(fig)


# ---------------------------------------------------------------------------
# 座標変換（WGS84 → Web メルカトル）
# ---------------------------------------------------------------------------


def _to_web_mercator(lat: float, lon: float) -> tuple[float, float]:
    """WGS84（緯度経度）を Web メルカトル座標（EPSG:3857）に変換する。"""
    from pyproj import Transformer

    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    x, y = transformer.transform(lon, lat)
    return x, y


# ---------------------------------------------------------------------------
# 実座標からの地図描画（use_geo=True）
# ---------------------------------------------------------------------------


def plot_route(
    coords: dict[str, tuple[float, float]],
    best_route: str,
    title: str = "Optimal Route",
    save_path: str | Path | None = None,
    zoom: int | None = None,
) -> None:
    """実座標（緯度経度）を使って OpenStreetMap 上にルートを描画する。

    Args:
        coords: ``{地名: (緯度, 経度)}`` の辞書。
        best_route: ``"福岡 → 大阪 → 東京 → 福岡"`` 形式のルート文字列。
        title: グラフのタイトル。
        save_path: 保存先パス（.png）。省略時はウィンドウ表示。
        zoom: 地図のズームレベル。省略時は自動調整。
    """
    import contextily as ctx

    route_names = [r.strip() for r in best_route.split("→")]

    # Web メルカトルに変換
    mercator: dict[str, tuple[float, float]] = {
        name: _to_web_mercator(lat, lon) for name, (lat, lon) in coords.items()
    }

    xs = [x for x, y in mercator.values()]
    ys = [y for x, y in mercator.values()]
    margin_x = (max(xs) - min(xs)) * 0.25 + 50000
    margin_y = (max(ys) - min(ys)) * 0.25 + 50000

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlim(min(xs) - margin_x, max(xs) + margin_x)
    ax.set_ylim(min(ys) - margin_y, max(ys) + margin_y)

    # OpenStreetMap タイルの取得を試みる
    tile_ok = False
    try:
        import contextily as ctx

        ctx.add_basemap(
            ax, crs="EPSG:3857", source=ctx.providers.OpenStreetMap.Mapnik, zoom=zoom
        )
        tile_ok = True
    except Exception as tile_err:
        print(f"  ⚠️  地図タイルの取得に失敗しました。背景なしで描画します。")

    if not tile_ok:
        ax.set_facecolor("#e8f4f8")
        ax.grid(True, alpha=0.25, linestyle="--", color="#90aec0")

    _draw_route(ax, mercator, route_names)
    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    ax.set_axis_off()
    _add_legend(ax)
    _save_or_show(fig, save_path, "地図")


# ---------------------------------------------------------------------------
# 距離行列からの近似座標描画（use_geo=False）
# ---------------------------------------------------------------------------


def plot_route_from_matrix(
    distance_matrix: list[list[float]],
    city_names: list[str],
    best_route: str,
    title: str = "Optimal Route (Distance-based Layout)",
    save_path: str | Path | None = None,
) -> None:
    """距離行列から MDS で近似座標を生成してルートを描画する。

    実際の地理座標は使わないため背景地図はなし。
    都市間の相対的な近遠関係を保った 2D 配置で描画する。

    Args:
        distance_matrix: n×n の距離行列。
        city_names: 距離行列の行・列に対応する都市名リスト。
        best_route: ``"A → B → C → A"`` 形式のルート文字列。
        title: グラフのタイトル。
        save_path: 保存先パス（.png）。省略時はウィンドウ表示。
    """
    coords_list = _mds_coords(distance_matrix)
    coords_2d = {name: coords_list[i] for i, name in enumerate(city_names)}

    route_names = [r.strip() for r in best_route.split("→")]

    xs = [x for x, y in coords_2d.values()]
    ys = [y for x, y in coords_2d.values()]
    margin_x = (max(xs) - min(xs)) * 0.20 + 1
    margin_y = (max(ys) - min(ys)) * 0.20 + 1

    fig, ax = plt.subplots(figsize=(8, 7))
    ax.set_xlim(min(xs) - margin_x, max(xs) + margin_x)
    ax.set_ylim(min(ys) - margin_y, max(ys) + margin_y)
    ax.set_facecolor("#f8f9fa")
    ax.grid(True, alpha=0.3, linestyle="--")

    # 全都市間の距離を薄い線で表示
    n = len(city_names)
    for i in range(n):
        for j in range(i + 1, n):
            x1, y1 = coords_2d[city_names[i]]
            x2, y2 = coords_2d[city_names[j]]
            ax.plot(
                [x1, x2], [y1, y2], color="#dee2e6", linewidth=0.8, zorder=1, alpha=0.6
            )

    _draw_route(ax, coords_2d, route_names)

    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("MDS Dimension 1 (relative distance)")
    ax.set_ylabel("MDS Dimension 2 (relative distance)")

    # 距離の凡例注記
    ax.text(
        0.01,
        0.01,
        "* Layout approximated from distance matrix using MDS.\n"
        "  Relative distances are preserved; absolute positions are not.",
        transform=ax.transAxes,
        fontsize=7,
        color="#6c757d",
        verticalalignment="bottom",
    )

    _add_legend(ax)
    _save_or_show(fig, save_path, "近似座標マップ")
