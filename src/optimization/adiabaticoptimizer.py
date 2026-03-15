# ==================== 定数定義 ====================

# シミュレーション設定
DEFAULT_ANNEALING_TIME = 10.0  # デフォルトのアニーリング時間 T [s]
DEFAULT_STEPS = 40  # デフォルトの刻み数 N
DEFAULT_SHOTS = 1024  # 測定回数

# スケジュール設定
SCHEDULE_LINEAR = "linear"  # 線形スケジュール
SCHEDULE_SIN_SQ = "sin_sq"  # sin^2 スケジュール

# ==================== ここまで定数 ====================

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


class AdiabaticOptimizer:
    """量子断熱計算 (Adiabatic Quantum Computation) を用いた汎用最適化クラス.

    このクラスは、ハミルトニアンの断熱発展を量子ゲート（RX, RZ, CX）の組み合わせでシミュレートし、
    組み合わせ最適化問題の基底状態（最適解）を探索します。
    ユーザーは任意の1量子ビット制約（磁場項）と2量子ビット相互作用（結合項）を定義できます。

    Theory:
        全ハミルトニアン H(t) = A(t)H_start + B(t)H_target において、
        - H_start: 初期状態で全探索を行うための横磁場 (ΣX_i)。量子的な重ね合わせを作ります。
        - H_target: 解きたい問題を表現したコスト関数 (Σh_i Z_i + ΣJ_ij Z_i Z_j)。

        断熱定理により、H(t)を十分にゆっくり変化させることで、システムは常に基底状態を維持し、
        最終的に H_target の最小エネルギー状態（最適解）に到達します。

    Attributes:
        num_qubits (int): 使用する量子ビットの数。
        h_terms (list): 単一ビット制約 [ (index, weight), ... ]。
        j_terms (list): 二ビット間相互作用 [ (i, j, weight), ... ]。

    Example:
        >>> opt = AdiabaticOptimizer(2)
        >>> opt.add_j_term(0, 1, 1.0) # 0番と1番を逆の向きに導く(Max-Cut)
        >>> counts, qc = opt.run()
    """

    def __init__(self, num_qubits: int):
        """
        Args:
            num_qubits (int): 使用する量子ビットの数（頂点数）。
        """
        self.num_qubits = num_qubits
        self.h_terms = []  # 単一ビット制約 (h_i * Z_i)
        self.j_terms = []  # 2ビット間相互作用 (J_ij * Z_i * Z_j)

    def add_h_term(self, i: int, weight: float) -> None:
        """単一ビット制約（局所磁場項）を追加します.

        ビット i が 0 または 1 のどちらかの状態に偏るようにエネルギーを定義します。
        負の重みは |1> への偏り（上向き磁場）を、正の重みは |0> への偏りを強めます。

        Args:
            i (int): 対象となる量子ビットのインデックス (0 ~ num_qubits-1)。
            weight (float): 項の重み（係数）。
        """
        if 0 <= i < self.num_qubits:
            self.h_terms.append((i, weight))
        else:
            print(f"Error: Qubit index {i} is out of range.")

    def add_j_term(self, i: int, j: int, weight: float) -> None:
        """二ビット間相互作用（結合項）を追加します.

        ビット i と j の間の相関（同じ向きか、違う向きか）に基づく制約を定義します。
        正の重みは「違う向き（反強磁性的）」を、
        負の重みは「同じ向き（強磁性的）」をエネルギー的に優先します。

        Args:
            i (int): 量子ビットAのインデックス。
            j (int): 量子ビットBのインデックス。
            weight (float): 相互作用の強さ（J_ij）。
        """
        if 0 <= i < self.num_qubits and 0 <= j < self.num_qubits:
            self.j_terms.append((i, j, weight))
        else:
            print(f"Error: Qubit index {i} or {j} is out of range.")

    def _get_schedule(self, s: float, mode: str = SCHEDULE_LINEAR) -> tuple:
        """アニーリング推移（スケジューリング関数）を計算します.

        正規化された時間 s における A(s) と B(s) を決定します。
        A(s) は初期ハミルトニアン（揺らぎ）、B(s) は目的ハミルトニアンの強さを制御します。

        Args:
            s (float): 正規化された時間 (0.0 ~ 1.0)。
            mode (str): スケジュールの種類 ('linear' または 'sin_sq')。

        Returns:
            tuple[float, float]: (1-b, b) の係数タプル。
        """
        if mode == SCHEDULE_SIN_SQ:
            # S字曲線状に遷移させることで、断熱性を維持しやすくする
            b = np.sin(s * np.pi / 2) ** 2
        else:
            # 直線的に遷移させる
            b = s
        return 1 - b, b

    def build_circuit(
        self,
        T: float = DEFAULT_ANNEALING_TIME,
        N: int = DEFAULT_STEPS,
        schedule: str = SCHEDULE_LINEAR,
    ) -> QuantumCircuit:
        """設定されたハミルトニアンに基づいて量子回路を構築します.

        トロッター分解を用いて連続的な断熱発展を離散的な量子ゲートに変換します。

        Args:
            T (float): 全アニーリング時間 [s]。
            N (int): トロッター分解のステップ数（刻み数）。
            schedule (str): 使用するスケジュール方式名。

        Returns:
            QuantumCircuit: 構築された量子回路。
        """
        dt = T / N  # 1ステップあたりの時間短冊
        s_vals = np.linspace(0, 1, N + 1)
        qc = QuantumCircuit(self.num_qubits)

        # 1. 初期状態: 全パターンの平等な重ね合わせ |+>^n を準備
        qc.h(range(self.num_qubits))
        qc.barrier()

        # 2. 時間発展ループ (アニーリング遷移過程)
        for step in range(N):
            A, B = self._get_schedule(s_vals[step], mode=schedule)

            # --- Mixing Hamiltonian (X-項): 量子的な探索（揺らぎ）の付与 ---
            for i in range(self.num_qubits):
                # 横方向にビットを回転させ、重ね合わせを維持する
                qc.rx(-2 * A * dt, i)

            # --- Cost Hamiltonian (Z-項): 解決したい問題の制約を適用 ---
            # 1-qubit terms (磁場係数 h_i)
            for i, w in self.h_terms:
                qc.rz(2 * B * dt * w, i)

            # 2-qubit terms (相互作用係数 J_ij)
            for i, j, w in self.j_terms:
                qc.cx(i, j)
                qc.rz(2 * B * dt * w, j)
                qc.cx(i, j)

            qc.barrier()

        qc.measure_all()
        return qc

    def run(
        self,
        T: float = DEFAULT_ANNEALING_TIME,
        N: int = DEFAULT_STEPS,
        schedule: str = SCHEDULE_LINEAR,
        shots: int = DEFAULT_SHOTS,
    ):
        """シミュレーションを実行し、測定結果を取得します.

        Args:
            T (float): 全アニーリング時間。
            N (int): ステップ数。
            schedule (str): スケジュール方式。
            shots (int): 測定の試行回数。

        Returns:
            tuple[dict, QuantumCircuit]: (測定カウントの辞書, 実行された回路オブジェクト)。
        """
        qc = self.build_circuit(T, N, schedule)
        sim = AerSimulator()
        t_qc = transpile(qc, sim)
        result = sim.run(t_qc, shots=shots).result()
        return result.get_counts(), qc


if __name__ == "__main__":
    # --- シンプルな動作テスト (3ノード相互作用問題) ---
    print("\n--- AdiabaticOptimizer Test Run ---")
    opt = AdiabaticOptimizer(3)
    # 0-1, 1-2 間に斥力（違う値になれ）を働かせる
    opt.add_j_term(0, 1, 1.0)
    opt.add_j_term(1, 2, 1.0)

    counts, _ = opt.run(T=10.0, N=30, schedule=SCHEDULE_SIN_SQ)
    print("測定結果 (上位):")
    sorted_counts = dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))
    for bit, count in list(sorted_counts.items())[:3]:
        print(f" 状態 |{bit}⟩: {count}回")
