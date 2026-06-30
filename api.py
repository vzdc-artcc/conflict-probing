from fastapi import FastAPI, BackgroundTasks
from threading import Lock, Thread
from datetime import datetime, timedelta
import time
import json
import os

from config import REPEAT_TIME, DATA_CACHE_FILE, config_vars
from conflict_probing import get_aircraft_conflict_status
from feather import convert_all_navdata_csv_to_feather
from utils.faa import clear_navdata_cache, update_prd_csv

app = FastAPI()

cache_lock = Lock()
last_update = 0
is_updating = False
nightly_refresh_thread: Thread | None = None

NIGHTLY_REFRESH_LOG_PREFIX = "[Nightly Navdata Refresh]"


def update_cache():
    global last_update, is_updating
    if is_updating:
        return
    is_updating = True
    try:
        conflicting, non_conflicting, timestamp = get_aircraft_conflict_status()

        cache_dir = os.path.dirname(DATA_CACHE_FILE)
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)

        with cache_lock:
            with open(DATA_CACHE_FILE, "w") as f:
                json.dump({
                    "alerts": conflicting,
                    "non_alerts": non_conflicting,
                    "timestamp": timestamp
                }, f)
        last_update = timestamp
    finally:
        is_updating = False


def get_cached_data():
    if not os.path.exists(DATA_CACHE_FILE):
        return None
    with cache_lock:
        with open(DATA_CACHE_FILE, "r") as f:
            return json.load(f)


def _seconds_until_local_midnight() -> float:
    now = datetime.now()
    tomorrow = (now.replace(hour=0, minute=0, second=0, microsecond=0)
                + timedelta(days=1))
    return max((tomorrow - now).total_seconds(), 0)


def _nightly_navdata_loop() -> None:
    while True:
        sleep_seconds = _seconds_until_local_midnight()
        print(f"{NIGHTLY_REFRESH_LOG_PREFIX} Sleeping {sleep_seconds:.0f}s until midnight")
        time.sleep(sleep_seconds)
        try:
            print(f"{NIGHTLY_REFRESH_LOG_PREFIX} Starting navdata refresh")
            convert_all_navdata_csv_to_feather()
            clear_navdata_cache()  # Clear cache so new data is loaded
            update_cache()
            print(f"{NIGHTLY_REFRESH_LOG_PREFIX} Successfully refreshed navdata")
        except Exception as exc:
            print(f"{NIGHTLY_REFRESH_LOG_PREFIX} Refresh failed: {exc}")


WEEKLY_PRD_REFRESH_LOG_PREFIX = "[Weekly PRD Refresh]"


def _weekly_prd_loop() -> None:
    while True:
        time.sleep(7 * 24 * 60 * 60)
        try:
            print(f"{WEEKLY_PRD_REFRESH_LOG_PREFIX} Starting PRD refresh")
            update_prd_csv()
            clear_navdata_cache()
            print(f"{WEEKLY_PRD_REFRESH_LOG_PREFIX} Successfully refreshed PRD data")
        except Exception as exc:
            print(f"{WEEKLY_PRD_REFRESH_LOG_PREFIX} Refresh failed: {exc}")


weekly_prd_thread: Thread | None = None


def _start_weekly_prd_thread() -> None:
    global weekly_prd_thread
    if weekly_prd_thread and weekly_prd_thread.is_alive():
        return
    weekly_prd_thread = Thread(target=_weekly_prd_loop, daemon=True)
    weekly_prd_thread.start()


def _start_nightly_navdata_thread() -> None:
    global nightly_refresh_thread
    if nightly_refresh_thread and nightly_refresh_thread.is_alive():
        return
    nightly_refresh_thread = Thread(target=_nightly_navdata_loop, daemon=True)
    nightly_refresh_thread.start()


@app.on_event("startup")
def startup_event():
    clear_navdata_cache()  # Ensure clean start
    convert_all_navdata_csv_to_feather()
    update_cache()
    _start_nightly_navdata_thread()
    _start_weekly_prd_thread()


@app.get("/data")
def get_data(background_tasks: BackgroundTasks):
    data = get_cached_data()

    if data is None:
        background_tasks.add_task(update_cache)
        return {"status": "initializing, please wait"}

    if time.time() - last_update > REPEAT_TIME:
        background_tasks.add_task(update_cache)

    return data


@app.get("/decode")
def decode_route(route: str = ""):
    from core.flightplan_route import route_to_lat_lon
    if route.strip() == "":
        return []
    return route_to_lat_lon(route)

@app.get("/atc_data")
def atc_data(id: str = ""):
    from utils.faa import get_atc_data
    return get_atc_data(id)

@app.get("/config")
def config():
    return config_vars()

@app.get("/prd")
def prd(departure: str = "", arrival: str = ""):
    from utils.faa import get_prd_routes
    dep = departure.strip().upper() or None
    arr = arrival.strip().upper() or None
    if not dep and not arr:
        return {"error": "Provide at least one of: departure, arrival"}
    return get_prd_routes(departure=dep, arrival=arr)

