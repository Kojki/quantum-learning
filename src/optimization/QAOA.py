import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from scipy.optimize import minimize


class QAOAOptimizer:
    """量子近似最適化アルゴリズム (QAOA) を用いた最適化クラス.

    AQC (断熱量子計算) を離散化し、各ステップ（層）の時間をパラメータ化したものです。
    古典最適化アルゴリズムを用いて、コストハミルトニアンの期待値を最小化するパラメータを探索します。

    Theory:
        |ψ(γ, β)> = M(β_p) C(γ_p) ... M(β_1) C(γ_1) |+>^n
        - C(γ): コスト・オペレータ exp(-i γ H_cost)
        - M(β): ミキサー・オペレータ exp(-i β H_mixer)

        期待値 <ψ|H_cost|ψ> を古典最適化により最小化します。

    Attributes:
        num_qubits (int): 量子ビット数。
        h_terms (list): 1量子ビット磁場項 [(i, w), ...]。
        j_terms (list): 2量子ビット相互作用項 [(i, j, w), ...]。
        p (int): QAOAの層数（ステップ数）。
    """

    def __init__(self, num_qubits: int, p: int = 1):
        self.num_qubits = num_qubits
        self.p = p
        self.h_terms = []
        self.j_terms = []

    def add_h_term(self, i: int, weight: float):
        """コストハミルトニアンの単一項 (h_i Z_i) を追加."""
        self.h_terms.append((i, weight))

    def add_j_term(self, i: int, j: int, weight: float):
        """コストハミルトニアンの相互作用項 (J_ij Z_i Z_j) を追加."""
        self.j_terms.append((i, j, weight))

    def build_circuit(self, gammas, betas):
        """指定されたパラメータでQAOA回路を構築."""
        qc = QuantumCircuit(self.num_qubits)

        # 初期状態: |+>^n
        qc.h(range(self.num_qubits))

        for i in range(self.p):
            gamma = gammas[i]
            beta = betas[i]

            # --- Cost Operator ---
            for idx, w in self.h_terms:
                qc.rz(2 * gamma * w, idx)
            for idx1, idx2, w in self.j_terms:
                qc.cx(idx1, idx2)
                qc.rz(2 * gamma * w, idx2)
                qc.cx(idx1, idx2)

            # --- Mixer Operator ---
            for idx in range(self.num_qubits):
                qc.rx(2 * beta, idx)

        return qc

    def get_expectation(self, params):
        """コストハミルトニアンの期待値を計算（古典最適化用）."""
        gammas = params[: self.p]
        betas = params[self.p :]

        qc = self.build_circuit(gammas, betas)
        qc.measure_all()

        sim = AerSimulator()
        t_qc = transpile(qc, sim)
        shots = 1024
        counts = sim.run(t_qc, shots=shots).result().get_counts()

        avg_cost = 0
        for sample, count in counts.items():
            # 各測定結果（ビット文字列）のコストを計算
            cost = 0
            # ビット文字列を逆順に（Qiskitのエンディアン対応）
            bits = [
                1 if b == "1" else -1 for b in sample[::-1]
            ]  # Z基底: |0>->1, |1>->-1

            for i, w in self.h_terms:
                cost += w * bits[i]
            for i, j, w in self.j_terms:
                cost += w * bits[i] * bits[j]

            avg_cost += cost * (count / shots)

        return avg_cost

    def optimize(self, method="COBYLA"):
        """古典最適化を実行して最適なパラメータを探索."""
        init_params = np.concatenate(
            [np.random.uniform(0, np.pi, self.p), np.random.uniform(0, np.pi, self.p)]
        )

        res = minimize(self.get_expectation, init_params, method=method)
        return res

    def run(self, params, shots=1024):
        """最適化されたパラメータで最終的な測定を実行."""
        gammas = params[: self.p]
        betas = params[self.p :]
        qc = self.build_circuit(gammas, betas)
        qc.measure_all()

        sim = AerSimulator()
        t_qc = transpile(qc, sim)
        result = sim.run(t_qc, shots=shots).result()
        return result.get_counts(), qc


if __name__ == "__main__":
    # --- シンプルな動作テスト (2ノード相互作用問題) ---
    print("\n--- QAOAOptimizer Test Run (Max-Cut) ---")
    opt = QAOAOptimizer(num_qubits=2, p=1)
    opt.add_j_term(0, 1, 1.0)  # 0-1間に反強磁性的相互作用

    print("最適化を開始します...")
    result = opt.optimize()
    print(f"最適パラメータ: {result.x}")

    counts, _ = opt.run(result.x)
    print("測定結果:")
    print(dict(sorted(counts.items(), key=lambda x: x[1], reverse=True)))
