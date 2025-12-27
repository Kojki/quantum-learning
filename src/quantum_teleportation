def quantum_teleportation_circuit():

    from qiskit.circuit import (
        Parameter,
        QuantumCircuit,
        ClassicalRegister,
        QuantumRegister,
    )

    import matplotlib.pyplot as plt

    q = QuantumRegister(3, "q")
    alpha = ClassicalRegister(2, "alpha")

    circuit = QuantumCircuit(q, alpha)

    circuit.barrier()

    circuit.h(1)
    circuit.cx(1, 2)

    circuit.barrier()

    circuit.cx(0, 1)
    circuit.h(0)

    circuit.measure([0, 1], alpha)

    with circuit.if_test((alpha, 1)):
        circuit.x(2)
    with circuit.if_test((alpha, 2)):
        circuit.z(2)
    with circuit.if_test((alpha, 3)):
        circuit.y(2)

    circuit.draw("mpl")
    plt.show()

    result = circuit.measure(q, 3)
    return result
