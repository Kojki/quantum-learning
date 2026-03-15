# Grover Simulation

Welcome to this "Grover Simulation" page!

Grover のアルゴリズムを用いて組み合わせ最適化問題を解くシミュレーターです。  
量子と古典の探索を比較し、ノイズの影響も含めて可視化することを目的としています。

---

## 特徴

- **Durr-Hoyer アルゴリズム**による反復的な最適解探索（しきい値を事前に知る必要がない）
- **古典（全探索）との比較**：実行時間・探索ステップ数・最適解の一致を自動で比較
- **ノイズモデルの選択**：理想・脱分極・熱緩和・実機相当（IBM Eagle r3 など）から選択可能
- **対話形式の入力**：都市数・都市名・距離行列などをターミナルから入力可能
- **地名→座標の自動取得**：地名を入力すると OpenStreetMap から座標を取得し、実距離を自動計算
- **可視化**：確率変化アニメーション・古典 vs 量子レース・地図上のルート描画

---

## ディレクトリ構成
```
src/grover_simulation/
├── main.py                  # 実行エントリーポイント
├── config.py                # デフォルト設定
├── input_handler.py         # 対話形式の入力処理
│
├── problems/                # 最適化問題の定義
│   ├── base.py              # 抽象基底クラス（OptimizationProblem）
│   ├── routing.py           # 巡回セールスマン問題（TSP）
│   ├── knapsack.py          # ナップサック問題（未実装）
│   └── scheduling.py        # スケジューリング問題（未実装）
│
├── quantum/                 # 量子アルゴリズム
│   ├── oracle.py            # オラクル回路の構築
│   ├── grover.py            # Grover 回路・Durr-Hoyer アルゴリズム
│   ├── noise.py             # ノイズモデルの構築（実機パラメータ対応）
│   └── simulator.py         # （未実装）
│
├── classical/               # 古典アルゴリズム
│   ├── brute_force.py       # 全探索
│   └── heuristic.py         # ヒューリスティック（未実装）
│
├── benchmark/               # ベンチマーク・評価
│   └── metrics.py           # 量子 vs 古典のメトリクス算出
│
├── visualizer/              # 可視化
│   ├── core.py              # 共通ユーティリティ（フォント・色・保存）
│   ├── animation.py         # 確率変化アニメーション（理想 vs ノイズあり）
│   ├── state_plotter.py     # 古典 vs 量子レースアニメーション
│   ├── landscape.py         # 3D 成功確率サーフェス（未実装）
│   └── state_plotter.py     # 量子状態プロット（未実装）
│
├── geo/                     # 地図・座標関連
│   ├── geocoder.py          # 地名→緯度経度の自動取得（geopy）
│   ├── distance.py          # 座標間の実距離計算（haversine 公式）
│   └── map_plotter.py       # 地図上へのルート描画（contextily）
│
├── data/                    # 実験データ管理（未実装）
│   ├── experiments.py
│   └── persistence.py
│
├── animation/               # アニメーション実行（未実装）
│   └── runner.py
│
├── docs/                    # ドキュメント
│   └── grover_simulation_requirements.md  # 要件定義書
│
└── references/              # 参考文献・出典まとめ
    ├── noise_models.md      # ノイズパラメータの出典
    ├── algorithms.md        # （未実装）
    ├── benchmarks.md        # （未実装）
    └── datasets.md          # （未実装）
```

---

## 動作環境

- Python 3.10 以上
- 以下のライブラリが必要です：
```bash
pip install qiskit qiskit-aer matplotlib numpy scipy scikit-learn
pip install geopy contextily pyproj
```

---

## 実行方法
```bash
cd src/grover_simulation
python main.py
```

起動すると以下のメニューが表示されます：
```
==================================================
  Grover シミュレーター
==================================================

設定の読み込み方法を選んでください：
  1. config.py の設定をそのまま使う
  2. 対話形式で入力する
```

### 対話形式の入力モード

「2」を選ぶと以下の項目を順番に入力できます：

**都市の入力方法：**
- `1` — 都市数だけ指定（名前は A, B, C... と自動設定）
- `2` — 都市名を自分で入力（距離行列の手動入力、または地名から自動取得）
- `3` — サンプル問題を選ぶ（日本の主要都市・ヨーロッパの主要都市など）

**その他の設定：**
- Durr-Hoyer アルゴリズムの最大反復回数
- ショット数・ancilla モード
- ノイズモデル（`ideal` / `depol` / `thermal` / `combined`）
- 乱数シード
- GIF 保存先ディレクトリ

---

## アルゴリズムの説明

### Grover のアルゴリズム

Grover のアルゴリズムは、N 個の候補の中から正解を探す問題を  
古典の O(N) に対して O(√N) のステップで解く量子探索アルゴリズムです。

回路の構造：
```
|0⟩ ── H ──┬── Oracle ── Diffusion ──┬── 測定
            │                         │
            └────── k 回繰り返す ──────┘
```

- **Oracle**：正解のビット列に -1 の位相を付与する
- **Diffusion**：平均値を軸とした位相反転（振幅増幅）
- **最適反復回数**：π/4 × √(N/M)（M = 正解の数）

### Durr-Hoyer アルゴリズム

最適化問題では「正解」が事前にわかりません。  
Durr-Hoyer アルゴリズムはしきい値を事前に指定せず、  
反復的にしきい値を下げながら最適解に近づきます。
```
1. 実行可能解からランダムに1つ選び、そのコストを初期しきい値とする
2. 「現在のしきい値より良い解」を Grover で探す
3. 見つかればしきい値を更新して 2 に戻る
4. 見つからなければ現在の最良解を返す
```

出典：Durr, C. & Hoyer, P., "A quantum algorithm for finding the minimum",  
arXiv:quant-ph/9607014, 1996.

### ノイズモデル

実機（IBM Quantum）のパラメータを使ったノイズモデルを選択できます。

| モード | 内容 |
|---|---|
| `ideal` | ノイズなし（理想シミュレーション） |
| `depol` | 脱分極ノイズのみ |
| `thermal` | 熱緩和ノイズのみ（T1・T2） |
| `combined` | 脱分極＋熱緩和＋読み出しエラーの合成 |

デバイスプリセット：`eagle_r3` / `heron_r1` / `heron_r2` / `heron_r3`  
パラメータの出典は `references/noise_models.md` を参照してください。

---

## 出力ファイル

実行後、`output/` フォルダに以下が保存されます：

| ファイル | 内容 |
|---|---|
| `grover_animation.gif` | 確率変化アニメーション（理想 vs ノイズあり） |
| `classical_vs_quantum.gif` | 古典 vs 量子レースアニメーション |
| `route_map.png` | 地図上の最適ルート（地名入力モードのみ） |

---

## 現在の実装状況

| フェーズ | 内容 | 状態 |
|---|---|---|
| 1 | 要件定義 | 完了 |
| 2 | 基本・詳細設計 | 完了 |
| 3 | 基盤実装 | 完了 |
| 4 | オラクル・ノイズ実装 | 完了 |
| 5 | 評価と統合 | 進行中 |

未実装：`knapsack.py`・`scheduling.py`・`heuristic.py`・`data/`・一部 `visualizer/`

---

## ライセンス

MIT License