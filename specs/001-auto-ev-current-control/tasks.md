# Tasks: Automatyczne sterowanie pradem ladowania EV (MVP)

**Input**: Design documents from `/specs/001-auto-ev-current-control/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Nie dodano osobnych zadan testowych, bo specification nie wymaga TDD ani jawnego test-first workflow. Walidacja i testability pozostaja uwzglednione w zadaniach implementacyjnych i polish.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Utworzenie szkieletu integracji HACS i podstawowego zaplecza developerskiego.

- [X] T001 Create integration bootstrap package in custom_components/ev_charge_controller/__init__.py
- [X] T002 Create HACS integration manifest in custom_components/ev_charge_controller/manifest.json
- [X] T003 [P] Create repository HACS metadata in hacs.json
- [X] T004 [P] Create development dependencies file in requirements-dev.txt
- [X] T005 [P] Create pytest configuration in pytest.ini
- [X] T006 [P] Create unit test harness fixture in tests/unit/conftest.py
- [X] T007 [P] Create integration test harness fixture in tests/integration/conftest.py
- [X] T008 [P] Create Home Assistant UI strings scaffold in custom_components/ev_charge_controller/strings.json

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T009 Create shared constants and config keys in custom_components/ev_charge_controller/const.py
- [X] T010 [P] Define shared enums and dataclasses in custom_components/ev_charge_controller/domain/models.py
- [X] T011 [P] Create domain package exports in custom_components/ev_charge_controller/domain/__init__.py
- [X] T012 Implement config entry setup and platform forwarding in custom_components/ev_charge_controller/__init__.py
- [X] T013 Implement initial config flow and options flow schema in custom_components/ev_charge_controller/config_flow.py
- [X] T014 Implement coordinator shell and telemetry collection pipeline in custom_components/ev_charge_controller/coordinator.py
- [X] T015 [P] Implement charging mode select entity scaffold with restore-state behavior in custom_components/ev_charge_controller/entities/mode_select.py
- [X] T016 [P] Implement HA actuator service abstraction in custom_components/ev_charge_controller/domain/actuator.py
- [X] T017 [P] Implement diagnostics scaffold in custom_components/ev_charge_controller/diagnostics.py
- [X] T018 [P] Create automation status sensor scaffold in custom_components/ev_charge_controller/entities/status_sensor.py
- [X] T019 [P] Create commanded current sensor scaffold in custom_components/ev_charge_controller/entities/current_sensor.py

**Checkpoint**: Foundation ready - user story implementation can now begin.

---

## Phase 3: User Story 1 - Bezpieczne automatyczne sterowanie co minute (Priority: P1) 🎯 MVP

**Goal**: Dostarczyc przewidywalna automatyke balanced-mode, ktora co minute wyznacza prad ladowania, respektuje hard-limity, fail-safe, battery protection i OBC throttle 5 A.

**Independent Test**: Skonfigurowac komplet encji, uruchomic tryb balanced i potwierdzic, ze system co minute wyznacza prad bez przekraczania limitu przylacza oraz przechodzi do fail-safe przy zlej jakosci danych.

- [X] T020 [P] [US1] Implement SafetyGuard for stale, missing, and contradictory data in custom_components/ev_charge_controller/domain/safety_guard.py
- [X] T021 [P] [US1] Implement SignalSmoother with 1-minute and 5-minute windows in custom_components/ev_charge_controller/domain/signal_smoother.py
- [X] T022 [P] [US1] Implement tiered battery protection evaluator in custom_components/ev_charge_controller/domain/battery_protection.py
- [X] T023 [P] [US1] Implement stop condition evaluator with OR logic and hysteresis counter in custom_components/ev_charge_controller/domain/stop_condition.py
- [X] T024 [US1] Implement balanced-mode RuleEngine with hard-limit clamping, fail-safe, and OBC 5 A throttle behavior in custom_components/ev_charge_controller/domain/rule_engine.py
- [X] T025 [US1] Wire balanced automation pipeline, EVSE/OBC commands, and fail-safe transitions in custom_components/ev_charge_controller/coordinator.py
- [X] T026 [US1] Publish balanced-mode automation states and decision reasons in custom_components/ev_charge_controller/entities/status_sensor.py
- [X] T027 [US1] Publish effective commanded current state for active, stopped, and fail-safe paths in custom_components/ev_charge_controller/entities/current_sensor.py

**Checkpoint**: User Story 1 should be fully functional as the MVP baseline.

---

## Phase 4: User Story 2 - Sterowanie zalezne od trybu pracy (Priority: P2)

**Goal**: Rozszerzyc automatyke o fast, economical i manual, wraz z per-mode thresholdami i analiza cen biezacych oraz przyszlych.

**Independent Test**: Na tych samych danych wejsciowych przelaczac tryby balanced, fast, economical i manual, a nastepnie potwierdzic, ze decyzje odzwierciedlaja priorytety trybu bez naruszenia safety.

- [X] T028 [US2] Extend options flow with per-mode stop thresholds, price thresholds, and fast-mode discharge configuration in custom_components/ev_charge_controller/config_flow.py
- [X] T029 [US2] Extend RuleEngine with fast, economical, and manual branches plus mode-specific priority ordering in custom_components/ev_charge_controller/domain/rule_engine.py
- [X] T030 [US2] Parse future-price attributes and mode-specific threshold inputs during coordinator telemetry updates in custom_components/ev_charge_controller/coordinator.py
- [X] T031 [US2] Expose active mode, price constraints, and stop-threshold sources in custom_components/ev_charge_controller/entities/status_sensor.py
- [X] T032 [US2] Finalize persisted mode transitions and explicit user-controlled mode switching in custom_components/ev_charge_controller/entities/mode_select.py

**Checkpoint**: User Stories 1 and 2 should both work, with mode-specific behavior independently demonstrable.

---

## Phase 5: User Story 3 - Manual override i wyjasnialnosc decyzji (Priority: P3)

**Goal**: Dodac wykrywanie manual override, jawne przejscie do manual i pelna explainability przez encje, atrybuty oraz diagnostyke.

**Independent Test**: Recznie zmienic zachowanie ladowania przez HA, EVSE lub EV i potwierdzic, ze integracja przechodzi do manual, zatrzymuje automatyczne zmiany i wystawia kompletne uzasadnienie ostatniej decyzji.

- [X] T033 [P] [US3] Implement override detector for expected-vs-actual effective current comparison in custom_components/ev_charge_controller/domain/override_detector.py
- [X] T034 [US3] Integrate manual override switching and restart-safe recovery semantics in custom_components/ev_charge_controller/coordinator.py
- [X] T035 [US3] Enrich decision explanation payload with override flags, hysteresis state, and active constraints in custom_components/ev_charge_controller/entities/status_sensor.py
- [X] T036 [US3] Implement config entry diagnostics dump for config, telemetry, smoothed values, and decisions in custom_components/ev_charge_controller/diagnostics.py
- [X] T037 [US3] Finalize commanded-current sensor behavior for manual and stopped states in custom_components/ev_charge_controller/entities/current_sensor.py

**Checkpoint**: All user stories should now be independently functional and observable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final alignment across documentation, metadata, and developer workflow.

- [X] T038 [P] Update installation, configuration, and operating-mode documentation in README.md
- [X] T039 [P] Finalize HACS quality metadata and integration fields in custom_components/ev_charge_controller/manifest.json
- [X] T040 [P] Finalize user-facing copy for config flow and entity descriptions in custom_components/ev_charge_controller/strings.json
- [X] T041 Run quickstart walkthrough validation against implemented structure in specs/001-auto-ev-current-control/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup**: No dependencies - can start immediately.
- **Phase 2: Foundational**: Depends on Phase 1 - blocks all user stories.
- **Phase 3: User Story 1**: Depends on Phase 2.
- **Phase 4: User Story 2**: Depends on Phase 2 and extends shared runtime introduced for US1.
- **Phase 5: User Story 3**: Depends on Phase 2 and can be validated independently after override and diagnostics integration.
- **Phase 6: Polish**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: No dependency on other user stories; this is the MVP slice.
- **US2 (P2)**: Reuses coordinator and rule engine surfaces introduced in US1, but remains independently testable as mode-selection behavior.
- **US3 (P3)**: Reuses shared coordinator and entity surfaces, but remains independently testable through override detection and diagnostics.

### Within Each User Story

- Shared models/config surfaces before coordinator integrations.
- Domain evaluators before RuleEngine orchestration.
- RuleEngine before entity-state publication.
- Coordinator integration before story-level polish.

---

## Parallel Opportunities

- **Setup**: T003-T008 can run in parallel after T001-T002.
- **Foundational**: T010, T011, T015, T016, T017, T018, and T019 can run in parallel once T009 is in place.
- **US1**: T020-T023 can run in parallel before T024.
- **US3**: T033 can proceed in parallel with diagnostics work in T036.
- **Polish**: T038-T040 can run in parallel.

---

## Parallel Example: User Story 1

```bash
# Parallel domain implementation for US1:
T020 Implement SafetyGuard in custom_components/ev_charge_controller/domain/safety_guard.py
T021 Implement SignalSmoother in custom_components/ev_charge_controller/domain/signal_smoother.py
T022 Implement tiered battery protection evaluator in custom_components/ev_charge_controller/domain/battery_protection.py
T023 Implement stop condition evaluator in custom_components/ev_charge_controller/domain/stop_condition.py
```

## Parallel Example: Foundational Phase

```bash
# Parallel scaffolding after constants are defined:
T010 Define shared enums and dataclasses in custom_components/ev_charge_controller/domain/models.py
T015 Implement charging mode select entity scaffold in custom_components/ev_charge_controller/entities/mode_select.py
T016 Implement HA actuator service abstraction in custom_components/ev_charge_controller/domain/actuator.py
T017 Implement diagnostics scaffold in custom_components/ev_charge_controller/diagnostics.py
T018 Create automation status sensor scaffold in custom_components/ev_charge_controller/entities/status_sensor.py
T019 Create commanded current sensor scaffold in custom_components/ev_charge_controller/entities/current_sensor.py
```

## Parallel Example: User Story 2

```bash
# Parallel follow-up after core balanced automation exists:
T028 Extend options flow with per-mode stop thresholds in custom_components/ev_charge_controller/config_flow.py
T032 Finalize persisted mode transitions in custom_components/ev_charge_controller/entities/mode_select.py
```

## Parallel Example: User Story 3

```bash
# Parallel observability and override work for US3:
T033 Implement override detector in custom_components/ev_charge_controller/domain/override_detector.py
T036 Implement config entry diagnostics dump in custom_components/ev_charge_controller/diagnostics.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Validate balanced-mode automation, fail-safe, hard-limit enforcement, and OBC 5 A throttle behavior.
5. Stop and review before adding mode-specific behavior.

### Incremental Delivery

1. Deliver US1 as the safe balanced-mode MVP.
2. Add US2 to introduce fast/economical/manual behavior without changing safety precedence.
3. Add US3 to make manual override and diagnostics explicit and debuggable.
4. Finish with Phase 6 for HACS-quality metadata and documentation alignment.

### Team Strategy

1. One developer completes Setup + Foundational.
2. Then split by slices:
   - Developer A: US1 domain evaluators and coordinator integration.
   - Developer B: US2 mode logic and options flow.
   - Developer C: US3 override detection and diagnostics.
3. Merge Polish tasks after all story slices are validated.

---

## Notes

- Wszystkie taski zachowuja wymagany format checklisty i zawieraja jawne sciezki plikow.
- Zadania `[P]` sa oznaczone tylko tam, gdzie mozna pracowac na roznych plikach bez oczekiwania na niezakonczony task zaleznosci.
- MVP scope pozostaje ograniczony do jednego feature’a opisanego w specification.
- Safety, determinism, explainability i local-only runtime pozostaja nadrzedne wobec optymalizacji w kazdej fazie.