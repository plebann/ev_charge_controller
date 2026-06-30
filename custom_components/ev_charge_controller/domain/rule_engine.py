from __future__ import annotations

from datetime import UTC, datetime
from math import floor

from custom_components.ev_charge_controller.domain.battery_protection import max_current_from_battery
from custom_components.ev_charge_controller.domain.models import (
    AutomationStatus,
    ChargingConfig,
    ChargingMode,
    ControlDecision,
    DataQuality,
    DecisionExplanation,
    HardLimits,
    SmoothedMetricsWindow,
    StopConditionState,
    TelemetrySnapshot,
)


def _power_to_current(power_w: float, hard_limits: HardLimits) -> int:
    return max(0, floor(power_w / (230 * hard_limits.phase_count)))


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def _economical_should_wait(snapshot: TelemetrySnapshot) -> bool:
    if snapshot.buy_price is None or not snapshot.future_prices:
        return False
    future_min = min(price.price for price in snapshot.future_prices)
    return future_min < snapshot.buy_price


def decide(
    snapshot: TelemetrySnapshot,
    smoothed: SmoothedMetricsWindow,
    data_quality: DataQuality,
    stop_state: StopConditionState,
    config: ChargingConfig,
    mode: ChargingMode,
    override_detected: bool,
) -> ControlDecision:
    hard_limits = config.hard_limits
    explanation = DecisionExplanation(
        mode=mode.value,
        reason="decision_pending",
        key_inputs={
            "grid_power_w": snapshot.grid_power_w,
            "battery_power_w": snapshot.battery_power_w,
            "pv_power_w": snapshot.pv_power_w,
            "buy_price": snapshot.buy_price,
            "sell_price": snapshot.sell_price,
        },
        data_quality=data_quality.reason,
        stop_condition_active=stop_state.stop_active,
        hysteresis_counter=stop_state.consecutive_breach_count,
        override_detected=override_detected,
    )

    if override_detected or mode == ChargingMode.MANUAL:
        explanation.reason = "manual_override" if override_detected else "manual_mode"
        return ControlDecision(datetime.now(UTC), ChargingMode.MANUAL, AutomationStatus.MANUAL, None, None, None, explanation)

    if not data_quality.is_valid and snapshot.charging_active:
        explanation.reason = data_quality.reason
        explanation.applied_constraints.append("fail_safe")
        return ControlDecision(
            datetime.now(UTC),
            mode,
            AutomationStatus.FAIL_SAFE,
            hard_limits.fail_safe_current_a,
            None,
            hard_limits.fail_safe_current_a,
            explanation,
        )

    if not data_quality.is_valid and not snapshot.charging_active:
        explanation.reason = f"no_start:{data_quality.reason}"
        explanation.applied_constraints.append("no_start")
        return ControlDecision(datetime.now(UTC), mode, AutomationStatus.FAIL_SAFE, None, None, None, explanation)

    if stop_state.stop_active:
        explanation.reason = "stop_condition_active"
        explanation.applied_constraints.append("stop_condition")
        return ControlDecision(datetime.now(UTC), mode, AutomationStatus.STOPPED, None, None, None, explanation)

    grid_cap = _power_to_current(max(hard_limits.grid_power_limit_w - max(snapshot.grid_power_w or 0.0, 0.0), 0.0), hard_limits)
    battery_cap, battery_tier = max_current_from_battery(snapshot, config.battery_protection, hard_limits, mode)
    explanation.battery_tier_active = battery_tier

    pv_current = _power_to_current(max(snapshot.pv_power_w or 0.0, 0.0), hard_limits)
    current_now = int(round(snapshot.evse_actual_current_a or 0.0))
    desired = current_now if current_now > 0 else hard_limits.evse_min_current_a

    if mode == ChargingMode.FAST:
        desired = hard_limits.evse_max_current_a
        explanation.reason = "fast_mode"
    elif mode == ChargingMode.ECONOMICAL:
        if _economical_should_wait(snapshot) and not snapshot.charging_active:
            explanation.reason = "economical_wait_for_lower_future_price"
            return ControlDecision(datetime.now(UTC), mode, AutomationStatus.STOPPED, None, None, None, explanation)
        desired = max(pv_current, hard_limits.evse_min_current_a)
        explanation.reason = "economical_mode"
    else:
        desired = max(pv_current, hard_limits.evse_min_current_a if snapshot.ev_connected else 0)
        explanation.reason = "balanced_mode"

    if battery_cap is not None:
        desired = min(desired, battery_cap)
        explanation.applied_constraints.append("battery_protection")
    if grid_cap > 0:
        desired = min(desired, grid_cap)
        explanation.applied_constraints.append("grid_limit")

    if current_now > 0 and abs(desired - current_now) < 1:
        desired = current_now
        explanation.applied_constraints.append("stability_hold")

    if desired <= 0:
        explanation.reason = "insufficient_safe_power"
        explanation.applied_constraints.append("stopped")
        return ControlDecision(datetime.now(UTC), mode, AutomationStatus.STOPPED, None, None, None, explanation)

    if desired < hard_limits.evse_min_current_a:
        if desired == hard_limits.obc_throttle_current_a and config.entity_mapping.obc_set_current:
            explanation.applied_constraints.append("obc_throttle")
            return ControlDecision(
                datetime.now(UTC),
                mode,
                AutomationStatus.LIMITED,
                hard_limits.evse_min_current_a,
                hard_limits.obc_throttle_current_a,
                hard_limits.obc_throttle_current_a,
                explanation,
            )
        desired = hard_limits.evse_min_current_a

    desired = _clamp(desired, hard_limits.evse_min_current_a, hard_limits.evse_max_current_a)
    status = AutomationStatus.LIMITED if explanation.applied_constraints else AutomationStatus.ACTIVE
    return ControlDecision(datetime.now(UTC), mode, status, desired, None, desired, explanation)
