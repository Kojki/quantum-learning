from __future__ import annotations

import sys
from threading import Thread, Event

from flask import Flask, render_template, request, jsonify

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


@app.route("/geocode", methods=["POST"])
def geocode():
    """都市名リストの座標をジオコーディングして返す。
    UIの座標確認ステップで使用する。
    """
    from geo.geocoder import geocode_cities

    data = request.get_json()
    city_names = data.get("city_names", [])
    try:
        coords = geocode_cities(city_names)
        return jsonify(
            {
                "status": "ok",
                "coords": {
                    name: {"lat": lat, "lng": lng}
                    for name, (lat, lng) in coords.items()
                },
                "failed": [n for n in city_names if n not in coords],
            }
        )
    except RuntimeError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/submit", methods=["POST"])
def submit():
    """Web UI（ステップ形式）から設定を受け取る。"""
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
    global _cfg_result
    _cfg_result = None
    _cfg_ready.clear()

    def _run_server() -> None:
        import logging

        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)
        app.run(port=5000, debug=False, use_reloader=False)

    t = Thread(target=_run_server, daemon=True)
    t.start()

    print("\nブラウザで http://127.0.0.1:5000 を開いて設定してください。")
    print("設定完了後『コードを生成』ボタンを押してください。")
    print("中断する場合は Ctrl+C を押してください。\n")

    try:
        while not _cfg_ready.is_set():
            _cfg_ready.wait(timeout=0.5)
    except KeyboardInterrupt:
        print("\n⚠️  中断されました。終了します。")
        sys.exit(0)

    return _cfg_result
