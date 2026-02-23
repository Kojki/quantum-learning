<img src= https://img.shields.io/github/directory-file-count/Kojki/quantum-learning/README.md>

# Integrated Quantum Simulation Portfolio

## 1. 動機・背景
本プロジェクトは、量子計算、量子通信、および量子センシングの基礎から応用までを統合的に学習し、実装することを目的に立ち上げました。理論をコードに落とし込み、グラフや図を用いて可視化をすることで理解を深めることを重視しています。


---

## 2. 実装内容

### ■ 量子通信 (Quantum Communication)
量子的な性質を利用して、盗聴不可能な通信を実現するプロトコルを実装しています。
- **BB84プロトコル**: 量子鍵配送（QKD）の代表的なアルゴリズム。距離による減衰やノイズ、盗聴者（Eve）の干渉、および誤り訂正・プライバシー増幅までを実装しています。
- **量子テレポーテーション**: 量子もつれ（Entanglement）を利用して、未知の量子状態を離れた場所へ転送する仕組みを Qiskit の動的回路（Dynamic Circuits）を用いて実装しています。

### ■ 量子センシング (Quantum Sensing)
量子ビットを極めて鋭敏なセンサとして利用する技術です。
- **ラムゼー干渉計 (Ramsey Interferometry)**: 位相変化を測定確率に変換する基礎理論。
- **反復位相推定 (IPE)**: 少ない量子ビットで高精度な測定を実現するキャリブレーションの手法。
- **量子フィードバック位相制御 (Quantum Feedback Phase Control)**: リアルタイムで環境の変化（物理的な振動や磁場）に追従し、センサを常に最大感度点に保つ PID 制御を実装しています。

### ■ 量子最適化 (Quantum Optimization)
- **QAOA (Quantum Approximate Optimization Algorithm)**:

---

## 3. 使用技術・ライブラリ
- **Language**: Python 3.10+
- **Framework**: [Qiskit](https://qiskit.org/) (IBM Quantum), [Qulacs](https://docs.qulacs.org/) (QunaSys)
- **Simulator**: Qiskit Aer
- **Visualization**: Matplotlib
- **Math**: NumPy, SymPy

---

## 4. 実行方法
### 環境構築
```bash
# 仮想環境の作成を推奨
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# ライブラリのインストール
pip install qiskit qiskit-aer matplotlib numpy sympy
```

### デモの実行
```bash
```

---

## 5. 学習記録・メモ
- **つまずいた点**: 
- **解決策**: 
- **気づき**: 

---

## 6. 今後の展望実際のハードウェア（IBM Quantum）での実行を想定し、ノイズモデルを取り入れたより現実的なシミュレーションへの拡張。

---

## 7. 参考文献

---

## 8. ライセンス
本プロジェクトは [MIT License](LICENSE) のもとで公開されています。教育および研究目的での利用・改変を歓迎します。