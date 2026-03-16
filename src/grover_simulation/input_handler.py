"""対話形式でシミュレーションの設定を入力するモジュール。

main.py から呼び出され、ユーザーの入力を受け取り
config.py と同じ形式の設定辞書を返す。
入力を省略した場合は config.py のデフォルト値を使用する。
"""

from __future__ import annotations

from pathlib import Path

import config


# ---------------------------------------------------------------------------
# サンプル問題
# ---------------------------------------------------------------------------

SAMPLE_PROBLEMS = {
    "1": {
        "label": "日本の主要都市（4都市）",
        "city_names": ["東京", "大阪", "名古屋", "福岡"],
        "use_geo": True,
    },
    "2": {
        "label": "ヨーロッパの主要都市（4都市）",
        "city_names": ["London", "Paris", "Berlin", "Rome"],
        "use_geo": True,
    },
    "3": {
        "label": "シンプルなテスト問題（3都市・距離は手動設定）",
        "city_names": ["A", "B", "C"],
        "use_geo": False,
        "distance_matrix": [
            [0, 10, 25],
            [10, 0, 15],
            [25, 15, 0],
        ],
    },
}


# ---------------------------------------------------------------------------
# 内部ユーティリティ
# ---------------------------------------------------------------------------


def _ask(prompt: str, default) -> str:
    """デフォルト値付きの入力プロンプトを表示し、入力文字列を返す。"""
    raw = input(f"{prompt} [デフォルト: {default}]: ").strip()
    return raw if raw else str(default)


def _ask_int(prompt: str, default: int) -> int:
    """整数値の入力を受け取る。不正な値は再入力を促す。"""
    while True:
        raw = _ask(prompt, default)
        try:
            return int(raw)
        except ValueError:
            print("  ⚠️  整数で入力してください。")


def _ask_float(prompt: str, default: float) -> float:
    """浮動小数点数の入力を受け取る。不正な値は再入力を促す。"""
    while True:
        raw = _ask(prompt, default)
        try:
            return float(raw)
        except ValueError:
            print("  ⚠️  数値で入力してください。")


def _ask_choice(prompt: str, choices: list[str], default: str) -> str:
    """選択肢の中から入力を受け取る。選択肢外の値は再入力を促す。"""
    choices_str = "/".join(choices)
    while True:
        raw = _ask(f"{prompt}（{choices_str}）", default)
        if raw in choices:
            return raw
        print(f"  ⚠️  {choices_str} のいずれかを入力してください。")


# ---------------------------------------------------------------------------
# 都市・距離行列の入力（3パターン）
# ---------------------------------------------------------------------------


def _input_by_count() -> tuple[list[str], list[list[float]], bool]:
    """都市数だけ指定し、名前は A, B, C... と自動設定する。

    Returns:
        (city_names, distance_matrix, use_geo)
    """
    while True:
        n = _ask_int("都市数（2以上）", len(config.CITY_NAMES))
        if n >= 2:
            break
        print("  ⚠️  2以上を入力してください。")

    city_names = [chr(ord("A") + i) for i in range(n)]
    print(f"  都市名を自動設定しました: {city_names}")
    distance_matrix = _input_distance_matrix(city_names)
    return city_names, distance_matrix, False


def _input_by_name() -> tuple[list[str], list[list[float]], bool]:
    """都市名を入力し、座標自動取得か距離手動入力かを選ぶ。

    Returns:
        (city_names, distance_matrix, use_geo)
    """
    while True:
        raw = _ask(
            "都市名（カンマ区切り、2都市以上）",
            ",".join(config.CITY_NAMES),
        )
        names = [n.strip() for n in raw.split(",") if n.strip()]
        if len(names) >= 2:
            break
        print("  ⚠️  2都市以上を入力してください。")

    print("\n距離の設定方法を選んでください：")
    print("  1. 地名から座標を自動取得して実距離を計算する（インターネット接続が必要）")
    print("  2. 距離行列を手動で入力する")

    while True:
        choice = input("選択 [1/2]: ").strip()
        if choice == "1":
            return names, [], True
        if choice == "2":
            matrix = _input_distance_matrix(names)
            return names, matrix, False
        print("  ⚠️  1 または 2 を入力してください。")


def _input_by_sample() -> tuple[list[str], list[list[float]], bool]:
    """用意されたサンプル問題を選ぶ。

    Returns:
        (city_names, distance_matrix, use_geo)
    """
    print("\nサンプル問題を選んでください：")
    for key, sample in SAMPLE_PROBLEMS.items():
        print(f"  {key}. {sample['label']}")

    while True:
        choice = input("選択: ").strip()
        if choice in SAMPLE_PROBLEMS:
            sample = SAMPLE_PROBLEMS[choice]
            print(f"  「{sample['label']}」を選択しました。")
            if sample["use_geo"]:
                return sample["city_names"], [], True
            else:
                return (
                    sample["city_names"],
                    sample["distance_matrix"],
                    False,
                )
        print(f"  ⚠️  {'/'.join(SAMPLE_PROBLEMS.keys())} のいずれかを入力してください。")


def _input_distance_matrix(city_names: list[str]) -> list[list[float]]:
    """距離行列を1行ずつ入力する。"""
    n = len(city_names)
    print(f"\n  距離行列を入力します（{n}×{n}、スペース区切り）。")
    print("  対角成分（自分→自分）は 0 にしてください。")

    if len(config.DISTANCE_MATRIX) == n:
        default_matrix = config.DISTANCE_MATRIX
    else:
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


# ---------------------------------------------------------------------------
# 都市入力モードの選択
# ---------------------------------------------------------------------------


def _select_city_input_mode() -> tuple[list[str], list[list[float]], bool]:
    """都市の入力方法を選ぶ。

    Returns:
        (city_names, distance_matrix, use_geo)
        use_geo が True の場合、distance_matrix は空リストで返す。
        main.py 側で geo モジュールを使って距離行列を生成する。
    """
    print("\n【都市の入力方法】")
    print("  1. 都市数だけ指定する（名前は A, B, C... と自動設定）")
    print("  2. 都市名を自分で入力する")
    print("  3. サンプル問題を選ぶ")

    while True:
        choice = input("選択 [1/2/3]: ").strip()
        if choice == "1":
            return _input_by_count()
        if choice == "2":
            return _input_by_name()
        if choice == "3":
            return _input_by_sample()
        print("  ⚠️  1、2、3 のいずれかを入力してください。")


# ---------------------------------------------------------------------------
# メイン入力関数
# ---------------------------------------------------------------------------


def load_config_interactive() -> dict:
    """対話形式で設定を入力し、設定辞書を返す。

    Returns:
        以下のキーを持つ設定辞書：
            city_names, distance_matrix, use_geo,
            shots, ancilla_mode, noise_model,
            device, gate_time_1q, seed, output_dir
    """
    print("\n" + "=" * 50)
    print("  対話形式で設定を入力します。")
    print("  Enterを押すとデフォルト値を使用します。")
    print("=" * 50)

    # --- 都市の設定 ---
    print("\n【問題の設定】")
    city_names, distance_matrix, use_geo = _select_city_input_mode()

    max_iterations = _ask_int(
        "\nDurr-Hoyer の最大反復回数",
        config.MAX_ITERATIONS,
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
        ["ideal", "depol", "thermal", "combined", "readout"],
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
        "use_geo": use_geo,
        "max_iterations": max_iterations,
        "shots": shots,
        "ancilla_mode": ancilla_mode,
        "noise_model": noise_model,
        "device": device,
        "gate_time_1q": config.GATE_TIME_1Q,
        "seed": seed,
        "output_dir": output_dir,
    }


def _input_gif_path() -> str | None:
    """GIF保存先パスを入力する。空欄ならウィンドウ表示。"""
    default_str = str(Path("output"))
    raw = input(
        f"  GIF 保存先ディレクトリ（空欄でウィンドウ表示）[デフォルト: {default_str}]: "
    ).strip()
    if not raw:
        raw = default_str
    if raw.lower() in ("none", "なし"):
        return None
    return raw


def load_config_from_file() -> dict:
    """config.py の設定をそのまま辞書として返す。"""
    return {
        "city_names": config.CITY_NAMES,
        "distance_matrix": config.DISTANCE_MATRIX,
        "use_geo": False,
        "max_iterations": config.MAX_ITERATIONS,
        "shots": config.SHOTS,
        "ancilla_mode": config.ANCILLA_MODE,
        "noise_model": config.NOISE_MODEL,
        "device": config.DEVICE,
        "gate_time_1q": config.GATE_TIME_1Q,
        "seed": config.SEED,
        "output_dir": str(Path("output")),
    }


def select_config_mode() -> dict:
    """起動時に config.py を使うか対話入力するかを選ぶ。"""
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
