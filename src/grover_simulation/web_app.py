from __future__ import annotations

import signal
import sys
from threading import Thread, Event

from flask import Flask, render_template, request

import config

app = Flask(__name__)

_cfg_ready = Event()
_cfg_result: dict | None = None

# ---------------------------------------------------------------------------
# ルート
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    return render_template("grover_config_ui.html")


@app.route("/submit", methods=["POST"])
def submit():
    """Web UI（ステップ形式）から設定を受け取る。

    gate_time_1q はデバイスプリセットから自動補完する。
    """
    global _cfg_result
    from quantum.noise import DEVICE_PRESETS

    data = request.get_json()
    preset = DEVICE_PRESETS.get(
        data.get("device", "eagle_r3"), DEVICE_PRESETS["eagle_r3"]
    )
    data["gate_time_1q"] = preset["gate_time_1q"]
    _cfg_result = data
    _cfg_ready.set()
    return "設定を受け取りました。ターミナルに戻ってください。"


@app.route("/submit_file", methods=["POST"])
def submit_file():
    """「config.py の設定をそのまま使う」モード用エンドポイント。"""
    global _cfg_result
    _cfg_result = _load_config_from_file()
    _cfg_ready.set()
    return "config.py の設定を読み込みました。ターミナルに戻ってください。"


# ---------------------------------------------------------------------------
# config.py 読み込み
# ---------------------------------------------------------------------------


def _load_config_from_file() -> dict:
    """config.py の設定をそのまま辞書として返す。"""
    from pathlib import Path
    from quantum.noise import DEVICE_PRESETS

    preset = DEVICE_PRESETS.get(config.DEVICE, DEVICE_PRESETS["eagle_r3"])
    return {
        "city_names": config.CITY_NAMES,
        "distance_matrix": config.DISTANCE_MATRIX,
        "use_geo": False,
        "max_iterations": config.MAX_ITERATIONS,
        "shots": config.SHOTS,
        "ancilla_mode": config.ANCILLA_MODE,
        "noise_model": config.NOISE_MODEL,
        "device": config.DEVICE,
        "gate_time_1q": preset["gate_time_1q"],
        "seed": config.SEED,
        "output_dir": str(Path("output")),
    }


# ---------------------------------------------------------------------------
# エントリポイント
# ---------------------------------------------------------------------------


def get_config_from_web() -> dict:
    """Flask サーバーを起動し、Web UI から設定が届くまで待機して返す。

    Ctrl+C を受け取った場合はプロセスを終了する。
    """
    global _cfg_result
    _cfg_result = None
    _cfg_ready.clear()

    def _run_server() -> None:
        # Flask の開発サーバーログを最小限に抑える
        import logging

        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)
        app.run(port=5000, debug=False, use_reloader=False)

    t = Thread(target=_run_server, daemon=True)
    t.start()

    print("\nブラウザで http://127.0.0.1:5000 を開いて設定してください。")
    print("設定完了後『コードを生成』ボタンを押してください。")
    print("中断する場合は Ctrl+C を押してください。\n")

    # Ctrl+C でブロックを解除してプロセスを終了できるよう
    # タイムアウト付きのポーリングループで待機する
    try:
        while not _cfg_ready.is_set():
            _cfg_ready.wait(timeout=0.5)
    except KeyboardInterrupt:
        print("\n⚠️  中断されました。終了します。")
        sys.exit(0)

    return _cfg_result
