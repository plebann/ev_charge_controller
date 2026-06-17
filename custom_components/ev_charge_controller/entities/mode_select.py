from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import callback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.ev_charge_controller.const import DOMAIN, MODE_BALANCED, MODE_OPTIONS
from custom_components.ev_charge_controller.coordinator import EVChargeCoordinator


class ChargingModeSelect(CoordinatorEntity[EVChargeCoordinator], RestoreEntity, SelectEntity):
    _attr_has_entity_name = True
    _attr_name = "Mode"
    _attr_options = MODE_OPTIONS

    def __init__(self, coordinator: EVChargeCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_mode"
        self._current_option = MODE_BALANCED

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state and last_state.state in MODE_OPTIONS:
            self._current_option = last_state.state
        self.coordinator.entry.runtime_data_mode_entity = self

    @property
    def current_option(self) -> str:
        return self._current_option

    async def async_select_option(self, option: str) -> None:
        self._current_option = option
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    @callback
    def set_option(self, option: str) -> None:
        self._current_option = option
        self.async_write_ha_state()
