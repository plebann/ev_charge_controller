from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.ev_charge_controller import EVChargeControllerConfigEntry


def _serialize(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    return value


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    config_entry = entry if isinstance(entry, ConfigEntry) else None
    coordinator = config_entry.runtime_data if config_entry is not None else None
    return {
        "entry_data": dict(entry.data),
        "entry_options": dict(entry.options),
        "latest_snapshot": getattr(coordinator, "latest_snapshot", {}),
        "latest_smoothed": getattr(coordinator, "latest_smoothed", {}),
        "latest_decision": _serialize(getattr(coordinator, "latest_decision", None)),
        "stop_condition_breach_count": getattr(coordinator, "stop_condition_breach_count", 0),
        "active_mode": getattr(coordinator, "active_mode", None),
    }
