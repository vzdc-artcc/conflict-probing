import inspect

REPEAT_TIME=15

VATSIM_DATA_URL = "https://data.vatsim.net/v3/vatsim-data.json"

# Geographic bounds for monitoring
# (bottom-left latitude, bottom-left longitude)
BOTTOM_LEFT_LIMIT = (32.0, -130.0)
# (top-right latitude, top-right longitude)
TOP_RIGHT_LIMIT = (48.0, -62.6)

# Aircraft filtering
ALTITUDE_LIMIT_FT = 18000  # Minimum altitude to track (FL180)
VS_ZERO_RANGE = (-150, 150)

# Waypoint and route settings
WAYPOINT_TOLERANCE_NM = 4  # Distance from route considered "on course"

# Prediction settings
PREDICTION_MINUTES_AHEAD = 10  # How far ahead to predict
PREDICTION_PRECISION_MINUTES = 1  # Time increment for predictions

# Separation thresholds
LATERAL_SEPARATION_RED_NM = 5.0  # Red alert threshold
VERTICAL_SEPARATION_RED_FT = 1000.0  # Red alert threshold
LATERAL_SEPARATION_YELLOW_NM = 12.0  # Yellow alert threshold
VERTICAL_SEPARATION_YELLOW_FT = 1000.0  # Yellow alert threshold
VERTICAL_TOLERANCE_FT = 100  # Added margin for vertical calculations

# FAA NASR Data
NAVDATA_PATH = "navdata_feather/"
FIX_FILE = NAVDATA_PATH + "FIX_BASE.feather"
NAV_FILE = NAVDATA_PATH + "NAV_BASE.feather"
AWY_FILE = NAVDATA_PATH + "AWY_BASE.feather"
APT_FILE = NAVDATA_PATH + "APT_BASE.feather"
FILE_READ_MODE = 'feather'

VERTICAL_SPEED_CACHE_FILE = "data/vertical_speed_data.json"

def print_config_vars():
    for name, val in globals().items():
        if name.startswith('__'):
            continue
        if inspect.isroutine(val) or inspect.isclass(val) or inspect.ismodule(val):
            continue
        print(f"\t{name} = {repr(val)} ")