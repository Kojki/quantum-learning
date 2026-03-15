"""量子回路を実行するシミュレータモジュール。"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel


@dataclass
class SimulationResult:
    """量子シミュレーションの実行結果を保持するデータクラス。"""

    counts: dict[str, int]
    execution_time: float
    shots: int
    n_qubits: int
    depth: int | None = None


class QuantumSimulator:
    """Groverの量子回路を実行するためのシミュレータ。"""

    def __init__(
        self,
        noise_model: NoiseModel | None = None,
        shots: int = 1024,
        basis_gates: list[str] | None = None,
        optimization_level: int = 1,
    ):
        """
        Args:
            noise_model: Qiskitのノイズモデル。Noneの場合は理想的なシミュレータ。
            shots: サンプリング回数。
            basis_gates: トランスパイル時に展開する基本ゲートのリスト。
            optimization_level: Qiskitのトランスパイル最適化レベル (0-3)。
        """
        self.noise_model = noise_model
        self.shots = shots
        self.basis_gates = basis_gates
        self.optimization_level = optimization_level

        # AerSimulator の初期化
        # ノイズがある場合は noise_model をセット
        if self.noise_model is not None:
            self.backend = AerSimulator(noise_model=self.noise_model)
        else:
            self.backend = AerSimulator()

    def run(self, circuit: QuantumCircuit) -> SimulationResult:
        """量子回路をシミュレータで実行し、結果を返す。

        Args:
            circuit: 実行するQuantumCircuit（測定ゲートが含まれていること）

        Returns:
            SimulationResult オブジェクト（カウント結果と実行メタデータを含む）
        """
        start_time = time.perf_counter()

        # 1. 実行対象のバックエンドに合わせて回路をトランスパイル（変換・最適化）
        transpiled_circuit = transpile(
            circuit,
            backend=self.backend,
            basis_gates=self.basis_gates,
            optimization_level=self.optimization_level,
        )

        # 2. シミュレータで実行
        job = self.backend.run(transpiled_circuit, shots=self.shots)
        result = job.result()

        # 3. 結果の抽出
        # 測定結果の辞書を取得（例: {'010': 15, '111': 1009}）
        counts = dict(result.get_counts(transpiled_circuit))

        execution_time = time.perf_counter() - start_time

        return SimulationResult(
            counts=counts,
            execution_time=execution_time,
            shots=self.shots,
            n_qubits=transpiled_circuit.num_qubits,
            depth=transpiled_circuit.depth(),
        )
