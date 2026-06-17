from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.ev_charge_controller import EVChargeControllerConfigEntry
from custom_components.ev_charge_controller.entities.current_sensor import CommandedCurrentSensor
from custom_components.ev_charge_controller.entities.status_sensor import AutomationStatusSensor


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EVChargeControllerConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities(
        [
            AutomationStatusSensor(entry.runtime_data),
            CommandedCurrentSensor(entry.runtime_data),
        ]
    )
