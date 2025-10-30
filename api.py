from fastapi import FastAPI, BackgroundTasks
from threading import Lock
import time
import json
import os

from config import REPEAT_TIME, DATA_CACHE_FILE, config_vars
from conflict_probing import get_aircraft_conflict_status

app = FastAPI()

cache_lock = Lock()
last_update = 0
is_updating = False

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


@app.on_event("startup")
def startup_event():
    update_cache()


@app.get("/data")
def get_data(background_tasks: BackgroundTasks):
    data = get_cached_data()

    if data is None:
        background_tasks.add_task(update_cache)
        return {"status": "initializing, please wait"}

    if time.time() - last_update > REPEAT_TIME:
        background_tasks.add_task(update_cache)

    return data


@app.get("/config")
def config():
    return config_vars()