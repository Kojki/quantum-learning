import numpy as np
import time
from typing import List, Callable, Dict, Any, Optional

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from ..quantum.oracle import build_oracle, make_condition_from_cost, _enumerate_targets
from ..quantum.grover import build_diffusion
from ...visualization.animation import AnimationPlotter

class GroverAnimationRunner:
    """A specialized runner that extracts Statevectors at each Grover iteration.
    
    This class is required because standard simulation backends (AerSimulator)
    do not naturally persist the full statevector intermediate steps during a 
    circuit run with measurements.
    
    This runner reconstructs the circuit step-by-step up to `i` iterations,
    extracts the Statevector, and uses AnimationPlotter to generate an MP4/GIF.
    """
    
    def __init__(self, problem: Any, threshold: Optional[float] = None):
        """
        Args:
            problem: An OptimizationProblem instance (e.g., Knapsack).
            threshold: The target cost threshold to consider an answer 'correct'.
        """
        self.problem = problem
        self.threshold = threshold
        self.plotter = AnimationPlotter()
        
    def generate_animation(self, 
                           max_iterations: int, 
                           save_path: str = "grover_amplification.mp4", 
                           fps: int = 2) -> Dict[str, Any]:
        """Runs the Grover step-by-step and generates an animation video.
        
        Args:
            max_iterations: How many Grover iterations to animate.
            save_path: Output file path (.mp4 or .gif).
            fps: Frames per second of the resulting animation.
            
        Returns:
            Dictionary with execution metadata.
        """
        start_time = time.perf_counter()
        n_qubits = self.problem.n_qubits_required()
        
        # Determine the condition and target indices
        if self.threshold is None:
            raise ValueError("A threshold must be provided for the animation.")
            
        condition = make_condition_from_cost(
            cost_fn=self.problem.cost,
            threshold=self.threshold,
            feasibility_fn=self.problem.is_feasible,
        )
        
        # Enumerate target strings to highlight them in the plot
        target_bitstrings = _enumerate_targets(n_qubits, condition)
        target_indices = [int(bs, 2) for bs in target_bitstrings]
        
        if not target_indices:
            raise ValueError("No targets meet the threshold condition.")
            
        oracle = build_oracle(n_qubits, condition, verbose=False)
        diffusion = build_diffusion(n_qubits)
        
        history_amplitudes: List[np.ndarray] = []
        
        # We need to build and simulate the circuit incrementally for each iteration step
        for i in range(max_iterations + 1):
            circuit = QuantumCircuit(n_qubits + 1)
            circuit.h(range(n_qubits)) # Initial superposition
            
            for _ in range(i):
                # Apply Oracle
                circuit.append(oracle, list(range(n_qubits + 1)))
                # Apply Diffusion
                circuit.append(diffusion, list(range(n_qubits)))
                
            # Simulate the circuit to get the Statevector
            # Note: qiskit's Statevector.from_instruction() is perfect for exact classical simulation
            state = Statevector.from_instruction(circuit)
            
            # Since the circuit includes the ancilla qubit at index n_qubits, 
            # we need to trace it out or extract only the state amplitudes for the data qubits.
            # Statevector dimensions: 2^(n_qubits+1). We care about the first 2^n_qubits indices 
            # assuming the ancilla is in the |0> state after the uncompute step in the oracle.
            
            # The amplitudes corresponding to the computational basis of the n_qubits.
            # Because ancilla (q[n]) is restored to |0> (or |-> if kicked back correctly, let's verify).
            # If ancilla is |->, the probabilities are split.
            # For visualization, computing probabilities of data qubits is safer via density matrix or tracing,
            # but taking the partial trace analytically via probabilities works best.
            probabilities_dict = state.probabilities_dict(qargs=range(n_qubits))
            
            # Convert dict back to an array of size 2^n_qubits
            # To interface with AnimationPlotter, we pass an array of 'amplitudes'.
            # Since Plotter currently uses np.abs(history_amplitudes)**2 for probabilities,
            # we will pass sqrt(probs) as fake amplitudes.
            pseudo_amplitudes = np.zeros(2**n_qubits)
            for bitstring, prob in probabilities_dict.items():
                idx = int(bitstring, 2)
                pseudo_amplitudes[idx] = np.sqrt(prob)
                
            history_amplitudes.append(pseudo_amplitudes)
            
        print(f"Captured statevectors for {max_iterations} iterations. Generating animation...")
        self.plotter.animate_grover_amplitudes(
            history_amplitudes=history_amplitudes,
            target_indices=target_indices,
            save_path=save_path,
            fps=fps
        )
        
        elapsed = time.perf_counter() - start_time
        return {
            "status": "success",
            "iterations_animated": max_iterations,
            "target_count": len(target_indices),
            "elapsed_sec": elapsed,
            "save_path": save_path
        }
