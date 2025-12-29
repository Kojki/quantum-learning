from qiskit.circuit import Parameter, QuantumCircuit, ClassicalRegister, QuantumRegister
import tkinter as tk
from tkinter import ttk


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
        "00100000": "ち",
        "00100001": "つ",
        "00100010": "て",
        "00100011": "と",
        "00100100": "な",
        "00100101": "に",
        "00100110": "ぬ",
        "00100111": "ね",
        "00101000": "の",
        "00101001": "は",
        "00101010": "ひ",
        "00101011": "ふ",
        "00101100": "へ",
        "00101101": "ほ",
        "00101110": "ま",
        "00101111": "み",
        "01000000": "む",
        "01000001": "め",
        "01000010": "も",
        "01000011": "や",
        "01000100": "ゆ",
        "01000101": "よ",
        "01000110": "ら",
        "01000111": "り",
        "01001000": "る",
        "01001001": "れ",
        "01001010": "ろ",
        "00101011": "わ",
        "00101100": "を",
        "00101101": "ん",
        "00101110": "が",
        "00101111": "ぎ",
        "01000000": "ぐ",
        "01000001": "げ",
        "01000010": "ご",
        "01000011": "ざ",
        "01000100": "じ",
        "01000101": "ず",
        "01000110": "ぜ",
        "01000111": "ぞ",
        "01001000": "だ",
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
    input_data = input("伝えたいメッセージを入力してください。: ")
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


selected_mode = introduction()

if selected_mode == "1":
    print("BB84について扱います。")
    to_str_table, to_bit_table = correspondence_table()
    message_original = information_input()
    bit_sequence = encode_message(message_original, to_bit_table)
    print("ビットへの変換が完了しました:", bit_sequence)
    print("ビット列の長さ:", len(bit_sequence))

    q = QuantumRegister(len(bit_sequence), "q")
    circuit = QuantumCircuit(q)
    for i, bit in enumerate(bit_sequence):
        if bit == "1":
            circuit.x(q[i])


# 量子乱数
# ゲート操作

"""
from qulacs import QuantumState
from qulacs.gate import H


state = QuantumState(1)

state.set_zero_state()
gate = H(0)
gate.update_quantum_state(state)

count = len(bit_sequence)
"""
