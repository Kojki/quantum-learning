# Grover Simulation

Welcome to this "Grover Simulation" page!

このページではグローバーのアルゴリズムについて扱います。

## 主な特徴

* コードの部分では量子回路の中身まで扱います。
* 出力されたシミュレーション結果に対して逐次グラフや回路図を表示して可視化します。
* ビット数や探索対象について、ユーザが最初に値を入力することができます。

## このプロジェクトでの全体像
```
OptimizationProblem（抽象クラス）
  ├── abstractmethod: encode()
  ├── abstractmethod: decode()
  ├── abstractmethod: cost()
  ├── abstractmethod: is_feasible()
  ├── abstractmethod: n_qubits_required()
  ├── abstractmethod: describe()
  └── 通常メソッド: make_condition()  ← 共通処理

        ↓ 継承

VehicleRoutingProblem     KnapsackProblem     SchedulingProblem
  └── cost(): 距離計算      └── cost(): 価値計算  └── cost(): 時間計算
  └── encode(): ルート→bits └── encode(): ...    └── encode(): ...
  └── ...                   └── ...              └── ...

…作成中
```



## 推奨環境
- Python 3.12 以上
- qiskit
- qiskit-aer
- matplotlib
- numpy

## インストール手順
```bash
# クローン
git clone https://github.com/Kojki/quantum-learning.git
cd quantum-learning

# ライブラリのインストール
pip install qiskit qiskit-aer matplotlib numpy
```

# ファイル
以下は以前検討したファイル群です。　今後もしばらく構成を変える可能性が高いのでこのままにしておきます。
* [main.py](https://github.com/Kojki/quantum-learning/tree/main/src/grover_simulation/main.py)
* [oracle.py](https://github.com/Kojki/quantum-learning/tree/main/src/grover_simulation/oracle.py)
* [grover.py](https://github.com/Kojki/quantum-learning/tree/main/src/grover_simulation/grover.py)
* [simulator.py](https://github.com/Kojki/quantum-learning/tree/main/src/grover_simulation/simulator.py)
* [visualizer.py](https://github.com/Kojki/quantum-learning/tree/main/src/grover_simulation/visualizer.py)

# アルゴリズムの説明
作成中...

--------------------------------------------