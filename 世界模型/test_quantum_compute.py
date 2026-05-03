import unittest
import numpy as np

from quantum_compute import (
    CNOT,
    CZ,
    H,
    I,
    SWAP,
    X,
    apply_gate,
    bell_state_phi_plus,
    ket_0,
    ket_1,
    measure_probabilities,
    run_gate_sequence,
    superposition,
    tensor_product,
    two_qubit_gate,
)


class QuantumComputeTests(unittest.TestCase):
    def test_x_gate_flips_zero_to_one(self):
        out = apply_gate(ket_0(), X)
        np.testing.assert_allclose(out, ket_1())

    def test_h_gate_on_zero_creates_equal_probabilities(self):
        out = apply_gate(ket_0(), H)
        probs = measure_probabilities(out)
        np.testing.assert_allclose(probs, np.array([0.5, 0.5]), atol=1e-10)

    def test_superposition_raises_for_zero_vector(self):
        with self.assertRaises(ValueError):
            superposition(0, 0)

    def test_tensor_product_shapes(self):
        state = tensor_product(ket_0(), ket_1())
        self.assertEqual(state.shape, (4,))
        np.testing.assert_allclose(state, np.array([0, 1, 0, 0], dtype=complex))

    def test_cnot_maps_10_to_11(self):
        state_10 = np.array([0, 0, 1, 0], dtype=complex)
        out = apply_gate(state_10, CNOT)
        np.testing.assert_allclose(out, np.array([0, 0, 0, 1], dtype=complex))

    def test_bell_state_phi_plus(self):
        bell = bell_state_phi_plus()
        expected = np.array([1 / np.sqrt(2), 0, 0, 1 / np.sqrt(2)], dtype=complex)
        np.testing.assert_allclose(bell, expected, atol=1e-10)
        np.testing.assert_allclose(measure_probabilities(bell), np.array([0.5, 0.0, 0.0, 0.5]))

    def test_h_tensor_i_on_00(self):
        h_on_first = np.kron(H, I)
        state_00 = tensor_product(ket_0(), ket_0())
        out = apply_gate(state_00, h_on_first)
        expected = np.array([1 / np.sqrt(2), 0, 1 / np.sqrt(2), 0], dtype=complex)
        np.testing.assert_allclose(out, expected, atol=1e-10)

    def test_two_qubit_gate_target_1(self):
        h_on_second = two_qubit_gate(H, target=1)
        state_00 = tensor_product(ket_0(), ket_0())
        out = apply_gate(state_00, h_on_second)
        expected = np.array([1 / np.sqrt(2), 1 / np.sqrt(2), 0, 0], dtype=complex)
        np.testing.assert_allclose(out, expected, atol=1e-10)

    def test_run_gate_sequence_bell(self):
        state_00 = tensor_product(ket_0(), ket_0())
        out = run_gate_sequence(state_00, [two_qubit_gate(H, target=0), CNOT])
        expected = np.array([1 / np.sqrt(2), 0, 0, 1 / np.sqrt(2)], dtype=complex)
        np.testing.assert_allclose(out, expected, atol=1e-10)

    def test_run_gate_sequence_shape_mismatch_raises(self):
        with self.assertRaises(ValueError):
            run_gate_sequence(ket_0(), [CNOT])

    def test_cz_flips_11_phase(self):
        state_11 = np.array([0, 0, 0, 1], dtype=complex)
        out = apply_gate(state_11, CZ)
        np.testing.assert_allclose(out, np.array([0, 0, 0, -1], dtype=complex))

    def test_swap_maps_01_to_10(self):
        state_01 = np.array([0, 1, 0, 0], dtype=complex)
        out = apply_gate(state_01, SWAP)
        np.testing.assert_allclose(out, np.array([0, 0, 1, 0], dtype=complex))


if __name__ == "__main__":
    unittest.main()
