# Implementation Plan: Automatyczne sterowanie pradem ladowania EV (MVP)

**Branch**: `001-create-spec-branch` | **Date**: 2026-06-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from [specs/001-auto-ev-current-control/spec.md](spec.md)

## Summary

Integracja Home Assistant steruje prądem ładowania EV dla jednej instalacji (1 EV, 1 EVSE, 1 magazyn, 1 przyłącze). Co minutę odczytuje dane z encji HA wskazanych przez użytkownika, przepuszcza je przez deterministyczny rule engine, i zapisuje docelowy prąd do encji sterującej EVSE (oraz opcjonalnie OBC). Decyzje są explainable przez atrybuty encji diagnostycznej. Bezpieczeństwo jest egzekwowane przez nieomijalne warstwy (SafetyGuard, BatteryProtection, hard limits) przed jakąkolwiek optymalizacją.

---

## Technical Context

**Language/Version**: Python 3.12+ (wymagane przez HA ≥2024.1.0)
**Primary Dependencies**: `homeassistant` (core framework, DataUpdateCoordinator, entity types, config flow); `pytest-homeassistant-custom-component` (testy)
**Storage**: HA ConfigEntry (konfiguracja), HA entity state + restore_last_state (tryb pracy); in-memory (deque dla okien czasowych, licznik histerezy)
**Testing**: `pytest`, `pytest-homeassistant-custom-component`, `pytest-asyncio`; logika domenowa testowana pure Python bez HA
**Target Platform**: Home Assistant (local, Linux/Docker/HAOS); HACS distribution
**Project Type**: HACS custom integration (`iot_class: local_polling`)
**Performance Goals**: Decyzja wyznaczana w <5s od startu cyklu minutowego
**Constraints**: Brak zależności od chmury; brak numpy/scipy; całość w `custom_components/ev_charge_controller/`
**Scale/Scope**: 1 instalacja, 1 EV, 1 EVSE; ~10 wymaganych encji wejściowych

---

## Constitution Check

*GATE: Przejście przed Phase 0. Ponowna ocena po Phase 1.*

| Zasada | Weryfikacja | Status |
|--------|------------|--------|
| I. HA Native First | DataUpdateCoordinator, ConfigFlow, SelectEntity, SensorEntity, diagnostics platform | ✅ |
| II. Local-Only Runtime | Brak external API; wszystkie dane z encji HA; brak chmury w runtime | ✅ |
| III. Safety > Optimization | SafetyGuard i hard limits wykonywane przed RuleEngine; fail-safe 6A niekonfigurowalny | ✅ |
| IV. Deterministic & Explainable | Rule engine z explicitnymi regułami; DecisionExplanation w atrybutach encji; pure-function design | ✅ |
| V. Battery Protection | Tiered SoC protection (50/70/90%) z limitami mocy; oddzielny limit dla trybu fast | ✅ |
| VI. Mode-Dependent Optimization | 4 tryby; progi stop condition i cenowe per tryb; priorytety egzekwowane przez RuleEngine | ✅ |
| VII. Safe Data Handling | Staleness 60s; contradiction detection; fail-safe przy złych danych; graceful degradation cen przyszłych | ✅ |
| VIII. Manual Override Wins | Override detector na każdym cyklu; automatyczny switch do MANUAL; powrót tylko przez explicit user action | ✅ |
| IX. Stable Control | Okna 1-min + 5-min; histereza stop condition (N≥2 cykli); próg zmiany ~700W/1A | ✅ |
| X. Physical Limits are Hard | Grid limit nigdy nie przekraczany; EVSE 6-16A range; OBC 5A throttle — wszystko egzekwowane przed aktuacją | ✅ |
| XI. Configuration-Driven | Wszystkie progi i limity w ConfigEntry; defaults konserwatywne (stop condition domyślnie wyłączony) | ✅ |
| XII. Testability | domain/ bez zależności od HA; pure unit tests dla każdego komponentu logiki | ✅ |
| XIII. Diagnostics Required | SensorEntity z DecisionExplanation; HA diagnostics platform; logi per cykl | ✅ |
| XIV. HACS Quality | manifest.json z quality_scale, config flow, tests, strings.json, no deprecated APIs | ✅ |

**GATE RESULT: PASS** — Brak naruszeń. Implementacja może przebiegać.

---

## Project Structure

### Documentation (this feature)

```text
specs/001-auto-ev-current-control/
├── plan.md              # Ten plik
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── ha-config-flow.md
│   └── ha-entity-interface.md
└── tasks.md             # Phase 2 output (/speckit.tasks — nie tworzony tutaj)
```

### Source Code

```text
custom_components/
└── ev_charge_controller/
    ├── __init__.py              # async_setup_entry, async_unload_entry
    ├── manifest.json            # HACS: iot_class=local_polling, config_flow=true
    ├── hacs.json                # HACS repository metadata
    ├── config_flow.py           # 3-step ConfigFlow + OptionsFlow
    ├── coordinator.py           # EVChargeCoordinator(DataUpdateCoordinator)
    ├── const.py                 # DOMAIN, defaults, config keys
    ├── diagnostics.py           # async_get_config_entry_diagnostics
    ├── strings.json             # UI strings
    ├── domain/
    │   ├── __init__.py
    │   ├── models.py            # Dataclasses: wszystkie encje z data-model.md
    │   ├── safety_guard.py      # SafetyGuard: staleness, contradiction, quality
    │   ├── signal_smoother.py   # SignalSmoother: deque-based 1min+5min averages
    │   ├── override_detector.py # OverrideDetector: commanded vs actual delta
    │   ├── stop_condition.py    # StopConditionEvaluator: 4 sub-thresholds + hysteresis
    │   ├── battery_protection.py# BatteryProtectionEvaluator: tiered SoC rules
    │   └── rule_engine.py       # RuleEngine: mode-aware current decision
    └── entities/
        ├── __init__.py
        ├── mode_select.py       # ChargingModeSelect(SelectEntity + RestoreEntity)
        ├── status_sensor.py     # AutomationStatusSensor(SensorEntity)
        └── current_sensor.py   # CommandedCurrentSensor(SensorEntity)

tests/
├── unit/
│   ├── conftest.py              # Pure Python fixtures (no HA)
│   ├── test_safety_guard.py
│   ├── test_signal_smoother.py
│   ├── test_override_detector.py
│   ├── test_stop_condition.py
│   ├── test_battery_protection.py
│   └── test_rule_engine.py
└── integration/
    ├── conftest.py              # HA hass fixture
    ├── test_config_flow.py
    ├── test_coordinator.py
    └── test_entities.py
```

**Structure Decision**: Single-project HACS custom integration layout. Domain logic isolated in `domain/` as pure Python (no HA imports) for independent unit testing. HA integration code in `entities/`, `coordinator.py`, `config_flow.py`.

---

## Architecture

### Component Responsibilities

#### EVChargeCoordinator (`coordinator.py`)
- Rozszerza `DataUpdateCoordinator` z `update_interval=timedelta(minutes=1)`
- Orkiestruje pełny cykl decyzyjny w `_async_update_data()`
- Zarządza stanem między cyklami: `last_commanded_evse_a`, `last_commanded_obc_a`, `stop_condition_breach_count`, `signal_deques`
- Czyta aktywny tryb z `ChargingModeSelect` entity
- Po decyzji: aktualizuje encje i wywołuje `Actuator`
- Przy restarcie: odtwarza tryb z encji (RestoreEntity); reset licznika histerezy do 0 (safe)

#### SafetyGuard (`domain/safety_guard.py`)
- Wejście: `TelemetrySnapshot`, `HardLimits`
- Wyjście: `DataQuality`
- Sprawdza: wartość każdej wymaganej encji, wiek < 60s, brak sprzeczności (import+eksport>0 jednocześnie)
- Czysta funkcja — deterministyczna dla tych samych wejść

#### SignalSmoother (`domain/signal_smoother.py`)
- Stan: `dict[str, deque(maxlen=5)]` — okno 5 ostatnich wartości minutowych per sygnał
- `1min` = ostatnia wartość w deque; `5min` = mean(deque)
- Gdy `len(deque) < 2` → sygnały wygładzone = None (za mało danych po restarcie)

#### OverrideDetector (`domain/override_detector.py`)
- Wejście: `TelemetrySnapshot`, `last_commanded_evse_a`, `last_commanded_obc_a`, `HardLimits`
- Wyjście: `bool`
- Reguła: `|actual - expected_effective| > 1A` gdzie `expected_effective = 5A` gdy OBC aktywny i cel=5A, else `last_commanded_evse_a`
- Gdy `last_commanded = None` (pierwsza pętla po restarcie) → zawsze False (brak override)

#### StopConditionEvaluator (`domain/stop_condition.py`)
- Stan (w Coordinator): `consecutive_breach_count: int`
- OR po 4 sub-progach na danych wygładzonych (5-min avg; fallback: 1-min)
- Histereza: inkrementuje licznik przy naruszeniu; reset do 0 gdy brak naruszenia; `stop_active = (count >= hysteresis_cycles)`

#### BatteryProtectionEvaluator (`domain/battery_protection.py`)
- Wybiera aktywny tier na podstawie `battery_soc_pct`
- Tryb fast: używa `fast_mode_discharge_limit_w` (lub brak ograniczenia gdy None)
- Konwertuje limit mocy rozładowania na max. prąd: `max_a = floor(battery_discharge_limit_w / (230V * phases))`
- Gdy `battery_power_w >= 0` (ładowanie magazynu) → brak ograniczenia

#### RuleEngine (`domain/rule_engine.py`)
Kolejność reguł (priority order, nieomijalna):

1. **MANUAL** → brak akcji, `AutomationStatus.MANUAL`
2. **FAIL_SAFE** (data invalid + charging active) → 6A, `fail_safe`
3. **NO_START** (data invalid + not charging) → brak akcji, `fail_safe`
4. **STOP_CONDITION** (`stop_active=True`) → zatrzymaj, `stopped`
5. **GRID_LIMIT** → ogranicz prąd do nieprzekraczania `grid_power_limit_w`
6. **BATTERY_PROTECTION** → ogranicz do `max_current_from_battery`
7. **PRICE_THRESHOLD** (mode-specific) → ogranicz/zatrzymaj przy złej cenie
8. **STABILITY** (zmiana < ~700W equiv. = zmiana < 1A) → utrzymaj bieżący prąd
9. **MODE_OPTIMIZE** → wybierz optymalny prąd dla trybu
10. **CLAMP** → ogranicz do [6, 16] A

Każda reguła dokumentuje powód w `DecisionExplanation`. Pierwsza reguła, która decyduje — wygrywa.

#### Actuator (`domain/actuator.py`)
- Wywołuje `hass.services.async_call("number", "set_value", ...)` do EVSE/OBC
- Przy cel=5A (OBC throttle): EVSE=6A, OBC=5A
- Przy cel≥6A: tylko EVSE; OBC nie dostaje polecenia
- Przy `stopped`: ustawia EVSE na `evse_min_current_a` (6A)
- Przy `manual`/`no_start`: brak service call

---

## Data Flow

```
HA Entity States
      │
      ▼
TelemetryCollector.collect() → TelemetrySnapshot
      │
      ▼
SignalSmoother.update() → SmoothedMetricsWindow
      │
      ▼
SafetyGuard.evaluate() → DataQuality
  ├─ invalid + no charge → ControlDecision(NO_START)
  ├─ invalid + charging  → ControlDecision(FAIL_SAFE 6A)
  └─ valid ──────────────────────────────────┐
                                             ▼
                                OverrideDetector.check()
                                    override? → YES → MANUAL mode, ControlDecision(MANUAL)
                                        │ NO
                                        ▼
                                mode == MANUAL? → YES → ControlDecision(MANUAL)
                                        │ NO
                                        ▼
                                StopConditionEvaluator.evaluate() → StopConditionState
                                        │
                                BatteryProtectionEvaluator.evaluate() → max_current_a
                                        │
                                RuleEngine.decide() → ControlDecision
                                        │
                                Actuator.apply() → service calls to EVSE/OBC
                                        │
                                Update HA Entities (mode_select, status_sensor, current_sensor)
```

---

## State Model

### Persistent (survives HA restart)

| State | Storage | Mechanism |
|-------|---------|-----------|
| Active charging mode | `ChargingModeSelect` entity state | `restore_last_state = True` |
| User configuration | HA `ConfigEntry` | config/options flow |

### In-Memory (reset on restart)

| State | Initial | Notes |
|-------|---------|-------|
| `last_commanded_evse_a` | `None` | Skip override detection on first cycle |
| `last_commanded_obc_a` | `None` | Skip override detection on first cycle |
| `stop_condition_breach_count` | `0` | Requires N fresh cycles before stop triggers |
| `signal_deques` | empty | Rebuilds over 5 cycles; averages = None until then |

---

## Configuration Defaults

| Parameter | Default | Type |
|-----------|---------|------|
| `fail_safe_current_a` | `6` | Niekonfigurowalny |
| `stale_data_timeout_s` | `60` | Niekonfigurowalny |
| `override_delta_a` | `1` | Niekonfigurowalny |
| `obc_throttle_current_a` | `5` | Niekonfigurowalny |
| `evse_min_current_a` | `6` | Niekonfigurowalny (standard) |
| `evse_max_current_a` | `16` | Niekonfigurowalny (standard) |
| Stop condition sub-progi | `None` (wyłączone) | Konserwatywny default |
| `hysteresis_cycles` | `2` | Konfigurowalny |
| `buy_threshold` | `0.0` | Konfigurowalny per mode |
| `sell_threshold` | `0.0` | Konfigurowalny per mode |
| `battery_tier_50_max_discharge_w` | `500` | Konfigurowalny |
| `battery_tier_70_max_discharge_w` | `1500` | Konfigurowalny |
| `battery_tier_90_max_discharge_w` | `3000` | Konfigurowalny |

---

## Safety Enforcement Layers

```
Layer 1: SafetyGuard (data quality) — cannot be disabled
Layer 2: Grid Power Limit (hard limit) — configurable value, cannot be bypassed
Layer 3: EVSE Range Clamp [6, 16A] — cannot be disabled
Layer 4: Battery Protection (tiered SoC) — configurable limits
Layer 5: Stop Condition (economic/protective) — configurable per mode, disabled by default
```

---

## Manual Override Detection and Recovery

**Detection** (every cycle after data validation):
1. `expected_effective_a`: 5A if OBC throttle mode, else `last_commanded_evse_a`
2. If `|actual - expected| > 1A` AND `last_commanded != None` → override detected
3. Write `MANUAL` to mode entity → persists via restore_last_state
4. Update `status_sensor` attributes; log at WARNING level

**Recovery**: User explicitly changes mode entity from `MANUAL` to balanced/fast/economical. No automatic return.

---

## Explainability Implementation

Every `ControlDecision` writes `DecisionExplanation` to `status_sensor` attributes each cycle:

```yaml
mode: economical
reason: "Stop condition active: grid import 4200W exceeds limit 3000W (2/2 cycles)"
target_current_a: null
evse_current_a: null
obc_current_a: null
data_quality: ok
stop_condition_active: true
hysteresis_counter: 2
battery_tier: "<70%"
override_detected: false
applied_constraints:
  - "battery_discharge_limited: <70% tier, max 1500W"
  - "stop_condition: grid_import_breached"
key_inputs:
  battery_soc_pct: 65.3
  grid_power_1min_w: 4200.0
  buy_price: 0.82
  sell_price: 0.45
last_decision_at: "2026-06-14T14:23:00+02:00"
```

---

## Testing Strategy

### Unit Tests (domain/ — pure Python, no HA)

| Test file | Coverage |
|-----------|---------|
| `test_safety_guard.py` | Stale (60s), missing, contradiction, all-valid |
| `test_signal_smoother.py` | deque, 1/5-min avg, insufficient data, warm-up |
| `test_override_detector.py` | Delta ≤1A, delta >1A, OBC throttle mode, last_commanded=None |
| `test_stop_condition.py` | Each sub-threshold, OR logic, hysteresis counter, mode-specific values |
| `test_battery_protection.py` | Each SoC tier, fast mode limit, no-limit, charging battery |
| `test_rule_engine.py` | All 10 priority layers; parameterized mode scenarios |

### Integration Tests (pytest-homeassistant-custom-component)

| Test file | Coverage |
|-----------|---------|
| `test_config_flow.py` | Full config flow, validation errors, options flow |
| `test_coordinator.py` | Full cycle, restart recovery, mode restore |
| `test_entities.py` | SelectEntity restore, SensorEntity attributes, override → mode switch |

---

## Technical Risks and Open Questions

### Risks

| ID | Risk | Mitigation |
|----|------|-----------|
| R-001 | EVSE entity type varies between manufacturers | Make service call type configurable; document supported patterns |
| R-002 | `number.set_value` fails silently if entity unavailable | try/except; log ERROR; coordinator continues |
| R-003 | OBC actual current not reliably updated | Fall back to EVSE-only override detection if OBC entity stale >60s |
| R-004 | Future price attribute format varies by integration | Make attribute name and key names configurable (OQ-001) |
| R-005 | Grid power sensor sign convention varies by inverter | Document expected convention; add config flow validation hint |
| R-006 | `restore_last_state` returns None on first install | Handle None → default to `balanced` |

### Design Decisions (confirm before tasks)

| ID | Decision | Assumption |
|----|---------|-----------|
| DD-001 | Przy `stopped`: EVSE dostaje 6A czy poprzednia wartość | Ustawia 6A (min) — bezpieczniejsze |
| DD-002 | fail_safe vs stop_condition gdy oba aktywne | fail_safe (layer 1) > stop_condition (layer 4) |
| DD-003 | Restart w trybie MANUAL zachowuje MANUAL | Tak — restore_last_state (zamierzone) |
| DD-004 | Liczba faz dla konwersji W→A | 3 fazy domyślnie (konfigurowalne) — do potwierdzenia |

### Open Questions (from research.md)

| ID | Question | When |
|----|---------|------|
| OQ-001 | Format atrybutu cen przyszłych (klucze) | Przed tasks |
| OQ-002 | Czy EVSE raportuje prąd jako state czy atrybut | Przed tasks |
| OQ-003 | Czy OBC wystawia osobny sensor prądu | Przed tasks |
| OQ-004 | Minimalny zakres testów dla HACS silver | Przed tasks |

---

## Constitution Check (Post-Design)

| Zasada | Status po designie |
|--------|--------------------|
| I. HA Native | ✅ DataUpdateCoordinator, ConfigFlow, SelectEntity, SensorEntity, diagnostics |
| II. Local-Only | ✅ Żaden komponent nie wywołuje zewnętrznych URL |
| III. Safety > Opt. | ✅ Warstwy 1-3 przed logiką optymalizacji 7-9 w RuleEngine |
| IV. Deterministic | ✅ Każdy komponent domain/ to czysta funkcja lub deterministyczny automat |
| V-XIV. Remaining | ✅ Wszystkie weryfikacje jak w Pre-Design gate |

**POST-DESIGN GATE: PASS**
