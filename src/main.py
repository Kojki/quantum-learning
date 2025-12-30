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
        "01001001": "ぢ",
        "01001010": "づ",
        "01001011": "で",
        "01001100": "ど",
        "01001101": "ば",
        "01001110": "び",
        "01001111": "ぶ",
        "01010000": "べ",
        "01010001": "ぼ",
        "01010010": "ぱ",
        "01010011": "ぴ",
        "01010100": "ぷ",
        "01010101": "ぺ",
        "01010110": "ぽ",
        "01010111": "ぁ",
        "01001000": "ぃ",
        "01001001": "ぅ",
        "01001010": "ぇ",
        "01001011": "ぉ",
        "01001100": "ゃ",
        "01001101": "ゅ",
        "01001110": "ょ",
        "01001111": "っ",
        "01010000": "ー",
        "01010001": "、",
        "01010010": "。",
        "01010011": "・",
        "01010100": "「",
        "01010101": "」",
        "01010110": " ",
        "01010111": "！",
        "01011000": "？",
        "01011001": "0",
        "01011010": "1",
        "01011011": "2",
        "01011100": "3",
        "01011101": "4",
        "01011110": "5",
        "01011111": "6",
        "01100000": "7",
        "01100001": "8",
        "01100010": "9",
        "01100011": "A",
        "01100100": "B",
        "01100101": "C",
        "01100110": "D",
        "01100111": "E",
        "01101000": "F",
        "01101001": "G",
        "01101010": "H",
        "01101011": "I",
        "01101100": "J",
        "01101101": "K",
        "01101110": "L",
        "01101111": "M",
        "01110000": "N",
        "01110001": "O",
        "01110010": "P",
        "01110011": "Q",
        "01110100": "R",
        "01110101": "S",
        "01110110": "T",
        "01110111": "U",
        "01111000": "V",
        "01111001": "W",
        "01111010": "X",
        "01111011": "Y",
        "01111100": "Z",
        "01111101": "a",
        "01111110": "b",
        "01111111": "c",
        "10000000": "d",
        "10000001": "e",
        "10000010": "f",
        "10000011": "g",
        "10000100": "h",
        "10000101": "i",
        "10000110": "j",
        "10000111": "k",
        "10001000": "l",
        "10001001": "m",
        "10001010": "n",
        "10001011": "o",
        "10001100": "p",
        "10001101": "q",
        "10001110": "r",
        "10001111": "s",
        "10010000": "t",
        "10010001": "u",
        "10010010": "v",
        "10010011": "w",
        "10010100": "x",
        "10010101": "y",
        "10010110": "z",
        "10010111": "!",
        "10011000": "?",
        "10011001": ".",
        "10011010": ",",
        "10011011": ":",
        "10011100": ";",
        "10011101": "(",
        "10011110": ")",
        "10011111": "[",
        "10100000": "]",
        "10100001": "{",
        "10100010": "}",
        "10100011": "@",
        "10100100": "#",
        "10100101": "$",
        "10100110": "%",
        "10100111": "^",
        "10101000": "&",
        "10101001": "*",
        "10101010": "+",
        "10101011": "=",
        "10101100": "<",
        "10101101": ">",
        "10101110": "/",
        "10101111": "\\",
        "10110000": "-",
        "10110001": "_",
        "10110010": "~",
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

    # バッチ処理
    batch_size = 100
    for start in range(0, len(bit_sequence), batch_size):
        end = min(start + batch_size, len(bit_sequence))
        current_bits = bit_sequence[start:end]
        n_current = len(current_bits)

    # 回路の初期化（全ビット分）
    qr = QuantumRegister(n_bits, "q")
    cr = ClassicalRegister(n_bits, "c")
    qc = QuantumCircuit(qr, cr)

    # Alice（送信準備）
    for i in range(n_bits):
        a_base = generate_quantum_random_bit(1)
        alice_bases.append(a_base)

        if bit_sequence[i] == "1":
            qc.x(i)
        if a_base == 1:
            qc.h(i)
    qc.barrier()  # 作業終了

    # Eve（盗聴）
    if eve_present:
        for i in range(n_bits):
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
    for i in range(n_bits):
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
    result = job.result()

    # Qiskitを用いているためビット順を反転
    measured_bits_str = result.get_memory()[0][::-1]

    alice_bits = bit_sequence
    bob_bits = measured_bits_str

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
