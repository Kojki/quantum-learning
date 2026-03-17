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
    """Oracle と Diffusion を組み合わせた Grover 回路を構築する。"""
    circuit = QuantumCircuit(n_qubits + 1, n_qubits)
    circuit.h(range(n_qubits))
    diffusion = build_diffusion(n_qubits)
    for _ in range(n_iterations):
        circuit.append(oracle, list(range(n_qubits + 1)))
        circuit.append(diffusion, list(range(n_qubits)))
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
    """追加 ancilla を使って mcx を分解した、回路深さの浅い Grover 回路を構築する。"""
    n_extra = max(0, n_qubits - 2)
    n_total = n_qubits + 1 + n_extra
    circuit = QuantumCircuit(n_total, n_qubits)
    circuit.h(range(n_qubits))
    diffusion = build_diffusion(n_qubits)
    for _ in range(n_iterations):
        circuit.append(oracle, list(range(n_qubits + 1)))
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
# 5. シミュレーション実行（中断対応）
# ---------------------------------------------------------------------------


def _run_circuit(
    circuit: QuantumCircuit,
    shots: int,
    noise_model=None,
    seed: int | None = None,
) -> dict[str, int]:
    """回路を実行して測定カウントを返す。

    Ctrl+C（KeyboardInterrupt）を受け取ったとき job をキャンセルして
    InterruptedError を送出する。これにより呼び出し元が中断を検知できる。
    """
    simulator = AerSimulator()
    options: dict = {"shots": shots}
    if noise_model is not None:
        options["noise_model"] = noise_model
    if seed is not None:
        options["seed_simulator"] = seed

    compiled = transpile(circuit, simulator)
    job = simulator.run(compiled, **options)

    try:
        counts = job.result().get_counts()
    except KeyboardInterrupt:
        job.cancel()
        raise InterruptedError("シミュレーションが中断されました（Ctrl+C）。")

    # リトルエンディアン → ビッグエンディアン
    normalized: dict[str, int] = {}
    for bitstring, count in counts.items():
        key = bitstring.replace(" ", "")[::-1]
        normalized[key] = normalized.get(key, 0) + count
    return normalized


# ---------------------------------------------------------------------------
# 6. エントリーポイント（単発 Grover）
# ---------------------------------------------------------------------------


def solve(
    problem: "OptimizationProblem",
    shots: int = 1024,
    condition: Callable[[str], bool] | None = None,
    threshold: float | None = None,
    n_iterations: int | None = None,
    top_k: int = 5,
    ancilla_mode: str = "single",
    noise_model=None,
    seed: int | None = None,
) -> dict:
    """Grover のアルゴリズムで最適解を探索する（単発）。

    Args:
        problem: OptimizationProblem のインスタンス
        shots: シミュレーションのショット数
        condition: 外部から渡す condition（省略時は threshold から自動生成）
        threshold: condition 省略時に使うコストしきい値
        n_iterations: 反復回数（省略時は自動計算）
        top_k: 返り値 top_k リストの件数
        ancilla_mode: 'single' | 'extra' | 'compare'
        noise_model: Qiskit Aer のノイズモデル（省略時はノイズなし）
        seed: 乱数シード
    """
    if ancilla_mode not in ("single", "extra", "compare"):
        raise ValueError(
            f"ancilla_mode は 'single' / 'extra' / 'compare' のいずれかです。got: {ancilla_mode!r}"
        )

    start = time.perf_counter()
    n_qubits = problem.n_qubits_required()

    if condition is None:
        if threshold is None:
            raise ValueError("condition か threshold のどちらかを指定してください。")
        condition = make_condition_from_cost(
            cost_fn=problem.cost,
            threshold=threshold,
            feasibility_fn=problem.is_feasible,
        )

    try:
        oracle = build_oracle(n_qubits, condition, verbose=False)
    except ValueError as e:
        return {
            "status": "no_solution",
            "error": str(e),
            "elapsed_sec": time.perf_counter() - start,
        }

    from quantum.oracle import _enumerate_targets

    n_targets = len(_enumerate_targets(n_qubits, condition))

    if n_iterations is None:
        n_iterations = optimal_iterations(n_qubits, n_targets)

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
    else:  # compare
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
        circuit = circuit_s

    circuit_depth = circuit.depth()

    try:
        normalized = _run_circuit(circuit, shots, noise_model=noise_model, seed=seed)
    except InterruptedError as e:
        return {
            "status": "interrupted",
            "error": str(e),
            "elapsed_sec": time.perf_counter() - start,
        }

    best_bitstring = None
    best_cost = float("inf")
    for bitstring in sorted(normalized, key=lambda b: -normalized[b]):
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
        {"bitstring": bs, "count": cnt, "probability": round(cnt / shots, 4)}
        for bs, cnt in sorted(normalized.items(), key=lambda x: -x[1])[:top_k]
    ]

    return {
        "status": "ok",
        "best_bitstring": best_bitstring,
        "best_cost": best_cost,
        "best_route": problem.route_to_str(best_bitstring),
        "elapsed_sec": elapsed,
        "counts": normalized,
        "n_iterations": n_iterations,
        "circuit_depth": circuit_depth,
        "top_k": top_k_list,
        **ancilla_info,
    }


# ---------------------------------------------------------------------------
# 7. Durr-Hoyer アルゴリズム（反復型 Grover）
# ---------------------------------------------------------------------------


def solve_iterative(
    problem: "OptimizationProblem",
    shots: int = 1024,
    max_iterations: int = 10,
    top_k: int = 5,
    ancilla_mode: str = "single",
    noise_model=None,
    seed: int | None = None,
    verbose: bool = True,
) -> dict:
    """Durr-Hoyer アルゴリズムで最適解を探索する。

    手順:
        1. ランダムに初期解を選ぶ
        2. 現在の解のコスト threshold で Grover を実行
        3. より良い解が見つかれば threshold を更新
        4. max_iterations 回繰り返す

    Ctrl+C を受け取った場合はその時点の最良解を返す（interrupted フラグ付き）。

    Args:
        problem: OptimizationProblem のインスタンス
        shots: 各反復のショット数
        max_iterations: 最大反復回数
        top_k: 返り値 top_k リストの件数
        ancilla_mode: 'single' | 'extra' | 'compare'
        noise_model: Qiskit Aer のノイズモデル
        seed: 乱数シード
        verbose: 各反復の進捗を表示するか
    """
    import random as _random

    start = time.perf_counter()

    # ── 初期解をランダムに選ぶ ──
    n_qubits = problem.n_qubits_required()
    rng = _random.Random(seed)

    best_bitstring: str | None = None
    best_cost = float("inf")

    # 実行可能な初期解を探す
    for _ in range(2**n_qubits):
        candidate = format(rng.randint(0, 2**n_qubits - 1), f"0{n_qubits}b")
        if problem.is_feasible(candidate):
            best_bitstring = candidate
            best_cost = problem.cost(candidate)
            break

    if best_bitstring is None:
        return {
            "status": "no_feasible_solution",
            "error": "初期解が見つかりませんでした。",
            "elapsed_sec": 0.0,
        }

    if verbose:
        print(
            f"  初期解: {problem.route_to_str(best_bitstring)}  コスト: {best_cost:.1f}"
        )

    history = []
    n_grover_calls = 0
    interrupted = False

    try:
        for iteration in range(1, max_iterations + 1):
            # 現在の best_cost より小さい解を探す
            result = solve(
                problem=problem,
                shots=shots,
                threshold=best_cost,
                top_k=top_k,
                ancilla_mode=ancilla_mode,
                noise_model=noise_model,
                seed=seed,
            )
            n_grover_calls += 1

            if result["status"] == "interrupted":
                if verbose:
                    print(f"\n  ⚠️  反復 {iteration} で中断されました。")
                interrupted = True
                break

            if result["status"] == "ok" and result["best_cost"] < best_cost:
                best_cost = result["best_cost"]
                best_bitstring = result["best_bitstring"]
                improved = True
                if verbose:
                    print(
                        f"  ✅ 反復 {iteration:2d}  改善: コスト {best_cost:.1f}  ルート: {problem.route_to_str(best_bitstring)}"
                    )
            else:
                improved = False
                if verbose:
                    print(
                        f"     反復 {iteration:2d}  改善なし（閾値: {best_cost:.1f}）"
                    )

            history.append(
                {
                    "iteration": iteration,
                    "threshold": best_cost,
                    "route": (
                        problem.route_to_str(best_bitstring) if best_bitstring else None
                    ),
                    "improved": improved,
                }
            )

    except KeyboardInterrupt:
        if verbose:
            print(f"\n  ⚠️  Ctrl+C を受け取りました。現在の最良解を返します。")
        interrupted = True

    elapsed = time.perf_counter() - start

    if best_bitstring is None:
        return {"status": "no_feasible_solution", "elapsed_sec": elapsed}

    # solve() と同じ形式で top_k を構成（最終反復の結果を使う）
    top_k_list = result.get("top_k", []) if "result" in dir() else []

    return {
        "status": "ok",
        "best_bitstring": best_bitstring,
        "best_cost": best_cost,
        "best_route": problem.route_to_str(best_bitstring),
        "elapsed_sec": elapsed,
        "n_grover_calls": n_grover_calls,
        "history": history,
        "top_k": top_k_list,
        "interrupted": interrupted,
    }
