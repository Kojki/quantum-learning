from qiskit.circuit import Parameter, QuantumCircuit, ClassicalRegister, QuantumRegister
import tkinter as tk
from tkinter import ttk
from qulacs import QuantumState
from qulacs.gate import H
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram, plot_state_city
import qiskit.quantum_info as qi
from tqdm import tqdm
import time
import matplotlib.pyplot as plt
from qiskit.primitives import BackendSamplerV2
from qiskit_aer.noise import NoiseModel
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_ibm_runtime import SamplerV2 as Sampler
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_aer.noise import pauli_error, depolarizing_error
import numpy as np
import random


# ひらがな（および一部記号・英数字）と7ビットバイナリの対応表
def correspondence_table():
    # ビット→文字の対応表
    to_str_table = {
        "00000000": "あ",
        "00000001": "い",
        "00000010": "う",
        "00000011": "え",
        "00000100": "お",
        "00000101": "か",
        "00000110": "き",
        "00000111": "く",
        "00001000": "け",
        "00001001": "こ",
        "00001010": "さ",
        "00001011": "し",
        "00001100": "す",
        "00001101": "せ",
        "00001110": "そ",
        "00001111": "た",
        "00010000": "ち",
        "00010001": "つ",
        "00010010": "て",
        "00010011": "と",
        "00010100": "な",
        "00010101": "に",
        "00010110": "ぬ",
        "00010111": "ね",
        "00100000": "の",
        "00100001": "は",
        "00100010": "ひ",
        "00100011": "ふ",
        "00100100": "へ",
        "00100101": "ほ",
        "00100110": "ま",
        "00100111": "み",
        "00101000": "む",
        "00101001": "め",
        "00101010": "も",
        "00101011": "や",
        "00101100": "ゆ",
        "00101101": "よ",
        "00101110": "ら",
        "00101111": "り",
        "00110000": "る",
        "00110001": "れ",
        "00110010": "ろ",
        "00110011": "わ",
        "00110100": "を",
        "00110101": "ん",
        "00110110": "が",
        "00110111": "ぎ",
        "00111000": "ぐ",
        "00111001": "げ",
        "00111010": "ご",
        "00111011": "ざ",
        "00111100": "じ",
        "00111101": "ず",
        "00111110": "ぜ",
        "00111111": "ぞ",
        "01000000": "だ",
        "01000001": "ぢ",
        "01000010": "づ",
        "01000011": "で",
        "01000100": "ど",
        "01000101": "ば",
        "01000110": "び",
        "01000111": "ぶ",
        "01001000": "べ",
        "01001001": "ぼ",
        "01001010": "ぱ",
        "01001011": "ぴ",
        "01001100": "ぷ",
        "01001101": "ぺ",
        "01001110": "ぽ",
        "01001111": "ぁ",
        "01010000": "ぃ",
        "01010001": "ぅ",
        "01010010": "ぇ",
        "01010011": "ぉ",
        "01010100": "ゃ",
        "01010101": "ゅ",
        "01010110": "ょ",
        "01010111": "っ",
        "01011000": "ー",
        "01011001": "、",
        "01011010": "。",
        "01011011": "・",
        "01011100": "「",
        "01011101": "」",
        "01011110": " ",
        "01011111": "！",
        "01100000": "？",
        "01100001": "0",
        "01100010": "1",
        "01100011": "2",
        "01100100": "3",
        "01100101": "4",
        "01100110": "5",
        "01100111": "6",
        "01101000": "7",
        "01101001": "8",
        "01101010": "9",
        "01101011": "A",
        "01101100": "B",
        "01101101": "C",
        "01101110": "D",
        "01101111": "E",
        "01110000": "F",
        "01110001": "G",
        "01110010": "H",
        "01110011": "I",
        "01110100": "J",
        "01110101": "K",
        "01110110": "L",
        "01110111": "M",
        "01111000": "N",
        "01111001": "O",
        "01111010": "P",
        "01111011": "Q",
        "01111100": "R",
        "01111101": "S",
        "01111110": "T",
        "01111111": "U",
        "10000000": "V",
        "10000001": "W",
        "10000010": "X",
        "10000011": "Y",
        "10000100": "Z",
        "10000101": "a",
        "10000110": "b",
        "10000111": "c",
        "10001000": "d",
        "10001001": "e",
        "10001010": "f",
        "10001011": "g",
        "10001100": "h",
        "10001101": "i",
        "10001110": "j",
        "10001111": "k",
        "10010000": "l",
        "10010001": "m",
        "10010010": "n",
        "10010011": "o",
        "10010100": "p",
        "10010101": "q",
        "10010110": "r",
        "10010111": "s",
        "10011000": "t",
        "10011001": "u",
        "10011010": "v",
        "10011011": "w",
        "10011100": "x",
        "10011101": "y",
        "10011110": "z",
        "10011111": "!",
        "10100000": "?",
        "10100001": ".",
        "10100010": ",",
        "10100011": ":",
        "10100100": ";",
        "10100101": "(",
        "10100110": ")",
        "10100111": "[",
        "10101000": "]",
        "10101001": "{",
        "10101010": "}",
        "10101011": "@",
        "10101100": "#",
        "10101101": "$",
        "10101110": "%",
        "10101111": "^",
        "10110000": "&",
        "10110001": "*",
        "10110010": "+",
        "10110011": "=",
        "10110100": "<",
        "10110101": ">",
        "10110110": "/",
        "10110111": "\\",
        "10111000": "-",
        "10111001": "_",
        "10111010": "~",
    }
    # 文字→ビットの対応表
    to_bit_table = {v: k for k, v in to_str_table.items()}

    return to_str_table, to_bit_table


def introduction():
    print("このツールでは量子通信に関する簡単なシミュレーションができます。")
    selected_value = {"val": None}

    root = tk.Tk()
    root.title("選択")
    root.geometry("300x150")

    label = tk.Label(root, text="扱いたいテーマを選んでください。")
    label.pack(pady=10)

    values = ["BB84", "2", "3"]
    combobox = ttk.Combobox(root, values=values)
    combobox.pack(pady=10)

    def on_select():
        selected_value["val"] = combobox.get()
        root.destroy()

    button = tk.Button(root, text="決定", command=on_select)
    button.pack()
    root.mainloop()
    return selected_value["val"]


def information_input():
    # 入力
    input_data = input(
        "最適な長さの文字列を入力してください。それに応じたビット列を生成します。\n"
        "最終的に残るビット数は1/4程度になります。: "
    )
    return input_data


def encode_message(message_original, to_bit_table):
    # 文字をビットに変換
    encoded_list = []
    for character in message_original:
        if character in to_bit_table:
            encoded_list.append(to_bit_table[character])
            encoded = "".join(encoded_list)
        else:
            print(f"警告: '{character}' は対応表にありません")
            encoded_list.append("11111111")
            encoded = "".join(encoded_list)
    return encoded


def decode_message(bit_string, to_str_table):
    # ビットを文字に変換
    decoded_list = []
    for i in range(0, len(bit_string), 8):
        bit_chunk = bit_string[i : i + 8]
        if bit_chunk in to_str_table:
            decoded_list.append(to_str_table[bit_chunk])
            decoded = "".join(decoded_list)
        else:
            print(f"警告:通信がうまくいっていません。")
    return "".join(decoded)


# 量子乱数
def generate_quantum_random_bit(number_of_bits):
    state = QuantumState(1)
    state.set_zero_state()
    gate = H(0)
    gate.update_quantum_state(state)

    # 測定
    result = state.sampling(number_of_bits)[0]
    return result


# ノイズモデル
def get_advanced_noise_model(distance_km):
    noise_model = NoiseModel()

    # 通信路ノイズ
    # 距離に応じて減衰
    p_chan = 1 - np.exp(-0.0005 * distance_km)
    error_chan = depolarizing_error(p_chan, 1)
    noise_model.add_all_qubit_quantum_error(error_chan, ["h", "x"])

    # 暗計数ノイズ
    # 0.5%の確率で誤検出
    p_dark = 0.005
    error_dark = pauli_error([("X", p_dark), ("I", 1 - p_dark)])
    noise_model.add_all_qubit_quantum_error(error_dark, "measure")

    return noise_model


# QBER解析
def analyze_qber(alice_bits, bob_bits, alice_bases, bob_bases, sample_ratio=0.2):
    # 基底が一致しているか
    matches = [i for i in range(len(alice_bases)) if alice_bases[i] == bob_bases[i]]
    if not matches:
        return 0, 0, "", ""

    # サンプルの抽出
    sample_size = int(len(matches) * sample_ratio)
    sample_size = max(4, sample_size)
    sample_sequence = random.sample(matches, sample_size)
    sample_errors = sum(1 for i in sample_sequence if alice_bits[i] != bob_bits[i])
    qber = sample_errors / sample_size

    # 最終鍵の生成
    key_sequence = [i for i in matches if i not in sample_sequence]
    final_alice_key = "".join([alice_bits[i] for i in key_sequence])
    final_bob_key = "".join([bob_bits[i] for i in key_sequence])

    return (
        qber,
        len(matches),
        final_alice_key,
        final_bob_key,
    )  # エラー率, 一致ビット数, 最終鍵(Alice, Bob)


# メイン処理
selected_mode = introduction()

if selected_mode == "BB84":
    print("--- BB84プロトコルシミュレーション ---")
    to_str_table, to_bit_table = correspondence_table()
    message_original = information_input()
    bit_sequence = encode_message(message_original, to_bit_table)

    n_bits = len(bit_sequence)
    print(f"送信ビット列: {bit_sequence} (長さ: {n_bits})")

    # 条件設定
    distance_km = float(input("通信の距離をkm単位で入力してください。: "))

    eve_present = input("イブ（盗聴者）を介入させますか？ (y/n): ").lower() == "y"

    alice_bases = []
    bob_bases = []
    eve_bases = []
    all_measured_bits = ""

    # バッチ処理
    batch_size = 100
    for batch_idx, start in enumerate(range(0, len(bit_sequence), batch_size)):
        end = min(start + batch_size, len(bit_sequence))
        current_bits = bit_sequence[start:end]  # バッチごとに送るビット
        n_current = len(current_bits)  # バッチごとの回路のサイズ
        print(f"バッチ {batch_idx + 1}: {start}~{end-1}ビット目を処理中...")

        # 各バッチごとに回路を作成
        qr = QuantumRegister(n_current, "q")
        cr = ClassicalRegister(n_current, "c")
        qc = QuantumCircuit(qr, cr)

        # Alice（送信準備）
        for i in range(n_current):
            a_base = generate_quantum_random_bit(1)
            alice_bases.append(a_base)

            if current_bits[i] == "1":
                qc.x(i)
            if a_base == 1:
                qc.h(i)
        qc.barrier()  # 作業終了

        # Eve（盗聴）
        if eve_present:
            for i in range(n_current):
                e_base = generate_quantum_random_bit(1)
                eve_bases.append(e_base)

                if e_base == 1:
                    qc.h(i)
                qc.measure(i, i)  # 盗聴
                # 測定後の辻褄合わせ
                if e_base == 1:
                    qc.h(i)
            qc.barrier()  # 作業終了
        # Bob（受信）
        for i in range(n_current):
            b_base = generate_quantum_random_bit(1)
            bob_bases.append(b_base)

            if b_base == 1:
                qc.h(i)
            qc.measure(i, i)  # Bobの測定
        qc.barrier()  # 作業終了

        # シミュレーション実行
        noise_model = get_advanced_noise_model(distance_km)
        simulator = AerSimulator(method="stabilizer", noise_model=noise_model)  # 高速化
        job = simulator.run(qc, shots=1, memory=True)
        batch_result = job.result()

        # Qiskitを用いているためビット順を反転
        measured_bits_str = batch_result.get_memory()[0][::-1]
        all_measured_bits += measured_bits_str
    print("\n全バッチの処理が完了しました。")

    alice_bits = bit_sequence
    bob_bits = all_measured_bits
    qber, key_len, final_alice_key, final_bob_key = analyze_qber(
        alice_bits, bob_bits, alice_bases, bob_bases
    )

    # 最終鍵の生成
    alice_final_key = final_alice_key
    bob_final_key = final_bob_key

    for i in tqdm(range(100), desc="最終鍵の生成中…"):
        time.sleep(0.05)

    print("\n--- 実行結果 ---")
    print("最大50ビットまで表示します。")

    print(f"距離 {distance_km}km")
    print(f"盗聴者の有無: {'あり' if eve_present else 'なし'}")
    print(f"アリスの最終鍵: {alice_final_key[:50]}...")
    print(f"ボブの最終鍵: {bob_final_key[:50]}...")
    print(f"生成された鍵の長さ: {len(alice_final_key)}")
    print(f"QBER (量子ビット誤り率): {qber * 100:.2f} %")
    print(f"基底が一致したビット数: {key_len}")

    # 結果
    if alice_final_key == bob_final_key:
        print("\n✅ 成功：安全な鍵が共有されました。")
    else:
        # 不一致のビット数とエラー率

        # 不一致のビットをペアにしてカウント
        diff_count = sum(1 for a, b in zip(alice_final_key, bob_final_key) if a != b)
        error_rate = (
            (diff_count / len(alice_final_key)) * 100 if len(alice_final_key) > 0 else 0
        )
        print(
            f"\n⚠️ 警告：不一致なビットが {diff_count} ビットあります (エラー率: {error_rate:.2f}%)"
        )
        print("イブによる盗聴が疑われます。")
