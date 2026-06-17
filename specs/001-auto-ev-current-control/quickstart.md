# Quickstart: EV Charge Controller Integration

**Feature**: Automatyczne sterowanie pradem ladowania EV (MVP)  
**Audience**: Developer setting up the integration for the first time

---

## Prerequisites

- Home Assistant ≥2024.1.0
- Python 3.12+ (provided by HA)
- HACS installed in HA
- Local sensors for: PV, battery SoC, battery power, grid power, buy/sell price, EV connection state, EV SoC
- EVSE with controllable HA entity (number/select) for charging current
- Optional: OBC controllable HA entity

---

## Development Setup

```bash
# Clone repository
git clone https://github.com/plebann/ev_charge_controller
cd ev_charge_controller

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or .venv\Scripts\Activate.ps1  # Windows PowerShell

# Install development dependencies
pip install -r requirements-dev.txt
# Includes: pytest, pytest-homeassistant-custom-component, pytest-asyncio

# Run syntax validation
python -m compileall custom_components tests

# Run focused domain assertions without the full pytest plugin harness
python -c "from tests.unit.test_domain_logic import test_safety_guard_marks_missing_or_stale_data, test_stop_condition_uses_hysteresis_counter, test_rule_engine_uses_obc_throttle_for_effective_5a, test_override_detector_flags_manual_intervention; test_safety_guard_marks_missing_or_stale_data(); test_stop_condition_uses_hysteresis_counter(); test_rule_engine_uses_obc_throttle_for_effective_5a(); test_override_detector_flags_manual_intervention(); print('domain logic ok')"
```

---

## Repository Structure

```text
ev_charge_controller/
├── custom_components/
│   └── ev_charge_controller/
│       ├── __init__.py              # Integration setup/teardown
│       ├── manifest.json            # HACS metadata
│       ├── config_flow.py           # Config + options flow
│       ├── coordinator.py           # DataUpdateCoordinator (1-min cycle)
│       ├── const.py                 # Constants, defaults, keys
│       ├── diagnostics.py           # HA diagnostics platform
│       ├── strings.json             # UI strings / translations
│       ├── domain/
│       │   ├── models.py            # Data classes: Config, Telemetry, Decision, etc.
│       │   ├── safety_guard.py      # Data quality + staleness + contradiction check
│       │   ├── signal_smoother.py   # 1-min + 5-min rolling averages (deque)
│       │   ├── override_detector.py # Compare commanded vs reported current
│       │   ├── stop_condition.py    # 4 sub-thresholds + OR + N-cycle hysteresis
│       │   ├── battery_protection.py# Tiered SoC rules + mode-specific limits
│       │   ├── rule_engine.py       # Mode-aware current decision orchestrator
│       │   └── actuator.py          # HA service calls to EVSE/OBC entities
│       └── entities/
│           ├── mode_select.py       # SelectEntity: balanced/fast/economical/manual
│           ├── status_sensor.py     # SensorEntity: automation status + explanation
│           └── current_sensor.py    # SensorEntity: commanded current display
├── tests/
│   ├── unit/                        # Pure Python tests — domain logic only
│   │   └── test_domain_logic.py
│   └── integration/                 # HA harness tests
│       ├── test_config_flow.py
│       ├── test_coordinator.py
│       └── test_entities.py
├── specs/                           # Speckit feature specs
├── requirements-dev.txt
└── hacs.json
```

---

## Key Concepts

### Decision Cycle (every 1 minute)

```
Coordinator.async_update()
  1. TelemetryCollector.collect() → TelemetrySnapshot
  2. SignalSmoother.update(snapshot) → SmoothedMetricsWindow
  3. SafetyGuard.evaluate(snapshot) → DataQuality
     └─ if not valid AND not charging → return: no action
     └─ if not valid AND charging → return: FAIL_SAFE (6A)
   4. OverrideDetector.check(snapshot, last_commanded) → override_detected
     └─ if override_detected → set mode = MANUAL, return
  5. if mode == MANUAL → return: no action
  6. StopConditionEvaluator.evaluate(snapshot, config, mode) → StopConditionState
  7. BatteryProtectionEvaluator.evaluate(snapshot, config, mode) → max_current_from_battery
  8. RuleEngine.decide(snapshot, smoothed, safety, stop, battery, config, mode) → ControlDecision
  9. Actuator.apply(decision, config) → service calls to EVSE/OBC
  10. Update entity states with ControlDecision
```

### Charging Current Range

```
Modes EVSE-only:  6A – 16A  (1A steps)
Mode OBC throttle: 5A only   (EVSE=6A + OBC=5A)
Fail-safe:         6A        (always, regardless of OBC)
Stopped:           no new current command; sensor state clears to None
```

### Safety Priority Order (enforced in code, not just docs)

```
1. Grid power limit (hard, never exceeded)
2. Data quality fail-safe (6A or no-start)
3. Manual override detection (→ MANUAL mode)
4. Battery protection tiers (reduce current)
5. Stop condition (stop charging)
6. Price/cost optimization (mode-dependent)
7. Stability (avoid flapping)
```
