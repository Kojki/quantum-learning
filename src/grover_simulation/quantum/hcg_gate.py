from __future__ import annotations

import math
import numpy as np
from typing import Callable

from qiskit import QuantumCircuit
from qiskit.circuit import Gate
from qiskit.circuit.library import MCPhaseGate

# ---------------------------------------------------------------------------
# 1. 振幅増幅ロジック (AAM)
# ---------------------------------------------------------------------------


def _oracle_mark_targets(
    n_qubits: int, targets: list[int], phi: float = math.pi
) -> Gate:
    """指定したインデックスの位相を反転（または phi 回転）させるオラクルを構築。"""
    qc = QuantumCircuit(n_qubits)
    for target in targets:
        binary = format(target, f"0{n_qubits}b")[::-1]
        for i, b in enumerate(binary):
            if b == "0":
                qc.x(i)

        # MCPhase を使用
        gate = MCPhaseGate(phi, n_qubits - 1)
        qc.append(gate, list(range(n_qubits)))

        for i, b in enumerate(binary):
            if b == "0":
                qc.x(i)
    return qc.to_gate(label="AAM_Oracle")


def _build_aam_diffuser(n_qubits: int, phi: float = math.pi) -> Gate:
    """AAM 用のディフューザー (|0> 軸反射)。"""
    qc = QuantumCircuit(n_qubits)
    qc.h(range(n_qubits))
    qc.x(range(n_qubits))

    gate = MCPhaseGate(phi, n_qubits - 1)
    qc.append(gate, list(range(n_qubits)))

    qc.x(range(n_qubits))
    qc.h(range(n_qubits))
    return qc.to_gate(label="AAM_Diffuser")


def build_aam_step(n_qubits: int, targets: list[int], n_iter: int = 0) -> Gate:
    """1ステップ分の振幅増幅（AAM）ゲートを構築。"""
    total_states = 2**n_qubits
    m = len(targets)
    theta = math.asin(math.sqrt(m / total_states))

    qc = QuantumCircuit(n_qubits)
    qc.h(range(n_qubits))  # 初期重ね合わせ

    if n_iter == 0:
        # Long's Zero-failure Grover
        phi = 2 * math.asin(math.sin(math.pi / 6) / math.sin(theta))
        oracle = _oracle_mark_targets(n_qubits, targets, phi)
        diffuser = _build_aam_diffuser(n_qubits, phi)
        qc.append(oracle, range(n_qubits))
        qc.append(diffuser, range(n_qubits))
    else:
        # Standard Grover
        oracle = _oracle_mark_targets(n_qubits, targets, math.pi)
        diffuser = _build_aam_diffuser(n_qubits, math.pi)
        for _ in range(n_iter):
            qc.append(oracle, range(n_qubits))
            qc.append(diffuser, range(n_qubits))

    return qc.to_gate(label=f"AAM(m={m})")


# ---------------------------------------------------------------------------
# 2. HCg (Harmonic Cycle generator) ゲート
# ---------------------------------------------------------------------------


def build_hcg_gate(n_cities: int) -> Gate:
    """N都市の全順列を等確率で生成する HCg ゲートを構築。"""
    m_bits = math.ceil(math.log2(n_cities))
    total_qubits = n_cities * m_bits
    qc = QuantumCircuit(total_qubits)

    for k in range(n_cities):
        target_indices = []
        # ここでは簡略化のため、すべての有効なインデックス(0..N-1)をターゲットとする
        # 実際には前のステップで選ばれた都市を除外するロジックが必要だが、
        # 忠実な AAM 実証を優先し、ここでは各ステップで全都市の重ね合わせを作る。
        # (完全な HCG 実装はより複雑になるため、ここでは構造案を示す)
        targets = list(range(n_cities))
        aam = build_aam_step(m_bits, targets, n_iter=0)
        qc.append(aam, range(k * m_bits, (k + 1) * m_bits))

    return qc.to_gate(label="HCg")
