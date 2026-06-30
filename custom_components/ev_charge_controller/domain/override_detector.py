from __future__ import annotations

from custom_components.ev_charge_controller.domain.models import HardLimits, TelemetrySnapshot


def detect(
    snapshot: TelemetrySnapshot,
    hard_limits: HardLimits,
    last_commanded_evse_a: int | None,
    last_commanded_obc_a: int | None,
) -> bool:
    if last_commanded_evse_a is None:
        return False

    expected_effective = (
        hard_limits.obc_throttle_current_a
        if last_commanded_obc_a == hard_limits.obc_throttle_current_a
        else last_commanded_evse_a
    )

    actual = snapshot.obc_actual_current_a if last_commanded_obc_a is not None and snapshot.obc_actual_current_a is not None else snapshot.evse_actual_current_a
    if actual is None:
        return False
    return abs(actual - expected_effective) > hard_limits.override_delta_a
