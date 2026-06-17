# Research: Automatyczne sterowanie pradem ladowania EV (MVP)

**Phase**: 0 — Pre-design research  
**Date**: 2026-06-14  
**Feature**: [spec.md](spec.md)

---

## R-001: Python i wersja Home Assistant

**Decision**: Python ≥3.12, Home Assistant ≥2024.1.0  
**Rationale**: Aktualne wersje HA (2024.x / 2025.x) wymagają Pythona 3.12+. Testy integracji używają `pytest-homeassistant-custom-component` kompatybilnego z tą wersją. Nowsze API DataUpdateCoordinator oraz type hints z `from __future__ import annotations` działają dobrze na 3.12.  
**Alternatives considered**: Python 3.11 — odrzucone, niekompatybilne z najnowszym HA runtime.

---

## R-002: Cykliczna ewaluacja co minutę — DataUpdateCoordinator

**Decision**: Użyć `DataUpdateCoordinator` z `update_interval=timedelta(minutes=1)`.  
**Rationale**: DataUpdateCoordinator jest HA-native pattern do periodicznie odświeżanych danych. Obsługuje setup, teardown, error-handling i propagację stanu do encji bez potrzeby pisania własnych timerów. Umożliwia asynchroniczne odczytywanie encji i wywoływanie logiki decyzyjnej w jednym miejscu.  
**Alternatives considered**: `async_track_time_interval` — możliwe, ale mniej standardowe; brak wbudowanego retry i error propagation pattern.

---

## R-003: Obliczanie średnich kroczących bez zewnętrznych bibliotek

**Decision**: `collections.deque(maxlen=N)` do przechowywania ostatnich N wartości; średnia liczona jako `sum(deque)/len(deque)`.  
**Rationale**: HA integracje mają restrykcje dotyczące zależności. `numpy` i `scipy` nie są dostępne w standardowym środowisku HA. `deque(maxlen=60)` dla okna 1-minutowego (próbkowanie co sekundę) lub `deque(maxlen=5)` gdy coordinator odpytuje co minutę. Dla okna 5-minutowego: `deque(maxlen=5)` cykli minutowych.  
**Alternatives considered**: `statistics.mean()` — może być użyty na liście z deque; nie wymaga dodatkowych zależności.

---

## R-004: Struktura HACS i wymagania jakościowe

**Decision**: Standard HACS custom integration layout z `manifest.json`, `hacs.json`, tłumaczeniami w `strings.json` i platformami HA (`sensor`, `select`, `number`).  
**Rationale**: HACS wymaga konkretnej struktury: `custom_components/<domain>/manifest.json` z polem `version`, `iot_class: local_polling`, `domain`, `name`, `documentation`, `issue_tracker`. Brak tych pól blokuje instalację przez HACS.  
**Key manifest fields**:
  - `iot_class`: `"local_polling"` (cykliczne odpytywanie, bez cloud)
  - `integration_type`: `"hub"` (zarządza encjami jako hub lokalny)
  - `config_flow`: `true`
  - `quality_scale`: docelowo `"silver"` (config flow, tests, no deprecated patterns)

---

## R-005: Persystencja trybu pracy po restarcie HA

**Decision**: `SelectEntity` z atrybutem `restore_last_state = True` lub dziedziczenie z `RestoreEntity`.  
**Rationale**: HA umożliwia encjom zachowanie stanu po restarcie przez mechanizm `last_state`. `SelectEntity` implementujący `async_added_to_hass()` z wywołaniem `await self.async_get_last_state()` odtwarza ostatnio wybrany tryb. Brak potrzeby własnej bazy danych ani external storage.  
**Alternatives considered**: `input_select` helper — odrzucone, to byłby anti-pattern (użytkownik zarządza encją poza integracją). Persistowany stan encji integracji to HA-native rozwiązanie.

---

## R-006: Typy encji HA dla sterowania i diagnostyki

**Decision**:
| Encja | Typ HA | Cel |
|-------|--------|-----|
| Tryb pracy | `SelectEntity` | Wybór: balanced/fast/economical/manual; restore_state |
| Zadany prąd EVSE | `NumberEntity` (read) | Wyświetlenie aktualnie zadanego prądu |
| Status automatyki | `SensorEntity` | Stan: active/limited/stopped/fail-safe/manual |
| Diagnostyka decyzji | `SensorEntity` z atrybutami | Wyjaśnienie: tryb, powód, dane wejściowe, ograniczenia |
| Aktywny prąd | odczyt z encji użytkownika | Prąd raportowany przez EVSE/OBC |

**Rationale**: HA-native typy. `SelectEntity` dla trybu zapewnia UX zgodny z HA (Lovelace). `SensorEntity` z rozbudowanymi atrybutami to standard dla diagnostyki. Odczyt prądu z encji wskazanej przez użytkownika eliminuje vendor-lock.

---

## R-007: Testowanie logiki domenowej niezależnie od HA

**Decision**: Logika domenowa (`domain/`) w czystych klasach Python bez zależności od `homeassistant.*`. Testy jednostkowe przez `pytest` bez `pytest-homeassistant-custom-component`. Testy integracji z HA przez `pytest-homeassistant-custom-component`.  
**Rationale**: Zgodnie z constitution (XII) logika decyzyjna musi być testowalna niezależnie od HA. Separacja `domain/` od `entities/` i `coordinator.py` pozwala testować RuleEngine, SafetyGuard, StopConditionEvaluator i SignalSmoother czystymi unit testami z `pytest` bez konieczności mockowania całego HA.  
**Alternatives considered**: Mockowanie HA we wszystkich testach — odrzucone; zbyt wysokie koszty utrzymania i brak gwarancji determinizmu.

---

## R-008: Sposób zapisu do encji EVSE/OBC

**Decision**: `hass.services.async_call("number", "set_value", {...})` lub `hass.states.async_set()` — **NIE**. Właściwe: `hass.services.async_call()` na serwisie encji docelowej lub bezpośredni zapis przez `entity_registry` → wywołanie `async_set_native_value()` na encji. Preferowane: service call `number.set_value` z `entity_id` wskazanym w konfiguracji.  
**Rationale**: Zapis przez service call jest idiomatic HA. Umożliwia też łatwą detekcję override (porównanie stanu encji po zapisie). Nie wymaga bezpośredniego dostępu do obiektu encji EVSE (vendor-agnostic).  
**Alternatives considered**: Bezpośredni zapis przez `hass.states.async_set()` — odrzucone; omija logikę encji i może powodować niespójności.

---

## R-009: Detekcja sprzecznych danych (bilans mocy)

**Decision**: Prosta reguła spójności: `|P_pv + P_battery + P_grid - P_load| > threshold_W` gdzie threshold jest konfigurowalny (domyślnie 500 W dla danych chwilowych). Jeśli sprzeczność wykryta → fail-safe.  
**Rationale**: Pełna walidacja bilansu wymaga wszystkich składowych. Przy braku danych o obciążeniu domu można zrezygnować z tej walidacji i skupić się na prostszych regułach: import i eksport sieci jednocześnie > 0 to zawsze błąd (mutual exclusivity). To deterministyczna, testowalnie jednoznaczna reguła.  
**Alternatives considered**: Sprawdzanie samego znaku import/eksport — uproszczone, może być wystarczające dla MVP.

---

## R-010: Obsługa cen przyszłych z atrybutów encji

**Decision**: Odczyt atrybutu encji cenowej (np. `forecast` lub `prices`) jako listy dict. Filtrowanie po kluczu `datetime` i wartości ceny. Brak zewnętrznych API — wszystko przez HA state/attributes.  
**Rationale**: Popularne integracje cenowe (Nordpool, Tibber lokalny, Energa) wystawiają ceny przyszłe w atrybutach encji. Integracja powinna być agnostyczna wobec formatu — użytkownik konfiguruje klucz atrybutu zawierający listę cen. Gdy atrybut niedostępny — graceful degradation do ceny bieżącej.  
**Alternatives considered**: Wymuszenie konkretnego formatu encji cenowej — odrzucone; zbyt vendor-specific.

---

## Otwarte kwestie do potwierdzenia przed implementacją

| ID | Kwestia | Domyślne założenie |
|----|---------|-------------------|
| OQ-001 | Format atrybutu cen przyszłych — jakie klucze konfigurować (nazwa atrybutu, klucze datetime/price wewnątrz listy) | Konfigurowalne w options flow; domyślnie `prices` z kluczami `start` i `price` |
| OQ-002 | Jak HA raportuje rzeczywisty prąd EVSE — czy jako `current` sensor czy jako state encji number? | Użytkownik wskazuje encję raportującą rzeczywisty prąd (osobna od encji sterującej) |
| OQ-003 | Czy OBC wystawia osobny sensor prądu ładowania do detekcji override? | Użytkownik wskazuje opcjonalnie encję raportującą prąd OBC |
| OQ-004 | Minimalny zakres testów wymagany dla HACS quality_scale silver | Co najmniej: unit testy logiki domenowej + config flow tests |
