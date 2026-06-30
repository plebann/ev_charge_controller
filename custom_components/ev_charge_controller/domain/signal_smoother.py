from __future__ import annotations

from collections import deque
from statistics import mean

from custom_components.ev_charge_controller.domain.models import SmoothedMetricsWindow, TelemetrySnapshot


class SignalSmoother:
    def __init__(self) -> None:
        self._windows: dict[str, deque[float]] = {
            "grid_power": deque(maxlen=5),
            "battery_power": deque(maxlen=5),
            "pv_power": deque(maxlen=5),
            "buy_price": deque(maxlen=5),
        }

    def update(self, snapshot: TelemetrySnapshot) -> SmoothedMetricsWindow:
        mapping = {
            "grid_power": snapshot.grid_power_w,
            "battery_power": snapshot.battery_power_w,
            "pv_power": snapshot.pv_power_w,
            "buy_price": snapshot.buy_price,
        }
        for key, value in mapping.items():
            if value is not None:
                self._windows[key].append(float(value))

        def latest(name: str) -> float | None:
            if not self._windows[name]:
                return None
            return self._windows[name][-1]

        def averaged(name: str) -> float | None:
            if len(self._windows[name]) < 2:
                return None
            return mean(self._windows[name])

        return SmoothedMetricsWindow(
            grid_power_1min_w=latest("grid_power"),
            grid_power_5min_w=averaged("grid_power"),
            battery_power_1min_w=latest("battery_power"),
            battery_power_5min_w=averaged("battery_power"),
            pv_power_1min_w=latest("pv_power"),
            pv_power_5min_w=averaged("pv_power"),
            buy_price_1min=latest("buy_price"),
            buy_price_5min=averaged("buy_price"),
        )
