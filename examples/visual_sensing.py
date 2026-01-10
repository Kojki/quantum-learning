import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from src.sensing.core import feedback_control_step, estimate_phase_ipe

steps = []
true_phases = []
corrections = []

true_base_phase = 1.23
current_correction = estimate_phase_ipe(true_base_phase, num_bits=6)
drift_rate = 0.02

for t in range(50):
    actual_field = true_base_phase + (t * drift_rate)

    current_correction, p0 = feedback_control_step(
        actual_field, current_correction, shots=100
    )

    steps.append(t)
    true_phases.append(actual_field)
    corrections.append(current_correction)
