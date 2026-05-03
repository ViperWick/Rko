"""
量子計算模組 — 可獨立使用
基於量子謎題的閘門運算：H、X、Z、疊加態、相位、測量
"""

import numpy as np
from typing import Optional, Sequence
from dataclasses import dataclass


# ============ 1. 量子閘門矩陣 ============

# 單量子位閘門（2x2 複數矩陣）
I = np.array([[1, 0], [0, 1]], dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)  # Pauli-X，翻轉
Z = np.array([[1, 0], [0, -1]], dtype=complex)  # Pauli-Z，相位
H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)  # Hadamard，疊加
# 雙量子位閘門（4x4）
CNOT = np.array(
    [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], dtype=complex
)
CZ = np.array(
    [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, -1]], dtype=complex
)
SWAP = np.array(
    [[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=complex
)


def phase_gate(phi: float) -> np.ndarray:
    """相位閘 Rz(φ)：|1⟩ → e^(iφ)|1⟩"""
    return np.array([[1, 0], [0, np.exp(1j * phi)]], dtype=complex)


# ============ 2. 量子態與運算 ============

def ket_0() -> np.ndarray:
    """|0⟩ 態"""
    return np.array([1, 0], dtype=complex)


def ket_1() -> np.ndarray:
    """|1⟩ 態"""
    return np.array([0, 1], dtype=complex)


def apply_gate(state: np.ndarray, gate: np.ndarray) -> np.ndarray:
    """對量子態施加閘門：|ψ'⟩ = U|ψ⟩"""
    return gate @ state


def superposition(alpha: float, beta: float) -> np.ndarray:
    """
    疊加態 |ψ⟩ = α|0⟩ + β|1⟩
    歸一化：|α|² + |β|² = 1
    """
    alpha_c = complex(alpha)
    beta_c = complex(beta)
    norm_sq = (np.abs(alpha_c) ** 2) + (np.abs(beta_c) ** 2)
    if norm_sq == 0:
        raise ValueError("alpha 與 beta 不可同時為 0")
    norm = np.sqrt(norm_sq)
    return np.array([alpha_c / norm, beta_c / norm], dtype=complex)


def measure_probabilities(state: np.ndarray) -> np.ndarray:
    """計算測量機率 P(0), P(1)"""
    probs = np.abs(state) ** 2
    total = probs.sum()
    if total == 0:
        raise ValueError("量子態機率總和不可為 0")
    return probs / total


def tensor_product(state_a: np.ndarray, state_b: np.ndarray) -> np.ndarray:
    """兩個量子態的張量積（Kronecker product）"""
    return np.kron(state_a, state_b)


def bell_state_phi_plus() -> np.ndarray:
    """
    建立 Bell state |Φ+⟩ = (|00⟩ + |11⟩)/√2
    流程：|00⟩ -> (H ⊗ I)|00⟩ -> CNOT(...)
    """
    state_00 = tensor_product(ket_0(), ket_0())
    h_on_first = np.kron(H, I)
    state = apply_gate(state_00, h_on_first)
    return apply_gate(state, CNOT)


def two_qubit_gate(single_qubit_gate: np.ndarray, target: int) -> np.ndarray:
    """
    建立雙量子位上的單量子位閘門
    target=0 => U ⊗ I, target=1 => I ⊗ U
    """
    if target not in (0, 1):
        raise ValueError("target 只能是 0 或 1")
    if single_qubit_gate.shape != (2, 2):
        raise ValueError("single_qubit_gate 必須是 2x2 矩陣")
    if target == 0:
        return np.kron(single_qubit_gate, I)
    return np.kron(I, single_qubit_gate)


def run_gate_sequence(state: np.ndarray, gates: Sequence[np.ndarray]) -> np.ndarray:
    """
    依序執行閘門序列：|ψ_out⟩ = U_n ... U_2 U_1 |ψ⟩
    會檢查每個 gate 維度是否與 state 相容。
    """
    out = np.array(state, dtype=complex, copy=True)
    if out.ndim != 1:
        raise ValueError("state 必須是一維向量")
    for gate in gates:
        if gate.ndim != 2 or gate.shape[0] != gate.shape[1]:
            raise ValueError("gate 必須是方陣")
        if gate.shape[1] != out.shape[0]:
            raise ValueError(
                f"gate 維度 {gate.shape} 與 state 維度 {out.shape} 不相容"
            )
        out = gate @ out
    return out


def quantum_measurement(state: np.ndarray, rng: Optional[np.random.Generator] = None) -> int:
    """依機率測量，返回 0 或 1"""
    probs = measure_probabilities(state)
    if rng is None:
        return int(np.random.choice([0, 1], p=probs))
    return int(rng.choice([0, 1], p=probs))


# ============ 3. 量子啟發的世界模型運算 ============

@dataclass
class QuantumPhaseParams:
    """量子相位參數"""
    period: float = 2 * np.pi
    amplitude: float = 1.0


def quantum_phase(t: float, params: QuantumPhaseParams) -> float:
    """
    量子相位演化：φ(t) = amplitude * sin(2πt/period)
    可用於調制螺旋週期或均值回歸
    """
    return params.amplitude * np.sin(2 * np.pi * t / params.period)


def quantum_superposition_value(t: float, base: float = 0.5) -> float:
    """
    量子疊加啟發的數值：結合 |0⟩ 與 |1⟩ 的機率振幅
    返回 0~1 之間的「疊加強度」
    """
    phase = np.sin(2 * np.pi * t / 10)
    alpha = np.cos(phase) ** 2
    beta = np.sin(phase) ** 2
    return alpha * 0 + beta * 1


def quantum_fluctuation(scale: float = 0.1, rng: Optional[np.random.Generator] = None) -> float:
    """量子啟發的隨機波動（模擬測量不確定性）"""
    if rng is None:
        return scale * (2 * np.random.random() - 1)
    return scale * (2 * rng.random() - 1)


def grover_inspired_amplitude(n_states: int, step: int) -> float:
    """
    Grover 搜尋啟發的振幅：隨步驟振盪放大目標態
    簡化版：sin²((2k+1)θ)，其中 θ ≈ arcsin(1/√N)
    """
    if n_states <= 1:
        return 1.0
    theta = np.arcsin(1 / np.sqrt(n_states))
    return np.sin((2 * step + 1) * theta) ** 2


def quantum_coherence(t: float, decay: float = 0.01) -> float:
    """量子相干度：模擬退相干，隨時間衰減"""
    return np.exp(-decay * t)


# ============ 4. 與世界模型的整合介面 ============

def quantum_modulated_spiral(
    t: float,
    spiral_value: float,
    quantum_phase_val: float,
    coupling: float = 0.1,
) -> float:
    """用量子相位調制螺旋值"""
    return spiral_value + coupling * quantum_phase_val


def quantum_modulated_mean_reversion(
    current: float,
    mean: float,
    quantum_fluctuation_val: float,
    coupling: float = 0.2,
) -> float:
    """用量子波動調制均值回歸的噪聲"""
    return current + coupling * quantum_fluctuation_val
