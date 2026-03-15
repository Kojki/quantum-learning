<img src= https://img.shields.io/github/directory-file-count/Kojki/quantum-learning/README.md>


""""""""" 作成途中です！！完成しているように見えるものでも完成していません。（暫定値を置いたりしています）ご了承ください！！ """"""""""

<div align="center">

# Integrated Quantum Simulation Portfolio

量子アルゴリズムの基礎から応用までを実装・検証するための学習リポジトリです。  
A learning repository for implementing and verifying quantum algorithms from basics to applications.

[![Qiskit](https://img.shields.io/badge/Framework-Qiskit-blueviolet)](https://qiskit.org/)
[![Qulacs](https://img.shields.io/badge/Framework-Qulacs-blue)](http://www.qulacs.org/)
[![Status](https://img.shields.io/badge/Status-In_Progress-yellow)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

> ⚠️ **作成途中のリポジトリです。** 完成しているように見えるファイルでも暫定値が含まれる場合があります。

---

## 概要 / Overview

このリポジトリは、量子技術の主要な分野を網羅的に実装・学習することを目的としています。  
単なるサンプルコードの集まりではなく、理論的背景・出典・実装の意図を丁寧に記述することを方針としています。

This repository aims to implement and study major areas of quantum technology comprehensively.  
The policy is to carefully document theoretical backgrounds, references, and implementation intent.

---

## ディレクトリ構成 / Directory Structure
```
quantum-learning/
├── src/
│   ├── sensing/              # 量子精密測定
│   ├── optimization/         # 量子最適化（QAOA・断熱計算・Grover）
│   ├── grover_simulation/    # Grover シミュレーター（詳細実装）
│   ├── communication/        # 量子通信（BB84・DI-QKD・量子テレポーテーション）
│   ├── ml/                   # 量子機械学習（VQC・量子カーネル）
│   └── pre_optimization/     # 古典最適化の前処理（作成中）
├── notebooks/                # Jupyter Notebook によるシミュレーション・可視化
├── docs/                     # 学習用ドキュメント
└── memo/                     # 作業メモ
```

---

## 実装内容 / Contents

### 1. 量子精密測定 / Quantum Sensing　[`src/sensing/`]

量子ビットをセンサとして使う技術を扱います。

| ファイル | 内容 | 状態 |
|---|---|---|
| `ipe_algorithm.py` | 反復位相推定（IPE）：1つの補助ビットで高精度な位相推定を実現 | ✅ |
| `pid_control.py` | PID制御：ノイズによるドリフトをリアルタイムで補正 | ✅ |

---

### 2. 量子最適化 / Quantum Optimization　[`src/optimization/`]

組み合わせ最適化問題を量子アルゴリズムで解くエンジン群です。

| ファイル | 内容 | 状態 |
|---|---|---|
| `QAOA.py` | 量子近似最適化アルゴリズム（QAOA） | ✅ |
| `adiabaticoptimizer.py` | 断熱量子計算（AQC）による最適化 | ✅ |
| `grover.py` | Grover を使った最適化（概要実装） | ✅ |

より詳細な Grover シミュレーションは [`src/grover_simulation/`](src/grover_simulation/README.md) を参照してください。

---

### 3. Grover シミュレーター / Grover Simulation　[`src/grover_simulation/`]

Grover のアルゴリズムを使った組み合わせ最適化の詳細実装です。  
ノイズモデル・Durr-Hoyer アルゴリズム・地図可視化まで含む本格的なシミュレーターです。

**主な機能：**
- Durr-Hoyer アルゴリズムによる反復的最適解探索
- 実機相当のノイズモデル（IBM Eagle r3 / Heron r1・r2・r3）
- 古典（全探索）との自動比較・ベンチマーク
- 確率変化アニメーション（理想 vs ノイズあり）
- 地名入力 → 座標自動取得 → 地図上のルート描画

詳細は [`src/grover_simulation/README.md`](src/grover_simulation/README.md) を参照してください。

---

### 4. 量子通信 / Quantum Communication　[`src/communication/`]

盗聴検知・安全な鍵配送・量子状態転送を扱います。

| ファイル | 内容 | 状態 |
|---|---|---|
| `BB84.py` | BB84 プロトコル：量子鍵配送の標準方式 | ✅ |
| `DI-QKD.py` | デバイス非依存 QKD（DI-QKD） | ✅ |
| `quantum_teleportation.py` | 量子テレポーテーション | ✅ |

---

### 5. 量子機械学習 / Quantum Machine Learning　[`src/ml/`]

量子コンピュータを機械学習に応用する手法を扱います。

| ファイル | 内容 | 状態 |
|---|---|---|
| `VQC.py` | 変分量子回路（VQC）による分類 | ✅ |
| `kernel.py` | 量子カーネル法：量子空間でのデータの類似度計算 | ✅ |

---

### 6. 古典最適化の前処理 / Pre-optimization　[`src/pre_optimization/`]

量子最適化を適用する前の古典的な定式化手法を扱います。

| ファイル | 内容 | 状態 |
|---|---|---|
| `mathematical_optimization.py` | 数理最適化の基礎 | ⬜ 作成中 |

---

## 学習の進め方 / Learning Path

初めてこのリポジトリを使う方には以下の順番をお勧めします。
```
1. notebooks/          ← まずここで動かして感覚をつかむ
2. src/sensing/        ← 量子ビットの基本的な動作を理解する
3. src/communication/  ← 量子の性質を通信に応用する仕組みを学ぶ
4. src/optimization/   ← 最適化問題への量子アルゴリズムの適用を概観する
5. src/grover_simulation/ ← Grover を深く掘り下げる
6. src/ml/             ← 機械学習との融合を学ぶ
```

---

## 環境構築 / Setup

### 必要なライブラリ
```bash
# 基本ライブラリ
pip install qiskit qiskit-aer matplotlib numpy scipy scikit-learn seaborn sympy

# grover_simulation で必要な追加ライブラリ
pip install geopy contextily pyproj
```

### 実行方法（Grover シミュレーター）
```bash
cd src/grover_simulation
python main.py
```

---

## 使用技術 / Tech Stack

| 用途 | ライブラリ |
|---|---|
| 量子回路 | [Qiskit](https://qiskit.org/)・[Qulacs](http://www.qulacs.org/) |
| シミュレーター | Qiskit Aer（ノイズモデル対応） |
| 数値計算 | NumPy・SciPy・SymPy |
| 機械学習 | Scikit-learn |
| 可視化 | Matplotlib・Seaborn |
| 地図・座標 | geopy・contextily・pyproj |

---

## ライセンス / License

MIT License — 詳細は [LICENSE](LICENSE) をご覧ください。