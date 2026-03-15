# 📚 量子計算の基礎：15のステップ学習ガイド
(Quantum Computing Fundamentals: A 15-Step Guide)

量子コンピュータの学習において、多くの人が「数式」と「物理」の壁に直面します。このガイドは、全くのゼロから始まり、ハミルトニアンやテンソル積といった高度な概念をなだらかに繋ぎ、最終的には実際のIBM Quantumハードウェアでの実行を見据えるレベルまで皆さんを導きます。

---

## 🧭 学習ロードマップ

### 【第1章：全くのゼロからの量子ビット】
直感的なイメージと、その数学的表現の入り口を学びます。
- [01. 量子ビットとは何か？（重ね合わせと観測問題）](./01_what_is_a_qubit.md)
- [02. ブラケット記法とベクトル表現（確率振幅）](./02_dirac_notation_and_vectors.md)
- [03. ブロッホ球での視覚化（位相の概念）](./03_bloch_sphere.md)

### 【第2章：量子ゲートと線形代数の基礎】
行列計算を使って、量子状態を「操作」する方法を学びます。
- [04. 1量子ビットゲート（X, Y, Z, H）](./04_single_qubit_gates.md)
- [05. ユニタリ行列による操作（確率の保存）](./05_unitary_matrices.md)
- [06. 複数ビットとテンソル積（次元の爆発）](./06_multiple_qubits_and_tensor_products.md)
- [07. 量子もつれとCNOTゲート（ベル状態）](./07_entanglement_and_cnot.md)

### 【第3章：測定と物理演算子（⚠️最大の壁）】
独学者が最もつまずきやすい「観測量」と「ハミルトニアン」の壁を越えます。
- [08. 観測量とエルミート行列](./08_observables_and_hermitian_matrices.md)
- [09. 期待値の計算と意味 ($\langle \psi | O | \psi \rangle$)](./09_expectation_values.md)
- [10. ハミルトニアンの完全理解（エネルギーパズル）](./10_understanding_hamiltonians.md)

### 【第4章：物理現象からアルゴリズムへ】
物理法則をアルゴリズム（QAOAやVQC）に変換する数学的テクニックです。
- [11. シュレーディンガー方程式と時間発展](./11_schrodinger_time_evolution.md)
- [12. トロッター分解と断熱量子計算 (AQC)](./12_trotterization_and_aqc.md)
- [13. Ansatzとハイブリッド計算ループ（VQC / QAOA）](./13_hybrid_quantum_classical_loop.md)

### 【第5章：現実世界の量子コンピュータへ】
シミュレータを離れ、IBM Quantum Platformなどの実機を使うための知識です。
- [14. ハードウェアノイズとデコヒーレンス（NISQの現実）](./14_hardware_noise_and_decoherence.md)
- [15. 誤り緩和 (EM) と誤り訂正 (QEC) への招待](./15_intro_to_error_mitigation_and_correction.md)

---
**準備はいいですか？ [Step 01: 量子ビットとは何か？](./01_what_is_a_qubit.md) から始めましょう！**
