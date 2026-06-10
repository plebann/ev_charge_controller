# Constitution

## Purpose

This project delivers a Home Assistant integration, distributed through HACS, that controls EV charging in a deterministic, explainable, and fully local way.

The integration optimizes charging behavior using only data exposed through Home Assistant entities, especially:

- PV production
- home battery state of charge
- battery charge and discharge power
- grid import and export power
- energy buy and sell prices, including forward price attributes exposed by Home Assistant
- EV connection state
- EV state of charge

The project exists to minimize the effective cost of EV charging while limiting unnecessary charging from the home battery and preserving safe, predictable operation.

Effective charging cost includes both:

- direct cost of imported grid energy
- opportunity cost of consuming energy that could otherwise be sold to the grid

---

## Core Principles

### I. Home Assistant Native First

The integration MUST follow Home Assistant-native architecture and UX patterns.

This includes:

- standard config flow and options flow
- Home Assistant-native entities and controls
- diagnostics support
- predictable entity behavior
- packaging and repository structure compatible with HACS expectations

The integration SHOULD feel like a normal Home Assistant integration, not like an automation script wrapped in entities.

### II. Local-Only Runtime

The integration MUST operate entirely locally.

It MUST NOT depend on cloud services, vendor APIs, or remote optimization engines during runtime.

All runtime inputs MUST come from Home Assistant entities selected by the user.

If required data is unavailable, the integration MUST degrade safely instead of inferring missing state from external sources.

### III. Safety and Predictability Before Optimization

Safety and predictable behavior take precedence over all optimization goals.

The integration MUST NEVER:

- exceed the configured grid connection power limit
- violate configured technical or electrical limits
- increase charging power using missing, stale, invalid, or contradictory data
- oscillate charging current aggressively
- silently fight manual user control

When optimization conflicts with safety, safety wins.

When optimization conflicts with predictability, predictability wins.

### IV. Deterministic and Explainable Decisions

The integration MUST use a deterministic rule engine that is easy to inspect, test, and debug.

For the same inputs and configuration, it MUST produce the same decision.

Each decision SHOULD be explainable through entities, attributes, logs, or diagnostics, including the active mode, key inputs, applied constraints, and the reason for the chosen current.

Opaque or black-box control logic is out of scope.

### V. Battery Protection Before Opportunistic Charging

The integration MUST avoid unnecessary discharge of the home battery for EV charging.

It SHOULD preserve home battery energy when SoC is low or when discharge would violate configured protection thresholds.

It SHOULD prefer using PV surplus when export value is unattractive relative to configured sell-price thresholds.

It MAY charge from the grid when the selected mode allows it and when current price conditions are favorable relative to configured buy-price thresholds.

### VI. Mode-Dependent Optimization

After safety, predictability, and explainability, optimization goals MUST depend on the selected mode.

The integration MUST support at least these modes:

- balanced
- fast
- economical
- manual

Mode intent:

- **balanced** prioritizes sensible cost control, battery protection, and stable charging behavior
- **fast** prioritizes EV charging progress while still respecting configured price limits and home battery protection
- **economical** prioritizes the lowest effective charging cost
- **manual** disables automatic control actions

Priorities related to battery protection, charging cost, PV surplus usage, and charging speed MAY be reordered by mode, but core safety principles MUST remain fixed.

---

## Runtime Safety Rules

### VII. Safe Handling of Missing, Stale, or Invalid Data

If required data is missing, stale, invalid, or contradictory, the integration MUST degrade safely.

Safe behavior:

- the integration MUST NOT start charging based on incomplete data
- if charging is already active, the integration MUST reduce charging to the minimum automatic value instead of continuing aggressive optimization
- if the user has taken manual control, the integration MUST respect that choice and avoid overriding it

The system SHOULD clearly expose why automation is limited, paused, or degraded.

### VIII. Manual Override Always Wins

If the user manually changes charging behavior through Home Assistant, the EVSE, or the EV, the integration MUST switch to manual mode and stop making automatic control changes.

Manual mode MUST be explicit and observable.

Returning from manual mode to automatic operation SHOULD require deliberate user action.

The integration MUST NOT silently retake control.

### IX. Stable Control, No Power Flapping

The integration MUST evaluate charging conditions every minute.

It MUST analyze smoothed signals using both:

- 1-minute averages
- 5-minute averages

Control logic MUST avoid unnecessary oscillation in charging current.

Stability rules:

- the minimum current adjustment step is 1 A
- adjustments SHOULD happen only when justified by rule evaluation
- charging SHOULD NOT be stopped and restarted unnecessarily
- current increases MUST respect EVSE, EV, and grid connection constraints
- current decreases MUST favor safe and stable behavior over reactive oscillation

The project MUST prefer stable control over hyper-reactive control.

---

## Technical Constraints

### X. Physical and Configurable Limits Are Hard Limits

The integration MUST enforce the following technical constraints:

- EVSE current can be controlled in 1 A increments
- EVSE allowed current range is 6 A to 16 A
- the EV can additionally reduce charging current down to 5 A
- the configured grid connection power limit MUST never be exceeded

The grid connection power limit MUST be a user-configurable option.

Site and hardware limits MUST be treated as hard constraints, never as optimization hints.

If a requested increase would exceed any hard limit, that increase MUST be capped or denied.

### XI. Configuration-Driven Site Protection

Site-specific protection behavior MUST be configurable.

This includes, at minimum:

- grid connection power limit
- home battery protection thresholds
- buy and sell price thresholds or threshold multipliers
- entity selection
- mode-related behavior settings where appropriate

Defaults SHOULD be conservative and safe.

---

## Engineering Principles

### XII. Testability Is a Core Requirement

Decision logic MUST be structured for deterministic unit testing.

Rules, thresholds, fail-safe behavior, and mode behavior SHOULD be testable independently from Home Assistant entity wiring.

The architecture SHOULD separate:

- data acquisition
- rule evaluation
- actuation
- diagnostics and explanation

### XIII. Diagnostics and Observability Are Required

The integration MUST provide enough visibility to understand:

- which inputs were used
- which values were smoothed or averaged
- which mode is active
- which constraints were applied
- why a specific current was selected
- why automation was limited, paused, or switched to manual mode

A user SHOULD be able to understand system behavior without reading the source code.

### XIV. Public HACS Quality, Even for a Personal Project

Although the integration is initially built for a personal installation, it MUST meet the quality bar expected from a public HACS project.

This means prioritizing:

- maintainable code structure
- safe defaults
- understandable configuration
- explicit diagnostics
- documented behavior
- robust handling of edge cases
- compatibility with normal Home Assistant workflows

A personal-use origin MUST NOT justify fragile or unclear implementation.

---

## Non-Goals

The project does NOT aim to:

- use external cloud optimization services
- depend on vendor-specific remote EV or EVSE APIs
- implement opaque predictive AI charging control
- optimize using unavailable or unverifiable data
- sacrifice explainability for theoretical efficiency gains

---

## Priority Order

The default project priority order is:

1. Home Assistant-native design and HACS quality
2. Safety and predictability
3. Deterministic, explainable decisions
4. Home battery protection
5. Charging cost minimization
6. PV surplus utilization
7. EV charging time optimization

Priorities 4 through 7 MAY change by charging mode, but priorities 1 through 3 MUST remain fixed.

---

## Final Rule

If there is uncertainty between a more aggressive optimization and a safer, clearer, more predictable action, the integration MUST choose the safer and more predictable action.
