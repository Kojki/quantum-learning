from flask import Flask, render_template, request
from threading import Thread
import time

app = Flask(__name__)
cfg_result = None


@app.route("/")
def index():
    return render_template("grover_config_ui.html")


@app.route("/submit", methods=["POST"])
def submit():
    global cfg_result
    cfg_result = request.get_json()
    return "設定を受け取りました。ターミナルに戻ってください。"


def get_config_from_web():
    global cfg_result
    cfg_result = None

    # Flaskサーバーを別スレッドで起動
    def run_server():
        app.run(port=5000, debug=False, use_reloader=False)

    t = Thread(target=run_server)
    t.daemon = True
    t.start()

    print("http://127.0.0.1:5000 を開いて設定してください")
    print("設定完了後『コードを生成』を押してください")

    # 設定が届くまで待機
    while cfg_result is None:
        time.sleep(0.2)

    return cfg_result
