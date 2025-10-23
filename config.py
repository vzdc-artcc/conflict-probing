import inspect

REPEAT_TIME=15

VATSIM_DATA_URL = "https://data.vatsim.net/v3/vatsim-data.json"

# USA Coords
BOTTOM_LEFT_LIMIT = (32, -130)
TOP_RIGHT_LIMIT = (48, -62.6)

# ZDC Coords
# BOTTOM_LEFT_LIMIT = (33.5, -82.5)
# TOP_RIGHT_LIMIT = (41, -71.5)

ALTITUDE_LIMIT_FT = 10000
VS_ZERO_RANGE = (-150, 150)

WAYPOINT_TOLERANCE_NM = 4

PREDICTION_MINUTES_AHEAD = 10
PREDICTION_PRECISION_MINUTES = 1

LATERAL_SEPARATION_RED_NM = 5.0
VERTICAL_SEPARATION_RED_FT = 1000.0
LATERAL_SEPARATION_YELLOW_NM = 12.0
VERTICAL_SEPARATION_YELLOW_FT = 1000.0
VERTICAL_TOLERANCE_FT = 150

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