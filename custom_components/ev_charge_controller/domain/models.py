from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from custom_components.ev_charge_controller.const import (
    DEFAULT_EVSE_MAX_CURRENT_A,
    DEFAULT_EVSE_MIN_CURRENT_A,
    DEFAULT_FAIL_SAFE_CURRENT_A,
    DEFAULT_HYSTERESIS_CYCLES,
    DEFAULT_OBC_THROTTLE_CURRENT_A,
    DEFAULT_OVERRIDE_DELTA_A,
    DEFAULT_PHASE_COUNT,
    DEFAULT_STALE_DATA_TIMEOUT_S,
)


class ChargingMode(str, Enum):
    BALANCED = "balanced"
    FAST = "fast"
    ECONOMICAL = "economical"
    MANUAL = "manual"


class AutomationStatus(str, Enum):
    ACTIVE = "active"
    LIMITED = "limited"
    STOPPED = "stopped"
    FAIL_SAFE = "fail_safe"
    MANUAL = "manual"


@dataclass(slots=True)
class EntityMapping:
    pv_power: str
    battery_soc: str
    battery_power: str
    grid_power: str
    buy_price: str
    sell_price: str
    ev_connected: str
    ev_soc: str
    evse_set_current: str
    evse_actual_current: str
    charging_mode_entity: str
    buy_price_forecast_attr: str | None = None
    forecast_price_key: str = "price"
    forecast_start_key: str = "start"
    obc_set_current: str | None = None
    obc_actual_current: str | None = None


@dataclass(slots=True)
class HardLimits:
    grid_power_limit_w: float
    evse_min_current_a: int = DEFAULT_EVSE_MIN_CURRENT_A
    evse_max_current_a: int = DEFAULT_EVSE_MAX_CURRENT_A
    obc_throttle_current_a: int = DEFAULT_OBC_THROTTLE_CURRENT_A
    stale_data_timeout_s: int = DEFAULT_STALE_DATA_TIMEOUT_S
    fail_safe_current_a: int = DEFAULT_FAIL_SAFE_CURRENT_A
    override_delta_a: int = DEFAULT_OVERRIDE_DELTA_A
    phase_count: int = DEFAULT_PHASE_COUNT


@dataclass(slots=True)
class BatteryProtectionTier:
    soc_threshold_pct: float
    max_discharge_power_w: float


@dataclass(slots=True)
class BatteryProtectionConfig:
    tiers: list[BatteryProtectionTier]
    fast_mode_discharge_limit_w: float | None = None


@dataclass(slots=True)
class StopConditionConfig:
    battery_discharge_limit_w: float | None = None
    grid_import_limit_w: float | None = None
    buy_price_limit: float | None = None
    sell_price_min: float | None = None
    hysteresis_cycles: int = DEFAULT_HYSTERESIS_CYCLES


@dataclass(slots=True)
class PriceThresholdConfig:
    buy_threshold: float = 0.0
    sell_threshold: float = 0.0


@dataclass(slots=True)
class ChargingConfig:
    entity_mapping: EntityMapping
    hard_limits: HardLimits
    battery_protection: BatteryProtectionConfig
    stop_condition: dict[ChargingMode, StopConditionConfig]
    price_thresholds: dict[ChargingMode, PriceThresholdConfig]


@dataclass(slots=True)
class FuturePrice:
    start: datetime
    price: float


@dataclass(slots=True)
class TelemetrySnapshot:
    timestamp: datetime
    pv_power_w: float | None = None
    battery_soc_pct: float | None = None
    battery_power_w: float | None = None
    grid_power_w: float | None = None
    buy_price: float | None = None
    sell_price: float | None = None
    future_prices: list[FuturePrice] = field(default_factory=list)
    ev_connected: bool | None = None
    ev_soc_pct: float | None = None
    evse_actual_current_a: float | None = None
    obc_actual_current_a: float | None = None
    entity_ages_s: dict[str, float] = field(default_factory=dict)

    @property
    def charging_active(self) -> bool:
        if self.obc_actual_current_a is not None:
            return self.obc_actual_current_a > 0
        if self.evse_actual_current_a is not None:
            return self.evse_actual_current_a > 0
        return False


@dataclass(slots=True)
class DataQuality:
    is_valid: bool
    missing_entities: list[str] = field(default_factory=list)
    stale_entities: list[str] = field(default_factory=list)
    contradiction_detected: bool = False
    reason: str = "ok"


@dataclass(slots=True)
class SmoothedMetricsWindow:
    grid_power_1min_w: float | None = None
    grid_power_5min_w: float | None = None
    battery_power_1min_w: float | None = None
    battery_power_5min_w: float | None = None
    pv_power_1min_w: float | None = None
    pv_power_5min_w: float | None = None
    buy_price_1min: float | None = None
    buy_price_5min: float | None = None


@dataclass(slots=True)
class StopConditionState:
    any_threshold_breached: bool = False
    battery_discharge_breached: bool = False
    grid_import_breached: bool = False
    buy_price_breached: bool = False
    sell_price_breached: bool = False
    consecutive_breach_count: int = 0
    stop_active: bool = False


@dataclass(slots=True)
class SafetyState:
    can_increase: bool = True
    can_maintain: bool = True
    must_reduce: bool = False
    must_fail_safe: bool = False
    must_stop: bool = False
    constraint_reason: str = "ok"


@dataclass(slots=True)
class DecisionExplanation:
    mode: str
    reason: str
    key_inputs: dict[str, Any] = field(default_factory=dict)
    applied_constraints: list[str] = field(default_factory=list)
    data_quality: str = "ok"
    stop_condition_active: bool = False
    hysteresis_counter: int = 0
    battery_tier_active: str | None = None
    override_detected: bool = False


@dataclass(slots=True)
class ControlDecision:
    timestamp: datetime
    mode: ChargingMode
    automation_status: AutomationStatus
    target_evse_current_a: int | None
    target_obc_current_a: int | None
    effective_current_a: int | None
    explanation: DecisionExplanation
