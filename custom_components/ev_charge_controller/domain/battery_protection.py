from __future__ import annotations

from math import floor

from custom_components.ev_charge_controller.domain.models import (
    BatteryProtectionConfig,
    BatteryProtectionTier,
    ChargingMode,
    HardLimits,
    TelemetrySnapshot,
)


def active_tier(snapshot: TelemetrySnapshot, config: BatteryProtectionConfig) -> BatteryProtectionTier | None:
    if snapshot.battery_soc_pct is None:
        return None
    matching = [tier for tier in config.tiers if snapshot.battery_soc_pct < tier.soc_threshold_pct]
    if not matching:
        return None
    return sorted(matching, key=lambda tier: tier.soc_threshold_pct)[0]


def max_current_from_battery(
    snapshot: TelemetrySnapshot,
    config: BatteryProtectionConfig,
    hard_limits: HardLimits,
    mode: ChargingMode,
) -> tuple[int | None, str | None]:
    tier = active_tier(snapshot, config)
    if tier is None:
        return None, None

    limit_w = tier.max_discharge_power_w
    if mode == ChargingMode.FAST and config.fast_mode_discharge_limit_w is not None:
        limit_w = config.fast_mode_discharge_limit_w
    if mode == ChargingMode.FAST and config.fast_mode_discharge_limit_w is None:
        return None, f"<{int(tier.soc_threshold_pct)}%"

    current_discharge = abs(snapshot.battery_power_w) if snapshot.battery_power_w is not None and snapshot.battery_power_w < 0 else 0.0
    remaining_headroom_w = max(limit_w - current_discharge, 0.0)
    amps = floor(remaining_headroom_w / (230 * hard_limits.phase_count))
    return max(amps, 0), f"<{int(tier.soc_threshold_pct)}%"
