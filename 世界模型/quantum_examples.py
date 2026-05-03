"""
量子模組快速示例
執行：python quantum_examples.py
"""

import numpy as np

from quantum_compute import (
    CNOT,
    CZ,
    H,
    SWAP,
    ket_0,
    measure_probabilities,
    run_gate_sequence,
    tensor_product,
    two_qubit_gate,
)


def show_state(title: str, state: np.ndarray) -> None:
    probs = measure_probabilities(state)
    print(f"\n[{title}]")
    print("state =", np.round(state, 6))
    print("probs =", np.round(probs, 6))


def example_bell_state() -> None:
    state_00 = tensor_product(ket_0(), ket_0())
    state = run_gate_sequence(state_00, [two_qubit_gate(H, target=0), CNOT])
    show_state("Bell Phi+", state)


def example_cz_phase_flip() -> None:
    # 先產生 Bell，再施加 CZ 讓 |11> 振幅翻相
    state_00 = tensor_product(ket_0(), ket_0())
    bell = run_gate_sequence(state_00, [two_qubit_gate(H, target=0), CNOT])
    phase_flipped = run_gate_sequence(bell, [CZ])
    show_state("Bell after CZ", phase_flipped)


def example_swap() -> None:
    # |01> 經 SWAP 變 |10>
    state_01 = np.array([0, 1, 0, 0], dtype=complex)
    swapped = run_gate_sequence(state_01, [SWAP])
    show_state("|01> after SWAP", swapped)


if __name__ == "__main__":
    example_bell_state()
    example_cz_phase_flip()
    example_swap()
