import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import ZGate
from qiskit_aer import AerSimulator


class GroverSearch:
    """Groverのアルゴリズムを用いた量子探索クラス。

    未整列のデータの中から正解の状態（ビット文字列）を O(√N) の計算量で見つけ出します。

    Theory:
        1. 初期化: 全状態の等確率重ね合わせ |s> = H^n |0>
        2. 反復処理 (Grover Iteration) を約 (π/4)√N 回繰り返す:
           - Oracle: 正解の状態の符号を反転させる (|x> -> -|x>)
           - Diffuser: 平均値を中心とした反転を行い、正解の振幅を増幅させる
        3. 測定: 確率が最大化した正解の状態を得る

    Attributes:
        num_qubits (int): 量子ビット数。探索空間のサイズ N = 2^num_qubits。
        target_bitstring (str): 探索対象となる正解のビット文字列（例: "101"）。
    """

    def __init__(self, num_qubits: int, target_bitstring: str):
        self.num_qubits = num_qubits
        self.target_bitstring = target_bitstring
        if len(target_bitstring) != num_qubits:
            raise ValueError(
                f"Target bitstring length must match num_qubits ({num_qubits})"
            )

    def build_oracle(self):
        """正解のビット文字列の符号を反転させるオラクル回路を構築."""
        qc = QuantumCircuit(self.num_qubits)

        # ターゲット文字列に応じて、0のビットにXを適用して「111...」の状態にする
        # Qiskitのエンディアン（右端が0番目）に注意
        for i, bit in enumerate(reversed(self.target_bitstring)):
            if bit == "0":
                qc.x(i)

        # 多制御Zゲート (MCZ) を適用して、全ビットが1の場合のみ符号を反転
        if self.num_qubits == 1:
            qc.z(0)
        else:
            # H-MCX-H は MCZ と等価で、対象ビットの符号を反転させる
            qc.h(self.num_qubits - 1)
            qc.mcx(list(range(self.num_qubits - 1)), self.num_qubits - 1)
            qc.h(self.num_qubits - 1)

        # 0のビットにXを適用し直して元に戻す
        for i, bit in enumerate(reversed(self.target_bitstring)):
            if bit == "0":
                qc.x(i)

        return qc

    def build_diffuser(self):
        """平均値周辺の反転を行うディフューザー回路を構築."""
        qc = QuantumCircuit(self.num_qubits)

        # Hをかけて重ね合わせ状態から「00...0」に近い状態に戻す
        qc.h(range(self.num_qubits))
        qc.x(range(self.num_qubits))

        # 00...0 状態のみ符号を反転
        qc.h(self.num_qubits - 1)
        qc.mcx(list(range(self.num_qubits - 1)), self.num_qubits - 1)
        qc.h(self.num_qubits - 1)

        qc.x(range(self.num_qubits))
        qc.h(range(self.num_qubits))

        return qc

    def construct_circuit(self, iterations: int = None):
        """指定された回数のGrover反復を含む回路を構築."""
        if iterations is None:
            # 最適な反復回数の近似: (π/4) * sqrt(2^n)
            iterations = int(np.floor(np.pi / 4 * np.sqrt(2**self.num_qubits)))

        qc = QuantumCircuit(self.num_qubits)

        # 1. 初期化
        qc.h(range(self.num_qubits))
        qc.barrier()

        # 2. Grover Iterations
        oracle = self.build_oracle()
        diffuser = self.build_diffuser()

        for _ in range(iterations):
            qc.compose(oracle, inplace=True)
            qc.barrier()
            qc.compose(diffuser, inplace=True)
            qc.barrier()

        qc.measure_all()
        return qc

    def run(self, iterations: int = None, shots: int = 1024):
        """シミュレーションを実行."""
        qc = self.construct_circuit(iterations)
        sim = AerSimulator()
        t_qc = transpile(qc, sim)
        result = sim.run(t_qc, shots=shots).result()
        return result.get_counts(), qc


if __name__ == "__main__":
    # --- シンプルな動作テスト (3量子ビット、ターゲット "101") ---
    target = "101"
    print(f"\n--- GroverSearch Test Run (Target: {target}) ---")
    grover = GroverSearch(num_qubits=3, target_bitstring=target)

    counts, _ = grover.run()

    print("測定結果 (上位):")
    sorted_counts = dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))
    for bit, count in list(sorted_counts.items())[:3]:
        print(f" 状態 |{bit}⟩: {count}回")
