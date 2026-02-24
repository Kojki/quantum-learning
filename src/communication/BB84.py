import sys
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
import hashlib


# ひらがな（および一部記号・英数字）と8ビットバイナリの対応表
def correspondence_table():
    """ひらがな（および一部記号・英数字）と8ビットバイナリ列の相互変換テーブルを生成する。
    ここでは8ビット（1バイト）を1文字の単位とする。
    """
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
    """この関数ではツールの紹介と、それを行うための入力を受け取ります。

    Returns:
        selected_value (str): 選択されたテーマの文字列
    """

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


def information_key_input():
    # 鍵の入力
    input_key_data = input(
        "最適な長さの文字列を入力してください。それに応じたビット列を生成します。\n"
        "最終的に残るビット数は1/4程度になります。: "
    )
    return input_key_data


def information_input():
    # 入力
    input_data = input("送りたいメッセージを入力してください。: ")
    return input_data


def encode_message(message_original, to_bit_table):
    """この関数では文字列をビット列に変換します。

    Args:
        message_original (str): 入力された文字列
        to_bit_table (dict): 文字からビット列への変換テーブル

    Returns:
        encoded (str): 変換後のビット列
    """
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
    """この関数ではビット列を文字列に変換します。

    Args:
        bit_string (str): 入力されたビット列
        to_str_table (dict): ビット列から文字への変換テーブル
    Returns:
        decoded (str): 変換後の文字列
    """
    decoded_list = []
    error_count = 0
    if len(bit_string) < 8:
        print(
            f"警告: 鍵の長さが足りません（現在 {len(bit_string)} ビット）。文字を復元するには8ビット以上必要です。"
        )
        return "復元不可能です。"

    for i in range(0, len(bit_string), 8):
        bit_chunk = bit_string[i : i + 8]
        if bit_chunk in to_str_table:
            decoded_list.append(to_str_table[bit_chunk])
            decoded = "".join(decoded_list)
        else:
            error_count += 1
            decoded_list.append("?")

    if error_count > 0:
        print(f"警告: 通信がうまくいっていません。")

    decoded = "".join(decoded_list)
    return decoded


def generate_quantum_random_bit():
    """この関数では量子乱数を生成します。

    Returns:
        result (int): 量子乱数ビット（0 or 1）
    """
    state = QuantumState(1)
    state.set_zero_state()
    gate = H(0)
    gate.update_quantum_state(state)

    # 測定
    result: list[int] = state.sampling(1)[0]
    return result


def get_hardware_noise_model():
    """この関数では測定器の暗計数に関するノイズモデルを生成します。

    Returns:
        noise_model (NoiseModel): 暗計数ノイズのノイズモデル
    """
    noise_model = NoiseModel()
    # 暗計数ノイズ
    # 0.5%の確率で誤検出
    p_dark = 0.005
    error_dark = pauli_error([("X", p_dark), ("I", 1 - p_dark)])
    noise_model.add_all_qubit_quantum_error(error_dark, "measure")
    return noise_model


def get_channel_noise_model(qc, n_qubits, distance_km):
    """この関数では通信距離に応じたノイズモデルを生成します。"""
    # 通信路ノイズ
    # 距離に応じて変化
    if distance_km <= 0:
        return
    p_chan = 1 - np.exp(-0.0005 * distance_km)
    if p_chan > 0:
        error_chan = depolarizing_error(p_chan, 1)
        for q in n_qubits:
            qc.append(error_chan, [q])


def get_parity(bits):
    """ビット列のパリティ（総和が奇数なら1, 偶数なら0）を計算する。
    Args:
        bits (str): 対象のビット列。
    Returns:
        int: 計算されたパリティ（0 or 1）。
    """
    return sum(int(b) for b in bits) % 2


def binary_search(a_bits, b_bits, offset=0):
    """この関数では二分探索を用いてエラー箇所を1つ特定します。
    Args:
        a_bits (str): アリス側のビットブロック。
        b_bits (str): ボブ側のビットブロック。
        offset (int): ブロックの開始位置。
    Returns:
        int: エラーの場所。
    """
    if len(a_bits) == 1:
        return offset

    mid = len(a_bits) // 2
    a_left = a_bits[:mid]
    b_left = b_bits[:mid]
    a_right = a_bits[mid:]
    b_right = b_bits[mid:]

    if (sum(int(a) for a in a_left) % 2) != (sum(int(b) for b in b_left) % 2):
        return binary_search(a_left, b_left, offset)
    else:
        return binary_search(a_right, b_right, offset + mid)


def analyze_qber(
    alice_bits,
    bob_bits,
    alice_bases,
    bob_bases,
    alice_labels,
    eve_bits=None,
    sample_ratio=0.2,
):
    """この関数ではQBER解析を行い、収率と最終鍵を算出します。

    Args:
        alice_bits (str): Aliceが送信した全ビット列
        bob_bits (str): Bobが受信した全ビット列（'F'を含む）
        alice_bases (list): Aliceが使用した基底リスト
        bob_bases (list): Bobが使用した基底リスト
        alice_labels (list): Aliceが割り当てた S / D ラベル
        eve_bits (str, optional): Eveが盗聴したビット列
        sample_ratio (float): エラー推定のために公開するビットの割合

    Returns:
        tuple: (qber, key_len, alice_key, bob_key, eve_key, eave_suspected)
    """
    eave_suspected = False

    # 1. 収率（Yield）の計算（全ビットが対象）
    s_sent = 0  # Aliceが送ったSignalの総数
    s_receive = 0  # 受信成功数(Signal)
    d_sent = 0  # Aliceが送ったDecoyの総数
    d_receive = 0  # 受信成功数(Decoy)

    for i in range(len(alice_labels)):
        if alice_labels[i] == "S":
            s_sent += 1
            if bob_bits[i] != "F":
                s_receive += 1
        else:
            d_sent += 1
            if bob_bits[i] != "F":
                d_receive += 1

    yield_s = s_receive / s_sent if s_sent > 0 else 0
    yield_d = d_receive / d_sent if d_sent > 0 else 0

    print(f"\n--- 収率解析 (Decoy Analysis) ---")
    print(f"信号ビット受信率: {yield_s*100:.2f} %")
    print(f"デコイビット受信率: {yield_d*100:.2f} %")

    # PNS攻撃の検知（暫定版）
    if yield_s == 0:
        print(
            "\n❌ 失敗：鍵を生成するために必要なビットが残っていません。通信を終了します。"
        )
        sys.exit()
    if yield_d / yield_s > 1.2:
        eave_suspected = True

    # 2. フィルタリング（基底が一致 AND ビットを受信）
    matches = [
        i
        for i in range(len(alice_bases))
        if alice_bases[i] == bob_bases[i] and bob_bits[i] != "F"
    ]

    if not matches:
        return 0.0, 0, "", "", eave_suspected, ""

    # 3. サンプリングによるQBER推定
    sample_size = max(4, int(len(matches) * sample_ratio))
    sample_sequence = random.sample(matches, sample_size)
    sample_errors = sum(1 for i in sample_sequence if alice_bits[i] != bob_bits[i])
    qber = sample_errors / sample_size

    # 4. 鍵の抽出（サンプルは除外）
    key_sequence = [i for i in matches if i not in sample_sequence]
    alice_key = "".join([alice_bits[i] for i in key_sequence])
    bob_key = "".join([bob_bits[i] for i in key_sequence])
    eve_key = "".join([eve_bits[i] for i in key_sequence if i < len(eve_bits)])

    key_len = len(alice_key)

    return qber, key_len, alice_key, bob_key, eave_suspected, eve_key


def reconcile_errors_binary(alice_key, bob_key, block_size=10):
    """鍵をブロックに分割し、二分探索を用いて誤り訂正を行います。

    Args:
        alice_key (str): アリス側の鍵（ビット列）
        bob_key (str): ボブ側の鍵（ビット列）
        block_size (int): ブロックあたりのビット数

    Returns:
        str: 修正後のボブの鍵
    """
    bob_key_list = list(bob_key)
    corrected_count = 0

    # ブロックごとに処理
    for start in range(0, len(alice_key), block_size):
        end = min(start + block_size, len(alice_key))

        a_block = alice_key[start:end]
        b_block = bob_key[start:end]

        # 二分探索
        if get_parity(a_block) != get_parity(b_block):
            # エラー箇所を特定
            error_idx = binary_search(a_block, b_block, start)
            # Bobのビットを反転
            bob_key_list[error_idx] = "1" if bob_key_list[error_idx] == "0" else "0"
            corrected_count += 1
    print(f"\n--- エラー訂正報告 ---")
    print(f"{corrected_count} 個のエラーを修正しました。")
    return "".join(bob_key_list)

    # イブ


def reconcile_errors_e_binary(alice_key, bob_key, eve_key, block_size=10):
    """鍵をブロックに分割し、二分探索を用いて誤り訂正を行います。(イブ用)

    Args:
        alice_key (str): アリス側の鍵（ビット列）
        bob_key (str): ボブ側の鍵（ビット列）
        eve_key (str): イブ側の鍵（ビット列）
        block_size (int): ブロックあたりのビット数

    Returns:
        str: 修正後のイブの鍵
    """
    eve_key_list = list(eve_key)
    corrected_count = 0

    # ブロックごとに処理
    count = 0
    for start in range(0, len(alice_key), block_size):
        end = min(start + block_size, len(alice_key))
        a_block = alice_key[start:end]
        b_block = bob_key[start:end]
        e_block = "".join(eve_key_list[start:end])

        # ボブがエラーを報告した場合
        if get_parity(a_block) != get_parity(b_block):
            # イブが自分もエラーだと気づいた場合
            if get_parity(a_block) != get_parity(e_block):
                idx = binary_search(a_block, e_block, start)
                eve_key_list[idx] = "1" if eve_key_list[idx] == "0" else "0"
                count += 1
        a_block = alice_key[start:end]
        e_block = "".join(eve_key_list[start:end])
        if get_parity(a_block) != get_parity(e_block):
            # エラー箇所を特定
            error_idx = binary_search(a_block, e_block, start)
            # Eveのビットを反転
            eve_key_list[error_idx] = "1" if eve_key_list[error_idx] == "0" else "0"
            corrected_count += 1

    print(f"\n--- (イブの)エラー訂正報告 ---")
    print(f"公開情報により、{corrected_count} 個のエラーを修正しました。")
    return "".join(eve_key_list)


def get_distance_input(eve_present, distance_ab_km=None):
    """この関数では通信距離をkm単位で入力します。
    Args:
        eve_present (bool): イブが存在するかどうか
        distance_ab_km (float, optional): AliceとBobの距離（km）

    Returns:
        float: 通信距離（km）
    """
    while True:
        if not eve_present:
            val = input("AliceとBobの距離をkm単位で入力してください: ")
            try:
                dist = float(val)
                if dist >= 0:
                    return dist
                print("距離は0以上にしてください。")
            except ValueError:
                print("有効な数値を入力してください。")
        else:
            if distance_ab_km is None:
                raise ValueError("イブの位置入力にはdistance_ab_kmが必要です")

            val = input(f"イブの待機位置を入力してください (0 ~ {distance_ab_km}km): ")
            try:
                dist = float(val)
                if 0 <= dist <= distance_ab_km:
                    return dist
                print(f"位置は0から{distance_ab_km}の間で指定してください。")
            except ValueError:
                print("有効な数値を入力してください。")


def assign_labels(n_batch, decoy_ratio=0.1):
    """この関数ではSignal、Decoyいずれかのラベルを割り当てます。

    Args:
        n_batch (int): ラベルを割り当てる数
        decoy_ratio (float): Decoyの割合

    Returns:
        labels (str): SとDのラベルのリスト
    """
    labels = []
    for _ in range(n_batch):
        labels.append("D" if random.random() < decoy_ratio else "S")
    return labels


def transmission_loss(distance_km):
    """この関数では通信路の損失をシミュレートします。

    Args:
        distance_km (float): 通信距離（km）
    Returns:
        bool: 通信が成功したかどうか （True: 成功, False: 損失）
    """
    transmittance = 10 ** (-0.02 * distance_km)
    return random.random() < transmittance


def privacy_amplification(key):
    """この関数ではハッシュ関数(SHA-256)を用いて、鍵のプライバシー増幅を行う。
    エラー訂正フェーズで漏洩したパリティ情報などを無効化する目的もある。

    Args:
        key (str): 修正済みの鍵（ビット列）。

    Returns:
        final_key (str): 増幅後の256ビットの鍵。
    """
    # ハッシュ計算
    hash_obj = hashlib.sha256(key.encode())
    hash_hex = hash_obj.hexdigest()

    # ハッシュ値（16進数）を256ビットのバイナリ（2進数）に変換
    final_key = bin(int(hash_hex, 16))[2:].zfill(256)

    print(f"\nプライバシー増幅を実行しました（SHA-256）。")
    return final_key


# メイン処理
def main():
    selected_mode = introduction()

    if selected_mode == "BB84":
        print("--- BB84プロトコルシミュレーション ---")
        to_str_table, to_bit_table = correspondence_table()
        key_original = information_key_input()
        bit_sequence = encode_message(key_original, to_bit_table)

        n_bits = len(bit_sequence)
        print(f"送信ビット列: {bit_sequence} (長さ: {n_bits})")

        eve_present = False
        # 条件設定
        try:
            distance_ab_km = get_distance_input(eve_present)
        except ValueError:
            print("無効な入力です。デフォルト値0kmを使用します。")
            distance_ab_km = 0.0

        distance_ae_km = 0.0

        eve_present = input("イブ（盗聴者）を介入させますか？ (y/n): ").lower() == "y"

        if eve_present:
            distance_ae_km = get_distance_input(eve_present, distance_ab_km)
            if distance_ae_km > distance_ab_km:
                distance_ae_km = distance_ab_km

        alice_labels = []
        alice_bases = []
        bob_bases = []
        eve_bases = []
        all_measured_bits = ""
        all_eve_bits = ""

        # バッチ処理
        batch_size = 100
        for batch_idx, start in enumerate(range(0, n_bits, batch_size)):
            end = min(start + batch_size, n_bits)
            batch_bits = bit_sequence[start:end]
            n_batch = len(batch_bits)  # バッチごとに送るビット数
            print(f"バッチ {batch_idx + 1}: {start+1}~{end}ビット目を処理中...")
            current_batch_labels = assign_labels(n_batch, decoy_ratio=0.1)
            alice_labels.extend(current_batch_labels)

            # 各バッチごとに回路を作成
            qr = QuantumRegister(n_batch, "q")
            cr_bob = ClassicalRegister(n_batch, "bob")
            registers = [qr, cr_bob]

            if eve_present:
                cr_eve = ClassicalRegister(n_batch, "eve")
                registers.append(cr_eve)
            qc = QuantumCircuit(*registers)

            # Alice（送信準備）
            for i in range(n_batch):
                a_base = generate_quantum_random_bit()
                alice_bases.append(a_base)
                if batch_bits[i] == "1":
                    qc.x(i)
                if a_base == 1:
                    qc.h(i)
            qc.barrier()  # 作業終了

            distance_eve_km = distance_ae_km if eve_present else distance_ab_km
            get_channel_noise_model(qc, range(n_batch), distance_eve_km)
            qc.barrier()

            # Eve（盗聴）
            if eve_present:
                for i in range(n_batch):
                    e_base = generate_quantum_random_bit()
                    eve_bases.append(e_base)

                    if e_base == 1:
                        qc.h(i)
                    qc.measure(i, cr_eve[i])  # 盗聴
                    # 測定後の辻褄合わせ
                    if e_base == 1:
                        qc.h(i)
                qc.barrier()  # 作業終了

                get_channel_noise_model(
                    qc, range(n_batch), distance_ab_km - distance_ae_km
                )
                qc.barrier()

            # Bob（受信）
            for i in range(n_batch):
                b_base = generate_quantum_random_bit()
                bob_bases.append(b_base)

                if b_base == 1:
                    qc.h(i)
                qc.measure(i, cr_bob[i])  # Bobの測定
            qc.barrier()  # 作業終了

            # シミュレーション実行
            noise_model = get_hardware_noise_model()
            simulator = AerSimulator(
                method="stabilizer", noise_model=noise_model
            )  # 高速化
            job = simulator.run(qc, shots=1, memory=True)
            batch_result = job.result().get_memory()[0]

            if " " in batch_result:
                eve_part, bob_part = batch_result.split(" ")
                batch_bob_bits = bob_part[::-1]
                batch_eve_bits = eve_part[::-1]
            else:
                batch_bob_bits = batch_result[::-1]
                batch_eve_bits = ""

            lossy_b_measured = ""
            lossy_e_measured = ""
            for i in range(n_batch):
                if eve_present:

                    if transmission_loss(distance_ae_km):
                        lossy_e_measured += batch_eve_bits[i]

                        if transmission_loss(distance_ab_km - distance_ae_km):
                            lossy_b_measured += batch_bob_bits[i]
                        else:
                            lossy_b_measured += "F"
                    else:
                        lossy_e_measured += "F"
                        lossy_b_measured += "F"
                else:
                    if transmission_loss(distance_ab_km):
                        lossy_b_measured += batch_bob_bits[i]
                    else:
                        lossy_b_measured += "F"

            all_measured_bits += lossy_b_measured
            all_eve_bits += lossy_e_measured

            time.sleep(0.5)

        print("\n全バッチの処理が完了しました。")

        alice_bits = bit_sequence
        bob_bits = all_measured_bits

        qber, key_len, alice_key, bob_key, eave_suspected, eve_key = analyze_qber(
            alice_bits, bob_bits, alice_bases, bob_bases, alice_labels, all_eve_bits
        )
        alice_second_key = alice_key
        if len(bob_key) > 0:
            bob_second_key = reconcile_errors_binary(alice_key, bob_key, block_size=10)
        else:
            bob_second_key = ""  # 空文字で初期化
            print("⚠️ 警告: ボブの鍵がありません。")

        if eve_present:
            if len(bob_key) > 0:
                eve_second_key = reconcile_errors_e_binary(
                    alice_key, bob_key, eve_key, block_size=10
                )
            else:
                eve_second_key = ""  # 空文字で初期化
                print("⚠️ 警告: イブの鍵がありません。")

        alice_final_key = privacy_amplification(alice_second_key)
        bob_final_key = privacy_amplification(bob_second_key)

        eve_final_key = ""
        if eve_present and eve_second_key:
            eve_final_key = privacy_amplification(eve_second_key.replace("F", "0"))

        # 最終鍵の生成
        for _ in tqdm(range(100), desc="最終鍵の生成中…"):
            time.sleep(0.01)

        eve_final_key = ""
        if eve_present and eve_key:
            eve_final_key = privacy_amplification(eve_key.replace("F", "0"))

        for _ in tqdm(range(100), desc="最終鍵の生成中…"):
            time.sleep(0.01)

        # --- BB84 レポート ---
        print("\n" + "=" * 50)
        print("BB84 最終レポート（Quantum Fusion Core）")
        print("=" * 50)
        print(
            f"距離 {distance_ab_km}km (Eve位置: {distance_ae_km if eve_present else 'なし'}km)"
        )
        print(f"盗聴者の有無: {'あり' if eve_present else 'なし'}")
        print(f"アリスの最終鍵: {alice_final_key[:40]}...")
        print(f"ボブの最終鍵:   {bob_final_key[:40]}...")
        print(f"QBER (量子ビット誤り率): {qber * 100:.2f} %")
        if eave_suspected:
            print("⚠️ 警告: 盗聴の可能性があります。")

        # --- イブのレポート ---
        if eve_present:
            print(f"\n" + "=" * 50)
            print("盗聴者イブのレポート")
            print("=" * 50)
            print(f" イブの位置: {distance_ae_km} km")
            print(
                f" イブの光子捕捉成功数: {len(all_eve_bits.replace('F', ''))} / {n_bits}"
            )
            print(f" イブが手に入れた鍵の断片: {eve_final_key[:50]}...")
            if not (alice_final_key == bob_final_key and len(alice_final_key) > 0):
                print(
                    f" 結論: 鍵共有に失敗したため、イブは暗号化されたメッセージを得る機会すらありませんでした。"
                )
            print("=" * 50)

        # --- 鍵共有成功時 ---
        if alice_final_key == bob_final_key and len(alice_final_key) > 0:
            print("\n✅ 成功：秘密鍵が共有されました。暗号通信を開始します。")
            secret_message_text = information_input()
            secret_bits = encode_message(secret_message_text, to_bit_table)

            # 暗号化
            encrypted_bits = "".join(
                [
                    str(int(secret_bits[i]) ^ int(alice_final_key[i % 256]))
                    for i in range(len(secret_bits))
                ]
            )
            print(f"送信中の暗号文: {encrypted_bits[:50]}...")

            # ボブが解読
            decrypted_bob_bits = "".join(
                [
                    str(int(encrypted_bits[i]) ^ int(bob_final_key[i % 256]))
                    for i in range(len(encrypted_bits))
                ]
            )
            print(
                f"ボブが復号した内容: {decode_message(decrypted_bob_bits, to_str_table)}"
            )

            # イブによる解読
            if eve_present and eve_final_key:
                print(f"\n >>> イブによる解読")
                decrypted_eve_bits = "".join(
                    [
                        str(int(encrypted_bits[i]) ^ int(eve_final_key[i % 256]))
                        for i in range(len(encrypted_bits))
                    ]
                )
                print(
                    f"イブが見た内容: {decode_message(decrypted_eve_bits, to_str_table)}"
                )
                print(
                    f"結果: ❌ 失敗 1ビットの差でも大きな違いが生まれ、メッセージが解読できません。"
                )
        else:
            print("\n❌ 失敗：安全な鍵が共有できませんでした。通信を終了します。")


if __name__ == "__main__":
    main()
