import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from scipy.optimize import minimize


class QuantumClassifier:
    """変分量子分類器 (Variational Quantum Classifier, VQC) の学習クラス.

    量子回路を機械学習のモデルとして利用し、入力データの分類を行います。
    古典的なニューラルネットワークの「層」や「重み」を、量子ゲートの「回転角」として表現します。

    Theory:
        VQCのプロセスは以下の3つの構成要素から成ります：
        1. Feature Map: 古典的なデータ(x)を量子状態に埋め込む (Angle Encoding等)
        2. Ansatz (Variational Circuit): パラメータ(w)を持つ学習可能な回路。
           これがニューラルネットワークの結合荷重に相当します。
        3. Measurement & Optimizer: 測定結果から損失関数を計算し、古典最適化手法でパラメータ(w)を更新する。

    Attributes:
        num_qubits (int): 使用する量子ビット数（特徴量の次元に影響）。
        reps (int): Ansatz内で基本構造を繰り返す回数。モデルの表現力に影響。
        weights (np.ndarray): 学習対象となる重みパラメータ。
    """

    def __init__(self, num_qubits=2, reps=2):
        self.num_qubits = num_qubits
        self.reps = reps
        # 重みの初期化 (RYゲートなどの回転角として使われる)
        # 各層の回転ゲートと、最初の一層分の重みを用意
        self.weights = np.random.rand(num_qubits * (reps + 1))
        self.sim = AerSimulator()

    def _feature_map(self, x):
        """データを量子回路に入力するための特徴量写像 (Angle Encoding).

        ここでは RY ゲートの回転角度としてデータ x を埋め込みます。
        """
        qc = QuantumCircuit(self.num_qubits)
        for i in range(min(len(x), self.num_qubits)):
            # x[i] の値に応じて y 軸周りに回転（北極|0>から南極|1>への広がり）
            qc.ry(x[i], i)
        return qc

    def _ansatz(self, params):
        """学習可能なパラメータを持つ量子回路 (Ansatz).

        回転ゲート (RY) と量子もつれゲート (CX) を組み合わせて、
        データの複雑な境界線を学習できるようにします。
        """
        qc = QuantumCircuit(self.num_qubits)
        param_idx = 0
        for r in range(self.reps + 1):
            # 1. 各ビットを学習パラメータで回転させる（回転層）
            for i in range(self.num_qubits):
                qc.ry(params[param_idx], i)
                param_idx += 1

            # 2. 隣接するビット間にもつれ (Entanglement) を作る（もつれ層）
            if r < self.reps:
                for i in range(self.num_qubits - 1):
                    qc.cx(i, i + 1)
        return qc

    def _create_circuit(self, x, params):
        """Feature Map と Ansatz を結合した全回路を構築."""
        qc = QuantumCircuit(self.num_qubits)
        # データの埋め込み
        qc.compose(self._feature_map(x), inplace=True)
        # 学習可能な層の追加
        qc.compose(self._ansatz(params), inplace=True)
        # 最終的な判定のための測定
        qc.measure_all()
        return qc

    def predict(self, x, params=None):
        """モデルを用いて入力データ x のラベルを予測します.

        Returns:
            int: 予測されたラベル (0 または 1)。
        """
        if params is None:
            params = self.weights

        qc = self._create_circuit(x, params)
        t_qc = transpile(qc, self.sim)
        # 量子コンピュータ（シミュレータ）で実行
        result = self.sim.run(t_qc, shots=1024).result()
        counts = result.get_counts()

        # 測定結果のパリティ（1の個数が偶数か奇数か）を用いて分類
        # 期待値計算の一種として機能します
        p0 = (
            sum(count for bit, count in counts.items() if bit.count("1") % 2 == 0)
            / 1024
        )
        return 0 if p0 > 0.5 else 1

    def fit(self, X, y, maxiter=20):
        """訓練データを用いて重みパラメータ w を最適化（学習）します。

        古典的な最適化アルゴリズム(COBYLA等)を用いて、損失関数を最小化します。
        """

        def objective(params):
            """損失関数: 予測確率と正解ラベルの差（MSE）を計算します."""
            loss = 0
            for i in range(len(X)):
                qc = self._create_circuit(X[i], params)
                t_qc = transpile(qc, self.sim)
                counts = self.sim.run(t_qc, shots=512).result().get_counts()

                # ラベル1である確率を期待値として抽出
                p1 = (
                    sum(
                        count
                        for bit, count in counts.items()
                        if bit.count("1") % 2 != 0
                    )
                    / 512
                )
                # 平均二乗誤差 (MSE) の蓄積
                loss += (p1 - y[i]) ** 2
            return loss / len(X)

        print(f"学習を開始します (最大イテレーション: {maxiter})...")
        # 古典オプティマイザが量子回路のパラメータを少しずつ動かして最適解を探す
        res = minimize(
            objective, self.weights, method="COBYLA", options={"maxiter": maxiter}
        )
        self.weights = res.x
        return res


if __name__ == "__main__":
    # --- シンプルな線形分離データの学習テスト ---
    # [x1, x2] の二次元データ
    X_train = np.array([[0.1, 0.1], [0.8, 0.8], [0.2, 0.3], [0.7, 0.6]])
    y_train = np.array([0, 1, 0, 1])

    # 2量子ビット、1レイヤーのシンプルな構成
    vqc = QuantumClassifier(num_qubits=2, reps=1)
    vqc.fit(X_train, y_train, maxiter=30)

    # テスト予測
    print("\n[テスト予測]")
    for test_x in [[0.2, 0.2], [0.9, 0.9]]:
        prediction = vqc.predict(test_x)
        print(f"入力 {test_x} に対する予測ラベル: {prediction}")
