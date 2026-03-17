from __future__ import annotations

from typing import Literal

from qiskit_aer.noise import (
    NoiseModel,
    depolarizing_error,
    thermal_relaxation_error,
    ReadoutError,
)

# ---------------------------------------------------------------------------
# デバイスプリセット（実測値）
# ---------------------------------------------------------------------------
# 各パラメータの出典は references/noise_models.md を参照。
# コメント内の [REF: #番号] は noise_models.md のセクション番号に対応。
#
# 【ゲートエラー率（depol_1q / depol_2q）について】
# SX / ECR / CZ error は RB（ランダム化ベンチマーク）由来の average gate error。
# 純粋な depolarizing エラーではなく全エラーの合計を depolarizing で近似している。
# 詳細は references/noise_models.md の NOTE 参照。
#
# 【読み出しエラー（p_meas0_prep1 / p_meas1_prep0）について】
# 論文が報告する「readout assignment error」は (P(0|1)+P(1|0))/2 の平均値であり、
# 混同行列に使う条件付きエラー P(0|1)・P(1|0) とは別の指標。
# コードでは混同行列用の条件付きエラー確率を直接使う。

IBM_EAGLE_R3: dict = {
    # 出典: IBM Quantum Platform キャリブレーションデータ（ibm_sherbrooke）
    # 取得日: 2026年3月（CSV: qc_e3_br.csv）, 全 qubit の中央値
    # 熱緩和 [REF: noise_models.md #1]
    "t1": 225.48e-6,  # 中央値 225.48 μs
    "t2": 135.23e-6,  # 中央値 135.23 μs
    # ゲート時間 [REF: noise_models.md #1]
    "gate_time_1q": 60e-9,  # 中央値 60 ns（Single-qubit gate length 列）
    "gate_time_2q": 660e-9,  # 中央値 660 ns（ECR gate）
    "gate_time_measure": 1500e-9,  # 中央値 1500 ns（Readout length）
    # RB 由来のゲートエラー率（depolarizing 近似）[REF: noise_models.md #1]
    "depol_1q": 2.594e-4,  # SX error 中央値
    "depol_2q": 7.463e-3,  # ECR error 中央値
    # 条件付き読み出しエラー確率 [REF: noise_models.md #1]
    "p_meas0_prep1": 2.783e-2,  # Prob. meas|0⟩ prep|1⟩ 中央値
    "p_meas1_prep0": 2.710e-2,  # Prob. meas|1⟩ prep|0⟩ 中央値
}

IBM_HERON_R1: dict = {
    # 出典: IBM Quantum Platform キャリブレーションデータ（ibm_torino）
    # 取得日: 2026年3月（CSV: qc_h1_to.csv）, 全 qubit の中央値
    # 熱緩和 [REF: noise_models.md #2]
    "t1": 175.85e-6,  # 中央値 175.85 μs
    "t2": 134.17e-6,  # 中央値 134.17 μs
    # ゲート時間 [REF: noise_models.md #2]
    "gate_time_1q": 32e-9,  # 中央値 32 ns（Single-qubit gate length 列）
    "gate_time_2q": 68e-9,  # 中央値 68 ns（CZ gate）
    "gate_time_measure": 1560e-9,  # 中央値 1560 ns（Readout length）
    # RB 由来のゲートエラー率（depolarizing 近似）[REF: noise_models.md #2]
    "depol_1q": 2.999e-4,  # SX error 中央値
    "depol_2q": 2.589e-3,  # CZ error 中央値
    # 条件付き読み出しエラー確率 [REF: noise_models.md #2]
    "p_meas0_prep1": 2.197e-2,  # Prob. meas|0⟩ prep|1⟩ 中央値
    "p_meas1_prep0": 2.734e-2,  # Prob. meas|1⟩ prep|0⟩ 中央値
}

IBM_HERON_R2: dict = {
    # 出典: IBM Quantum Platform キャリブレーションデータ（ibm_fez）
    # 取得日: 2026年3月（CSV: qc_h2_ki.csv）, 全 qubit の中央値
    # 熱緩和 [REF: noise_models.md #3]
    "t1": 225.25e-6,  # 中央値 225.25 μs
    "t2": 123.61e-6,  # 中央値 123.61 μs
    # ゲート時間 [REF: noise_models.md #3]
    "gate_time_1q": 32e-9,  # 中央値 32 ns（Single-qubit gate length 列）
    "gate_time_2q": 68e-9,  # 中央値 68 ns（CZ gate）
    "gate_time_measure": 2280e-9,  # 中央値 2280 ns（Readout length）
    # RB 由来のゲートエラー率（depolarizing 近似）[REF: noise_models.md #3]
    "depol_1q": 2.253e-4,  # SX error 中央値
    "depol_2q": 2.276e-3,  # CZ error 中央値
    # 条件付き読み出しエラー確率 [REF: noise_models.md #3]
    "p_meas0_prep1": 1.025e-2,  # Prob. meas|0⟩ prep|1⟩ 中央値
    "p_meas1_prep0": 6.348e-3,  # Prob. meas|1⟩ prep|0⟩ 中央値
}

IBM_HERON_R3: dict = {
    # 出典: IBM Quantum Platform キャリブレーションデータ（ibm_boston）
    # 取得日: 2026年3月（CSV: qc_h3_bo.csv）, 全 qubit の中央値
    # 熱緩和 [REF: noise_models.md #4]
    "t1": 288.17e-6,  # 中央値 288.17 μs
    "t2": 339.30e-6,  # 中央値 339.30 μs  ※ T2 > T1 だが T2 <= 2*T1 は満たす
    # ゲート時間 [REF: noise_models.md #4]
    "gate_time_1q": 32e-9,  # 中央値 32 ns（Single-qubit gate length 列）
    "gate_time_2q": 68e-9,  # 中央値 68 ns（CZ gate）
    "gate_time_measure": 2200e-9,  # 中央値 2200 ns（Readout length）
    # RB 由来のゲートエラー率（depolarizing 近似）[REF: noise_models.md #4]
    "depol_1q": 1.484e-4,  # SX error 中央値
    "depol_2q": 1.179e-3,  # CZ error 中央値
    # 条件付き読み出しエラー確率 [REF: noise_models.md #4]
    "p_meas0_prep1": 5.371e-3,  # Prob. meas|0⟩ prep|1⟩ 中央値
    "p_meas1_prep0": 6.592e-3,  # Prob. meas|1⟩ prep|0⟩ 中央値
}

DEVICE_PRESETS: dict[str, dict] = {
    "eagle_r3": IBM_EAGLE_R3,
    "heron_r1": IBM_HERON_R1,
    "heron_r2": IBM_HERON_R2,
    "heron_r3": IBM_HERON_R3,
}

# Qiskit が認識する標準ゲート名
_GATES_1Q = ["u1", "u2", "u3", "id", "h", "x", "y", "z", "s", "sdg", "t", "tdg", "sx"]
_GATES_2Q = ["cx", "cz", "ecr", "swap"]


# ---------------------------------------------------------------------------
# 内部ユーティリティ
# ---------------------------------------------------------------------------


def _to_ns(sec: float) -> float:
    """秒をナノ秒に変換する。

    `thermal_relaxation_error` はナノ秒単位で引数を受け取るため、
    各ビルド関数内で変換を統一するために使う。

    Args:
        sec: 時間（秒）。

    Returns:
        時間（ナノ秒）。
    """
    return sec * 1e9


def _rb_to_depol(r: float, n_qubits: int) -> float:
    """ランダム化ベンチマーク（RB）の平均ゲートエラー率 r を
    depolarizing channel のパラメータ p に変換する。

    変換式: p = d / (d - 1) * r   (d = 2^n_qubits)

    出典: Magesan, E. et al., PRL 106, 180504 (2011).
            または Nielsen & Chuang, Section 9.3.

    Args:
        r: RB による average gate error rate (= 1 - F_avg).
        n_qubits: ゲートの作用ビット数（1 または 2）。

    Returns:
        depolarizing channel のパラメータ p。
    """
    d = 2**n_qubits
    return d / (d - 1) * r


# ---------------------------------------------------------------------------
# ノイズモデル構築関数
# ---------------------------------------------------------------------------


def build_ideal_model() -> None:
    """ノイズなし（理想）シミュレーター用。NoiseModel は不要なので None を返す。"""
    return None


def build_depolarizing_model(
    depol_1q: float = IBM_EAGLE_R3["depol_1q"],
    depol_2q: float = IBM_EAGLE_R3["depol_2q"],
    gates_1q: list[str] = _GATES_1Q,
    gates_2q: list[str] = _GATES_2Q,
) -> NoiseModel:
    """RB 由来のゲートエラー率から脱分極ノイズモデルを構築する。

    引数には論文記載の RB 平均ゲートエラー率 r を渡す。
    内部で p = d/(d-1) * r に変換して `depolarizing_error()` へ渡す。

    理論的背景: references/noise_models.md「脱分極エラー」参照。

    Args:
        depol_1q: 1量子ビットゲートの RB 平均エラー率 r（デフォルト: Eagle r3 実測値）。
        depol_2q: 2量子ビットゲートの RB 平均エラー率 r（デフォルト: Eagle r3 実測値）。
        gates_1q: エラーを適用する 1Q ゲート名のリスト（デフォルト: _GATES_1Q）。
        gates_2q: エラーを適用する 2Q ゲート名のリスト（デフォルト: _GATES_2Q）。
    """
    noise_model = NoiseModel()

    p_1q = _rb_to_depol(depol_1q, n_qubits=1)
    p_2q = _rb_to_depol(depol_2q, n_qubits=2)

    error_1q = depolarizing_error(p_1q, 1)
    error_2q = depolarizing_error(p_2q, 2)

    noise_model.add_all_qubit_quantum_error(error_1q, gates_1q)
    noise_model.add_all_qubit_quantum_error(error_2q, gates_2q)

    return noise_model


def build_thermal_model(
    t1: float = IBM_EAGLE_R3["t1"],
    t2: float = IBM_EAGLE_R3["t2"],
    gate_time_1q: float = IBM_EAGLE_R3["gate_time_1q"],
    gate_time_2q: float = IBM_EAGLE_R3["gate_time_2q"],
    gate_time_measure: float = IBM_EAGLE_R3["gate_time_measure"],
    gates_1q: list[str] = _GATES_1Q,
    gates_2q: list[str] = _GATES_2Q,
) -> NoiseModel:
    """熱緩和エラー（T1・T2）のみのノイズモデルを構築する。

    理論的背景: references/noise_models.md「熱緩和エラー」参照。

    Args:
        t1: 振幅緩和時間（秒）。
        t2: 位相緩和時間（秒）。T2 <= 2*T1 の制約あり。
        gate_time_1q: 1量子ビットゲートの実行時間（秒）。
        gate_time_2q: 2量子ビットゲートの実行時間（秒）。
        gate_time_measure: 測定操作の実行時間（秒）。
        gates_1q: エラーを適用する 1Q ゲート名のリスト（デフォルト: _GATES_1Q）。
        gates_2q: エラーを適用する 2Q ゲート名のリスト（デフォルト: _GATES_2Q）。
    """
    if t2 > 2 * t1:
        raise ValueError(
            f"T2 ({t2 * 1e6:.1f} μs) が 2*T1 ({2 * t1 * 1e6:.1f} μs) を超えています。"
        )

    noise_model = NoiseModel()

    t1_ns = _to_ns(t1)
    t2_ns = _to_ns(t2)
    gate_time_1q_ns = _to_ns(gate_time_1q)
    gate_time_2q_ns = _to_ns(gate_time_2q)
    gate_time_meas_ns = _to_ns(gate_time_measure)

    error_1q = thermal_relaxation_error(t1_ns, t2_ns, gate_time_1q_ns)
    # 2Q ゲートには各 qubit 独立の熱緩和エラーを tensor 積で合成する
    error_2q = thermal_relaxation_error(t1_ns, t2_ns, gate_time_2q_ns).expand(
        thermal_relaxation_error(t1_ns, t2_ns, gate_time_2q_ns)
    )
    error_measure = thermal_relaxation_error(t1_ns, t2_ns, gate_time_meas_ns)

    noise_model.add_all_qubit_quantum_error(error_1q, gates_1q)
    noise_model.add_all_qubit_quantum_error(error_2q, gates_2q)
    noise_model.add_all_qubit_quantum_error(error_measure, ["measure"])

    return noise_model


def build_readout_model(
    p_meas1_prep0: float = IBM_EAGLE_R3["p_meas1_prep0"],
    p_meas0_prep1: float = IBM_EAGLE_R3["p_meas0_prep1"],
) -> NoiseModel:
    """読み出しエラーのみのノイズモデルを構築する。

    理論的背景: references/noise_models.md「読み出しエラー」参照。

    混同行列:
        [[1 - p_meas1_prep0,     p_meas0_prep1    ],
         [    p_meas1_prep0,  1 - p_meas0_prep1   ]]

    Args:
        p_meas1_prep0: |0⟩ を準備したのに '1' と読まれる確率。
        p_meas0_prep1: |1⟩ を準備したのに '0' と読まれる確率。
    """
    noise_model = NoiseModel()

    confusion_matrix = [
        [1 - p_meas1_prep0, p_meas1_prep0],
        [p_meas0_prep1, 1 - p_meas0_prep1],
    ]
    noise_model.add_all_qubit_readout_error(ReadoutError(confusion_matrix))

    return noise_model


def build_combined_model(
    device: Literal["eagle_r3", "heron_r1", "heron_r2", "heron_r3"] | None = None,
    t1: float | None = None,
    t2: float | None = None,
    gate_time_1q: float | None = None,
    gate_time_2q: float | None = None,
    gate_time_measure: float | None = None,
    depol_1q: float | None = None,
    depol_2q: float | None = None,
    p_meas1_prep0: float | None = None,
    p_meas0_prep1: float | None = None,
    gates_1q: list[str] = _GATES_1Q,
    gates_2q: list[str] = _GATES_2Q,
) -> NoiseModel:
    """脱分極・熱緩和・読み出しエラーを組み合わせた実機相当のノイズモデルを構築する。

    device プリセットを指定するとデフォルト値が実機実測値になる。
    個別パラメータを渡すとプリセット値を上書きできる。

    Args:
        device: プリセット名 ('eagle_r3' | 'heron_r1' | 'heron_r2' | 'heron_r3')。
                None の場合は Eagle r3 をデフォルトとして使う。
        t1: 振幅緩和時間（秒）。省略時はプリセット値を使う。
        t2: 位相緩和時間（秒）。省略時はプリセット値を使う。
        gate_time_1q: 1量子ビットゲートの実行時間（秒）。省略時はプリセット値を使う。
        gate_time_2q: 2量子ビットゲートの実行時間（秒）。省略時はプリセット値を使う。
        gate_time_measure: 測定操作の実行時間（秒）。省略時はプリセット値を使う。
        depol_1q: 1量子ビットゲートの RB 平均エラー率。省略時はプリセット値を使う。
        depol_2q: 2量子ビットゲートの RB 平均エラー率。省略時はプリセット値を使う。
        p_meas1_prep0: |0⟩ を準備したのに '1' と読まれる確率。省略時はプリセット値を使う。
        p_meas0_prep1: |1⟩ を準備したのに '0' と読まれる確率。省略時はプリセット値を使う。
        gates_1q: エラーを適用する 1Q ゲート名のリスト（デフォルト: _GATES_1Q）。
        gates_2q: エラーを適用する 2Q ゲート名のリスト（デフォルト: _GATES_2Q）。

    Raises:
        ValueError: プリセットに None が含まれていて、個別指定もない場合。
        ValueError: T2 > 2*T1 の場合。
    """
    preset = DEVICE_PRESETS.get(device or "eagle_r3", IBM_EAGLE_R3)

    def resolve(key: str, override):
        val = override if override is not None else preset.get(key)
        if val is None:
            raise ValueError(
                f"パラメータ '{key}' の値が未設定です。"
                f"device='{device}' では使用できないため、値を直接渡してください。"
            )
        return val

    p = {
        "t1": resolve("t1", t1),
        "t2": resolve("t2", t2),
        "gate_time_1q": resolve("gate_time_1q", gate_time_1q),
        "gate_time_2q": resolve("gate_time_2q", gate_time_2q),
        "gate_time_measure": resolve("gate_time_measure", gate_time_measure),
        "depol_1q": resolve("depol_1q", depol_1q),
        "depol_2q": resolve("depol_2q", depol_2q),
        "p_meas1_prep0": resolve("p_meas1_prep0", p_meas1_prep0),
        "p_meas0_prep1": resolve("p_meas0_prep1", p_meas0_prep1),
    }

    if p["t2"] > 2 * p["t1"]:
        raise ValueError(
            f"T2 ({p['t2'] * 1e6:.1f} μs) が 2*T1 ({2 * p['t1'] * 1e6:.1f} μs) を超えています。"
        )

    noise_model = NoiseModel()

    t1_ns = _to_ns(p["t1"])
    t2_ns = _to_ns(p["t2"])
    gate_time_1q_ns = _to_ns(p["gate_time_1q"])
    gate_time_2q_ns = _to_ns(p["gate_time_2q"])
    gate_time_meas_ns = _to_ns(p["gate_time_measure"])

    p_depol_1q = _rb_to_depol(p["depol_1q"], n_qubits=1)
    p_depol_2q = _rb_to_depol(p["depol_2q"], n_qubits=2)

    error_1q = depolarizing_error(p_depol_1q, 1).compose(
        thermal_relaxation_error(t1_ns, t2_ns, gate_time_1q_ns)
    )
    error_2q = depolarizing_error(p_depol_2q, 2).compose(
        thermal_relaxation_error(t1_ns, t2_ns, gate_time_2q_ns).expand(
            thermal_relaxation_error(t1_ns, t2_ns, gate_time_2q_ns)
        )
    )
    error_measure = thermal_relaxation_error(t1_ns, t2_ns, gate_time_meas_ns)

    noise_model.add_all_qubit_quantum_error(error_1q, gates_1q)
    noise_model.add_all_qubit_quantum_error(error_2q, gates_2q)
    noise_model.add_all_qubit_quantum_error(error_measure, ["measure"])

    confusion_matrix = [
        [1 - p["p_meas1_prep0"], p["p_meas1_prep0"]],
        [p["p_meas0_prep1"], 1 - p["p_meas0_prep1"]],
    ]
    noise_model.add_all_qubit_readout_error(ReadoutError(confusion_matrix))

    return noise_model


# ---------------------------------------------------------------------------
# ユーティリティ
# ---------------------------------------------------------------------------


def describe_preset(device: str) -> str:
    """指定したプリセットのパラメータを一覧表示する。

    Args:
        device: プリセット名。利用可能な値は DEVICE_PRESETS のキーを参照。

    Returns:
        パラメータ一覧の文字列。
    """
    preset = DEVICE_PRESETS.get(device)
    if preset is None:
        return f"不明なデバイス: {device!r}。利用可能: {list(DEVICE_PRESETS)}"

    def fmt(val: float | None, scale: float = 1.0, unit: str = "") -> str:
        if val is None:
            return "未設定"
        formatted = f"{val * scale:.3g}"
        return f"{formatted} {unit}".strip() if unit else formatted

    return (
        f"=== {device} ===\n"
        f"  T1               : {fmt(preset['t1'],            1e6,  'μs')}\n"
        f"  T2               : {fmt(preset['t2'],            1e6,  'μs')}\n"
        f"  gate_time_1q     : {fmt(preset['gate_time_1q'],  1e9,  'ns')}\n"
        f"  gate_time_2q     : {fmt(preset['gate_time_2q'],  1e9,  'ns')}\n"
        f"  gate_time_measure: {fmt(preset['gate_time_measure'], 1e9, 'ns')}\n"
        f"  1Q gate error    : {fmt(preset['depol_1q'])}\n"
        f"  2Q gate error    : {fmt(preset['depol_2q'])}\n"
        f"  Readout P(1|0)   : {fmt(preset['p_meas1_prep0'])}\n"
        f"  Readout P(0|1)   : {fmt(preset['p_meas0_prep1'])}\n"
    )
