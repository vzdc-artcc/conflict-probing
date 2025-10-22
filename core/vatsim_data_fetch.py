from config import VATSIM_DATA_URL, BOTTOM_LEFT_LIMIT, TOP_RIGHT_LIMIT, ALTITUDE_LIMIT_FT
from utils.vertical_speed import batch_compute_vertical_speed

def fetch_vatsim_data():
    import requests

    min_lat = BOTTOM_LEFT_LIMIT[0]
    min_lon = BOTTOM_LEFT_LIMIT[1]
    max_lat = TOP_RIGHT_LIMIT[0]
    max_lon = TOP_RIGHT_LIMIT[1]

    response = requests.get(VATSIM_DATA_URL)
    data = response.json()

    pilots = []

    for pilot in data['pilots']:
        lat = pilot.get('latitude')
        lon = pilot.get('longitude')
        altitude = pilot.get('altitude')

        if pilot.get('flight_plan') is None:
            continue
        elif pilot.get('flight_plan').get('flight_rules') == 'V':
            continue
        elif lat is None or lon is None or altitude is None or (ALTITUDE_LIMIT_FT is not None and altitude < ALTITUDE_LIMIT_FT):
            continue
        elif (lat < min_lat or lat > max_lat) or (lon < min_lon or lon > max_lon):
            continue
        pilots.append({
            'callsign': pilot.get('callsign'),
            'latitude': lat,
            'longitude': lon,
            'altitude': altitude,
            'ground_speed': pilot.get('groundspeed'),
            'heading': pilot.get('heading'),
            'departure': pilot.get('flight_plan', {}).get('departure'),
            'arrival': pilot.get('flight_plan', {}).get('arrival'),
            'route': pilot.get('flight_plan', {}).get('route'),
            'cruising_altitude': pilot.get('flight_plan', {}).get('altitude'),
            'vertical_speed': 0,
        })

    return batch_compute_vertical_speed(pilots)