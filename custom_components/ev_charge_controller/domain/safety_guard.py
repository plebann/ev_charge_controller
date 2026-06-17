from __future__ import annotations

from math import isnan

from custom_components.ev_charge_controller.domain.models import DataQuality, HardLimits, TelemetrySnapshot


REQUIRED_FIELDS = {
    "pv_power_w": "pv_power",
    "battery_soc_pct": "battery_soc",
    "battery_power_w": "battery_power",
    "grid_power_w": "grid_power",
    "buy_price": "buy_price",
    "sell_price": "sell_price",
    "ev_connected": "ev_connected",
    "ev_soc_pct": "ev_soc",
    "evse_actual_current_a": "evse_actual_current",
}


def evaluate(snapshot: TelemetrySnapshot, hard_limits: HardLimits) -> DataQuality:
    missing: list[str] = []
    stale: list[str] = []
    contradiction_detected = False

    for attr_name, logical_name in REQUIRED_FIELDS.items():
        value = getattr(snapshot, attr_name)
        if value is None:
            missing.append(logical_name)
            continue
        if isinstance(value, float) and isnan(value):
            missing.append(logical_name)
        age = snapshot.entity_ages_s.get(logical_name)
        if age is not None and age > hard_limits.stale_data_timeout_s:
            stale.append(logical_name)

    if snapshot.battery_soc_pct is not None and not 0 <= snapshot.battery_soc_pct <= 100:
        contradiction_detected = True
    if snapshot.ev_soc_pct is not None and not 0 <= snapshot.ev_soc_pct <= 100:
        contradiction_detected = True
    if snapshot.ev_connected is False and snapshot.charging_active:
        contradiction_detected = True

    if missing:
        return DataQuality(False, missing_entities=missing, contradiction_detected=contradiction_detected, reason=f"missing:{','.join(missing)}")
    if stale:
        return DataQuality(False, stale_entities=stale, contradiction_detected=contradiction_detected, reason=f"stale:{','.join(stale)}")
    if contradiction_detected:
        return DataQuality(False, contradiction_detected=True, reason="contradictory")
    return DataQuality(True)
