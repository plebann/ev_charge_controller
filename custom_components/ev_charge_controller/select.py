from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.ev_charge_controller import EVChargeControllerConfigEntry
from custom_components.ev_charge_controller.entities.mode_select import ChargingModeSelect


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EVChargeControllerConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([ChargingModeSelect(entry.runtime_data)])
