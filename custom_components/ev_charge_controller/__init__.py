from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.ev_charge_controller.const import DOMAIN, PLATFORMS
from custom_components.ev_charge_controller.coordinator import EVChargeCoordinator

type EVChargeControllerConfigEntry = ConfigEntry[EVChargeCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: EVChargeControllerConfigEntry) -> bool:
    coordinator = EVChargeCoordinator(hass=hass, entry=entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: EVChargeControllerConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
