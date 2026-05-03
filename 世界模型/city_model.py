"""
統一城市模型 — 三大預測類別（含耦合、預測區間、情境、預警、AI 影響監控）
1. 科技研發  2. 生產製造  3. 環境汙染與再生
"""

import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field

from world_model import (
    SpiralParams, spiral_value,
    MeanReversionParams, mean_reversion_step,
)


# ============ AI 影響模組 ============

def ai_adoption_level(t: float, t_inflection: float = 10, steepness: float = 0.5) -> float:
    """
    AI 採用率（S 曲線）：0 → 1
    t_inflection: 拐點時間（年），約此時採用率達 50%
    steepness: 曲線陡峭度
    """
    return 1 / (1 + np.exp(-steepness * (t - t_inflection)))


def ai_impact_modifier(
    base_value: float,
    ai_level: float,
    effect_strength: float,
    direction: float = 1,
) -> float:
    """
    AI 對單一指標的影響
    direction: 1=正向, -1=負向
    """
    delta = effect_strength * ai_level * direction * 0.1
    return np.clip(base_value + delta, 0.01, 0.99)


# ============ 預設情境 ============
SCENARIOS = {
    "基準": {
        "tech_mean": 0.6, "prod_mean": 0.75, "env_mean": 0.5,
        "coupling": 0.15, "tech_drift": 0.8, "prod_drift": 0.5, "env_drift": -0.2,
    },
    "高研發投入": {
        "tech_mean": 0.8, "prod_mean": 0.7, "env_mean": 0.55,
        "coupling": 0.2, "tech_drift": 1.2, "prod_drift": 0.4, "env_drift": -0.3,
    },
    "嚴格環保法規": {
        "tech_mean": 0.55, "prod_mean": 0.65, "env_mean": 0.75,
        "coupling": 0.25, "tech_drift": 0.6, "prod_drift": 0.3, "env_drift": -0.5,
    },
    "供應鏈中斷": {
        "tech_mean": 0.5, "prod_mean": 0.5, "env_mean": 0.45,
        "coupling": 0.3, "tech_drift": 0.3, "prod_drift": -0.2, "env_drift": 0.1,
    },
    "綠色轉型": {
        "tech_mean": 0.7, "prod_mean": 0.6, "env_mean": 0.8,
        "coupling": 0.22, "tech_drift": 1.0, "prod_drift": 0.2, "env_drift": -0.6,
    },
}


# ============ 預警閾值 ============
ALERT_THRESHOLDS = {
    "汙染指數_高": 6,
    "汙染指數_極高": 10,
    "再生率_低": 0.35,
    "再生率_極低": 0.25,
    "研發強度_低": 0.4,
    "製造產出_低": 0.5,
}


@dataclass
class CategoryState:
    """單一預測類別的即時狀態"""
    name: str
    cycle_value: float
    level_value: float
    label: str = ""


@dataclass
class Alert:
    """預警訊息"""
    category: str
    metric: str
    value: float
    threshold: float
    severity: str  # "warning" | "critical"
    message: str


class UnifiedCityModel:
    """
    三大預測類別模型（含類別間耦合）：
    - 科技 → 生產：研發提升製造上限
    - 生產 → 環境：產能增加汙染壓力
    - 環境 → 科技：再生率提升綠色研發
    """

    def __init__(
        self,
        seed: Optional[int] = None,
        scenario: str = "基準",
        coupling_strength: Optional[float] = None,
        # 科技研發
        tech_period: float = 12,
        tech_amplitude: float = 15,
        tech_mean: Optional[float] = None,
        # 生產製造
        prod_period: float = 7,
        prod_amplitude: float = 10,
        prod_mean: Optional[float] = None,
        # 環境汙染與再生
        env_period: float = 10,
        env_amplitude: float = 8,
        env_mean: Optional[float] = None,
    ):
        if seed is not None:
            np.random.seed(seed)

        s = SCENARIOS.get(scenario, SCENARIOS["基準"])
        coupling = coupling_strength if coupling_strength is not None else s["coupling"]

        # 情境覆蓋預設值
        tm = tech_mean if tech_mean is not None else s["tech_mean"]
        pm = prod_mean if prod_mean is not None else s["prod_mean"]
        em = env_mean if env_mean is not None else s["env_mean"]

        # ========== 1. 科技研發 ==========
        self.tech_spiral = SpiralParams(period=tech_period, amplitude=tech_amplitude, drift=s["tech_drift"])
        self.tech_mr = MeanReversionParams(mean=tm, speed=0.2, volatility=0.08)
        self._tech_value = tm * 0.8

        # ========== 2. 生產製造 ==========
        self.prod_spiral = SpiralParams(period=prod_period, amplitude=prod_amplitude, drift=s["prod_drift"])
        self.prod_mr = MeanReversionParams(mean=pm, speed=0.25, volatility=0.06)
        self._prod_value = pm * 0.9

        # ========== 3. 環境汙染與再生 ==========
        self.env_spiral = SpiralParams(period=env_period, amplitude=env_amplitude, drift=s["env_drift"])
        self.env_mr = MeanReversionParams(mean=em, speed=0.15, volatility=0.1)
        self._env_value = em * 0.7

        # ========== 耦合強度 ==========
        self.coupling = coupling
        self._scenario = scenario
        self._seed = seed if seed is not None else 42

    def _step_category(
        self,
        t: float,
        dt: float,
        spiral_params: SpiralParams,
        mr_params: MeanReversionParams,
        current_value: float,
        coupling_modifier: float,  # 來自其他類別的耦合影響
        name: str,
        label: str,
    ) -> CategoryState:
        """單一類別的時間步進（含耦合修正）"""
        cycle_val = spiral_value(t, spiral_params)
        modulated_mean = mr_params.mean + 0.08 * cycle_val + coupling_modifier
        params = MeanReversionParams(
            mean=modulated_mean,
            speed=mr_params.speed,
            volatility=mr_params.volatility,
        )
        new_value = mean_reversion_step(current_value, params, dt)
        new_value = np.clip(new_value, 0.01, 0.99)
        return CategoryState(name=name, cycle_value=cycle_val, level_value=new_value, label=label)

    def step(self, t: float, dt: float = 0.01) -> Dict[str, CategoryState]:
        """推進一個時間步（含類別間耦合）"""
        c = self.coupling

        # 科技：受環境再生率正向影響（綠色研發）
        tech_coupling = c * (self._env_value - 0.5)
        tech = self._step_category(
            t, dt, self.tech_spiral, self.tech_mr, self._tech_value,
            tech_coupling, "tech", "科技研發",
        )
        self._tech_value = tech.level_value

        # 生產：受科技研發正向影響，受環境汙染負向影響
        prod_coupling = c * (self._tech_value - 0.5) - 0.5 * c * max(0, self._env_value - 0.6)
        prod = self._step_category(
            t, dt, self.prod_spiral, self.prod_mr, self._prod_value,
            prod_coupling, "prod", "生產製造",
        )
        self._prod_value = prod.level_value

        # 環境：受生產負向影響（汙染），受科技正向影響（綠色技術）
        env_coupling = -c * (self._prod_value - 0.5) + 0.3 * c * (self._tech_value - 0.5)
        env = self._step_category(
            t, dt, self.env_spiral, self.env_mr, self._env_value,
            env_coupling, "env", "環境汙染與再生",
        )
        self._env_value = env.level_value

        return {"tech": tech, "prod": prod, "env": env}

    def _step_with_ai(
        self,
        t: float,
        dt: float,
        ai_level: float,
        ai_tech_effect: float,
        ai_prod_effect: float,
        ai_env_effect: float,
    ) -> Dict[str, CategoryState]:
        """含 AI 影響的時間步進"""
        c = self.coupling
        ai_t = ai_tech_effect * ai_level * 0.15
        ai_p = ai_prod_effect * ai_level * 0.12
        ai_e = ai_env_effect * ai_level * 0.12

        tech_coupling = c * (self._env_value - 0.5) + ai_t
        tech = self._step_category(
            t, dt, self.tech_spiral, self.tech_mr, self._tech_value,
            tech_coupling, "tech", "科技研發",
        )
        self._tech_value = tech.level_value

        prod_coupling = c * (self._tech_value - 0.5) - 0.5 * c * max(0, self._env_value - 0.6) + ai_p
        prod = self._step_category(
            t, dt, self.prod_spiral, self.prod_mr, self._prod_value,
            prod_coupling, "prod", "生產製造",
        )
        self._prod_value = prod.level_value

        env_coupling = -c * (self._prod_value - 0.5) + 0.3 * c * (self._tech_value - 0.5) + ai_e
        env = self._step_category(
            t, dt, self.env_spiral, self.env_mr, self._env_value,
            env_coupling, "env", "環境汙染與再生",
        )
        self._env_value = env.level_value

        return {"tech": tech, "prod": prod, "env": env}

    def simulate(
        self,
        T: float = 30,
        dt: float = 0.05,
    ) -> Dict[str, Any]:
        """模擬完整時間序列"""
        steps = int(T / dt)
        times = np.zeros(steps + 1)
        data = {
            "tech_cycle": np.zeros(steps + 1),
            "tech_level": np.zeros(steps + 1),
            "prod_cycle": np.zeros(steps + 1),
            "prod_level": np.zeros(steps + 1),
            "env_cycle": np.zeros(steps + 1),
            "env_level": np.zeros(steps + 1),
        }

        self._tech_value = self.tech_mr.mean * 0.8
        self._prod_value = self.prod_mr.mean * 0.9
        self._env_value = self.env_mr.mean * 0.7

        for i in range(steps + 1):
            t = i * dt
            states = self.step(t, dt)
            times[i] = t
            data["tech_cycle"][i] = states["tech"].cycle_value
            data["tech_level"][i] = states["tech"].level_value
            data["prod_cycle"][i] = states["prod"].cycle_value
            data["prod_level"][i] = states["prod"].level_value
            data["env_cycle"][i] = states["env"].cycle_value
            data["env_level"][i] = states["env"].level_value

        return {"time": times, **data}

    def simulate_with_ai(
        self,
        T: float = 30,
        dt: float = 0.05,
        ai_tech_effect: float = 1.0,
        ai_prod_effect: float = 0.8,
        ai_env_effect: float = 0.6,
        ai_inflection: float = 10,
        ai_steepness: float = 0.5,
    ) -> Dict[str, Any]:
        """模擬含 AI 影響的時間序列"""
        steps = int(T / dt)
        times = np.zeros(steps + 1)
        data = {
            "tech_cycle": np.zeros(steps + 1),
            "tech_level": np.zeros(steps + 1),
            "prod_cycle": np.zeros(steps + 1),
            "prod_level": np.zeros(steps + 1),
            "env_cycle": np.zeros(steps + 1),
            "env_level": np.zeros(steps + 1),
            "ai_adoption": np.zeros(steps + 1),
        }

        self._tech_value = self.tech_mr.mean * 0.8
        self._prod_value = self.prod_mr.mean * 0.9
        self._env_value = self.env_mr.mean * 0.7

        for i in range(steps + 1):
            t = i * dt
            ai_lvl = ai_adoption_level(t, ai_inflection, ai_steepness)
            states = self._step_with_ai(t, dt, ai_lvl, ai_tech_effect, ai_prod_effect, ai_env_effect)
            times[i] = t
            data["tech_cycle"][i] = states["tech"].cycle_value
            data["tech_level"][i] = states["tech"].level_value
            data["prod_cycle"][i] = states["prod"].cycle_value
            data["prod_level"][i] = states["prod"].level_value
            data["env_cycle"][i] = states["env"].cycle_value
            data["env_level"][i] = states["env"].level_value
            data["ai_adoption"][i] = ai_lvl

        return {"time": times, **data}

    def simulate_observer_view(
        self,
        T: float = 30,
        dt: float = 0.05,
        ai_tech_effect: float = 1.0,
        ai_prod_effect: float = 0.8,
        ai_env_effect: float = 0.6,
        ai_inflection: float = 10,
        ai_steepness: float = 0.5,
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        旁觀者視角：監控 AI 造成的改變 over time
        同時運行「無 AI」基準與「有 AI」情境，返回差異供時間監控
        """
        rng_seed = seed if seed is not None else getattr(self, "_seed", 42)
        base = UnifiedCityModel(
            seed=rng_seed,
            scenario=getattr(self, "_scenario", "基準"),
            coupling_strength=self.coupling,
            tech_period=self.tech_spiral.period,
            tech_amplitude=self.tech_spiral.amplitude,
            tech_mean=self.tech_mr.mean,
            prod_period=self.prod_spiral.period,
            prod_amplitude=self.prod_spiral.amplitude,
            prod_mean=self.prod_mr.mean,
            env_period=self.env_spiral.period,
            env_amplitude=self.env_spiral.amplitude,
            env_mean=self.env_mr.mean,
        )
        ai_model = UnifiedCityModel(
            seed=rng_seed,
            scenario=getattr(self, "_scenario", "基準"),
            coupling_strength=self.coupling,
            tech_period=self.tech_spiral.period,
            tech_amplitude=self.tech_spiral.amplitude,
            tech_mean=self.tech_mr.mean,
            prod_period=self.prod_spiral.period,
            prod_amplitude=self.prod_spiral.amplitude,
            prod_mean=self.prod_mr.mean,
            env_period=self.env_spiral.period,
            env_amplitude=self.env_spiral.amplitude,
            env_mean=self.env_mr.mean,
        )

        baseline = base.simulate(T=T, dt=dt)
        # ai_model 使用相同 seed，確保隨機路徑一致，差異僅來自 AI 影響
        with_ai = ai_model.simulate_with_ai(
            T=T, dt=dt,
            ai_tech_effect=ai_tech_effect,
            ai_prod_effect=ai_prod_effect,
            ai_env_effect=ai_env_effect,
            ai_inflection=ai_inflection,
            ai_steepness=ai_steepness,
        )

        # AI 造成的變化量（有 AI - 無 AI）
        return {
            "time": baseline["time"],
            "ai_adoption": with_ai["ai_adoption"],
            "tech_baseline": baseline["tech_level"],
            "tech_with_ai": with_ai["tech_level"],
            "tech_ai_delta": with_ai["tech_level"] - baseline["tech_level"],
            "prod_baseline": baseline["prod_level"],
            "prod_with_ai": with_ai["prod_level"],
            "prod_ai_delta": with_ai["prod_level"] - baseline["prod_level"],
            "env_baseline": baseline["env_level"],
            "env_with_ai": with_ai["env_level"],
            "env_ai_delta": with_ai["env_level"] - baseline["env_level"],
        }

    def simulate_monte_carlo(
        self,
        T: float = 30,
        dt: float = 0.05,
        n_sims: int = 100,
        seed_base: int = 42,
    ) -> Dict[str, Any]:
        """Monte Carlo 模擬，返回預測區間（5%, 50%, 95%）"""
        all_tech_level = []
        all_prod_level = []
        all_env_level = []
        steps = int(T / dt)
        times = np.linspace(0, T, steps + 1)

        for i in range(n_sims):
            model = UnifiedCityModel(
                seed=seed_base + i,
                scenario=getattr(self, "_scenario", "基準"),
                coupling_strength=self.coupling,
                tech_period=self.tech_spiral.period,
                tech_amplitude=self.tech_spiral.amplitude,
                tech_mean=self.tech_mr.mean,
                prod_period=self.prod_spiral.period,
                prod_amplitude=self.prod_spiral.amplitude,
                prod_mean=self.prod_mr.mean,
                env_period=self.env_spiral.period,
                env_amplitude=self.env_spiral.amplitude,
                env_mean=self.env_mr.mean,
            )
            res = model.simulate(T=T, dt=dt)
            all_tech_level.append(res["tech_level"])
            all_prod_level.append(res["prod_level"])
            all_env_level.append(res["env_level"])

        def percentiles(arr_list: List[np.ndarray]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
            stacked = np.array(arr_list)
            return (
                np.percentile(stacked, 5, axis=0),
                np.percentile(stacked, 50, axis=0),
                np.percentile(stacked, 95, axis=0),
            )

        t5, t50, t95 = percentiles(all_tech_level)
        p5, p50, p95 = percentiles(all_prod_level)
        e5, e50, e95 = percentiles(all_env_level)

        return {
            "time": times,
            "tech_level_p5": t5, "tech_level_p50": t50, "tech_level_p95": t95,
            "prod_level_p5": p5, "prod_level_p50": p50, "prod_level_p95": p95,
            "env_level_p5": e5, "env_level_p50": e50, "env_level_p95": e95,
        }

    def check_alerts(self, t: float = 0) -> List[Alert]:
        """檢查預警閾值"""
        states = self.step(t, 0.01)
        alerts = []

        env_cycle = states["env"].cycle_value
        if env_cycle >= ALERT_THRESHOLDS["汙染指數_極高"]:
            alerts.append(Alert("環境", "汙染指數", env_cycle, ALERT_THRESHOLDS["汙染指數_極高"],
                "critical", f"汙染指數極高 ({env_cycle:.1f})，建議立即採取減排措施"))
        elif env_cycle >= ALERT_THRESHOLDS["汙染指數_高"]:
            alerts.append(Alert("環境", "汙染指數", env_cycle, ALERT_THRESHOLDS["汙染指數_高"],
                "warning", f"汙染指數偏高 ({env_cycle:.1f})"))

        env_level = states["env"].level_value
        if env_level <= ALERT_THRESHOLDS["再生率_極低"]:
            alerts.append(Alert("環境", "再生率", env_level, ALERT_THRESHOLDS["再生率_極低"],
                "critical", f"再生率極低 ({env_level:.2f})，環境修復能力不足"))
        elif env_level <= ALERT_THRESHOLDS["再生率_低"]:
            alerts.append(Alert("環境", "再生率", env_level, ALERT_THRESHOLDS["再生率_低"],
                "warning", f"再生率偏低 ({env_level:.2f})"))

        tech_level = states["tech"].level_value
        if tech_level <= ALERT_THRESHOLDS["研發強度_低"]:
            alerts.append(Alert("科技", "研發強度", tech_level, ALERT_THRESHOLDS["研發強度_低"],
                "warning", f"研發強度偏低 ({tech_level:.2f})"))

        prod_level = states["prod"].level_value
        if prod_level <= ALERT_THRESHOLDS["製造產出_低"]:
            alerts.append(Alert("生產", "製造產出", prod_level, ALERT_THRESHOLDS["製造產出_低"],
                "warning", f"製造產出偏低 ({prod_level:.2f})"))

        return alerts

    def get_city_summary(self, t: float = 0) -> Dict[str, Any]:
        """取得即時摘要"""
        states = self.step(t, 0.01)
        return {
            "tech": {
                "創新週期指數": round(states["tech"].cycle_value, 2),
                "研發強度": round(states["tech"].level_value, 2),
            },
            "prod": {
                "產能週期指數": round(states["prod"].cycle_value, 2),
                "製造產出": round(states["prod"].level_value, 2),
            },
            "env": {
                "汙染指數": round(states["env"].cycle_value, 2),
                "再生率": round(states["env"].level_value, 2),
            },
        }
