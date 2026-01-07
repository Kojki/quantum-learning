import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit_aer import AerSimulator


def entanglement_alice_bob():
    """
    この関数ではQ1、Q2間に量子もつれを生成したのち測定し、古典情報をもとに修正をすることで量子テレポーテーションを実現します。
    """

    qr = QuantumRegister(3, "q")
    cr = ClassicalRegister(2, "c")
    qc = QuantumCircuit(qr, cr)

    qc.h(1)  # Hadamard
    qc.cx(1, 2)  # CNOT(Controll: Q1, Target: Q2)

    qc.barrier()

    print(qc.draw("text"))

    qc.cx(0, 1)  # CNOT(Controll: Q0, Target: Q1)
    qc.h(0)  # Hadamard

    qc.barrier()

    qc.measure([0, 1], [0, 1])

    print("回路の構成（アリスの測定完了まで）:")
    print(qc.draw("text"))

    # クラシカル・レジスタ(cr)の値に基づいて、ボブの量子ビット(Q2)を回転させる。
    # 01: Q0=1 -> Z補正
    # 10: Q1=1 -> X補正
    # 11: Q0,Q1=1 -> Y補正

    with qc.if_test((qc.cregs[0], 1)):
        qc.z(2)
    with qc.if_test((qc.cregs[0], 2)):
        qc.x(2)
    with qc.if_test((qc.cregs[0], 3)):
        qc.y(2)

    qc.barrier()

    print("回路:")
    print(qc.draw("text"))

    return qc


def verification():
    """
    AliceからBobに|+>を送る。
    1024回シミュレーションします。
    """
    print("\n" + "=" * 50)
    print(" 実験: |+>状態をテレポートする")
    print("=" * 50)

    qr = QuantumRegister(3, "q")
    cr_alice = ClassicalRegister(2, "alice")
    cr_bob = ClassicalRegister(1, "bob")
    qc = QuantumCircuit(qr, cr_alice, cr_bob)

    # Q0を |+> 状態にする
    qc.h(0)
    qc.barrier()

    qc.h(1)
    qc.cx(1, 2)
    qc.barrier()

    qc.cx(0, 1)
    qc.h(0)
    qc.measure([0, 1], cr_alice)
    qc.barrier()

    with qc.if_test((cr_alice, 1)):
        qc.z(2)
    with qc.if_test((cr_alice, 2)):
        qc.x(2)
    with qc.if_test((cr_alice, 3)):
        qc.x(2)
        qc.z(2)
    qc.barrier()

    # X基底で測定して確認
    # |+> -> 0, |-> -> 1
    qc.h(2)
    qc.measure(2, cr_bob)

    # --- 実行 ---
    sim = AerSimulator()
    qc_compiled = transpile(qc, sim)
    result = sim.run(qc_compiled, shots=1024).result()
    counts = result.get_counts()

    bob_zero_count = sum(count for key, count in counts.items() if key.startswith("0"))
    bob_one_count = sum(count for key, count in counts.items() if key.startswith("1"))

    bob_another_count = sum(
        count
        for key, count in counts.items()
        if not key.startswith("0") and key.startswith("1")
    )

    print(f"\nシミュレーション結果:")
    print(f" - ボブが |+> 状態を観測 (成功): {bob_zero_count} 回")
    print(f" - ボブがそれ以外の状態を観測: {bob_one_count + bob_another_count} 回")

    fidelity = bob_zero_count / 1024
    print(f"\n正答率: {fidelity:.2%}")

    if fidelity == 1.00:
        print("\n✅ 実験成功！")
    else:
        print("\n❌ 実験失敗。回路の構成を見直す必要があります。")


if __name__ == "__main__":
    # エンタングルメント
    qc_demo = entanglement_alice_bob()

    # 検証実験
    verification()
