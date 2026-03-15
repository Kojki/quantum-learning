"""可視化モジュール共通のユーティリティ。

色・ラベル・保存ロジックなど、animation.py と state_plotter.py の
両方から使う処理をまとめる。
"""

from __future__ import annotations

import math
from pathlib import Path

import platform

import matplotlib.pyplot as plt
import matplotlib.animation as anim
from matplotlib.animation import FuncAnimation
import matplotlib.font_manager as fm

# ---------------------------------------------------------------------------
# 日本語フォントの設定
# ---------------------------------------------------------------------------


def _setup_japanese_font() -> None:
    """OSに応じて日本語フォントを自動設定する。

    対応OS：
        Windows : Yu Gothic / MS Gothic
        macOS   : Hiragino Sans
        Linux   : システムにインストール済みの日本語フォントを自動検索
    """
    os_name = platform.system()

    if os_name == "Windows":
        candidates = ["Yu Gothic", "MS Gothic", "Meiryo"]
    elif os_name == "Darwin":  # macOS
        candidates = ["Hiragino Sans", "Hiragino Kaku Gothic Pro", "AppleGothic"]
    else:  # Linux
        # システムにインストール済みのフォントから日本語対応のものを探す
        available = {f.name for f in fm.fontManager.ttflist}
        candidates = [
            "Noto Sans CJK JP",
            "Noto Sans JP",
            "IPAexGothic",
            "IPAGothic",
            "TakaoGothic",
            "VL Gothic",
        ]
        candidates = [c for c in candidates if c in available]

    for font_name in candidates:
        try:
            plt.rcParams["font.family"] = font_name
            # テスト描画で確認
            fig, ax = plt.subplots()
            ax.set_title("テスト")
            plt.close(fig)
            return  # 成功したらそのまま使う
        except Exception:
            continue

    # どれも見つからない場合の警告
    print(
        "⚠️  日本語フォントが見つかりませんでした。"
        "Linux の場合は以下のコマンドでインストールできます：\n"
        "    sudo apt install fonts-noto-cjk\n"
        "インストール後、もう一度実行してください。"
    )


# フォント設定をモジュール読み込み時に自動実行
_setup_japanese_font()

# ---------------------------------------------------------------------------
# 色の定義
# ---------------------------------------------------------------------------

# 正解ビット列のハイライト色
COLOR_TARGET = "#e63946"  # 赤系（目立つ色）
# 通常のビット列の色（理想シミュレーション）
COLOR_IDEAL = "#457b9d"  # 青系
# 通常のビット列の色（ノイズありシミュレーション）
COLOR_NOISY = "#2a9d8f"  # 緑系
# グラフ背景
COLOR_BG = "#f8f9fa"


# ---------------------------------------------------------------------------
# ラベル生成
# ---------------------------------------------------------------------------


def make_bar_labels(n_qubits: int) -> list[str]:
    """全ビット列のラベルを生成する。

    Args:
        n_qubits: 量子ビット数。

    Returns:
        ``["000", "001", ..., "111"]`` 形式のリスト。
    """
    return [format(i, f"0{n_qubits}b") for i in range(2**n_qubits)]


def make_bar_colors(
    labels: list[str],
    target_bitstrings: list[str],
    base_color: str,
    target_color: str = COLOR_TARGET,
) -> list[str]:
    """各棒の色リストを返す。正解ビット列だけ target_color にする。

    Args:
        labels: make_bar_labels() が返すリスト。
        target_bitstrings: 正解のビット列リスト。
        base_color: 通常の棒の色。
        target_color: 正解の棒の色。

    Returns:
        labels と同じ長さの色文字列リスト。
    """
    target_set = set(target_bitstrings)
    return [target_color if label in target_set else base_color for label in labels]


def bitstring_to_route_label(
    bitstring: str,
    problem,
) -> str:
    """ビット列を都市名のルート表記に変換する。

    X軸ラベルをビット列ではなく人間が読める形で表示するために使う。

    Args:
        bitstring: エンコードされたビット列。
        problem: OptimizationProblem のインスタンス。

    Returns:
        例: ``"A→C→B"``。変換に失敗した場合はビット列をそのまま返す。
    """
    try:
        return problem.route_to_str(bitstring).replace(" → ", "→").rsplit("→", 1)[0]
    except Exception:
        return bitstring


def make_axis_labels(
    labels: list[str],
    problem,
    max_display: int = 20,
) -> tuple[list[int], list[str]]:
    """X軸に表示する目盛りの位置とラベルを返す。

    ビット列が多い場合は間引いて表示する。
    正解ビット列は必ず含める。

    Args:
        labels: 全ビット列のリスト。
        problem: OptimizationProblem のインスタンス。
        max_display: 最大表示数。

    Returns:
        (表示する目盛りのインデックスリスト, 対応するラベル文字列リスト)
    """
    n = len(labels)
    if n <= max_display:
        tick_indices = list(range(n))
    else:
        # 均等間引き
        step = n // max_display
        tick_indices = list(range(0, n, step))

    tick_labels = [bitstring_to_route_label(labels[i], problem) for i in tick_indices]
    return tick_indices, tick_labels


# ---------------------------------------------------------------------------
# 保存・表示の切り替え
# ---------------------------------------------------------------------------


def save_or_show(
    animation: FuncAnimation,
    save_path: str | Path | None,
    fps: int = 4,
    dpi: int = 120,
) -> None:
    """アニメーションを保存するか、ウィンドウで表示するかを切り替える。

    save_path が指定されていれば GIF として保存する。
    None の場合は ``plt.show()`` でリアルタイム表示する。

    Args:
        animation: matplotlib の FuncAnimation オブジェクト。
        save_path: 保存先のパス（拡張子 .gif）。None ならウィンドウ表示。
        fps: GIF のフレームレート。
        dpi: GIF の解像度。
    """
    if save_path is not None:
        path = Path(save_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        animation.save(str(path), writer="pillow", fps=fps, dpi=dpi)
        print(f"アニメーションを保存しました: {path}")
    else:
        plt.show()


# ---------------------------------------------------------------------------
# タイトル文字列の生成
# ---------------------------------------------------------------------------


def make_frame_title(iteration: int, n_iterations: int) -> str:
    """フレームタイトルを返す。

    Args:
        iteration: 現在の反復回数（0 = 初期状態）。
        n_iterations: 最適反復回数。

    Returns:
        例: ``"反復 2 / 3"`` または ``"初期状態（重ね合わせ）"``
    """
    if iteration == 0:
        return "初期状態（均一な重ね合わせ）"
    return f"反復 {iteration} / {n_iterations}"
