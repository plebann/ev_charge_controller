# Data Model: Automatyczne sterowanie pradem ladowania EV (MVP)

**Phase**: 1 — Design  
**Date**: 2026-06-14  
**Feature**: [spec.md](spec.md)

---

## Entities Overview

```
ChargingConfig
    └── EntityMapping (1:1)
    └── HardLimits (1:1)
    └── BatteryProtectionConfig (1:1)
    └── StopConditionConfig (1:1 per mode)
    └── PriceThresholdConfig (1:1 per mode)

TelemetrySnapshot
    └── RawReadings (1:1)
    └── DataQualityFlags (1:1)

SmoothedMetricsWindow
    └── OneMinuteAverage (per signal)
    └── FiveMinuteAverage (per signal)

ControlDecision
    └── SafetyState (1:1)
    └── StopConditionState (1:1)
    └── DecisionExplanation (1:1)
```

---

## ChargingConfig

Utrwalona konfiguracja użytkownika ładowana z ConfigEntry HA.

**Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `entity_mapping` | `EntityMapping` | Mapowanie nazw logicznych na entity_id HA |
| `hard_limits` | `HardLimits` | Niezmienne limity techniczne i bezpieczeństwa |
| `battery_protection` | `BatteryProtectionConfig` | Trójstopniowe progi SoC i mocy rozładowania |
| `stop_condition` | `dict[ChargingMode, StopConditionConfig]` | Sub-progi zatrzymania per tryb |
| `price_thresholds` | `dict[ChargingMode, PriceThresholdConfig]` | Progi cenowe per tryb |
| `active_mode` | `ChargingMode` | Odczytywany z encji trybu (nie z ConfigEntry) |

### EntityMapping

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pv_power` | `str` | Yes | entity_id — produkcja PV (W) |
| `battery_soc` | `str` | Yes | entity_id — SoC magazynu (%) |
| `battery_power` | `str` | Yes | entity_id — moc ład./rozład. magazynu (W, + = ładowanie) |
| `grid_power` | `str` | Yes | entity_id — import/eksport sieci (W, + = import) |
| `buy_price` | `str` | Yes | entity_id — aktualna cena zakupu (PLN/kWh) |
| `sell_price` | `str` | Yes | entity_id — aktualna cena sprzedaży (PLN/kWh) |
| `buy_price_forecast_attr` | `str` | No | Nazwa atrybutu encji buy_price z listą cen przyszłych |
| `forecast_price_key` | `str` | No | Klucz ceny w każdym elemencie listy (domyślnie `"price"`) |
| `forecast_start_key` | `str` | No | Klucz datetime w każdym elemencie listy (domyślnie `"start"`) |
| `ev_connected` | `str` | Yes | entity_id — stan podłączenia EV (binary_sensor) |
| `ev_soc` | `str` | Yes | entity_id — SoC EV (%) |
| `evse_set_current` | `str` | Yes | entity_id — encja sterująca prądem EVSE (number) |
| `evse_actual_current` | `str` | Yes | entity_id — encja raportująca rzeczywisty prąd EVSE (sensor) |
| `obc_set_current` | `str \| None` | No | entity_id — encja sterująca OBC (number), None = EVSE-only |
| `obc_actual_current` | `str \| None` | No | entity_id — encja raportująca prąd OBC (sensor) |
| `charging_mode_entity` | `str` | Yes | entity_id — encja SelectEntity trybu pracy (własna) |

### HardLimits

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `grid_power_limit_w` | `float` | — | Skonfigurowany limit mocy przyłącza (W); MUSI być ustawiony |
| `evse_min_current_a` | `int` | `6` | Min. prąd EVSE (A); niekonfigurowalny (standard) |
| `evse_max_current_a` | `int` | `16` | Max. prąd EVSE (A) |
| `obc_throttle_current_a` | `int` | `5` | Prąd OBC przy dławieniu (A); niekonfigurowalny |
| `stale_data_timeout_s` | `int` | `60` | Próg stale data (s); niekonfigurowalny |
| `fail_safe_current_a` | `int` | `6` | Prąd fail-safe (A); niekonfigurowalny |
| `override_delta_a` | `int` | `1` | Próg detekcji override (A); niekonfigurowalny |

### BatteryProtectionConfig

Trzy poziomy SoC z osobnymi limitami mocy rozładowania per tryb.

| Field | Type | Description |
|-------|------|-------------|
| `tiers` | `list[BatteryProtectionTier]` | Dokładnie 3 tiers: <50%, <70%, <90% |
| `fast_mode_discharge_limit_w` | `float \| None` | Limit mocy rozładowania w trybie fast (None = brak ograniczenia) |

**BatteryProtectionTier**:

| Field | Type | Description |
|-------|------|-------------|
| `soc_threshold_pct` | `float` | Próg SoC (50.0 / 70.0 / 90.0) |
| `max_discharge_power_w` | `float` | Max. moc rozładowania dla ładowania EV (W) w trybach balanced/economical |

### StopConditionConfig (per mode)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `battery_discharge_limit_w` | `float \| None` | `None` | Sub-próg: moc rozładowania magazynu (W); None = wyłączony |
| `grid_import_limit_w` | `float \| None` | `None` | Sub-próg: moc importu sieci (W); None = wyłączony |
| `buy_price_limit` | `float \| None` | `None` | Sub-próg: cena zakupu (PLN/kWh); None = wyłączony |
| `sell_price_min` | `float \| None` | `None` | Sub-próg: min. cena eksportu (PLN/kWh); None = wyłączony |
| `hysteresis_cycles` | `int` | `2` | Liczba kolejnych cykli naruszenia przed zatrzymaniem |

### PriceThresholdConfig (per mode)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `buy_threshold` | `float` | `0.0` | Max. cena zakupu do ładowania (PLN/kWh); 0 = zawsze kupuj |
| `sell_threshold` | `float` | `0.0` | Min. cena eksportu dla rezygnacji z ładowania; 0 = zawsze ładuj |

---

## ChargingMode

```python
class ChargingMode(str, Enum):
    BALANCED = "balanced"
    FAST = "fast"
    ECONOMICAL = "economical"
    MANUAL = "manual"
```

**State transitions**:

```
BALANCED / FAST / ECONOMICAL
    → MANUAL  : override_detected OR user_selects_manual
    
MANUAL
    → BALANCED / FAST / ECONOMICAL : user_explicit_selection_only
```

---

## TelemetrySnapshot

Spójny zestaw odczytów z jednego cyklu minutowego.

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | `datetime` | Czas odczytu |
| `pv_power_w` | `float \| None` | Produkcja PV (W) |
| `battery_soc_pct` | `float \| None` | SoC magazynu (%) |
| `battery_power_w` | `float \| None` | Moc magazynu (W; + = ładowanie, - = rozładowanie) |
| `grid_power_w` | `float \| None` | Moc sieciowa (W; + = import, - = eksport) |
| `buy_price` | `float \| None` | Aktualna cena zakupu (PLN/kWh) |
| `sell_price` | `float \| None` | Aktualna cena sprzedaży (PLN/kWh) |
| `future_prices` | `list[FuturePrice]` | Lista cen przyszłych (może być pusta) |
| `ev_connected` | `bool \| None` | Czy EV podłączone |
| `ev_soc_pct` | `float \| None` | SoC EV (%) |
| `evse_actual_current_a` | `float \| None` | Rzeczywisty prąd EVSE (A) |
| `obc_actual_current_a` | `float \| None` | Rzeczywisty prąd OBC (A); None jeśli OBC nieskonfigurowany |
| `entity_ages_s` | `dict[str, float]` | Wiek każdej encji w sekundach od ostatniej aktualizacji |

**FuturePrice**:

| Field | Type | Description |
|-------|------|-------------|
| `start` | `datetime` | Początek okresu |
| `price` | `float` | Cena zakupu (PLN/kWh) |

### DataQuality

Wynik walidacji TelemetrySnapshot.

| Field | Type | Description |
|-------|------|-------------|
| `is_valid` | `bool` | True jeśli wszystkie wymagane dane są świeże i spójne |
| `missing_entities` | `list[str]` | Encje bez wartości |
| `stale_entities` | `list[str]` | Encje starsze niż 60s |
| `contradiction_detected` | `bool` | True jeśli wykryto import i eksport jednocześnie |
| `reason` | `str` | Czytelny opis problemu (do logów i diagnostyki) |

---

## SmoothedMetricsWindow

Okna kroczące dla kluczowych sygnałów.

| Field | Type | Description |
|-------|------|-------------|
| `grid_power_1min_w` | `float \| None` | Średnia 1-min mocy sieciowej |
| `grid_power_5min_w` | `float \| None` | Średnia 5-min mocy sieciowej |
| `battery_power_1min_w` | `float \| None` | Średnia 1-min mocy magazynu |
| `battery_power_5min_w` | `float \| None` | Średnia 5-min mocy magazynu |
| `pv_power_1min_w` | `float \| None` | Średnia 1-min produkcji PV |
| `pv_power_5min_w` | `float \| None` | Średnia 5-min produkcji PV |
| `buy_price_1min` | `float \| None` | Średnia 1-min ceny zakupu |
| `buy_price_5min` | `float \| None` | Średnia 5-min ceny zakupu |

Implementacja: `deque(maxlen=5)` cykli minutowych per sygnał.  
Wartość 1-min = ostatni element; wartość 5-min = `mean(deque)`.  
Gdy `len(deque) < min_samples` (domyślnie 2) → `None` (niewystarczające dane).

---

## ControlDecision

Wynik pojedynczego cyklu decyzyjnego.

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | `datetime` | Czas decyzji |
| `mode` | `ChargingMode` | Aktywny tryb |
| `automation_status` | `AutomationStatus` | active / limited / stopped / fail_safe / manual |
| `target_evse_current_a` | `int \| None` | Docelowy prąd EVSE (A); None jeśli zatrzymane |
| `target_obc_current_a` | `int \| None` | Docelowy prąd OBC (A); None jeśli nie dławimy |
| `effective_current_a` | `int \| None` | Efektywny prąd ładowania (min(evse, obc) jeśli OBC aktywny) |
| `explanation` | `DecisionExplanation` | Pełne uzasadnienie decyzji |

```python
class AutomationStatus(str, Enum):
    ACTIVE = "active"          # Normalny tryb automatyczny
    LIMITED = "limited"        # Ograniczony przez battery/grid/safety
    STOPPED = "stopped"        # Zatrzymany przez stop condition
    FAIL_SAFE = "fail_safe"    # Degradacja do 6A z powodu złej jakości danych
    MANUAL = "manual"          # Tryb manual, brak akcji automatycznych
```

### DecisionExplanation

| Field | Type | Description |
|-------|------|-------------|
| `mode` | `str` | Aktywny tryb słownie |
| `reason` | `str` | Główny powód decyzji |
| `key_inputs` | `dict` | Kluczowe dane wejściowe użyte do decyzji |
| `applied_constraints` | `list[str]` | Lista aktywnych ograniczeń |
| `data_quality` | `str` | Skrót oceny jakości danych |
| `stop_condition_active` | `bool` | Czy stop condition jest aktywny |
| `hysteresis_counter` | `int` | Aktualny licznik cykli naruszenia stopu |
| `battery_tier_active` | `str \| None` | Aktywny tier ochrony magazynu |
| `override_detected` | `bool` | Czy wykryto manual override |

---

## SafetyState

Stan oceny bezpieczeństwa danych i limitów — obliczany przed RuleEngine.

| Field | Type | Description |
|-------|------|-------------|
| `can_increase` | `bool` | Czy można zwiększyć prąd |
| `can_maintain` | `bool` | Czy można utrzymać bieżący prąd |
| `must_reduce` | `bool` | Czy wymagana redukcja (battery tier lub grid limit) |
| `must_fail_safe` | `bool` | Czy wymagany fail-safe 6A (zła jakość danych) |
| `must_stop` | `bool` | Czy wymagane zatrzymanie (stop condition po histerezie) |
| `constraint_reason` | `str` | Opis aktywnego ograniczenia |

---

## StopConditionState

Stan ewaluacji progu zatrzymania z licznikiem histerezy.

| Field | Type | Description |
|-------|------|-------------|
| `any_threshold_breached` | `bool` | Czy którykolwiek sub-próg jest naruszony (OR) |
| `battery_discharge_breached` | `bool` | Sub-próg mocy rozładowania |
| `grid_import_breached` | `bool` | Sub-próg importu sieci |
| `buy_price_breached` | `bool` | Sub-próg ceny zakupu |
| `sell_price_breached` | `bool` | Sub-próg ceny eksportu |
| `consecutive_breach_count` | `int` | Liczba kolejnych cykli naruszenia |
| `stop_active` | `bool` | True gdy `consecutive_breach_count >= hysteresis_cycles` |

Stan `consecutive_breach_count` jest persystowany między cyklami minutowymi w pamięci Coordinator. Resetowany do 0 gdy `any_threshold_breached = False`.

---

## Persistence Summary

| Dane | Gdzie | Mechanizm |
|------|-------|-----------|
| Konfiguracja (encje, limity, progi) | HA ConfigEntry | config_flow + options_flow |
| Aktywny tryb pracy | SelectEntity own state | `restore_last_state = True` |
| Ostatnio zadany prąd EVSE | Coordinator in-memory + HA state | Stan encji number (diagnostics) |
| Licznik histerezy stop condition | Coordinator in-memory | Reset przy restarcie → safe (0 = brak naruszenia) |
| Okna kroczące (deque) | Coordinator in-memory | Reset przy restarcie → odbudowa po 5 cyklach |
| Wyjasnienie ostatniej decyzji | SensorEntity attributes | Odświeżane co cykl |
