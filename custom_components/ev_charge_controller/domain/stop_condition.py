from __future__ import annotations

from custom_components.ev_charge_controller.domain.models import SmoothedMetricsWindow, StopConditionConfig, StopConditionState, TelemetrySnapshot


def _pick(primary: float | None, fallback: float | None) -> float | None:
    return primary if primary is not None else fallback


def evaluate(
    snapshot: TelemetrySnapshot,
    smoothed: SmoothedMetricsWindow,
    config: StopConditionConfig,
    previous_breach_count: int,
) -> StopConditionState:
    battery_power = _pick(smoothed.battery_power_5min_w, _pick(smoothed.battery_power_1min_w, snapshot.battery_power_w))
    grid_power = _pick(smoothed.grid_power_5min_w, _pick(smoothed.grid_power_1min_w, snapshot.grid_power_w))
    buy_price = _pick(smoothed.buy_price_5min, _pick(smoothed.buy_price_1min, snapshot.buy_price))
    sell_price = snapshot.sell_price

    battery_discharge_breached = bool(
        config.battery_discharge_limit_w is not None
        and battery_power is not None
        and battery_power < 0
        and abs(battery_power) > config.battery_discharge_limit_w
    )
    grid_import_breached = bool(
        config.grid_import_limit_w is not None
        and grid_power is not None
        and grid_power > config.grid_import_limit_w
    )
    buy_price_breached = bool(
        config.buy_price_limit is not None
        and buy_price is not None
        and buy_price > config.buy_price_limit
    )
    sell_price_breached = bool(
        config.sell_price_min is not None
        and sell_price is not None
        and sell_price < config.sell_price_min
    )

    any_breached = any(
        [battery_discharge_breached, grid_import_breached, buy_price_breached, sell_price_breached]
    )
    breach_count = previous_breach_count + 1 if any_breached else 0
    return StopConditionState(
        any_threshold_breached=any_breached,
        battery_discharge_breached=battery_discharge_breached,
        grid_import_breached=grid_import_breached,
        buy_price_breached=buy_price_breached,
        sell_price_breached=sell_price_breached,
        consecutive_breach_count=breach_count,
        stop_active=any_breached and breach_count >= config.hysteresis_cycles,
    )
