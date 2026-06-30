import inspect

REPEAT_TIME=15

VATSIM_DATA_URL = "https://data.vatsim.net/v3/vatsim-data.json"

# USA COORDINATES
# BOTTOM_LEFT_LIMIT = (25, -130)
# TOP_RIGHT_LIMIT = (50, -62.6)

# ZDC COORDINATES
BOTTOM_LEFT_LIMIT = (33.5, -82.5)
TOP_RIGHT_LIMIT = (41, -71.5)

ALTITUDE_FLOOR_FT = 10000
VS_ZERO_RANGE = (-150, 150)

WAYPOINT_TOLERANCE_NM = 10

PREDICTION_MINUTES_AHEAD = 20
PREDICTION_PRECISION_MINUTES = 0.8

LATERAL_SEPARATION_RED_NM = 5.0
# account for pressure differences
VERTICAL_SEPARATION_RED_FT = 750.0
LATERAL_SEPARATION_YELLOW_NM = 12.0
VERTICAL_SEPARATION_YELLOW_FT = 1000.0
VERTICAL_TOLERANCE_FT = 300

NAVDATA_PATH = "navdata_feather/"
FIX_FILE = NAVDATA_PATH + "FIX_BASE.feather"
NAV_FILE = NAVDATA_PATH + "NAV_BASE.feather"
AWY_FILE = NAVDATA_PATH + "AWY_BASE.feather"
APT_FILE = NAVDATA_PATH + "APT_BASE.feather"
SID_FILE = NAVDATA_PATH + "DP_RTE.feather"
STAR_FILE = NAVDATA_PATH + "STAR_RTE.feather"
ATC_FILE = NAVDATA_PATH + "ATC_BASE.feather"

FEATHER_DIR = "navdata_feather"
CSV_DIR = "navdata_csv"
NASR_DOWNLOAD_URL = "https://nfdc.faa.gov/webContent/28DaySub/extra/"
NASR_REQUIRED_FILES = [
    "APT_BASE.csv",
    "AWY_BASE.csv",
    "DP_RTE.csv",
    "FIX_BASE.csv",
    "NAV_BASE.csv",
    "STAR_RTE.csv",
    "ATC_BASE.csv",
]
NASR_REQUIRED_FILES_SET = {name.upper() for name in NASR_REQUIRED_FILES}

PRD_DOWNLOAD_URL = "https://www.fly.faa.gov/rmt/data_file/prefroutes_db.csv"
PRD_CSV_FILE = CSV_DIR + "/prefroutes_db.csv"
PRD_FEATHER_FILE = NAVDATA_PATH + "prefroutes_db.feather"

VERTICAL_SPEED_CACHE_FILE = "data/vertical_speed_data.json"
DATA_CACHE_FILE = "data/cache.json"

def print_config_vars():
    for name, val in globals().items():
        if name.startswith('__'):
            continue
        if inspect.isroutine(val) or inspect.isclass(val) or inspect.ismodule(val):
            continue
        print(f"\t{name} = {repr(val)} ")

def config_vars():
    cfg = {}
    for name, val in globals().items():
        if name.startswith('__'):
            continue
        if inspect.isroutine(val) or inspect.isclass(val) or inspect.ismodule(val):
            continue
        cfg[name] = val
    return cfg