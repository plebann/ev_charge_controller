from __future__ import annotations

from homeassistant.core import HomeAssistant

from custom_components.ev_charge_controller.const import SERVICE_NUMBER_SET_VALUE
from custom_components.ev_charge_controller.domain.models import ChargingConfig, ControlDecision


async def apply_decision(hass: HomeAssistant, config: ChargingConfig, decision: ControlDecision) -> None:
    mapping = config.entity_mapping
    if decision.target_evse_current_a is not None:
        await hass.services.async_call(
            "number",
            SERVICE_NUMBER_SET_VALUE,
            {"entity_id": mapping.evse_set_current, "value": decision.target_evse_current_a},
            blocking=True,
        )
    if decision.target_obc_current_a is not None and mapping.obc_set_current:
        await hass.services.async_call(
            "number",
            SERVICE_NUMBER_SET_VALUE,
            {"entity_id": mapping.obc_set_current, "value": decision.target_obc_current_a},
            blocking=True,
        )
