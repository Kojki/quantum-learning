import sys
import os
import numpy as np
import matplotlib.pyplot as plt

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sensing.ipe_algorithm import iterative_phase_estimation
from src.communication.core import correspondence_table, encode_message, decode_message
from src.optimization.core import solve_maxcut_qaoa

def main():
    print("==================================================")
    print("   Integrated Quantum System Scenario Simulation")
    print("==================================================")
    
    # --- STEP 1: Quantum Sensing ---
    # 外部磁場の強さを量子センサで測定する
    print("\n[STEP 1] Quantum Sensing")
    true_magnetic_field = 0.85 # ラジアン単位の位相に相当
    print(f"環境の真の磁場強度 (位相): {true_magnetic_field} rad")
    
    measured_phase = iterative_phase_estimation(true_magnetic_field, num_bits=8)
    print(f"センサによる測定結果: {measured_phase:.4f} rad")
    
    # --- STEP 2: Quantum Communication ---
    # 測定結果をセキュアに送信する（BB84を想定したフロー）
    print("\n[STEP 2] Quantum Communication")
    message = f"VAL:{measured_phase:.2f}"
    print(f"送信メッセージ: '{message}'")
    
    to_str, to_bit = correspondence_table()
    bit_sequence = encode_message(message, to_bit)
    print(f"エンコードされたビット列: {bit_sequence}")
    
    # 本来はここで量子鍵配送(QKD)のシミュレーションが入るが、
    # ここでは既存のロジックを利用して「セキュアな転送」を模倣する
    received_message = decode_message(bit_sequence, to_str)
    print(f"受信・復号されたメッセージ: '{received_message}'")
    
    # 値の抽出
    decoded_value = float(received_message.split(":")[1])
    
    # --- STEP 3: Quantum Optimization ---
    # 受信した値を重みとしてグラフ最適化問題を解く
    print("\n[STEP 3] Quantum Optimization")
    print(f"受信した値 {decoded_value} をエッジの重みとしてMax-Cut問題を解きます。")
    
    # 重み付きグラフの定義
    # 0 --(w)-- 1 --(1.0)-- 2
    adj_matrix = np.array([
        [0, decoded_value, 0],
        [decoded_value, 0, 1.0],
        [0, 1.0, 0]
    ])
    
    print("QAOAエンジンを起動中...")
    params, counts, cost = solve_maxcut_qaoa(adj_matrix, p=1)
    
    print(f"最適化完了。最小化コスト: {cost:.4f}")
    
    # 結果の可視化
    best_cut = max(counts, key=counts.get)
    print(f"最も確率の高いカット状態: {best_cut}")
    
    # シンプルなプロット
    plt.figure(figsize=(8, 5))
    plt.bar(counts.keys(), counts.values())
    plt.xticks(rotation=45)
    plt.title(f"QAOA Result (Weight: {decoded_value})")
    plt.xlabel("State")
    plt.ylabel("Counts")
    plt.tight_layout()
    
    print("\nシナリオシミュレーションが正常に終了しました。")
    plt.show()

if __name__ == "__main__":
    main()
