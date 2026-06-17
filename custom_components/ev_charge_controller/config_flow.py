from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import UnitOfPower
from homeassistant.helpers import selector

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
    CONF_PHASE_COUNT,
    CONF_OBC_ACTUAL_CURRENT_ENTITY,
    CONF_OBC_SET_CURRENT_ENTITY,
    CONF_PV_POWER_ENTITY,
    CONF_SELL_PRICE_ENTITY,
    DOMAIN,
    MODE_BALANCED,
    MODE_ECONOMICAL,
    MODE_FAST,
)


def _entity_selector(domain_name: str) -> selector.EntitySelector:
    return selector.EntitySelector(selector.EntitySelectorConfig(domain=domain_name))


def _number_selector(minimum: float, maximum: float | None = None, unit: str | None = None) -> selector.NumberSelector:
    config = selector.NumberSelectorConfig(min=minimum, max=maximum, unit_of_measurement=unit, mode=selector.NumberSelectorMode.BOX)
    return selector.NumberSelector(config)


AUTO_MODES = (MODE_BALANCED, MODE_FAST, MODE_ECONOMICAL)


def _stop_condition_keys(mode: str) -> tuple[str, str, str, str, str]:
    return (
        f"{mode}_stop_battery_discharge_w",
        f"{mode}_stop_grid_import_w",
        f"{mode}_stop_buy_price",
        f"{mode}_stop_sell_price_min",
        f"{mode}_stop_hysteresis_cycles",
    )


def _price_threshold_keys(mode: str) -> tuple[str, str]:
    return (f"{mode}_buy_threshold", f"{mode}_sell_threshold")


def _schema_required_or_optional(key: str, default: Any | None) -> Any:
    if default is None:
        return vol.Required(key)
    return vol.Required(key, default=default)


def _schema_optional(key: str, default: Any | None = None) -> Any:
    if default in (None, ""):
        return vol.Optional(key)
    return vol.Optional(key, default=default)


def _build_entity_mapping_schema(defaults: Mapping[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            _schema_required_or_optional(CONF_PV_POWER_ENTITY, defaults.get(CONF_PV_POWER_ENTITY)): _entity_selector("sensor"),
            _schema_required_or_optional(CONF_BATTERY_SOC_ENTITY, defaults.get(CONF_BATTERY_SOC_ENTITY)): _entity_selector("sensor"),
            _schema_required_or_optional(CONF_BATTERY_POWER_ENTITY, defaults.get(CONF_BATTERY_POWER_ENTITY)): _entity_selector("sensor"),
            _schema_required_or_optional(CONF_GRID_POWER_ENTITY, defaults.get(CONF_GRID_POWER_ENTITY)): _entity_selector("sensor"),
            _schema_required_or_optional(CONF_BUY_PRICE_ENTITY, defaults.get(CONF_BUY_PRICE_ENTITY)): _entity_selector("sensor"),
            _schema_required_or_optional(CONF_SELL_PRICE_ENTITY, defaults.get(CONF_SELL_PRICE_ENTITY)): _entity_selector("sensor"),
            _schema_required_or_optional(CONF_EV_CONNECTED_ENTITY, defaults.get(CONF_EV_CONNECTED_ENTITY)): _entity_selector("binary_sensor"),
            _schema_required_or_optional(CONF_EV_SOC_ENTITY, defaults.get(CONF_EV_SOC_ENTITY)): _entity_selector("sensor"),
            _schema_required_or_optional(CONF_EVSE_SET_CURRENT_ENTITY, defaults.get(CONF_EVSE_SET_CURRENT_ENTITY)): _entity_selector("number"),
            _schema_required_or_optional(CONF_EVSE_ACTUAL_CURRENT_ENTITY, defaults.get(CONF_EVSE_ACTUAL_CURRENT_ENTITY)): _entity_selector("sensor"),
            _schema_required_or_optional(CONF_GRID_POWER_LIMIT_W, defaults.get(CONF_GRID_POWER_LIMIT_W, 1000)): _number_selector(1000, 50000, UnitOfPower.WATT),
        }
    )


def _build_optional_schema(defaults: Mapping[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            _schema_optional(CONF_OBC_SET_CURRENT_ENTITY, defaults.get(CONF_OBC_SET_CURRENT_ENTITY)): _entity_selector("number"),
            _schema_optional(CONF_OBC_ACTUAL_CURRENT_ENTITY, defaults.get(CONF_OBC_ACTUAL_CURRENT_ENTITY)): _entity_selector("sensor"),
            _schema_optional(CONF_BUY_PRICE_FORECAST_ATTR, defaults.get(CONF_BUY_PRICE_FORECAST_ATTR)): selector.TextSelector(),
            _schema_optional(CONF_FORECAST_PRICE_KEY, defaults.get(CONF_FORECAST_PRICE_KEY, "price")): selector.TextSelector(),
            _schema_optional(CONF_FORECAST_START_KEY, defaults.get(CONF_FORECAST_START_KEY, "start")): selector.TextSelector(),
            _schema_optional(CONF_PHASE_COUNT, defaults.get(CONF_PHASE_COUNT, 3)): _number_selector(1, 3),
        }
    )


def _build_battery_schema(defaults: Mapping[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            _schema_required_or_optional(CONF_BATTERY_TIER_50_MAX_DISCHARGE_W, defaults.get(CONF_BATTERY_TIER_50_MAX_DISCHARGE_W, 500)): _number_selector(0, 20000, UnitOfPower.WATT),
            _schema_required_or_optional(CONF_BATTERY_TIER_70_MAX_DISCHARGE_W, defaults.get(CONF_BATTERY_TIER_70_MAX_DISCHARGE_W, 1500)): _number_selector(0, 20000, UnitOfPower.WATT),
            _schema_required_or_optional(CONF_BATTERY_TIER_90_MAX_DISCHARGE_W, defaults.get(CONF_BATTERY_TIER_90_MAX_DISCHARGE_W, 3000)): _number_selector(0, 20000, UnitOfPower.WATT),
            _schema_optional(CONF_FAST_MODE_DISCHARGE_LIMIT_W, defaults.get(CONF_FAST_MODE_DISCHARGE_LIMIT_W)): _number_selector(0, 20000, UnitOfPower.WATT),
        }
    )


def _build_stop_condition_schema(defaults: Mapping[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    schema: dict[Any, Any] = {}
    for mode in AUTO_MODES:
        battery_key, grid_key, buy_key, sell_key, hysteresis_key = _stop_condition_keys(mode)
        schema[_schema_optional(battery_key, defaults.get(battery_key))] = _number_selector(0, 20000, UnitOfPower.WATT)
        schema[_schema_optional(grid_key, defaults.get(grid_key))] = _number_selector(0, 50000, UnitOfPower.WATT)
        schema[_schema_optional(buy_key, defaults.get(buy_key))] = _number_selector(0)
        schema[_schema_optional(sell_key, defaults.get(sell_key))] = _number_selector(0)
        schema[_schema_required_or_optional(hysteresis_key, defaults.get(hysteresis_key, 2))] = _number_selector(1, 10)
    return vol.Schema(schema)


def _build_price_threshold_schema(defaults: Mapping[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    schema: dict[Any, Any] = {}
    for mode in AUTO_MODES:
        buy_key, sell_key = _price_threshold_keys(mode)
        schema[_schema_required_or_optional(buy_key, defaults.get(buy_key, 0.0))] = _number_selector(0)
        schema[_schema_required_or_optional(sell_key, defaults.get(sell_key, 0.0))] = _number_selector(0)
    return vol.Schema(schema)


def _validate_common(data: Mapping[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}

    if float(data.get(CONF_GRID_POWER_LIMIT_W, 0)) <= 0:
        errors[CONF_GRID_POWER_LIMIT_W] = "must_be_positive"

    obc_set = data.get(CONF_OBC_SET_CURRENT_ENTITY)
    obc_actual = data.get(CONF_OBC_ACTUAL_CURRENT_ENTITY)
    if obc_set and not obc_actual:
        errors[CONF_OBC_ACTUAL_CURRENT_ENTITY] = "required_with_obc"

    forecast_attr = data.get(CONF_BUY_PRICE_FORECAST_ATTR)
    if forecast_attr and (not data.get(CONF_FORECAST_PRICE_KEY) or not data.get(CONF_FORECAST_START_KEY)):
        errors[CONF_BUY_PRICE_FORECAST_ATTR] = "forecast_keys_required"

    sensor_entities = {
        data.get(CONF_PV_POWER_ENTITY),
        data.get(CONF_BATTERY_SOC_ENTITY),
        data.get(CONF_BATTERY_POWER_ENTITY),
        data.get(CONF_GRID_POWER_ENTITY),
        data.get(CONF_BUY_PRICE_ENTITY),
        data.get(CONF_SELL_PRICE_ENTITY),
        data.get(CONF_EV_CONNECTED_ENTITY),
        data.get(CONF_EV_SOC_ENTITY),
        data.get(CONF_EVSE_ACTUAL_CURRENT_ENTITY),
        data.get(CONF_OBC_ACTUAL_CURRENT_ENTITY),
    }
    if data.get(CONF_EVSE_SET_CURRENT_ENTITY) in sensor_entities:
        errors[CONF_EVSE_SET_CURRENT_ENTITY] = "must_differ_from_sensors"
    if obc_set and obc_set in sensor_entities:
        errors[CONF_OBC_SET_CURRENT_ENTITY] = "must_differ_from_sensors"

    return errors


class EVChargeControllerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(self, user_input: Mapping[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            self._data.update(user_input)
            errors = _validate_common(self._data)
            if not errors:
                return await self.async_step_optional()
        return self.async_show_form(step_id="user", data_schema=_build_entity_mapping_schema(self._data), errors=errors)

    async def async_step_optional(self, user_input: Mapping[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            self._data.update(user_input)
            errors = _validate_common(self._data)
            if not errors:
                return await self.async_step_battery()
        return self.async_show_form(step_id="optional", data_schema=_build_optional_schema(self._data), errors=errors)

    async def async_step_battery(self, user_input: Mapping[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            self._data.update(user_input)
            errors = _validate_common(self._data)
            if not errors:
                return self.async_create_entry(title="EV Charge Controller", data=self._data)
        return self.async_show_form(step_id="battery", data_schema=_build_battery_schema(self._data), errors=errors)

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return EVChargeControllerOptionsFlow(config_entry)


class EVChargeControllerOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry
        self._data: dict[str, Any] = {**config_entry.data, **config_entry.options}

    async def async_step_init(self, user_input: Mapping[str, Any] | None = None):
        return await self.async_step_entity_mapping(user_input)

    async def async_step_entity_mapping(self, user_input: Mapping[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            self._data.update(user_input)
            errors = _validate_common(self._data)
            if not errors:
                return await self.async_step_optional_entities()
        return self.async_show_form(step_id="entity_mapping", data_schema=_build_entity_mapping_schema(self._data), errors=errors)

    async def async_step_optional_entities(self, user_input: Mapping[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            self._data.update(user_input)
            errors = _validate_common(self._data)
            if not errors:
                return await self.async_step_battery()
        return self.async_show_form(step_id="optional_entities", data_schema=_build_optional_schema(self._data), errors=errors)

    async def async_step_battery(self, user_input: Mapping[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            self._data.update(user_input)
            errors = _validate_common(self._data)
            if not errors:
                return await self.async_step_stop_conditions()
        return self.async_show_form(step_id="battery", data_schema=_build_battery_schema(self._data), errors=errors)

    async def async_step_stop_conditions(self, user_input: Mapping[str, Any] | None = None):
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_price_thresholds()
        return self.async_show_form(step_id="stop_conditions", data_schema=_build_stop_condition_schema(self._data))

    async def async_step_price_thresholds(self, user_input: Mapping[str, Any] | None = None):
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title="", data=self._data)
        return self.async_show_form(step_id="price_thresholds", data_schema=_build_price_threshold_schema(self._data))
