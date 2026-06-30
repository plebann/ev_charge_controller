# EV Charge Controller

Home Assistant custom integration for deterministic local control of EV charging current in a single installation.

The integration reads Home Assistant entities for PV production, battery state, grid import/export, prices, EV connection, and EVSE current. Every minute it derives a charging decision that respects hard limits, fail-safe behavior, battery-protection tiers, stop conditions, and mode-specific priorities.

## Current Scope

- Home Assistant custom integration distributed through HACS.
- Modes: `balanced`, `fast`, `economical`, `manual`.
- Deterministic 1-minute control loop with 1-minute and 5-minute smoothing windows.
- Fail-safe behavior for stale, missing, or contradictory data.
- Tiered battery discharge protection based on battery SoC.
- Per-mode stop thresholds and price thresholds.
- Optional OBC throttle path for effective `5A` charging (`EVSE=6A`, `OBC=5A`).
- Diagnostics and explainable entity attributes for last decision context.

## Repository Layout

```text
custom_components/ev_charge_controller/
	__init__.py
	manifest.json
	config_flow.py
	coordinator.py
	const.py
	diagnostics.py
	sensor.py
	select.py
	strings.json
	domain/
	entities/
tests/
specs/001-auto-ev-current-control/
```

## Configuration Flow

Initial setup is split into three steps:

1. Required entity mapping and site power limit.
2. Optional OBC entity mapping and future-price attribute parsing.
3. Battery-protection tiers and optional fast-mode discharge limit.

Options flow extends that with:

1. Entity mapping review.
2. Optional entities.
3. Battery protection.
4. Per-mode stop conditions.
5. Per-mode price thresholds.

Validation includes:

- `grid_power_limit_w > 0`
- OBC actual-current sensor required when OBC control is configured
- forecast keys required when future-price attribute parsing is configured
- control entities cannot reuse sensor entity ids

## Runtime Behavior

Decision priority is intentionally safety-first:

1. Invalid telemetry blocks charging start or moves active charging to fail-safe `6A`.
2. Manual override detection switches runtime behavior to `manual`.
3. Stop conditions apply OR logic with per-mode hysteresis.
4. Battery-protection tiers clamp allowed current.
5. Grid power limit clamps remaining current.
6. Mode-specific logic chooses the final target.
7. If the result is exactly `5A` and OBC is configured, the integration uses the OBC throttle path.

The integration currently treats `stopped` as a no-command state. It does not yet model a dedicated EVSE start/stop service, so a stop decision clears the commanded-current sensor and suppresses new current writes instead of calling a hard stop action.

## Development

Install dependencies:

```powershell
python -m pip install -r requirements-dev.txt
```

Syntax validation used during implementation:

```powershell
python -m compileall custom_components tests
```

Focused domain checks can be executed directly with Python if the local pytest plugin stack blocks Windows event-loop setup:

```powershell
python -c "from tests.unit.test_domain_logic import test_safety_guard_marks_missing_or_stale_data, test_stop_condition_uses_hysteresis_counter, test_rule_engine_uses_obc_throttle_for_effective_5a, test_override_detector_flags_manual_intervention; test_safety_guard_marks_missing_or_stale_data(); test_stop_condition_uses_hysteresis_counter(); test_rule_engine_uses_obc_throttle_for_effective_5a(); test_override_detector_flags_manual_intervention(); print('domain logic ok')"
```