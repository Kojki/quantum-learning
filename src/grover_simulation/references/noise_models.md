# Noise Models — 出典・データまとめ
 
対応コード: `quantum/noise.py`
 
---
 
## デバイスプリセット
 
**主要出典:**
- AbuGhanem, M., "IBM Quantum Computers: Evolution, Performance, and Future Directions",
  arXiv:2410.00916v1, September 17, 2024.
  https://arxiv.org/abs/2410.00916
 
**補助出典（IBM Quantum Platform）:**
- IBM Quantum Platform, "Compute Resources"
  https://quantum.ibm.com/services/resources?tab=systems
  取得日: 2026年3月17日
 
> [!NOTE]
> **2026年3月取得分のCSVについて**
>
> 各デバイスのキャリブレーションデータを IBM Quantum Platform からCSV形式でエクスポートし、
> 全 qubit の中央値をプリセット値として使用している。
> arXiv 論文（2024年7月3〜4日取得）と取得日が異なるため、値が更新されている場合がある。
> 以下の表の値はすべて **2026年3月取得のCSV中央値** を採用している。
 
---
 
> [!NOTE]
> **ゲートエラー率（SX error / ECR error / CZ error）について**
>
> 論文 Section VI より、これらの値は **ランダム化ベンチマーク（RB）による平均ゲート忠実度** から算出される。
> RB は depolarizing チャネルを仮定した全エラーの合計を測定するものであり、
> 純粋な depolarizing エラー率ではない（コヒーレントエラーやリークを含む可能性がある）。
> `quantum/noise.py` では depolarizing エラー率の近似値として使用している。
 
> [!NOTE]
> **読み出しエラー（readout error）の定義について**
>
> 論文 Section VI より、"readout assignment error" は次のように定義される:
> $$\varepsilon_{\text{readout}} = \frac{P(0|1) + P(1|0)}{2}$$
> これは両方向の条件付きエラー確率の単純平均であり、
> コード内で混同行列に使う P(0|1)、P(1|0) とは別の集計値である。
> 下表の「読み出しエラー率（assignment）」はコードでは使用しない。
 
---
 
### [1] IBM Eagle r3（ibm_sherbrooke）
 
**出典:** IBM Quantum Platform "Compute Resources"
**取得日:** 2026年3月17日
 
> **参考:** arXiv:2410.00916v1, Table VII（p.10）, July 3, 2024 の値との差異については
> 取得日の違いによるキャリブレーション更新の影響と考えられる。
 
**コードで使用する値（すべて全 qubit 中央値、出典: qc_e3_br.csv）:**
 
| パラメータ | 値 | コード内キー | CSV の列名 |
|---|---|---|---|
| T1 | 225.48 μs | `t1` | T1 (us) |
| T2 | 135.23 μs | `t2` | T2 (us) |
| 1Q ゲートエラー率（SX） | 2.594×10⁻⁴ | `depol_1q` ※1 | √x (sx) error |
| 2Q ゲートエラー率（ECR） | 7.463×10⁻³ | `depol_2q` ※1 | ECR error |
| P(meas 0 \| prep 1) | 2.783×10⁻² | `p_meas0_prep1` | Prob meas0 prep1 |
| P(meas 1 \| prep 0) | 2.710×10⁻² | `p_meas1_prep0` | Prob meas1 prep0 |
| 1Q ゲート時間 | 60 ns | `gate_time_1q` | Single-qubit gate length (ns) |
| 2Q ゲート時間（ECR） | 660 ns | `gate_time_2q` | Gate length (ns) |
| 読み出し時間 | 1500 ns | `gate_time_measure` | Readout length (ns) |
 
※1 RB 由来の average gate error を depolarizing エラー近似として使用。詳細は上記 NOTE 参照。
 
---
 
### [2] IBM Heron r1（ibm_torino）
 
**出典:** IBM Quantum Platform "Compute Resources"
**取得日:** 2026年3月17日
 
> **注意:** Heron r1 の Gate length 列および CZ error 列は
> `QUBIT_ID値` が連結した特殊形式（例: `150.00197...` = qubit 15, CZ error 0.00197）
> で格納されているため、正規表現によるパースを適用して中央値を算出している。
 
**コードで使用する値（すべて全 qubit 中央値、出典: qc_h1_to.csv）:**
 
| パラメータ | 値 | コード内キー | CSV の列名 |
|---|---|---|---|
| T1 | 175.85 μs | `t1` | T1 (us) |
| T2 | 134.17 μs | `t2` | T2 (us) |
| 1Q ゲートエラー率（SX） | 2.999×10⁻⁴ | `depol_1q` ※1 | √x (sx) error |
| 2Q ゲートエラー率（CZ） | 2.589×10⁻³ | `depol_2q` ※1 | CZ error |
| P(meas 0 \| prep 1) | 2.197×10⁻² | `p_meas0_prep1` | Prob meas0 prep1 |
| P(meas 1 \| prep 0) | 2.734×10⁻² | `p_meas1_prep0` | Prob meas1 prep0 |
| 1Q ゲート時間 | 32 ns | `gate_time_1q` | Single-qubit gate length (ns) |
| 2Q ゲート時間（CZ） | 68 ns | `gate_time_2q` | Gate length (ns) ※2 |
| 読み出し時間 | 1560 ns | `gate_time_measure` | Readout length (ns) |
 
※2 特殊形式のパースにより抽出。
 
---
 
### [3] IBM Heron r2（ibm_fez）
 
**出典:** IBM Quantum Platform "Compute Resources"
**取得日:** 2026年3月17日
 
**コードで使用する値（すべて全 qubit 中央値、出典: qc_h2_ki.csv）:**
 
| パラメータ | 値 | コード内キー | CSV の列名 |
|---|---|---|---|
| T1 | 225.25 μs | `t1` | T1 (us) |
| T2 | 123.61 μs | `t2` | T2 (us) |
| 1Q ゲートエラー率（SX） | 2.253×10⁻⁴ | `depol_1q` ※1 | √x (sx) error |
| 2Q ゲートエラー率（CZ） | 2.276×10⁻³ | `depol_2q` ※1 | CZ error |
| P(meas 0 \| prep 1) | 1.025×10⁻² | `p_meas0_prep1` | Prob meas0 prep1 |
| P(meas 1 \| prep 0) | 6.348×10⁻³ | `p_meas1_prep0` | Prob meas1 prep0 |
| 1Q ゲート時間 | 32 ns | `gate_time_1q` | Single-qubit gate length (ns) |
| 2Q ゲート時間（CZ） | 68 ns | `gate_time_2q` | Gate length (ns) |
| 読み出し時間 | 2280 ns | `gate_time_measure` | Readout length (ns) |
 
---
 
### [4] IBM Heron r3（ibm_boston）
 
**出典:** IBM Quantum Platform "Compute Resources"
**取得日:** 2026年3月17日
 
> **注意:** T2 (339.30 μs) > T1 (288.17 μs) となっているが、
> 物理的制約 T2 ≦ 2×T1 (= 576.34 μs) は満たしている。
> これはエコー系列（Hahn echo / CPMG）による T2 測定では
> 純粋位相緩和成分が小さく T2 が T1 に近い値を取りうるため生じる。
 
**コードで使用する値（すべて全 qubit 中央値、出典: qc_h3_bo.csv）:**
 
| パラメータ | 値 | コード内キー | CSV の列名 |
|---|---|---|---|
| T1 | 288.17 μs | `t1` | T1 (us) |
| T2 | 339.30 μs | `t2` | T2 (us) |
| 1Q ゲートエラー率（SX） | 1.484×10⁻⁴ | `depol_1q` ※1 | √x (sx) error |
| 2Q ゲートエラー率（CZ） | 1.179×10⁻³ | `depol_2q` ※1 | CZ error |
| P(meas 0 \| prep 1) | 5.371×10⁻³ | `p_meas0_prep1` | Prob meas0 prep1 |
| P(meas 1 \| prep 0) | 6.592×10⁻³ | `p_meas1_prep0` | Prob meas1 prep0 |
| 1Q ゲート時間 | 32 ns | `gate_time_1q` | Single-qubit gate length (ns) |
| 2Q ゲート時間（CZ） | 68 ns | `gate_time_2q` | Gate length (ns) |
| 読み出し時間 | 2200 ns | `gate_time_measure` | Readout length (ns) |
 
---
 
## ノイズモデルの理論的背景
 
### 脱分極エラー（Depolarizing Error）
 
**出典:**
- Nielsen, M. A. & Chuang, I. L., *Quantum Computation and Quantum Information*,
  Cambridge University Press, 2000. **Section 8.3「Examples of quantum noise」**
Eq. (8.103)
 
1量子ビットの脱分極チャネル（各 Pauli エラーの確率を `p/3` と置いた形）:
 
$$\mathcal{E}(\rho) = (1-p)\rho + \frac{p}{3}(X\rho X + Y\rho Y + Z\rho Z)$$
 
- `p`: X・Y・Z エラーが起こる確率の合計（= 3 × 各 Pauli の発生確率）
- `X, Y, Z`: Pauli 演算子
 
> [!NOTE]
> **p の定義について（Nielsen & Chuang 原書との違い）**
>
> Nielsen & Chuang の原書は次の形で定義する:
> $$\mathcal{E}(\rho) = (1 - p_{\text{NC}})\rho + p_{\text{NC}}\frac{I}{2}$$
> ここで $p_{\text{NC}}$ は「状態が最大混合状態 $I/2$ に完全に置き換わる確率」。
>
> 恒等式 $X\rho X + Y\rho Y + Z\rho Z = 2I - \rho$ を使うと、上の式と原書の式は
> $p_{\text{NC}} = \frac{4}{3}p$ という関係で一致する（数学的に等価）。
>
> Qiskit の `depolarizing_error(p, 1)` も同様の慣習を使うので、
> IBM の RB 測定値をそのまま渡すと誤差が生じる可能性がある（近似の範囲内）。
 
---
 
### 熱緩和エラー（Thermal Relaxation Error）
 
**出典:**
- Krantz, P. et al., "A quantum engineer's guide to superconducting qubits",
  *Applied Physics Reviews*, 6, 021318, 2019.
  https://doi.org/10.1063/1.5089550
  **Section III.B.2「Bloch-Redfield model of decoherence」**, Eq. (40)(41)
 
振幅緩和（T1）と位相緩和（T2）の関係（論文 Eq. 41 より）:
 
$$T_2 \leq 2T_1$$
 
> $\Gamma_2 = \Gamma_1/2 + \Gamma_\phi$（Eq. 41）。純粋位相緩和レート $\Gamma_\phi \geq 0$ なので、  
> $1/T_2 \geq 1/(2T_1)$、すなわち $T_2 \leq 2T_1$ が成り立つ。
 
ゲート時間 `t_gate` からエラー率の近似（T1緩和による励起状態確率の指数減衰 $P_{|1\rangle}(t) = e^{-t/T_1}$ より）:
 
$$p_{\text{thermal}} \approx 1 - e^{-t_{\text{gate}}/T_1}$$
 
> [!NOTE]
> 論文ではブロッホ–レッドフィールド方程式により、T1 と T2 の両方を含む密度行列の時間発展が導かれている。  
> 上式はその **T1 成分のみを取り出した近似**であり、コードでは Qiskit の  
> `thermal_relaxation_error(t1, t2, t_gate)` が **T1・T2 の両方を含むノイズチャネル**を計算する。
>
> Qiskit の `thermal_relaxation_error` はすべての引数を **ナノ秒単位**で受け取る。  
> コード内では `_to_ns()` で **秒 → ナノ秒** の変換を統一して行っている。
 
---
 
### 読み出しエラー（Readout Error / Measurement Error）
 
**出典:**
 
- Maciejewski, F. B. et al., *Mitigation of readout noise in near-term quantum devices by classical post-processing based on detector tomography*, Quantum 4, 308 (2020).  
    https://doi.org/10.22331/q-2020-04-24-257
 
量子ビット測定では、準備した状態と観測結果が一致しない **読み出しエラー** が発生する。  
NISQ デバイスではこの誤差を **古典的な非対称ビット反転ノイズ**としてモデル化し、  
測定結果の遷移確率を **混同行列（Confusion Matrix）** または  
**割り当て行列（Assignment Matrix）** として表す。
 
1量子ビットの場合、行列は
 
$$
M =
\begin{pmatrix}
1 - p_{1|0} & p_{1|0} \\
p_{0|1} & 1 - p_{0|1}
\end{pmatrix}
$$
 
で与えられる。
 
- $p_{1|0}$ = P(measuring 1 | prepared 0) = `p_meas1_prep0`  
- $p_{0|1}$ = P(measuring 0 | prepared 1) = `p_meas0_prep1`
 
> [!NOTE]
> 理想的な測定器ではこの行列は単位行列となる。実際の超伝導量子ビットでは  
> 測定中の T1 緩和（$|1\rangle \to |0\rangle$）などの影響により  
> $P(0|1)$ が $P(1|0)$ より大きくなる傾向がある。  
>  
> コードではこの行列を `ReadoutError(confusion_matrix)` として  
> Qiskit の読み出しノイズモデルに直接対応させている。