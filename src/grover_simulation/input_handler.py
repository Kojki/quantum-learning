"""対話形式でシミュレーションの設定を入力するモジュール。

main.py から呼び出され、ユーザーの入力を受け取り
config.py と同じ形式の設定辞書を返す。
入力を省略した場合は config.py のデフォルト値を使用する。
"""

from __future__ import annotations

from pathlib import Path

import config


# ---------------------------------------------------------------------------
# 内部ユーティリティ
# ---------------------------------------------------------------------------


def _ask(prompt: str, default) -> str:
    """デフォルト値付きの入力プロンプトを表示し、入力文字列を返す。

    何も入力せずにEnterを押した場合はデフォルト値を文字列に変換して返す。

    Args:
        prompt: 表示するプロンプト文字列。
        default: デフォルト値。

    Returns:
        入力された文字列、または str(default)。
    """
    raw = input(f"{prompt} [デフォルト: {default}]: ").strip()
    return raw if raw else str(default)


def _ask_int(prompt: str, default: int) -> int:
    """整数値の入力を受け取る。不正な値は再入力を促す。"""
    while True:
        raw = _ask(prompt, default)
        try:
            return int(raw)
        except ValueError:
            print(f"  ⚠️  整数で入力してください。")


def _ask_float(prompt: str, default: float) -> float:
    """浮動小数点数の入力を受け取る。不正な値は再入力を促す。"""
    while True:
        raw = _ask(prompt, default)
        try:
            return float(raw)
        except ValueError:
            print(f"  ⚠️  数値で入力してください。")


def _ask_choice(prompt: str, choices: list[str], default: str) -> str:
    """選択肢の中から入力を受け取る。選択肢外の値は再入力を促す。"""
    choices_str = "/".join(choices)
    while True:
        raw = _ask(f"{prompt}（{choices_str}）", default)
        if raw in choices:
            return raw
        print(f"  ⚠️  {choices_str} のいずれかを入力してください。")


# ---------------------------------------------------------------------------
# 各項目の入力
# ---------------------------------------------------------------------------


def _input_city_names() -> list[str]:
    """都市名をカンマ区切りで入力する。"""
    default_str = ",".join(config.CITY_NAMES)
    while True:
        raw = _ask("都市名（カンマ区切り、2都市以上）", default_str)
        names = [n.strip() for n in raw.split(",") if n.strip()]
        if len(names) >= 2:
            return names
        print("  ⚠️  2都市以上を入力してください。")


def _input_distance_matrix(city_names: list[str]) -> list[list[float]]:
    """距離行列を1行ずつ入力する。"""
    n = len(city_names)
    print(f"\n  距離行列を入力します（{n}×{n}、スペース区切り）。")
    print(f"  対角成分（自分→自分）は 0 にしてください。")

    # デフォルト値の準備（config と都市数が一致する場合はそのまま使う）
    if len(config.DISTANCE_MATRIX) == n:
        default_matrix = config.DISTANCE_MATRIX
    else:
        # 都市数が異なる場合は単純なデフォルト行列を生成
        default_matrix = [
            [0 if i == j else (i + j + 1) * 5 for j in range(n)] for i in range(n)
        ]

    matrix = []
    for i, name in enumerate(city_names):
        default_row = " ".join(str(v) for v in default_matrix[i])
        while True:
            raw = _ask(f"  {name} からの距離（{n}個）", default_row)
            values = raw.split()
            if len(values) != n:
                print(f"  ⚠️  {n}個の値をスペース区切りで入力してください。")
                continue
            try:
                row = [float(v) for v in values]
                if row[i] != 0:
                    print(f"  ⚠️  {name}→{name} の距離は 0 にしてください。")
                    continue
                matrix.append(row)
                break
            except ValueError:
                print("  ⚠️  数値で入力してください。")

    return matrix


def _input_gif_path() -> str | None:
    """GIF保存先パスを入力する。空欄ならウィンドウ表示。"""
    default_str = str(Path("output"))
    raw = input(
        f"  GIF 保存先ディレクトリ（空欄でウィンドウ表示）[デフォルト: {default_str}]: "
    ).strip()
    if not raw:
        raw = default_str
    if raw.lower() in ("none", "なし", ""):
        return None
    return raw


# ---------------------------------------------------------------------------
# メイン入力関数
# ---------------------------------------------------------------------------


def load_config_interactive() -> dict:
    """対話形式で設定を入力し、設定辞書を返す。

    各項目でEnterを押すと config.py のデフォルト値が使われる。

    Returns:
        以下のキーを持つ設定辞書：
            city_names, distance_matrix, cost_threshold,
            shots, ancilla_mode, noise_model, device,
            gate_time_1q, seed, output_dir
    """
    print("\n" + "=" * 50)
    print("  対話形式で設定を入力します。")
    print("  Enterを押すとデフォルト値を使用します。")
    print("=" * 50)

    # --- 問題の設定 ---
    print("\n【問題の設定】")
    city_names = _input_city_names()
    distance_matrix = _input_distance_matrix(city_names)
    cost_threshold = _ask_float(
        "コストのしきい値（この値以下のルートを正解とする）",
        config.COST_THRESHOLD,
    )

    # --- シミュレーションの設定 ---
    print("\n【シミュレーションの設定】")
    shots = _ask_int("ショット数", config.SHOTS)
    ancilla_mode = _ask_choice(
        "ancilla モード",
        ["single", "extra", "compare"],
        config.ANCILLA_MODE,
    )
    noise_model = _ask_choice(
        "ノイズモデル",
        ["ideal", "depol", "thermal", "combined"],
        config.NOISE_MODEL,
    )
    device = config.DEVICE
    if noise_model in ("thermal", "combined"):
        device = _ask_choice(
            "デバイスプリセット",
            ["eagle_r3", "heron_r1", "heron_r2", "heron_r3"],
            config.DEVICE,
        )
    seed = _ask_int("乱数シード", config.SEED)

    # --- 可視化の設定 ---
    print("\n【可視化の設定】")
    output_dir = _input_gif_path()

    print("\n設定の入力が完了しました。")

    return {
        "city_names": city_names,
        "distance_matrix": distance_matrix,
        "cost_threshold": cost_threshold,
        "shots": shots,
        "ancilla_mode": ancilla_mode,
        "noise_model": noise_model,
        "device": device,
        "gate_time_1q": config.GATE_TIME_1Q,
        "seed": seed,
        "output_dir": output_dir,
    }


def load_config_from_file() -> dict:
    """config.py の設定をそのまま辞書として返す。"""
    return {
        "city_names": config.CITY_NAMES,
        "distance_matrix": config.DISTANCE_MATRIX,
        "cost_threshold": config.COST_THRESHOLD,
        "shots": config.SHOTS,
        "ancilla_mode": config.ANCILLA_MODE,
        "noise_model": config.NOISE_MODEL,
        "device": config.DEVICE,
        "gate_time_1q": config.GATE_TIME_1Q,
        "seed": config.SEED,
        "output_dir": str(Path("output")),
    }


def select_config_mode() -> dict:
    """起動時に config.py を使うか対話入力するかを選ぶ。

    Returns:
        load_config_from_file() または load_config_interactive() の結果。
    """
    print("\n" + "=" * 50)
    print("  Grover シミュレーター")
    print("=" * 50)
    print("\n設定の読み込み方法を選んでください：")
    print("  1. config.py の設定をそのまま使う")
    print("  2. 対話形式で入力する")

    while True:
        raw = input("\n選択 [1/2]: ").strip()
        if raw == "1":
            print("\nconfig.py の設定を使用します。")
            return load_config_from_file()
        if raw == "2":
            return load_config_interactive()
        print("  ⚠️  1 または 2 を入力してください。")
