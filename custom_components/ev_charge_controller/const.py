from __future__ import annotations

from datetime import timedelta

DOMAIN = "ev_charge_controller"
NAME = "EV Charge Controller"

PLATFORMS = ["select", "sensor"]
UPDATE_INTERVAL = timedelta(minutes=1)

CONF_ENTITY_MAPPING = "entity_mapping"
CONF_HARD_LIMITS = "hard_limits"
CONF_BATTERY_PROTECTION = "battery_protection"
CONF_STOP_CONDITION = "stop_condition"
CONF_PRICE_THRESHOLDS = "price_thresholds"

CONF_PV_POWER_ENTITY = "pv_power_entity"
CONF_BATTERY_SOC_ENTITY = "battery_soc_entity"
CONF_BATTERY_POWER_ENTITY = "battery_power_entity"
CONF_GRID_POWER_ENTITY = "grid_power_entity"
CONF_BUY_PRICE_ENTITY = "buy_price_entity"
CONF_SELL_PRICE_ENTITY = "sell_price_entity"
CONF_BUY_PRICE_FORECAST_ATTR = "buy_price_forecast_attr"
CONF_FORECAST_PRICE_KEY = "forecast_price_key"
CONF_FORECAST_START_KEY = "forecast_start_key"
CONF_EV_CONNECTED_ENTITY = "ev_connected_entity"
CONF_EV_SOC_ENTITY = "ev_soc_entity"
CONF_EVSE_SET_CURRENT_ENTITY = "evse_set_current_entity"
CONF_EVSE_ACTUAL_CURRENT_ENTITY = "evse_actual_current_entity"
CONF_OBC_SET_CURRENT_ENTITY = "obc_set_current_entity"
CONF_OBC_ACTUAL_CURRENT_ENTITY = "obc_actual_current_entity"

CONF_GRID_POWER_LIMIT_W = "grid_power_limit_w"
CONF_BATTERY_TIER_50_MAX_DISCHARGE_W = "battery_tier_50_max_discharge_w"
CONF_BATTERY_TIER_70_MAX_DISCHARGE_W = "battery_tier_70_max_discharge_w"
CONF_BATTERY_TIER_90_MAX_DISCHARGE_W = "battery_tier_90_max_discharge_w"
CONF_FAST_MODE_DISCHARGE_LIMIT_W = "fast_mode_discharge_limit_w"

CONF_PHASE_COUNT = "phase_count"

MODE_BALANCED = "balanced"
MODE_FAST = "fast"
MODE_ECONOMICAL = "economical"
MODE_MANUAL = "manual"
MODE_OPTIONS = [MODE_BALANCED, MODE_FAST, MODE_ECONOMICAL, MODE_MANUAL]

DEFAULT_EVSE_MIN_CURRENT_A = 6
DEFAULT_EVSE_MAX_CURRENT_A = 16
DEFAULT_OBC_THROTTLE_CURRENT_A = 5
DEFAULT_FAIL_SAFE_CURRENT_A = 6
DEFAULT_STALE_DATA_TIMEOUT_S = 60
DEFAULT_OVERRIDE_DELTA_A = 1
DEFAULT_HYSTERESIS_CYCLES = 2
DEFAULT_BUY_THRESHOLD = 0.0
DEFAULT_SELL_THRESHOLD = 0.0
DEFAULT_PHASE_COUNT = 3
DEFAULT_BATTERY_TIER_50_MAX_DISCHARGE_W = 500.0
DEFAULT_BATTERY_TIER_70_MAX_DISCHARGE_W = 1500.0
DEFAULT_BATTERY_TIER_90_MAX_DISCHARGE_W = 3000.0

ATTR_MODE = "mode"
ATTR_REASON = "reason"
ATTR_TARGET_CURRENT_A = "target_current_a"
ATTR_EVSE_CURRENT_A = "evse_current_a"
ATTR_OBC_CURRENT_A = "obc_current_a"
ATTR_DATA_QUALITY = "data_quality"
ATTR_STOP_CONDITION_ACTIVE = "stop_condition_active"
ATTR_HYSTERESIS_COUNTER = "hysteresis_counter"
ATTR_BATTERY_TIER = "battery_tier"
ATTR_OVERRIDE_DETECTED = "override_detected"
ATTR_APPLIED_CONSTRAINTS = "applied_constraints"
ATTR_KEY_INPUTS = "key_inputs"
ATTR_LAST_DECISION_AT = "last_decision_at"
ATTR_PRICE_THRESHOLDS = "price_thresholds"
ATTR_STOP_THRESHOLDS = "stop_thresholds"

STATUS_ACTIVE = "active"
STATUS_LIMITED = "limited"
STATUS_STOPPED = "stopped"
STATUS_FAIL_SAFE = "fail_safe"
STATUS_MANUAL = "manual"

SERVICE_NUMBER_SET_VALUE = "set_value"
SERVICE_SELECT_SELECT_OPTION = "select_option"
