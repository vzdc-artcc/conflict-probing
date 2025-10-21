import json
import os
import time

VERTICAL_SPEED_FILE = 'vertical_speed_data.json'

def compute_vertical_speed(callsign, current_altitude):
    # Load previous data
    if os.path.exists(VERTICAL_SPEED_FILE):
        with open(VERTICAL_SPEED_FILE, 'r') as f:
            data = json.load(f)
    else:
        data = {}

    now = time.time()
    prev = data.get(callsign)
    vertical_speed = 0

    if prev:
        prev_altitude = prev['altitude']
        prev_time = prev['timestamp']
        time_diff = now - prev_time
        if 0 < time_diff < 600:  # only consider if within last 10 minutes
            # Calculate vertical speed in feet per minute
            vertical_speed = ((current_altitude - prev_altitude) / time_diff) * 60
            vertical_speed = int(vertical_speed)
        # Update data
        data[callsign] = {
            'altitude': current_altitude,
            'timestamp': now
        }
    else:
        # First time seeing this callsign
        data[callsign] = {
            'altitude': current_altitude,
            'timestamp': now
        }
    # Save updated data
    with open(VERTICAL_SPEED_FILE, 'w') as f:
        json.dump(data, f)
    return vertical_speed

def fetch_vatsim_data(bottom_left_limit, top_right_limit, altitude_limit=None):
    import requests

    min_lat = bottom_left_limit[0]
    min_lon = bottom_left_limit[1]
    max_lat = top_right_limit[0]
    max_lon = top_right_limit[1]

    url = "https://data.vatsim.net/v3/vatsim-data.json"
    response = requests.get(url)
    data = response.json()

    found_pilots = []

    for pilot in data['pilots']:
        lat = pilot.get('latitude')
        lon = pilot.get('longitude')
        altitude = pilot.get('altitude')
        if pilot.get('flight_plan') is None:
            continue
        if pilot.get('flight_plan').get('flight_rules') == 'V':
            continue
        if lat is None or lon is None or altitude is None or (altitude_limit is not None and altitude < altitude_limit):
            continue

        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            # save the callsign, lat, long, altitude, groundspeed, heading, route, cruising altitude
            formatted_pilot = {
                'callsign': pilot.get('callsign'),
                'latitude': lat,
                'longitude': lon,
                'altitude': altitude,
                'ground_speed': pilot.get('groundspeed'),
                'heading': pilot.get('heading'),
                'origin': pilot.get('flight_plan', {}).get('departure'),
                'destination': pilot.get('flight_plan', {}).get('arrival'),
                'route': pilot.get('flight_plan', {}).get('route'),
                'cruising_altitude': pilot.get('flight_plan', {}).get('altitude'),
                'vertical_speed': compute_vertical_speed(pilot.get('callsign'), altitude),
            }
            found_pilots.append(formatted_pilot)

    return found_pilots