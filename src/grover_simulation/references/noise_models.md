# Noise Models — 出典・データまとめ
 
対応コード: `quantum/noise.py`
 
---
 
## デバイスプリセット
 
**主要出典:**
- AbuGhanem, M., "IBM Quantum Computers: Evolution, Performance, and Future Directions",
  arXiv:2410.00916v1, September 17, 2024.
  https://arxiv.org/abs/2410.00916
 
**補助出典（IBM 公式ページ）:**
- IBM Quantum Platform, "コンピュート・リソース"
  https://quantum.ibm.com/services/resources?tab=systems
  取得日: 2026年3月14日
 
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
 
**出典:** arXiv:2410.00916v1, **Table VII**（p.10）
**取得日:** July 3, 2024
 
**該当箇所（Table VII 説明文）:**
> "The processor type is Eagle r3 (version 1.5.3). As of July 3, 2024, the system demonstrates a median ECR error of 7.400×10⁻³, and a median gate time of 533.333 ns."
 
**参考（Figure 4、ibm_sherbrooke, August 1, 2024）:**
> "median ECR error: 7.571×10⁻³, median SX error: 2.411×10⁻⁴, median readout error: 1.350×10⁻², median T1: 262.69 μs, and median T2: 176.67 μs, as of August 1, 2024."
 
*Figure 4 は取得日が異なる（August 1）ため、Table VII（July 3）の値に統一する。*
 
**コードで使用する値（すべて中央値、出典: Table VII）:**
 
| パラメータ | 値 | コード内キー | 論文の列名 |
|---|---|---|---|
| T1 | 269.50 μs | `t1` | T1 Median |
| T2 | 183.99 μs | `t2` | T2 Median |
| 2Q ゲートエラー率（ECR） | 7.400×10⁻³ | `depol_2q` ※1 | ECR error Median（キャプションより）|
| 1Q ゲートエラー率（SX） | 2.16×10⁻⁴ | `depol_1q` ※1 | SX error Median |
| 読み出しエラー率（assignment） | 1.220×10⁻² | — ※2 | Readout assignment error Median |
| P(meas 0 \| prep 1) | 1.340×10⁻² | `p_meas0_prep1` | Prob. meas\|0⟩ prep\|1⟩ Median |
| P(meas 1 \| prep 0) | 9.400×10⁻³ | `p_meas1_prep0` | Prob. meas\|1⟩ prep\|0⟩ Median |
| 2Q ゲート時間（ECR） | 533.333 ns | `gate_time_2q` | Gate time Median（キャプションより）|
| 読み出し時間 | 1244.444 ns | `gate_time_measure` | Readout length |
| 1Q ゲート時間 | **未確認** | `gate_time_1q` | 論文の表に未掲載 |
 
※1 RB 由来の average gate error を depolarizing エラー近似として使用。詳細は上記 NOTE 参照。
※2 assignment error はコードでは使用しない。混同行列には P(0|1)、P(1|0) を直接使う。
 
---
 
### [2] IBM Heron r1（ibm_torino）
 
**出典:** arXiv:2410.00916v1, **Table V**（p.9）
**取得日:** July 3, 2024
 
**該当箇所（Table V 説明文）:**
> "The processor type is Heron r1 (version 1.0.22). As of July 3, 2024, the system demonstrates a median CZ error of 4.769×10⁻³, and a median gate time of 84 ns."
 
**コードで使用する値（すべて中央値、出典: Table V）:**
 
| パラメータ | 値 | コード内キー | 論文の列名 |
|---|---|---|---|
| T1 | 162.91 μs | `t1` | T1 Median |
| T2 | 129.92 μs | `t2` | T2 Median |
| 2Q ゲートエラー率（CZ） | 4.769×10⁻³ | `depol_2q` ※1 | CZ error Median（キャプションより）|
| 1Q ゲートエラー率（SX） | 3.17×10⁻⁴ | `depol_1q` ※1 | SX error Median |
| 読み出しエラー率（assignment） | 2.050×10⁻² | — ※2 | Readout assignment error Median |
| P(meas 0 \| prep 1) | 2.200×10⁻² | `p_meas0_prep1` | Prob. meas\|0⟩ prep\|1⟩ Median |
| P(meas 1 \| prep 0) | 1.540×10⁻² | `p_meas1_prep0` | Prob. meas\|1⟩ prep\|0⟩ Median |
| 2Q ゲート時間（CZ） | 84 ns | `gate_time_2q` | Gate time Median（キャプションより）|
| 読み出し時間 | 1560 ns | `gate_time_measure` | Readout length |
| 1Q ゲート時間 | **未確認** | `gate_time_1q` | 論文の表に未掲載 |
 
---
 
### [3] IBM Heron r2（ibm_fez）
 
**出典:** arXiv:2410.00916v1, **Table IV**（p.9）
**取得日:** July 4, 2024
 
**該当箇所（Table IV 説明文）:**
> "The processor type is Heron r2 (version 1.0.0). As of July 4, 2024, the system demonstrates a median CZ error of 2.848×10⁻³, and a median gate time of 68 ns."
 
**コードで使用する値（すべて中央値、出典: Table IV）:**
 
| パラメータ | 値 | コード内キー | 論文の列名 |
|---|---|---|---|
| T1 | 136.52 μs | `t1` | T1 Median |
| T2 | 78.58 μs | `t2` | T2 Median |
| 2Q ゲートエラー率（CZ） | 2.848×10⁻³ | `depol_2q` ※1 | CZ error Median（キャプションより）|
| 1Q ゲートエラー率（SX） | 2.88×10⁻⁴ | `depol_1q` ※1 | SX error Median |
| 読み出しエラー率（assignment） | 1.630×10⁻² | — ※2 | Readout assignment error Median |
| P(meas 0 \| prep 1) | 2.000×10⁻² | `p_meas0_prep1` | Prob. meas\|0⟩ prep\|1⟩ Median |
| P(meas 1 \| prep 0) | 1.270×10⁻² | `p_meas1_prep0` | Prob. meas\|1⟩ prep\|0⟩ Median |
| 2Q ゲート時間（CZ） | 68 ns | `gate_time_2q` | Gate time Median（キャプションより）|
| 読み出し時間 | 1560 ns | `gate_time_measure` | Readout length |
| 1Q ゲート時間 | **未確認** | `gate_time_1q` | 論文の表に未掲載 |
 
---
 
### [4] IBM Heron r3（ibm_boston / ibm_pittsburgh / ibm_aachen）
 
**出典:** IBM Quantum Platform 公式ページ（2026年3月）
 
**確認済みパラメータのみ:**
 
| QPU名 | 2Q エラー（中央値） | 読み出しエラー（中央値） |
|---|---|---|
| ibm_boston | 1.21×10⁻³ | 5.371×10⁻³ |
| ibm_pittsburgh | 1.52×10⁻³ | 4.272×10⁻³ |
| ibm_aachen | 1.56×10⁻³ | 6.714×10⁻³ |
| **3機の中央値** | **1.52×10⁻³** | **5.371×10⁻³** |
 
> [!NOTE]
> 上表の「読み出しエラー（中央値）」は IBM 公式ページの合計値であり、
> P(0|1)・P(1|0) への非対称分割は出典が確認できていない。
> コードでは `p_meas0_prep1` / `p_meas1_prep0` ともに `None` としている。
 
**未確認パラメータ（コード内では `None`）:**
T1・T2・1Q ゲートエラー率・各ゲート時間・読み出しエラーの非対称分割（P(0|1)・P(1|0)）
 
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

### gate_time_1q の扱いについて

arXiv:2410.00916v1 の各テーブルには 1Q ゲート時間の中央値が掲載されていない。
IBM Quantum Platform 上では量子ビットごとの値を個別に参照できるが、
論文テーブルと同じ形式（全量子ビットの中央値）での値は論文から取得できなかった。

コードでは暫定値として **50 ns** を使用しているが、これは出典のある値ではない。
`gate_time_2q`（Eagle r3：533 ns）と比べて1桁小さいため、
熱緩和エラーへの影響は限定的であるが、正確な値が判明した時点で更新すること。