from __future__ import annotations

from datetime import UTC, datetime, timedelta

from custom_components.ev_charge_controller.domain.battery_protection import max_current_from_battery
from custom_components.ev_charge_controller.domain.models import (
    BatteryProtectionConfig,
    BatteryProtectionTier,
    ChargingConfig,
    ChargingMode,
    EntityMapping,
    HardLimits,
    PriceThresholdConfig,
    SmoothedMetricsWindow,
    StopConditionConfig,
    TelemetrySnapshot,
)
from custom_components.ev_charge_controller.domain.override_detector import detect
from custom_components.ev_charge_controller.domain.rule_engine import decide
from custom_components.ev_charge_controller.domain.safety_guard import evaluate
from custom_components.ev_charge_controller.domain.stop_condition import evaluate as evaluate_stop_condition


def _base_config() -> ChargingConfig:
    return ChargingConfig(
        entity_mapping=EntityMapping(
            pv_power="sensor.pv",
            battery_soc="sensor.battery_soc",
            battery_power="sensor.battery_power",
            grid_power="sensor.grid",
            buy_price="sensor.buy_price",
            sell_price="sensor.sell_price",
            ev_connected="binary_sensor.ev_connected",
            ev_soc="sensor.ev_soc",
            evse_set_current="number.evse_set_current",
            evse_actual_current="sensor.evse_actual_current",
            obc_set_current="number.obc_set_current",
            obc_actual_current="sensor.obc_actual_current",
            charging_mode_entity="select.ev_mode",
        ),
        hard_limits=HardLimits(grid_power_limit_w=11040),
        battery_protection=BatteryProtectionConfig(
            tiers=[
                BatteryProtectionTier(50.0, 3450.0),
                BatteryProtectionTier(70.0, 5000.0),
                BatteryProtectionTier(90.0, 8000.0),
            ]
        ),
        stop_condition={
            ChargingMode.BALANCED: StopConditionConfig(),
            ChargingMode.FAST: StopConditionConfig(),
            ChargingMode.ECONOMICAL: StopConditionConfig(),
            ChargingMode.MANUAL: StopConditionConfig(),
        },
        price_thresholds={
            ChargingMode.BALANCED: PriceThresholdConfig(),
            ChargingMode.FAST: PriceThresholdConfig(),
            ChargingMode.ECONOMICAL: PriceThresholdConfig(),
            ChargingMode.MANUAL: PriceThresholdConfig(),
        },
    )


def test_safety_guard_marks_missing_or_stale_data() -> None:
    snapshot = TelemetrySnapshot(
        timestamp=datetime.now(UTC),
        pv_power_w=None,
        battery_soc_pct=50,
        battery_power_w=0,
        grid_power_w=0,
        buy_price=1.0,
        sell_price=0.5,
        ev_connected=True,
        ev_soc_pct=70,
        evse_actual_current_a=6,
        entity_ages_s={"battery_soc": 70},
    )

    result = evaluate(snapshot, HardLimits(grid_power_limit_w=10000, stale_data_timeout_s=60))

    assert result.is_valid is False
    assert "pv_power" in result.missing_entities or "battery_soc" in result.stale_entities


def test_stop_condition_uses_hysteresis_counter() -> None:
    snapshot = TelemetrySnapshot(
        timestamp=datetime.now(UTC),
        battery_power_w=-2500,
        grid_power_w=500,
        buy_price=1.2,
        sell_price=0.4,
    )
    config = StopConditionConfig(battery_discharge_limit_w=2000, hysteresis_cycles=2)

    first = evaluate_stop_condition(snapshot, SmoothedMetricsWindow(), config, 0)
    second = evaluate_stop_condition(snapshot, SmoothedMetricsWindow(), config, first.consecutive_breach_count)

    assert first.stop_active is False
    assert second.stop_active is True


def test_rule_engine_uses_obc_throttle_for_effective_5a() -> None:
    config = _base_config()
    snapshot = TelemetrySnapshot(
        timestamp=datetime.now(UTC),
        pv_power_w=9000,
        battery_soc_pct=40,
        battery_power_w=0,
        grid_power_w=-9000,
        buy_price=0.8,
        sell_price=0.4,
        ev_connected=True,
        ev_soc_pct=25,
        evse_actual_current_a=0,
        obc_actual_current_a=0,
    )

    decision = decide(
        snapshot=snapshot,
        smoothed=SmoothedMetricsWindow(grid_power_1min_w=-9000, grid_power_5min_w=-9000),
        data_quality=evaluate(snapshot, config.hard_limits),
        stop_state=evaluate_stop_condition(snapshot, SmoothedMetricsWindow(), StopConditionConfig(), 0),
        config=config,
        mode=ChargingMode.BALANCED,
        override_detected=False,
    )

    assert max_current_from_battery(snapshot, config.battery_protection, config.hard_limits, ChargingMode.BALANCED)[0] == 5
    assert decision.target_evse_current_a == 6
    assert decision.target_obc_current_a == 5
    assert decision.effective_current_a == 5


def test_override_detector_flags_manual_intervention() -> None:
    snapshot = TelemetrySnapshot(
        timestamp=datetime.now(UTC),
        evse_actual_current_a=10,
        obc_actual_current_a=10,
    )

    assert detect(snapshot, HardLimits(grid_power_limit_w=10000, override_delta_a=1), 6, None) is True