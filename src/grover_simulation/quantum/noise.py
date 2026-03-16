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
# すべて IBM Quantum Platform キャリブレーションデータより取得（2026年3月）。
#
# 【Eagle r3】
#   ibm_sherbrooke は退役済みのためキャリブレーションデータ未取得。
#   T1/T2/depol/readout は arXiv:2410.00916v1, Table VII（2024年7月）の論文値を使用。
#   gate_time_1q は論文にも未掲載のため暫定値 30ns を使用。
#   ⚠️ gate_time_1q = 30e-9 は暫定値。実測値が判明次第更新すること。
#
# 【Heron r1・r2・r3】
#   IBM Quantum Platform の各 QPU キャリブレーションデータより全 qubit 中央値を算出。
#   T1 < 5 µs の故障 qubit は除外。
#   参考として論文値（arXiv:2410.00916v1）との比較:
#
#   プリセット  | T1 論文→IBM   | T2 論文→IBM   | gate_time_1q 論文→IBM
#   heron_r1  | 163µs→176µs  | 130µs→134µs  | 未掲載→32ns
#   heron_r2  | 137µs→145µs  | 79µs→99µs    | 未掲載→24ns
#   heron_r3  | -    →293µs  | -    →323µs  | 未掲載→32ns
# ---------------------------------------------------------------------------

IBM_EAGLE_R3: dict = {
    # 出典: arXiv:2410.00916v1, Table VII（ibm_sherbrooke, July 3, 2024）
    # ⚠️ ibm_sherbrooke は退役済み。キャリブレーションデータ未取得。
    "t1": 269.50e-6,
    "t2": 183.99e-6,
    "gate_time_1q": 30e-9,  # ⚠️ 暫定値 30ns。論文未掲載・キャリブレーション未取得。実測値が判明次第更新すること。
    "gate_time_2q": 533.333e-9,
    "gate_time_measure": 1244.444e-9,
    "depol_1q": 2.16e-4,
    "depol_2q": 7.400e-3,
    "p_meas0_prep1": 1.340e-2,
    "p_meas1_prep0": 9.400e-3,
}

IBM_HERON_R1: dict = {
    # 出典: ibm_torino キャリブレーションデータ（IBM Quantum Platform、2026年3月取得）
    # 全 qubit 中央値（有効 125/133 qubit、T1 < 5 µs の故障 qubit を除外）
    # 参考: arXiv:2410.00916v1, Table V の論文値は t1=163µs, t2=130µs
    "t1": 1.75850e-4,  # 175.85 µs
    "t2": 1.34170e-4,  # 134.17 µs（T2 ≤ 2×T1 確認済み）
    "gate_time_1q": 3.20000e-8,  # 32 ns（SX ゲート）
    "gate_time_2q": 6.80000e-8,  # 68 ns（CZ ゲート）
    "gate_time_measure": 1.56000e-6,  # 1560 ns
    "depol_1q": 2.74000e-4,  # SX error 全 qubit 中央値
    "depol_2q": 2.49890e-3,  # CZ error 全ペア中央値
    "p_meas0_prep1": 2.19800e-2,  # Prob meas0 prep1 全 qubit 中央値
    "p_meas1_prep0": 2.68600e-2,  # Prob meas1 prep0 全 qubit 中央値
}

IBM_HERON_R2: dict = {
    # 出典: ibm_fez キャリブレーションデータ（IBM Quantum Platform、2026年3月取得）
    # 全 qubit 中央値（有効 139/156 qubit、T1 < 5 µs の故障 qubit を除外）
    # 参考: arXiv:2410.00916v1, Table IV の論文値は t1=137µs, t2=79µs
    "t1": 1.45380e-4,  # 145.38 µs
    "t2": 9.91600e-5,  # 99.16 µs（T2 ≤ 2×T1 確認済み）
    "gate_time_1q": 2.40000e-8,  # 24 ns（SX ゲート）
    "gate_time_2q": 6.80000e-8,  # 68 ns（CZ ゲート）
    "gate_time_measure": 1.56000e-6,  # 1560 ns
    "depol_1q": 2.82000e-4,  # SX error 全 qubit 中央値
    "depol_2q": 2.46750e-3,  # CZ error 全ペア中央値
    "p_meas0_prep1": 1.95300e-2,  # Prob meas0 prep1 全 qubit 中央値
    "p_meas1_prep0": 1.22100e-2,  # Prob meas1 prep0 全 qubit 中央値
}

IBM_HERON_R3: dict = {
    # 出典: ibm_boston (QPU v1.0.4) + ibm_pittsburgh (QPU v1.0.16)
    # キャリブレーションデータ（IBM Quantum Platform、2026年3月取得）
    # 2機の全 qubit 合算中央値（有効 311/312 qubit、T1 < 5 µs の故障 qubit を除外）
    "t1": 2.93450e-4,  # 293.45 µs
    "t2": 3.22890e-4,  # 322.89 µs（T2 ≤ 2×T1 確認済み）
    "gate_time_1q": 3.20000e-8,  # 32 ns（SX ゲート）
    "gate_time_2q": 7.80000e-8,  # 78 ns（boston=68ns, pittsburgh=88ns の中央値）
    "gate_time_measure": 2.39200e-6,  # 2392 ns（boston=2200ns, pittsburgh=2584ns の中央値）
    "depol_1q": 1.67500e-4,  # SX error 全 qubit 中央値
    "depol_2q": 1.31200e-3,  # CZ error 機体中央値
    "p_meas0_prep1": 4.88000e-3,  # Prob meas0 prep1 全 qubit 中央値
    "p_meas1_prep0": 3.42000e-3,  # Prob meas1 prep0 全 qubit 中央値
}

DEVICE_PRESETS: dict[str, dict] = {
    "eagle_r3": IBM_EAGLE_R3,
    "heron_r1": IBM_HERON_R1,
    "heron_r2": IBM_HERON_R2,
    "heron_r3": IBM_HERON_R3,
}

_GATES_1Q = ["u1", "u2", "u3", "id", "h", "x", "y", "z", "s", "sdg", "t", "tdg", "sx"]
_GATES_2Q = ["cx", "cz", "ecr", "swap"]


# ---------------------------------------------------------------------------
# 内部ユーティリティ
# ---------------------------------------------------------------------------


def _to_ns(sec: float) -> float:
    return sec * 1e9


def _rb_to_depol(r: float, n_qubits: int) -> float:
    d = 2**n_qubits
    return d / (d - 1) * r


# ---------------------------------------------------------------------------
# ノイズモデル構築関数
# ---------------------------------------------------------------------------


def build_ideal_model() -> None:
    return None


def build_depolarizing_model(
    depol_1q: float = IBM_EAGLE_R3["depol_1q"],
    depol_2q: float = IBM_EAGLE_R3["depol_2q"],
    gates_1q: list[str] = _GATES_1Q,
    gates_2q: list[str] = _GATES_2Q,
) -> NoiseModel:
    noise_model = NoiseModel()
    p_1q = _rb_to_depol(depol_1q, n_qubits=1)
    p_2q = _rb_to_depol(depol_2q, n_qubits=2)
    noise_model.add_all_qubit_quantum_error(depolarizing_error(p_1q, 1), gates_1q)
    noise_model.add_all_qubit_quantum_error(depolarizing_error(p_2q, 2), gates_2q)
    return noise_model


def build_thermal_model(
    t1: float | None = None,
    t2: float | None = None,
    gate_time_1q: float | None = None,
    gate_time_2q: float | None = None,
    gate_time_measure: float | None = None,
    gates_1q: list[str] = _GATES_1Q,
    gates_2q: list[str] = _GATES_2Q,
) -> NoiseModel:
    _t1 = t1 if t1 is not None else IBM_EAGLE_R3["t1"]
    _t2 = t2 if t2 is not None else IBM_EAGLE_R3["t2"]
    _gt2 = gate_time_2q if gate_time_2q is not None else IBM_EAGLE_R3["gate_time_2q"]
    _gtm = (
        gate_time_measure
        if gate_time_measure is not None
        else IBM_EAGLE_R3["gate_time_measure"]
    )

    if gate_time_1q is None:
        raise ValueError("gate_time_1q を指定してください。（例: gate_time_1q=50e-9）")
    if _t2 > 2 * _t1:
        raise ValueError(
            f"T2 ({_t2 * 1e6:.1f} µs) が 2×T1 ({2 * _t1 * 1e6:.1f} µs) を超えています。"
        )

    noise_model = NoiseModel()
    t1ns, t2ns = _to_ns(_t1), _to_ns(_t2)
    noise_model.add_all_qubit_quantum_error(
        thermal_relaxation_error(t1ns, t2ns, _to_ns(gate_time_1q)), gates_1q
    )
    noise_model.add_all_qubit_quantum_error(
        thermal_relaxation_error(t1ns, t2ns, _to_ns(_gt2)), gates_2q
    )
    noise_model.add_all_qubit_quantum_error(
        thermal_relaxation_error(t1ns, t2ns, _to_ns(_gtm)), ["measure"]
    )
    return noise_model


def build_readout_model(
    p_meas1_prep0: float = IBM_EAGLE_R3["p_meas1_prep0"],
    p_meas0_prep1: float = IBM_EAGLE_R3["p_meas0_prep1"],
) -> NoiseModel:
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
    preset = DEVICE_PRESETS.get(device or "eagle_r3", IBM_EAGLE_R3)

    def resolve(key: str, override):
        val = override if override is not None else preset.get(key)
        if val is None:
            raise ValueError(
                f"パラメータ '{key}' の出典が確認できていません。"
                f"device='{device}' では使用できないため、値を直接渡してください。"
            )
        return val

    p = {
        k: resolve(k, v)
        for k, v in {
            "t1": t1,
            "t2": t2,
            "gate_time_1q": gate_time_1q,
            "gate_time_2q": gate_time_2q,
            "gate_time_measure": gate_time_measure,
            "depol_1q": depol_1q,
            "depol_2q": depol_2q,
            "p_meas1_prep0": p_meas1_prep0,
            "p_meas0_prep1": p_meas0_prep1,
        }.items()
    }

    if p["t2"] > 2 * p["t1"]:
        raise ValueError(
            f"T2 ({p['t2'] * 1e6:.1f} µs) が 2×T1 ({2 * p['t1'] * 1e6:.1f} µs) を超えています。"
        )

    noise_model = NoiseModel()
    t1ns, t2ns = _to_ns(p["t1"]), _to_ns(p["t2"])
    p1 = _rb_to_depol(p["depol_1q"], n_qubits=1)
    p2 = _rb_to_depol(p["depol_2q"], n_qubits=2)

    error_1q = depolarizing_error(p1, 1).compose(
        thermal_relaxation_error(t1ns, t2ns, _to_ns(p["gate_time_1q"]))
    )
    error_2q = depolarizing_error(p2, 2).compose(
        thermal_relaxation_error(t1ns, t2ns, _to_ns(p["gate_time_2q"])).expand(
            thermal_relaxation_error(t1ns, t2ns, _to_ns(p["gate_time_2q"]))
        )
    )
    error_m = thermal_relaxation_error(t1ns, t2ns, _to_ns(p["gate_time_measure"]))

    noise_model.add_all_qubit_quantum_error(error_1q, gates_1q)
    noise_model.add_all_qubit_quantum_error(error_2q, gates_2q)
    noise_model.add_all_qubit_quantum_error(error_m, ["measure"])
    noise_model.add_all_qubit_readout_error(
        ReadoutError(
            [
                [1 - p["p_meas1_prep0"], p["p_meas1_prep0"]],
                [p["p_meas0_prep1"], 1 - p["p_meas0_prep1"]],
            ]
        )
    )
    return noise_model


# ---------------------------------------------------------------------------
# ユーティリティ
# ---------------------------------------------------------------------------


def describe_preset(device: str) -> str:
    preset = DEVICE_PRESETS.get(device)
    if preset is None:
        return f"不明なデバイス: {device!r}。利用可能: {list(DEVICE_PRESETS)}"

    def fmt(val, scale=1.0, unit=""):
        if val is None:
            return "⚠️ 未確認"
        return f"{val * scale:.3g} {unit}".strip()

    return (
        f"=== {device} ===\n"
        f"  T1             : {fmt(preset['t1'],            1e6,  'µs')}\n"
        f"  T2             : {fmt(preset['t2'],            1e6,  'µs')}\n"
        f"  gate_time_1q   : {fmt(preset['gate_time_1q'],  1e9,  'ns')}\n"
        f"  gate_time_2q   : {fmt(preset['gate_time_2q'],  1e9,  'ns')}\n"
        f"  1Q gate error  : {fmt(preset['depol_1q'])}\n"
        f"  2Q gate error  : {fmt(preset['depol_2q'])}\n"
        f"  Readout P(1|0) : {fmt(preset['p_meas1_prep0'])}\n"
        f"  Readout P(0|1) : {fmt(preset['p_meas0_prep1'])}\n"
    )
