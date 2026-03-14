from __future__ import annotations

from typing import Callable

from qiskit import QuantumCircuit


# ---------------------------------------------------------------------------
# condition ファクトリ関数
# ---------------------------------------------------------------------------


def make_condition_from_list(targets: list[str]) -> Callable[[str], bool]:
    """ターゲットのビット文字列リストから condition を生成する。"""
    target_set = set(targets)
    return lambda x: x in target_set


def make_condition_from_pattern(pattern: str) -> Callable[[str], bool]:
    """ワイルドカードパターン（'*' = 任意の1ビット）から condition を生成する。
    例: '1*0' → '100', '110'
    """

    def condition(x: str) -> bool:
        if len(x) != len(pattern):
            return False
        return all(p == "*" or p == b for p, b in zip(pattern, x))

    return condition


def make_condition_from_cost(
    cost_fn: Callable[[str], float],
    threshold: float,
    feasibility_fn: Callable[[str], bool] | None = None,
    minimize: bool = True,
) -> Callable[[str], bool]:
    """コスト関数としきい値から condition を生成する。

    Args:
        cost_fn: ビット文字列 → コスト値
        threshold: コストのしきい値
        feasibility_fn: 実行可能解かどうかの判定（省略可）
        minimize: True なら cost <= threshold、False なら cost >= threshold
    """

    def condition(x: str) -> bool:
        if feasibility_fn is not None and not feasibility_fn(x):
            return False
        c = cost_fn(x)
        return c <= threshold if minimize else c >= threshold

    return condition


# ---------------------------------------------------------------------------
# 内部ユーティリティ
# ---------------------------------------------------------------------------


def _enumerate_targets(n_qubits: int, condition: Callable[[str], bool]) -> list[str]:
    """探索空間全体をまわり、 condition を満たすビット文字列を列挙する。"""
    targets = []
    for i in range(2**n_qubits):
        bits = format(i, f"0{n_qubits}b")
        if condition(bits):
            targets.append(bits)
    return targets


def _apply_phase_kickback(
    circuit: QuantumCircuit,
    n_qubits: int,
    target: str,
) -> None:
    """位相反転を使って target ビット文字列に -1 位相を付与する。

    量子ビット構成:
        q[0..n_qubits-1] : 入力レジスタ
        q[n_qubits]      : 補助 qubit（ancilla）

    Qiskit は Little Endian なので
    target を逆方向から処理する。
    """
    ancilla = n_qubits

    # 1. 補助 qubit を |−⟩ に初期化
    circuit.x(ancilla)
    circuit.h(ancilla)

    # 2. target の '0' ビット位置に X ゲート（条件を反転して mcx が効くようにする）
    for i, bit in enumerate(reversed(target)):
        if bit == "0":
            circuit.x(i)

    # 3. multi-controlled X（入力レジスタ全体で ancilla を制御）
    circuit.mcx(list(range(n_qubits)), ancilla)

    # 4. アンコンピュート（手順 2 の X を元に戻す）
    for i, bit in enumerate(reversed(target)):
        if bit == "0":
            circuit.x(i)

    # 5. 補助 qubit を |0⟩ に戻す
    circuit.h(ancilla)
    circuit.x(ancilla)


# ---------------------------------------------------------------------------
# メイン関数
# ---------------------------------------------------------------------------


def build_oracle(
    n_qubits: int,
    condition: Callable[[str], bool],
    verbose: bool = False,
) -> QuantumCircuit:
    """Grover のオラクルを構築してゲートとして返す。

    Args:
        n_qubits: 入力レジスタのビット数
        condition: マーク対象を判定する関数 (bitstring -> bool)
        verbose: True なら target リストを表示する

    Returns:
        QuantumCircuit を .to_gate(label='Oracle') でゲート化したもの
        （n_qubits + 1 本の量子ビットを持つ）

    Raises:
        ValueError: condition を満たすターゲットが 0 件の場合
    """
    targets = _enumerate_targets(n_qubits, condition)

    if verbose:
        print(f"[oracle] n_qubits={n_qubits}, targets={targets} ({len(targets)} 件)")

    if len(targets) == 0:
        raise ValueError("condition を満たすビット文字列が存在しません。")

    # 回路は n_qubits + 1（ancilla 込み）
    circuit = QuantumCircuit(n_qubits + 1)

    for target in targets:
        _apply_phase_kickback(circuit, n_qubits, target)

    return circuit.to_gate(label="Oracle")
