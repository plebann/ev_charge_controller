from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.ev_charge_controller.const import (
    ATTR_APPLIED_CONSTRAINTS,
    ATTR_BATTERY_TIER,
    ATTR_DATA_QUALITY,
    ATTR_EVSE_CURRENT_A,
    ATTR_HYSTERESIS_COUNTER,
    ATTR_KEY_INPUTS,
    ATTR_LAST_DECISION_AT,
    ATTR_MODE,
    ATTR_OBC_CURRENT_A,
    ATTR_OVERRIDE_DETECTED,
    ATTR_PRICE_THRESHOLDS,
    ATTR_REASON,
    ATTR_STOP_CONDITION_ACTIVE,
    ATTR_STOP_THRESHOLDS,
    ATTR_TARGET_CURRENT_A,
    DOMAIN,
)
from custom_components.ev_charge_controller.domain.models import ChargingMode
from custom_components.ev_charge_controller.coordinator import EVChargeCoordinator


class AutomationStatusSensor(CoordinatorEntity[EVChargeCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Status"

    def __init__(self, coordinator: EVChargeCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_status"

    @property
    def native_value(self) -> str:
        if self.coordinator.latest_decision is None:
            return "unknown"
        return self.coordinator.latest_decision.automation_status.value

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        decision = self.coordinator.latest_decision
        if decision is None:
            return {}
        explanation = decision.explanation
        active_mode = ChargingMode(explanation.mode)
        stop_config = self.coordinator.config.stop_condition.get(active_mode)
        price_config = self.coordinator.config.price_thresholds.get(active_mode)
        return {
            ATTR_MODE: explanation.mode,
            ATTR_REASON: explanation.reason,
            ATTR_TARGET_CURRENT_A: decision.effective_current_a,
            ATTR_EVSE_CURRENT_A: decision.target_evse_current_a,
            ATTR_OBC_CURRENT_A: decision.target_obc_current_a,
            ATTR_DATA_QUALITY: explanation.data_quality,
            ATTR_STOP_CONDITION_ACTIVE: explanation.stop_condition_active,
            ATTR_HYSTERESIS_COUNTER: explanation.hysteresis_counter,
            ATTR_BATTERY_TIER: explanation.battery_tier_active,
            ATTR_OVERRIDE_DETECTED: explanation.override_detected,
            ATTR_APPLIED_CONSTRAINTS: explanation.applied_constraints,
            ATTR_KEY_INPUTS: explanation.key_inputs,
            ATTR_STOP_THRESHOLDS: {
                "battery_discharge_limit_w": getattr(stop_config, "battery_discharge_limit_w", None),
                "grid_import_limit_w": getattr(stop_config, "grid_import_limit_w", None),
                "buy_price_limit": getattr(stop_config, "buy_price_limit", None),
                "sell_price_min": getattr(stop_config, "sell_price_min", None),
                "hysteresis_cycles": getattr(stop_config, "hysteresis_cycles", None),
            },
            ATTR_PRICE_THRESHOLDS: {
                "buy_threshold": getattr(price_config, "buy_threshold", None),
                "sell_threshold": getattr(price_config, "sell_threshold", None),
            },
            ATTR_LAST_DECISION_AT: decision.timestamp.isoformat(),
        }
