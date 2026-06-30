# Contract: HA Config Flow Interface

**Type**: User-facing configuration contract  
**Feature**: Automatyczne sterowanie pradem ladowania EV (MVP)

---

## Config Flow (initial setup)

Użytkownik przechodzi przez config flow podczas dodawania integracji.

### Step 1: Entity Mapping — Required Entities

**Inputs** (wszystkie wymagane):

| Field | HA Input Type | Description |
|-------|--------------|-------------|
| `pv_power_entity` | `EntitySelector(sensor)` | Sensor produkcji PV (W) |
| `battery_soc_entity` | `EntitySelector(sensor)` | Sensor SoC magazynu (%) |
| `battery_power_entity` | `EntitySelector(sensor)` | Sensor mocy magazynu (W) |
| `grid_power_entity` | `EntitySelector(sensor)` | Sensor mocy sieciowej (W) |
| `buy_price_entity` | `EntitySelector(sensor)` | Sensor ceny zakupu (PLN/kWh) |
| `sell_price_entity` | `EntitySelector(sensor)` | Sensor ceny sprzedaży (PLN/kWh) |
| `ev_connected_entity` | `EntitySelector(binary_sensor)` | Sensor podłączenia EV |
| `ev_soc_entity` | `EntitySelector(sensor)` | Sensor SoC EV (%) |
| `evse_set_current_entity` | `EntitySelector(number)` | Encja sterująca prądem EVSE |
| `evse_actual_current_entity` | `EntitySelector(sensor)` | Sensor rzeczywistego prądu EVSE |
| `grid_power_limit_w` | `NumberSelector(min=1000, max=50000, unit=W)` | Limit mocy przyłącza |

### Step 2: Optional Entities

| Field | HA Input Type | Description |
|-------|--------------|-------------|
| `obc_set_current_entity` | `EntitySelector(number)` (optional) | Encja sterująca OBC |
| `obc_actual_current_entity` | `EntitySelector(sensor)` (optional) | Sensor prądu OBC |
| `buy_price_forecast_attr` | `TextSelector` (optional) | Nazwa atrybutu z listą cen przyszłych |
| `forecast_price_key` | `TextSelector` (optional, default: `"price"`) | Klucz ceny w liście |
| `forecast_start_key` | `TextSelector` (optional, default: `"start"`) | Klucz datetime w liście |

### Step 3: Battery Protection

| Field | HA Input Type | Default | Description |
|-------|--------------|---------|-------------|
| `battery_tier_50_max_discharge_w` | `NumberSelector(min=0, max=20000, unit=W)` | `500` | Max rozładowanie przy SoC <50% |
| `battery_tier_70_max_discharge_w` | `NumberSelector(min=0, max=20000, unit=W)` | `1500` | Max rozładowanie przy SoC <70% |
| `battery_tier_90_max_discharge_w` | `NumberSelector(min=0, max=20000, unit=W)` | `3000` | Max rozładowanie przy SoC <90% |
| `fast_mode_discharge_limit_w` | `NumberSelector` (optional) | `None` | Limit rozładowania w trybie fast (brak = bez ograniczenia) |

---

## Options Flow (reconfiguration)

Wszystkie pola dostępne do edycji po instalacji, plus tryb pracy (choć tryb zarządzany przez SelectEntity). Sekcje:

1. Entity Mapping (jak wyżej)
2. Battery Protection (jak wyżej)
3. Stop Condition per mode (balanced, fast, economical)
4. Price Thresholds per mode

### Stop Condition (per mode: balanced, fast, economical)

| Field | HA Input Type | Default | Description |
|-------|--------------|---------|-------------|
| `{mode}_stop_battery_discharge_w` | `NumberSelector` (optional) | `None` | Sub-próg rozładowania magazynu |
| `{mode}_stop_grid_import_w` | `NumberSelector` (optional) | `None` | Sub-próg importu sieci |
| `{mode}_stop_buy_price` | `NumberSelector` (optional) | `None` | Sub-próg ceny zakupu |
| `{mode}_stop_sell_price_min` | `NumberSelector` (optional) | `None` | Sub-próg min. ceny eksportu |
| `{mode}_stop_hysteresis_cycles` | `NumberSelector(min=1, max=10, int)` | `2` | Liczba cykli histerezy |

### Price Thresholds (per mode: balanced, fast, economical)

| Field | HA Input Type | Default | Description |
|-------|--------------|---------|-------------|
| `{mode}_buy_threshold` | `NumberSelector(min=0)` | `0.0` | Max cena zakupu do ładowania |
| `{mode}_sell_threshold` | `NumberSelector(min=0)` | `0.0` | Min cena eksportu dla rezygnacji |

---

## Validation Rules (config flow)

- `grid_power_limit_w` MUST be > 0
- Jeśli `obc_set_current_entity` skonfigurowany, `obc_actual_current_entity` jest wymagany
- Jeśli `buy_price_forecast_attr` skonfigurowany, `forecast_price_key` i `forecast_start_key` są wymagane
- Encje sterujące (evse_set_current, obc_set_current) nie mogą być tymi samymi encjami co sensoryczne
