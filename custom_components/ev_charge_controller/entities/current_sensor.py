from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfElectricCurrent
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.ev_charge_controller.const import DOMAIN
from custom_components.ev_charge_controller.coordinator import EVChargeCoordinator


class CommandedCurrentSensor(CoordinatorEntity[EVChargeCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Commanded Current"
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: EVChargeCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_commanded_current"

    @property
    def native_value(self) -> int | None:
        if self.coordinator.latest_decision is None:
            return None
        return self.coordinator.latest_decision.effective_current_a
