from __future__ import annotations

import logging
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from custom_components.ev_charge_controller.const import (
    CONF_BATTERY_POWER_ENTITY,
    CONF_BATTERY_SOC_ENTITY,
    CONF_BATTERY_TIER_50_MAX_DISCHARGE_W,
    CONF_BATTERY_TIER_70_MAX_DISCHARGE_W,
    CONF_BATTERY_TIER_90_MAX_DISCHARGE_W,
    CONF_BUY_PRICE_ENTITY,
    CONF_BUY_PRICE_FORECAST_ATTR,
    CONF_EV_CONNECTED_ENTITY,
    CONF_EV_SOC_ENTITY,
    CONF_EVSE_ACTUAL_CURRENT_ENTITY,
    CONF_EVSE_SET_CURRENT_ENTITY,
    CONF_FAST_MODE_DISCHARGE_LIMIT_W,
    CONF_FORECAST_PRICE_KEY,
    CONF_FORECAST_START_KEY,
    CONF_GRID_POWER_ENTITY,
    CONF_GRID_POWER_LIMIT_W,
    CONF_OBC_ACTUAL_CURRENT_ENTITY,
    CONF_OBC_SET_CURRENT_ENTITY,
    CONF_PHASE_COUNT,
    CONF_PV_POWER_ENTITY,
    CONF_SELL_PRICE_ENTITY,
    DEFAULT_BATTERY_TIER_50_MAX_DISCHARGE_W,
    DEFAULT_BATTERY_TIER_70_MAX_DISCHARGE_W,
    DEFAULT_BATTERY_TIER_90_MAX_DISCHARGE_W,
    DEFAULT_BUY_THRESHOLD,
    DEFAULT_HYSTERESIS_CYCLES,
    DEFAULT_PHASE_COUNT,
    DEFAULT_SELL_THRESHOLD,
    MODE_BALANCED,
    MODE_ECONOMICAL,
    MODE_FAST,
    MODE_MANUAL,
    UPDATE_INTERVAL,
)
from custom_components.ev_charge_controller.domain import (
    BatteryProtectionConfig,
    BatteryProtectionTier,
    ChargingConfig,
    ChargingMode,
    ControlDecision,
    EntityMapping,
    FuturePrice,
    HardLimits,
    PriceThresholdConfig,
    StopConditionConfig,
    TelemetrySnapshot,
)
from custom_components.ev_charge_controller.domain.actuator import apply_decision
from custom_components.ev_charge_controller.domain.override_detector import detect as detect_override
from custom_components.ev_charge_controller.domain.rule_engine import decide
from custom_components.ev_charge_controller.domain.safety_guard import evaluate as evaluate_quality
from custom_components.ev_charge_controller.domain.signal_smoother import SignalSmoother
from custom_components.ev_charge_controller.domain.stop_condition import evaluate as evaluate_stop_condition


LOGGER = logging.getLogger(__name__)


def _mode_stop_keys(mode: str) -> tuple[str, str, str, str, str]:
    return (
        f"{mode}_stop_battery_discharge_w",
        f"{mode}_stop_grid_import_w",
        f"{mode}_stop_buy_price",
        f"{mode}_stop_sell_price_min",
        f"{mode}_stop_hysteresis_cycles",
    )


def _mode_price_keys(mode: str) -> tuple[str, str]:
    return (f"{mode}_buy_threshold", f"{mode}_sell_threshold")


class EVChargeCoordinator(DataUpdateCoordinator[ControlDecision | None]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            logger=LOGGER,
            name="EV Charge Controller",
            update_interval=UPDATE_INTERVAL,
        )
        self.entry = entry
        self.last_commanded_evse_a: int | None = None
        self.last_commanded_obc_a: int | None = None
        self.stop_condition_breach_count = 0
        self.smoother = SignalSmoother()
        self.latest_snapshot: dict[str, Any] = {}
        self.latest_smoothed: dict[str, Any] = {}
        self.latest_decision: ControlDecision | None = None
        self.override_detected = False
        self.active_mode = MODE_BALANCED
        self.config = self._build_config()

    async def _async_update_data(self) -> ControlDecision | None:
        try:
            self.config = self._build_config()
            snapshot = self._collect_snapshot()
            self.latest_snapshot = asdict(snapshot)
            smoothed = self.smoother.update(snapshot)
            self.latest_smoothed = asdict(smoothed)
            self.active_mode = self._read_mode()
            data_quality = evaluate_quality(snapshot, self.config.hard_limits)
            override_detected = detect_override(
                snapshot,
                self.config.hard_limits,
                self.last_commanded_evse_a,
                self.last_commanded_obc_a,
            )
            if override_detected and self.active_mode != MODE_MANUAL:
                mode_entity = getattr(self.entry, "runtime_data_mode_entity", None)
                if mode_entity is not None:
                    mode_entity.set_option(MODE_MANUAL)
                self.active_mode = MODE_MANUAL
            stop_state = evaluate_stop_condition(
                snapshot,
                smoothed,
                self.config.stop_condition[ChargingMode(self.active_mode)] if self.active_mode != MODE_MANUAL else StopConditionConfig(),
                self.stop_condition_breach_count,
            )
            self.stop_condition_breach_count = stop_state.consecutive_breach_count
            decision = decide(
                snapshot,
                smoothed,
                data_quality,
                stop_state,
                self.config,
                ChargingMode(self.active_mode),
                override_detected,
            )
            if decision.mode != ChargingMode.MANUAL and (
                decision.target_evse_current_a is not None or decision.target_obc_current_a is not None
            ):
                await apply_decision(self.hass, self.config, decision)
            if decision.target_evse_current_a is not None:
                self.last_commanded_evse_a = decision.target_evse_current_a
            self.last_commanded_obc_a = decision.target_obc_current_a
            self.latest_decision = decision
            return decision
        except Exception as err:  # pragma: no cover - surfaced via coordinator
            raise UpdateFailed(f"Failed to update EV charge controller state: {err}") from err

    def _read_mode(self) -> str:
        mode_entity = self.entry.runtime_data_mode_entity if hasattr(self.entry, "runtime_data_mode_entity") else None
        if mode_entity is not None:
            return mode_entity.current_option or MODE_BALANCED
        return self.entry.options.get("active_mode", MODE_BALANCED)

    def _collect_snapshot(self) -> TelemetrySnapshot:
        mapping = self.config.entity_mapping
        timestamp = datetime.now(UTC)

        def _float(entity_id: str | None) -> float | None:
            if not entity_id:
                return None
            state = self.hass.states.get(entity_id)
            if state is None or state.state in {"unknown", "unavailable", "None", "none"}:
                return None
            try:
                return float(state.state)
            except ValueError:
                return None

        def _bool(entity_id: str | None) -> bool | None:
            if not entity_id:
                return None
            state = self.hass.states.get(entity_id)
            if state is None or state.state in {"unknown", "unavailable"}:
                return None
            return state.state.lower() in {"on", "true", "1", "home", "connected"}

        def _age(entity_id: str | None) -> float | None:
            if not entity_id:
                return None
            state = self.hass.states.get(entity_id)
            if state is None or state.last_updated is None:
                return None
            return (timestamp - state.last_updated).total_seconds()

        future_prices: list[FuturePrice] = []
        buy_state = self.hass.states.get(mapping.buy_price)
        if buy_state and mapping.buy_price_forecast_attr:
            raw_prices = buy_state.attributes.get(mapping.buy_price_forecast_attr, [])
            if isinstance(raw_prices, list):
                for item in raw_prices:
                    if not isinstance(item, dict):
                        continue
                    start = item.get(mapping.forecast_start_key)
                    price = item.get(mapping.forecast_price_key)
                    if start is None or price is None:
                        continue
                    try:
                        future_prices.append(FuturePrice(start=datetime.fromisoformat(str(start)), price=float(price)))
                    except (TypeError, ValueError):
                        continue

        entity_ages = {
            "pv_power": _age(mapping.pv_power),
            "battery_soc": _age(mapping.battery_soc),
            "battery_power": _age(mapping.battery_power),
            "grid_power": _age(mapping.grid_power),
            "buy_price": _age(mapping.buy_price),
            "sell_price": _age(mapping.sell_price),
            "ev_connected": _age(mapping.ev_connected),
            "ev_soc": _age(mapping.ev_soc),
            "evse_actual_current": _age(mapping.evse_actual_current),
        }
        if mapping.obc_actual_current:
            entity_ages["obc_actual_current"] = _age(mapping.obc_actual_current)

        return TelemetrySnapshot(
            timestamp=timestamp,
            pv_power_w=_float(mapping.pv_power),
            battery_soc_pct=_float(mapping.battery_soc),
            battery_power_w=_float(mapping.battery_power),
            grid_power_w=_float(mapping.grid_power),
            buy_price=_float(mapping.buy_price),
            sell_price=_float(mapping.sell_price),
            future_prices=future_prices,
            ev_connected=_bool(mapping.ev_connected),
            ev_soc_pct=_float(mapping.ev_soc),
            evse_actual_current_a=_float(mapping.evse_actual_current),
            obc_actual_current_a=_float(mapping.obc_actual_current),
            entity_ages_s={key: value for key, value in entity_ages.items() if value is not None},
        )

    def _build_config(self) -> ChargingConfig:
        data = {**self.entry.data, **self.entry.options}
        mapping = EntityMapping(
            pv_power=data[CONF_PV_POWER_ENTITY],
            battery_soc=data[CONF_BATTERY_SOC_ENTITY],
            battery_power=data[CONF_BATTERY_POWER_ENTITY],
            grid_power=data[CONF_GRID_POWER_ENTITY],
            buy_price=data[CONF_BUY_PRICE_ENTITY],
            sell_price=data[CONF_SELL_PRICE_ENTITY],
            ev_connected=data[CONF_EV_CONNECTED_ENTITY],
            ev_soc=data[CONF_EV_SOC_ENTITY],
            evse_set_current=data[CONF_EVSE_SET_CURRENT_ENTITY],
            evse_actual_current=data[CONF_EVSE_ACTUAL_CURRENT_ENTITY],
            charging_mode_entity="select.ev_charge_controller_mode",
            buy_price_forecast_attr=data.get(CONF_BUY_PRICE_FORECAST_ATTR),
            forecast_price_key=data.get(CONF_FORECAST_PRICE_KEY, "price"),
            forecast_start_key=data.get(CONF_FORECAST_START_KEY, "start"),
            obc_set_current=data.get(CONF_OBC_SET_CURRENT_ENTITY),
            obc_actual_current=data.get(CONF_OBC_ACTUAL_CURRENT_ENTITY),
        )
        hard_limits = HardLimits(
            grid_power_limit_w=float(data[CONF_GRID_POWER_LIMIT_W]),
            phase_count=int(data.get(CONF_PHASE_COUNT, DEFAULT_PHASE_COUNT)),
        )
        battery = BatteryProtectionConfig(
            tiers=[
                BatteryProtectionTier(50.0, float(data.get(CONF_BATTERY_TIER_50_MAX_DISCHARGE_W, DEFAULT_BATTERY_TIER_50_MAX_DISCHARGE_W))),
                BatteryProtectionTier(70.0, float(data.get(CONF_BATTERY_TIER_70_MAX_DISCHARGE_W, DEFAULT_BATTERY_TIER_70_MAX_DISCHARGE_W))),
                BatteryProtectionTier(90.0, float(data.get(CONF_BATTERY_TIER_90_MAX_DISCHARGE_W, DEFAULT_BATTERY_TIER_90_MAX_DISCHARGE_W))),
            ],
            fast_mode_discharge_limit_w=(
                float(data[CONF_FAST_MODE_DISCHARGE_LIMIT_W])
                if data.get(CONF_FAST_MODE_DISCHARGE_LIMIT_W) not in (None, "")
                else None
            ),
        )

        stop_condition: dict[ChargingMode, StopConditionConfig] = {}
        price_thresholds: dict[ChargingMode, PriceThresholdConfig] = {}
        for mode in (MODE_BALANCED, MODE_FAST, MODE_ECONOMICAL):
            stop_battery_key, stop_grid_key, stop_buy_key, stop_sell_key, stop_hysteresis_key = _mode_stop_keys(mode)
            buy_key, sell_key = _mode_price_keys(mode)
            stop_condition[ChargingMode(mode)] = StopConditionConfig(
                battery_discharge_limit_w=_optional_float(data.get(stop_battery_key)),
                grid_import_limit_w=_optional_float(data.get(stop_grid_key)),
                buy_price_limit=_optional_float(data.get(stop_buy_key)),
                sell_price_min=_optional_float(data.get(stop_sell_key)),
                hysteresis_cycles=int(data.get(stop_hysteresis_key, DEFAULT_HYSTERESIS_CYCLES)),
            )
            price_thresholds[ChargingMode(mode)] = PriceThresholdConfig(
                buy_threshold=float(data.get(buy_key, DEFAULT_BUY_THRESHOLD)),
                sell_threshold=float(data.get(sell_key, DEFAULT_SELL_THRESHOLD)),
            )

        stop_condition[ChargingMode.MANUAL] = StopConditionConfig()
        price_thresholds[ChargingMode.MANUAL] = PriceThresholdConfig()
        return ChargingConfig(mapping, hard_limits, battery, stop_condition, price_thresholds)


def _optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)
