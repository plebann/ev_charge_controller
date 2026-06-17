# Contract: HA Entity Interface

**Type**: Integration-exposed entity contract  
**Feature**: Automatyczne sterowanie pradem ladowania EV (MVP)

---

## Entities Exposed by Integration

### 1. Charging Mode Select

| Property | Value |
|----------|-------|
| Platform | `select` |
| Entity ID pattern | `select.ev_charge_controller_mode` |
| Options | `balanced`, `fast`, `economical`, `manual` |
| restore_last_state | `True` |
| Write | User-facing (Lovelace, automations) |
| Read | Coordinator reads every cycle |

**State transitions**: Any option writable by user. Coordinator writes `manual` on override detection. 

**Attributes**: none beyond standard HA select attributes.

---

### 2. Automation Status Sensor

| Property | Value |
|----------|-------|
| Platform | `sensor` |
| Entity ID pattern | `sensor.ev_charge_controller_status` |
| State values | `active`, `limited`, `stopped`, `fail_safe`, `manual` |
| Device class | none |
| Update frequency | Every coordinator cycle (1 min) |

**Attributes**:

| Attribute | Type | Description |
|-----------|------|-------------|
| `mode` | `str` | Active charging mode |
| `reason` | `str` | Human-readable decision reason |
| `target_current_a` | `int \| None` | Commanded effective current |
| `evse_current_a` | `int \| None` | Commanded EVSE current |
| `obc_current_a` | `int \| None` | Commanded OBC current (None if not used) |
| `data_quality` | `str` | `ok` / `stale:<entity>` / `missing:<entity>` / `contradictory` |
| `stop_condition_active` | `bool` | Whether stop condition is currently triggered |
| `hysteresis_counter` | `int` | Current consecutive breach count |
| `battery_tier` | `str \| None` | Active battery protection tier (e.g., `"<50%"`) |
| `override_detected` | `bool` | Whether manual override was just detected |
| `applied_constraints` | `list[str]` | Active constraints list |
| `key_inputs` | `dict` | Key input values used for decision |
| `last_decision_at` | `str` | ISO timestamp of last decision |

---

### 3. Commanded Current Number (read-only display)

| Property | Value |
|----------|-------|
| Platform | `sensor` |
| Entity ID pattern | `sensor.ev_charge_controller_commanded_current` |
| Unit | `A` |
| Device class | `current` |
| State | Effective commanded current (A) or `unknown` if stopped/manual |

---

## Diagnostic Platform

Exposed via HA Diagnostics (`diagnostics` platform). Provides sanitized dump of:
- Current `ChargingConfig` (entity IDs masked to logical names)
- Latest `TelemetrySnapshot` values
- Latest `SmoothedMetricsWindow` values
- Latest `ControlDecision` and `DecisionExplanation`
- Current `StopConditionState`
- Current mode and `AutomationStatus`

Sensitive values (entity_ids, prices) are NOT redacted — this is a local-only integration.

---

## EVSE / OBC Write Contract

The integration writes to user-configured entities via HA service calls.

### EVSE Set Current

```
service: number.set_value
target:
  entity_id: <evse_set_current_entity from config>
data:
  value: <int: 6–16>
```

**Preconditions**:
- Value MUST be in range [evse_min_current_a, evse_max_current_a]
- Called only when automation_status != manual
- Called only when ev_connected == True

### OBC Set Current (optional)

```
service: number.set_value
target:
  entity_id: <obc_set_current_entity from config>
data:
  value: 5
```

**Preconditions**:
- Called ONLY when effective target current = 5 A (OBC throttle mode)
- Called only when obc_set_current_entity is configured
- When target >= 6 A, OBC entity is NOT written (EVSE-only control)

### Override Detection Read Contract

After each write, on next cycle the coordinator reads:
- `evse_actual_current_entity` state → `float` (A)
- `obc_actual_current_entity` state → `float` (A) if configured

Comparison: `|actual - expected_effective| > override_delta_a (1A)` → switch to manual.
