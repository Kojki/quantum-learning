import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


class DI_QKD_Simulator:
    """Device-Independent QKD (DI-QKD) のシミュレータクラス。

    CHSH不等式の破れをチェックすることで、通信機器（デバイス）が途中で
    盗聴者（Eve）にすり替えられていないか、完全に信頼しなくても安全性を
    保証できるプロトコルです。

    Theory:
        1. アリスとボブの間で、量子もつれ状態（ベルペア）を共有します。
        2. アリスはランダムに基底 A0(Z測定), A1(X測定) のいずれかを選びます。
        3. ボブはランダムに基底 B0(Z測定), B1(斜め: Z+X), B2(斜め: Z-X) を選びます。
        4. 基底が一致した (A0, B0) すなわち共に Z 測定をした結果を「暗号鍵」とします。
        5. それ以外の組み合わせから CHSH 不等式
           S = E(A0,B1) + E(A0,B2) + E(A1,B1) - E(A1,B2)
           を計算し、S が古典の限界(2)を超えて量子限界(2√2 ≒ 2.82)に近ければ、
           デバイスが安全（もつれが本物であること）が証明されます。
    """

    def __init__(self, num_pairs: int = 2000):
        self.num_pairs = num_pairs
        self.sim = AerSimulator()

    def generate_random_bases(self):
        """アリスとボブがランダムな測定基底を選択する"""
        # アリスは A0=0(Z), A1=1(X)
        alice_bases = np.random.choice([0, 1], size=self.num_pairs)
        # ボブは B0=0(Z), B1=1(Z+X), B2=2(Z-X)
        # 鍵生成効率を上げるために B0 の確率を高くすることも可能ですが、ここでは等確率にします
        bob_bases = np.random.choice([0, 1, 2], size=self.num_pairs)
        return alice_bases, bob_bases

    def create_bell_pair_circuit(self):
        """理想的なベルペア |Φ+> = (|00> + |11>)/√2 を作成する回路"""
        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.cx(0, 1)
        return qc

    def apply_measurement_basis(
        self, qc: QuantumCircuit, qubit: int, basis_type: int, actor: str
    ):
        """アリスとボブの測定基底（角度）を適用し、最終的にZ測定へ帰着させる"""
        # アリス
        if actor == "alice":
            if basis_type == 0:  # A0: Z基底 (何もしない)
                pass
            elif basis_type == 1:  # A1: X基底 (HゲートでZに変換)
                qc.h(qubit)

        # ボブ
        elif actor == "bob":
            if basis_type == 0:  # B0: Z基底 (鍵生成用)
                pass
            elif basis_type == 1:  # B1: 45度回転 (CHSH用, W基底) -- Z+X に対応
                qc.ry(-np.pi / 4, qubit)
            elif basis_type == 2:  # B2: -45度回転 (CHSH用, V基底) -- Z-X に対応
                qc.ry(np.pi / 4, qubit)

    def run_protocol(self):
        """DI-QKDプロトコル全体を実行し、全ペアの測定結果を取得する"""
        alice_bases, bob_bases = self.generate_random_bases()
        alice_results = []
        bob_results = []

        print(f"[{self.num_pairs} pairs] DI-QKDプロトコルを実行中...")

        # 各ベルペアに対して個別に回路を回す (学習上の分かりやすさのため)
        for i in range(self.num_pairs):
            qc = self.create_bell_pair_circuit()

            # アリス(qubit 0) と ボブ(qubit 1) それぞれに基底回転を適用
            self.apply_measurement_basis(qc, 0, alice_bases[i], "alice")
            self.apply_measurement_basis(qc, 1, bob_bases[i], "bob")

            qc.measure(0, 0)
            qc.measure(1, 1)

            t_qc = transpile(qc, self.sim)
            # shots=1で各ペアを1回だけ測定
            result = self.sim.run(t_qc, shots=1).result().get_counts()

            # 結果は '00', '01', '10', '11' のいずれか1つのキーのみを持つ
            meas = list(result.keys())[0]

            # Qiskitのエンディアンは c[1]c[0] (ボブの結果が左、アリスが右)
            b_res = int(meas[0])
            a_res = int(meas[1])

            # 期待値計算の数式に合わせて、結果を {0, 1} から {+1, -1} に変換する
            a_val = 1 if a_res == 0 else -1
            b_val = 1 if b_res == 0 else -1

            alice_results.append(a_val)
            bob_results.append(b_val)

        return alice_bases, bob_bases, alice_results, bob_results

    def analyze_results(self, a_bases, b_bases, a_res, b_res):
        """得られた測定結果から「暗号鍵」を生成し、「CHSH不等式」をチェックする"""

        # --- 1. 鍵の生成 (Sifting) ---
        # アリスがA0(Z測定)、ボブがB0(Z測定)を偶然選んだペアだけを抽出する
        key_indices = [
            i for i in range(self.num_pairs) if a_bases[i] == 0 and b_bases[i] == 0
        ]

        # 鍵（ビット列）に戻すため、+1 -> 0, -1 -> 1 に戻す
        alice_key = [0 if a_res[i] == 1 else 1 for i in key_indices]
        bob_key = [0 if b_res[i] == 1 else 1 for i in key_indices]

        # エラーレート（QBER）の計算
        errors = sum([1 for a, b in zip(alice_key, bob_key) if a != b])
        qber = errors / len(alice_key) if len(alice_key) > 0 else 0

        # --- 2. CHSH不等式のチェック ---
        # 期待値 E(A, B) = <A * B> の計算関数
        def calc_expectation(a_base_val, b_base_val):
            indices = [
                i
                for i in range(self.num_pairs)
                if a_bases[i] == a_base_val and b_bases[i] == b_base_val
            ]
            if not indices:
                return 0
            # 結果（+1 または -1）の積の平均をとる
            product_sum = sum(a_res[i] * b_res[i] for i in indices)
            return product_sum / len(indices)

        e_01 = calc_expectation(0, 1)  # E(A0, B1)
        e_02 = calc_expectation(0, 2)  # E(A0, B2)
        e_11 = calc_expectation(1, 1)  # E(A1, B1)
        e_12 = calc_expectation(1, 2)  # E(A1, B2)

        # CHSH スコア S = E(A0, B1) + E(A0, B2) + E(A1, B1) - E(A1, B2)
        chsh_score = e_01 + e_02 + e_11 - e_12

        # --- 3. 結果の表示 ---
        print("\n--- 鍵生成シミュレーション ---")
        print(f"共有されたベルペア総数: {self.num_pairs} pairs")
        print(f"生成されたシフト鍵の長さ: {len(alice_key)} bits")
        print(f"Alice's Key (partial): {alice_key[:15]}")
        print(f"Bob's Key   (partial): {bob_key[:15]}")
        print(f"QBER (量子ビット誤り率): {qber:.2%} (理想は0%)")

        print("\n--- デバイスの安全性検証 (CHSH Test) ---")
        print(f"E(A0, B1) = {e_01:.3f} (理論値:  0.707)")
        print(f"E(A0, B2) = {e_02:.3f} (理論値:  0.707)")
        print(f"E(A1, B1) = {e_11:.3f} (理論値:  0.707)")
        print(f"E(A1, B2) = {e_12:.3f} (理論値: -0.707)")
        print(f"\nCHSH Score S = |{chsh_score:.3f}|")
        print("【判定基準】")
        print(
            "  S <= 2.0      : 古典的な限界（デバイスはハッキングされている、盗聴の危険あり）"
        )
        print("  S ≒ 2.82(2√2) : 量子限界（デバイスは完全に安全、本物のもつれが存在）")

        print("\n結論:")
        if abs(chsh_score) > 2.0:
            print("  CHSH不等式が破れました")
            print(
                "  デバイスは意図通り強力な「量子もつれ」を生成しており、生成された鍵は安全(DI)です。"
            )
        else:
            print("  CHSH不等式が破れていません。")
            print(
                "  途中で盗聴されているか、デバイスのノイズが多すぎるため、鍵は破棄すべきです。"
            )


if __name__ == "__main__":
    # 統計的ばらつきを減らすためにペア数を多め(4000)にして実行
    simulator = DI_QKD_Simulator(num_pairs=4000)
    bases_a, bases_b, res_a, res_b = simulator.run_protocol()
    simulator.analyze_results(bases_a, bases_b, res_a, res_b)
