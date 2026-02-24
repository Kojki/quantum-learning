import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram

project_root = os.getcwd()
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from src.optimization.core import AdiabaticOptimizer

    print("Successfully imported AdiabaticOptimizer from src.optimization.core")
except ImportError:
    print("Error: src/optimization/core.py could not be found.")
    print("Please make sure the file exists in your project directory.")


def interactive_main():
    print("\n" + "=" * 50)
    print("   Quantum Adiabatic Solver - Interactive Mode")
    print("=" * 50)
    print("対話形式で問題を定義して、量子断熱計算（AQC）を実行します。")

    try:
        # [1] 量子ビット数の設定
        num_qubits_input = input(
            "\n[1/4] 量子ビットの数（頂点の数）を入力してください: "
        )
        if not num_qubits_input:
            return
        num_qubits = int(num_qubits_input)
        optimizer = AdiabaticOptimizer(num_qubits)

        # [2] 単体制約 (h項)
        print("\n[2/4] 個別のビットに対する制約（h項）を入力します。")
        print(
            "💡 例: '0, -1.0' (0番を1に偏らせる) / 終了するには Enter のみ押してください。"
        )
        while True:
            h_input = input("頂点索引, 重み: ").strip()
            if not h_input:
                break
            i, w = map(float, h_input.split(","))
            optimizer.add_h_term(int(i), w)

        # [3] 相互作用 (J項)
        print("\n[3/4] ビット間の相互作用（J項/エッジ）を入力します。")
        print(
            "💡 例: '0, 1, 1.0' (0と1を違う組にする) / 終了するには Enter のみ押してください。"
        )
        while True:
            j_input = input("頂点A, 頂点B, 重み: ").strip()
            if not j_input:
                break
            i, j, w = map(float, j_input.split(","))
            optimizer.add_j_term(int(i), int(j), w)

        # [4] 実行パラメータ設定
        print("\n[4/4] 実行パラメータを設定します。")
        t_val = float(
            input("アニーリング時間 T (推奨 10~20) [デフォルト 10.0]: ") or 10.0
        )
        n_val = int(input("ステップ数 N (推奨 30~50) [デフォルト 40]: ") or 40)
        sched = (
            input("スケジュール (linear / sin_sq) [デフォルト linear]: ").strip()
            or "linear"
        )

        # 計算開始
        print("\n" + "-" * 30)
        print("量子回路を構築し、シミュレーションを開始します...")
        print("-" * 30)

        counts, _ = optimizer.run(T=t_val, N=n_val, schedule=sched)

        # 結果の表示
        print("\n[結果] 測定された状態（出現頻度順）:")
        sorted_counts = dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))
        for i, (bit, count) in enumerate(sorted_counts.items()):
            if i >= 5:
                break  # 上位5つを表示
            print(f" 状態 {bit} : {count}回")

        # グラフの表示
        fig = plot_histogram(counts)
        display(fig)  # ノートブック上でインライン表示させる

    except ValueError:
        print("\n❌ 入力エラー: 数値を正しく入力してください（例: 0, 1, 1.0）。")
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")


if __name__ == "__main__":
    interactive_main()
