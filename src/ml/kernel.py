import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from sklearn.svm import SVC

class QuantumKernelSVC:
    """量子カーネル法を用いたサポートベクター分類器 (SVC).

    量子回路を「高次元空間への写像」として使い、古典的なSVMで分類を行います。

    Theory:
        1. Feature Map: データ x を量子状態 |ψ(x)> に変換する。
        2. Quantum Kernel: 2つのデータ x, y の類似度を、量子状態の内積の2乗
           K(x, y) = |<ψ(x)|ψ(y)>|^2 として定義する。
        3. 古典SVM: この量子的な類似度行列（カーネル行列）を用いて、
           古典コンピュータがデータの境界線を決定する。

    Merit:
        古典コンピュータでは計算が非常に困難な「複雑な重なり」を持つデータを、
        巨大な量子特徴空間に飛ばすことで、鮮やかに分離できる可能性があります。
    """

    def __init__(self, num_qubits=2):
        self.num_qubits = num_qubits
        self.sim = AerSimulator()
        self.svc = SVC(kernel='precomputed') # 量子カーネルを外部から与える設定

    def _feature_map(self, x):
        """データを量子状態に写像する。"""
        qc = QuantumCircuit(self.num_qubits)
        for i in range(min(len(x), self.num_qubits)):
            qc.h(i)
            qc.rz(x[i], i)
        # もつれを追加して複雑な相関を表現
        for i in range(self.num_qubits - 1):
            qc.cx(i, i + 1)
        return qc

    def calculate_kernel_element(self, x1, x2):
        """2つのデータ点間の量子カーネル値 K(x1, x2) を計算."""
        # |<ψ(x1)|ψ(x2)>|^2 を計算するために、
        # <0| U(x2)† U(x1) |0> の遷移確率を測定する
        qc = QuantumCircuit(self.num_qubits)
        
        # U(x1) を適用
        qc.compose(self._feature_map(x1), inplace=True)
        # U(x2)† (逆操作) を適用
        qc.compose(self._feature_map(x2).inverse(), inplace=True)
        
        qc.measure_all()
        
        t_qc = transpile(qc, self.sim)
        shots = 1024
        result = self.sim.run(t_qc, shots=shots).result()
        counts = result.get_counts()
        
        # 全てが '00...0' に戻る確率が、内積の2乗（類似度）になる
        return counts.get('0' * self.num_qubits, 0) / shots

    def compute_kernel_matrix(self, X1, X2):
        """データセット間のカーネル行列を計算."""
        matrix = np.zeros((X1.shape[0], X2.shape[0]))
        for i in range(X1.shape[0]):
            for j in range(X2.shape[0]):
                matrix[i, j] = self.calculate_kernel_element(X1[i], X2[j])
        return matrix

    def fit(self, X, y):
        """量子カーネル行列を計算し、SVMを訓練."""
        print(f"量子カーネル行列の計算を開始します (データ数: {len(X)})...")
        K_train = self.compute_kernel_matrix(X, X)
        self.train_X = X
        return self.svc.fit(K_train, y)

    def predict(self, X):
        """未知のデータに対するラベルを予測."""
        K_test = self.compute_kernel_matrix(X, self.train_X)
        return self.svc.predict(K_test)

if __name__ == "__main__":
    # --- シンプルな動作テスト (非線形な XOR 風データ) ---
    X_train = np.array([[0, 0], [np.pi, np.pi], [0, np.pi], [np.pi, 0]])
    y_train = np.array([0, 0, 1, 1]) # 同じものは 0, 違うものは 1
    
    qkernel = QuantumKernelSVC(num_qubits=2)
    qkernel.fit(X_train, y_train)
    
    print("\n[テスト予測]")
    test_data = np.array([[0.1, 0.1], [0.1, 3.0]])
    predictions = qkernel.predict(test_data)
    for data, pred in zip(test_data, predictions):
        print(f"入力 {data} への予測: Class {pred}")
