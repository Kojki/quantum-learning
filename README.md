# 🌌 Quantum Learning Hub: 実践・量子計算ポートフォリオ

[![Qiskit](https://img.shields.io/badge/Framework-Qiskit-blueviolet)](https://qiskit.org/)
[![Qulacs](https://img.shields.io/badge/Simulator-Qulacs-blue)](http://www.qulacs.org/)
[![Status](https://img.shields.io/badge/Project--Status-In--Progress-yellow)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 「理論をコードで動かし、視覚的に理解する」をコンセプトにした、量子計算の総合学習リポジトリです。

---

## 👩‍🏫 はじめて学習される方へ
このリポジトリは、量子コンピュータの基礎から応用までをステップバイステップで学べるように構成されています。以下の順番で進めるのがおすすめです：

1.  **[量子計算 15の基礎ステップ](./docs/fundamentals/00_README.md)**: まったくのゼロからハミルトニアンの壁を越え、実機エラーの理解までをなだらかに繋ぐ究極のガイド。
2.  **[アルゴリズム実戦解説](./docs/ALGORITHM_GUIDE.md)**: 各フォルダにあるコードの「仕組み」を詳しく解説しています。

---

## 📂 ディレクトリ構成 (Directory Tour)
リポジトリ内部の整理整頓された構造を紹介します。学習の目的に合わせて探索してください。

- **`notebooks/`**: 🧪 **体験学習用ノートブック**
  - 初心者向けのチュートリアルが含まれています。コードを1セルずつ動かしながら、理論がグラフに変わる瞬間を体験できます。
- **`src/`**: ⚙️ **コア・アルゴリズム実装**
  - **`sensing/`**: 量子ビットをセンサとして使うための制御ロジック（IPE, PIDなど）を格納。
  - **`optimization/`**: 最適化問題を解くためのエンジン（QAOA, AQC, Grover）を実装。
  - **`communication/`**: 暗号通信（BB84）や状態転送（Teleportation）のプロトコル群。
  - **`ml/`**: 量子的なパターン認識を行う分類器（VQC, Kernel）を実装。
- **`docs/`**: 📚 **ナレッジベース**
  - 理論と実装を繋ぐための詳しい解説ドキュメント。

---

## 🔬 扱っている量子技術 (Quantum Technologies)
本リポジトリでは、「なぜその技術が必要なのか」という実用的な視点を重視しています。

### **1. 量子精密測定 (Sensing)**
- **反復位相推定 (IPE)**: わずか1つの補助ビットで、高い測定精度を叩き出す「リソース節約術」。
- **リアルタイム・フィードバック**: ノイズによるドリフトを検知し、瞬時に補正を加える「自律安定化」技術。

### **2. 組み合わせ最適化 (Optimization)**
- **QUBO マッピング**: 現実の問題を「エネルギーのパズル」に変換する技術。
- **QAOA / AQC**: 量子の力を借りて、膨大な選択肢の中から最短ルートを見つけ出す。

### **3. セキュア通信 (Communication)**
- **QKD (量子鍵配送)**: 盗聴者が「見た」だけでバレてしまう物理法則を利用した暗号。
- **プライバシー増幅**: わずかに漏れた情報さえも、ハッシュ化によって無効化する数学的防御。

### **4. 次世代機械学習 (ML)**
- **量子カーネル法**: 人間の目や古典コンピュータには見えない複雑なデータの「模様」を量子空間で捉える。

---

## 🧭 学習ロードマップ (Learning Path)
各フォルダの `.ipynb` (Jupyter Notebook) を実行することで、理論とシミュレーションを同時に学べます。

### 1. 量子センシング (Sensing)
量子ビットを「超高感度センサ」として使う技術。
- [x] **01_Physics_of_Phase**: 位相が確率に変わる干渉の仕組み。
- [x] **02_Scaling_Precision**: 反復推定(IPE)で精度を指数関数的に高める方法。
- [x] **03_Feedback_Stabilization**: ドリフト（外部ノイズ）をリアルタイムで補正する。

### 2. 量子最適化 (Optimization)
複雑なパズルの最適解を高速に探す技術。
- [x] **01_Mapping_to_QUBO**: 現実の問題をハミルトニアン（数式）に変換。
- [x] **02_Adiabatic_Optimization**: ゆっくり時間をかけて正解に導く断熱計算。
- [x] **03_QAOA_Optimization_Engine**: 量子と古典のハイブリッドによる高速化。

### 3. 量子通信 (Communication)
物理法則で守られた、絶対に盗聴できない通信。
- [x] **01_BB84_Security_Principle**: なぜ盗聴を確実に検知できるのか？
- [x] **02_Noise_Limit_Analysis**: どの程度のノイズまでなら安全が守れるか。

### 4. 量子機械学習 (Machine Learning)
量子ビットの広大な空間で、データの複雑な相関を捉える。
- [x] **01_Variational_Classifier**: 量子回路をニューラルネットワークのように学習。
- [x] **02_Quantum_Kernel_Basics**: 量子の力でデータをスッキリ分離する。

---

## 🛠 使用技術
- **Language**: Python 3.10+
- **Quantum Framework**: [Qiskit](https://qiskit.org/)
- **Simulator**: AerSimulator (ノイズモデル対応)
- **Math & Data**: NumPy, Scipy, Scikit-learn, Sympy
- **UI & Graphics**: Matplotlib, Seaborn, Tkinter

---

## 🚀 環境構築と実行
```bash
# クローン
git clone https://github.com/Kojki/quantum-learning.git
cd quantum-learning

# 依存ライブラリのインストール
pip install qiskit qiskit-aer matplotlib numpy scipy scikit-learn seaborn sympy
```

---

## 🤝 貢献とフィードバック
本プロジェクトは、量子計算を学ぶすべての人に開かれています。誤植の指摘や、新しいアルゴリズムの提案など、IssueやPull Requestをお待ちしております！

---

## 📜 ライセンス
MIT License - 詳細は [LICENSE](LICENSE) をご覧ください。
