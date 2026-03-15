from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING, Callable

from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Gate
from qiskit_aer import AerSimulator

from quantum.oracle import build_oracle, make_condition_from_cost

if TYPE_CHECKING:
    from problems.base import OptimizationProblem


# ---------------------------------------------------------------------------
# 1. Diffusion 演算子
# ---------------------------------------------------------------------------


def build_diffusion(n_qubits: int) -> Gate:
    """Grover の Diffusion 演算子（振幅反転）を構築してゲートとして返す。

    |s⟩ = H^n|0⟩ を軸とした反射:  2|s⟩⟨s| - I

    回路の構造:
        H^n → X^n → H on q[n-1] → mcx → H on q[n-1] → X^n → H^n

    ancilla は含まない（入力レジスタの n_qubits 本のみ）。
    """
    circuit = QuantumCircuit(n_qubits)

    circuit.h(range(n_qubits))
    circuit.x(range(n_qubits))

    # 最後の qubit を標的にした multi-controlled Z（H で挟んで CX → CZ に変換）
    circuit.h(n_qubits - 1)
    circuit.mcx(list(range(n_qubits - 1)), n_qubits - 1)
    circuit.h(n_qubits - 1)

    circuit.x(range(n_qubits))
    circuit.h(range(n_qubits))

    return circuit.to_gate(label="Diffusion")


# ---------------------------------------------------------------------------
# 2. 最適反復回数
# ---------------------------------------------------------------------------


def optimal_iterations(n_qubits: int, n_targets: int) -> int:
    """Grover の最適反復回数を返す。

    最適回数 = round( π/4 × √(N/M) )
        N = 2^n_qubits（探索空間のサイズ）
        M = n_targets（正解の数）

    ターゲットが 0 件または探索空間以上の場合は 1 を返す（安全策）。
    """
    n_space = 2**n_qubits
    if n_targets <= 0 or n_targets >= n_space:
        return 1
    return max(1, round(math.pi / 4 * math.sqrt(n_space / n_targets)))


# ---------------------------------------------------------------------------
# 3. 回路全体の組み立て
# ---------------------------------------------------------------------------


def build_grover_circuit(
    n_qubits: int,
    oracle: Gate,
    n_iterations: int,
) -> QuantumCircuit:
    """Oracle と Diffusion を組み合わせた Grover 回路を構築する。

    量子ビット構成:
        q[0..n_qubits-1] : 入力レジスタ
        q[n_qubits]      : ancilla（oracle が使用）

    Args:
        n_qubits: 入力レジスタのビット数
        oracle: build_oracle() が返すゲート（n_qubits + 1 本）
        n_iterations: Grover 反復回数

    Returns:
        測定込みの QuantumCircuit
    """
    # ancilla 込みで初期化
    circuit = QuantumCircuit(n_qubits + 1, n_qubits)

    # 入力レジスタを均一重ね合わせ状態に
    circuit.h(range(n_qubits))

    diffusion = build_diffusion(n_qubits)

    for _ in range(n_iterations):
        # Oracle：入力レジスタ + ancilla
        circuit.append(oracle, list(range(n_qubits + 1)))
        # Diffusion：入力レジスタのみ
        circuit.append(diffusion, list(range(n_qubits)))

    # 入力レジスタのみ測定
    circuit.measure(range(n_qubits), range(n_qubits))

    return circuit


# ---------------------------------------------------------------------------
# 4. 追加 ancilla を使った回路（extra モード）
# ---------------------------------------------------------------------------


def build_grover_circuit_extra_ancilla(
    n_qubits: int,
    oracle: Gate,
    n_iterations: int,
) -> QuantumCircuit:
    """追加 ancilla を使って mcx を分解した、回路深さの浅い Grover 回路を構築する。

    通常の mcx（multi-controlled X）は制御 qubit が増えると回路が深くなる。
    追加の ancilla を「作業台」として使うことで、大きな mcx を
    小さな Toffoli（CCX）ゲートの連鎖に分解できる。

    追加 ancilla の数 = max(0, n_qubits - 2)
        制御 qubit が 2 本以下なら追加不要（CCX で直接表現できるため）

    量子ビット構成:
        q[0..n_qubits-1]                     : 入力レジスタ
        q[n_qubits]                           : oracle 用 ancilla（位相キックバック）
        q[n_qubits+1 .. n_qubits+n_extra]     : mcx 分解用 ancilla

    Args:
        n_qubits: 入力レジスタのビット数
        oracle: build_oracle() が返すゲート（n_qubits + 1 本）
        n_iterations: Grover 反復回数

    Returns:
        測定込みの QuantumCircuit
    """
    n_extra = max(0, n_qubits - 2)
    n_total = n_qubits + 1 + n_extra  # 入力 + oracle ancilla + extra ancilla

    circuit = QuantumCircuit(n_total, n_qubits)

    # 入力レジスタを均一重ね合わせ状態に
    circuit.h(range(n_qubits))

    diffusion = build_diffusion(n_qubits)

    for _ in range(n_iterations):
        # Oracle は入力レジスタ + oracle ancilla のみ使用
        circuit.append(oracle, list(range(n_qubits + 1)))

        # Diffusion 内の mcx を extra ancilla を使って分解
        # Qiskit の mcx は ancilla_qubits 引数で追加 ancilla を受け取れる
        if n_extra > 0:
            extra_qubits = list(range(n_qubits + 1, n_total))
            _append_diffusion_with_ancilla(circuit, n_qubits, extra_qubits)
        else:
            circuit.append(diffusion, list(range(n_qubits)))

    circuit.measure(range(n_qubits), range(n_qubits))
    return circuit


def _append_diffusion_with_ancilla(
    circuit: QuantumCircuit,
    n_qubits: int,
    extra_qubits: list[int],
) -> None:
    """extra ancilla を使って Diffusion を回路に直接追記する。

    build_diffusion と同じ構造だが、mcx に ancilla_qubits を渡して
    ゲートを浅く分解する。ゲート化せず直接 append することで
    Qiskit の transpile が ancilla を認識できるようにしている。
    """
    qubits = list(range(n_qubits))
    target = n_qubits - 1
    controls = list(range(n_qubits - 1))

    circuit.h(qubits)
    circuit.x(qubits)
    circuit.h(target)
    circuit.mcx(controls, target, ancilla_qubits=extra_qubits)
    circuit.h(target)
    circuit.x(qubits)
    circuit.h(qubits)


# ---------------------------------------------------------------------------
# 5. エントリーポイント
# ---------------------------------------------------------------------------


def solve(
    problem: "OptimizationProblem",
    shots: int = 1024,
    condition: Callable[[str], bool] | None = None,
    threshold: float | None = None,
    top_k: int = 5,
    ancilla_mode: str = "single",
) -> dict:
    """Grover のアルゴリズムで最適解を探索する。

    brute_force.solve() と同じ dict 形式で返すことで
    benchmark/runner.py での比較を容易にする。

    Args:
        problem: OptimizationProblem のインスタンス
        shots: シミュレーションのショット数
        condition: 外部から渡す condition（省略時は threshold から自動生成）
        threshold: condition 省略時に使うコストしきい値
        top_k: 返り値 top_k リストの件数
        ancilla_mode: ancilla の使い方を指定する
            'single'  → oracle 用 ancilla 1本のみ（デフォルト・シンプル）
            'extra'   → 追加 ancilla で mcx を分解（回路が浅くなる・実機向き）
            'compare' → single と extra の両方を実行して回路深さを比較

    Returns:
        dict。ancilla_mode='compare' のときは 'ancilla_comparison' キーが追加される。

    Raises:
        ValueError: condition も threshold も指定されていない場合
        ValueError: ancilla_mode が不正な値の場合
    """
    if ancilla_mode not in ("single", "extra", "compare"):
        raise ValueError(
            f"ancilla_mode は 'single' / 'extra' / 'compare' のいずれかです。got: {ancilla_mode!r}"
        )

    start = time.perf_counter()
    n_qubits = problem.n_qubits_required()

    # --- condition の決定 ---
    if condition is None:
        if threshold is None:
            raise ValueError("condition か threshold のどちらかを指定してください。")
        condition = make_condition_from_cost(
            cost_fn=problem.cost,
            threshold=threshold,
            feasibility_fn=problem.is_feasible,
        )

    # --- Oracle 構築 ---
    try:
        oracle = build_oracle(n_qubits, condition, verbose=False)
    except ValueError as e:
        elapsed = time.perf_counter() - start
        return {"status": "no_solution", "error": str(e), "elapsed_sec": elapsed}

    from quantum.oracle import _enumerate_targets

    n_targets = len(_enumerate_targets(n_qubits, condition))
    n_iterations = optimal_iterations(n_qubits, n_targets)

    # --- 回路構築（モードに応じて分岐）---
    if ancilla_mode == "single":
        circuit = build_grover_circuit(n_qubits, oracle, n_iterations)
        ancilla_info = {
            "mode": "single",
            "n_ancilla": 1,
            "n_qubits_total": n_qubits + 1,
        }

    elif ancilla_mode == "extra":
        circuit = build_grover_circuit_extra_ancilla(n_qubits, oracle, n_iterations)
        n_extra = max(0, n_qubits - 2)
        ancilla_info = {
            "mode": "extra",
            "n_ancilla": 1 + n_extra,
            "n_qubits_total": n_qubits + 1 + n_extra,
        }

    else:  # 'compare'
        circuit_s = build_grover_circuit(n_qubits, oracle, n_iterations)
        circuit_e = build_grover_circuit_extra_ancilla(n_qubits, oracle, n_iterations)
        n_extra = max(0, n_qubits - 2)
        ancilla_info = {
            "mode": "compare",
            "ancilla_comparison": {
                "single": {
                    "n_ancilla": 1,
                    "n_qubits_total": n_qubits + 1,
                    "circuit_depth": circuit_s.depth(),
                },
                "extra": {
                    "n_ancilla": 1 + n_extra,
                    "n_qubits_total": n_qubits + 1 + n_extra,
                    "circuit_depth": circuit_e.depth(),
                },
            },
        }
        # compare モードは single の回路で実際に測定する
        circuit = circuit_s

    circuit_depth = circuit.depth()

    # --- シミュレーション実行 ---
    simulator = AerSimulator()
    compiled = transpile(circuit, simulator)
    job = simulator.run(compiled, shots=shots)
    counts = job.result().get_counts()

    # --- 結果の解析（リトルエンディアン → ビッグエンディアン）---
    normalized: dict[str, int] = {}
    for bitstring, count in counts.items():
        key = bitstring.replace(" ", "")[::-1]
        normalized[key] = normalized.get(key, 0) + count

    best_bitstring = None
    best_cost = float("inf")
    for bitstring, count in sorted(normalized.items(), key=lambda x: -x[1]):
        if problem.is_feasible(bitstring):
            cost = problem.cost(bitstring)
            if cost < best_cost:
                best_cost = cost
                best_bitstring = bitstring

    elapsed = time.perf_counter() - start

    if best_bitstring is None:
        return {
            "status": "no_feasible_solution",
            "counts": normalized,
            "n_iterations": n_iterations,
            "circuit_depth": circuit_depth,
            "elapsed_sec": elapsed,
            **ancilla_info,
        }

    top_k_list = [
        {
            "bitstring": bs,
            "count": cnt,
            "probability": round(cnt / shots, 4),
        }
        for bs, cnt in sorted(normalized.items(), key=lambda x: -x[1])[:top_k]
    ]

    return {
        # brute_force と共通キー
        "status": "ok",
        "best_bitstring": best_bitstring,
        "best_cost": best_cost,
        "best_route": problem.route_to_str(best_bitstring),
        "elapsed_sec": elapsed,
        # 量子固有
        "counts": normalized,
        "n_iterations": n_iterations,
        "circuit_depth": circuit_depth,
        "top_k": top_k_list,
        # ancilla 情報（mode に応じて内容が変わる）
        **ancilla_info,
    }
