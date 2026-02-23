import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


class AdiabaticOptimizer:

    def __init__(self, num_qubits):
        self.num_qubits = num_qubits
        self.h_terms = []  # 単一ビット制約 (h_i * Z_i)
        self.j_terms = []  # 2ビット間相互作用 (J_ij * Z_i * Z_j)

    def add_h_term(self, i, weight):
        """ビット i が 0 か 1 かに偏らせる制約を追加"""
        if 0 <= i < self.num_qubits:
            self.h_terms.append((i, weight))
        else:
            print(f"Error: Qubit index {i} is out of range.")

    def add_j_term(self, i, j, weight):
        """ビット i と j の間の相関の制約を追加"""
        if 0 <= i < self.num_qubits and 0 <= j < self.num_qubits:
            self.j_terms.append((i, j, weight))
        else:
            print(f"Error: Qubit index {i} or {j} is out of range.")

    def _get_schedule(self, s, mode="linear"):
        """アニーリング推移を計算する補助関数"""
        if mode == "sin_sq":
            b = np.sin(s * np.pi / 2) ** 2
        else:
            b = s
        return 1 - b, b

    def build_circuit(self, T=10.0, N=40, schedule="linear"):
        """設定に基づいて量子回路を構築する"""
        dt = T / N
        s_vals = np.linspace(0, 1, N + 1)
        qc = QuantumCircuit(self.num_qubits)

        # 初期状態: |+>
        qc.h(range(self.num_qubits))
        qc.barrier()

        for step in range(N):
            A, B = self._get_schedule(s_vals[step], mode=schedule)

            # Mixing Hamiltonian (X) - 揺らぎ
            for i in range(self.num_qubits):
                qc.rx(-2 * A * dt, i)

            # 1-qubit terms (Z) - 磁場
            for i, w in self.h_terms:
                qc.rz(2 * B * dt * w, i)

            # 2-qubit terms (ZZ) - 相互作用
            for i, j, w in self.j_terms:
                qc.cx(i, j)
                qc.rz(2 * B * dt * w, j)
                qc.cx(i, j)
            qc.barrier()

        qc.measure_all()
        return qc

    def run(self, T=10.0, N=40, schedule="linear", shots=1024):
        """シミュレーションの実行"""
        qc = self.build_circuit(T, N, schedule)
        sim = AerSimulator()
        t_qc = transpile(qc, sim)
        result = sim.run(t_qc, shots=shots).result()
        return result.get_counts(), qc
