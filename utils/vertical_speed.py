import json
import os
import time
from config import VERTICAL_SPEED_CACHE_FILE


def batch_compute_vertical_speed(aircraft_list):
    dirpath = os.path.dirname(VERTICAL_SPEED_CACHE_FILE)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)

    if os.path.exists(VERTICAL_SPEED_CACHE_FILE):
        with open(VERTICAL_SPEED_CACHE_FILE, 'r') as f:
            data = json.load(f)
    else:
        data = {}

    for aircraft in aircraft_list:
        new_data, vertical_speed = compute_vertical_speed(aircraft['callsign'], aircraft['altitude'], data)
        aircraft['vertical_speed'] = vertical_speed
        data = new_data

    with open(VERTICAL_SPEED_CACHE_FILE, 'w') as f:
        json.dump(data, f)

    return aircraft_list


def compute_vertical_speed(callsign, current_altitude, data):
    now = time.time()
    prev = data.get(callsign)
    vertical_speed = 0

    if prev:
        prev_altitude = prev['altitude']
        prev_time = prev['timestamp']
        time_diff = now - prev_time
        if 0 < time_diff < 600:
            vertical_speed = ((current_altitude - prev_altitude) / time_diff) * 60
            vertical_speed = int(vertical_speed)

    data[callsign] = {
        'altitude': current_altitude,
        'timestamp': now
    }

    return data, vertical_speed