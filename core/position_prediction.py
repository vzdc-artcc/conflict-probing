import numpy as np

from config import VS_ZERO_RANGE
from utils.great_circle import great_circle_destination, haversine_distance

def track_between_points(lat1, lon1, lat2, lon2):
    # convert degrees to radians
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(np.radians, (lat1, lon1, lat2, lon2))
    dlon = lon2_rad - lon1_rad
    y = np.sin(dlon) * np.cos(lat2_rad)
    x = np.cos(lat1_rad) * np.sin(lat2_rad) - np.sin(lat1_rad) * np.cos(lat2_rad) * np.cos(dlon)
    bearing_deg = np.degrees(np.arctan2(y, x))
    return float((bearing_deg + 360) % 360)

def predict_lat_long_alt(lat, long, alt, vs, gs, trk, next_waypoint, waypoints, crz, mins):
    # waypoints is a list of dicts with keys: 'name','latitude','longitude'
    next_waypoints = waypoints[waypoints.index(next_waypoint):]

    if not next_waypoints:
        return None, None, None

    if VS_ZERO_RANGE[0] <= vs <= VS_ZERO_RANGE[1]:
        vs = 0

    pred_alt = alt + (vs * mins)

    if crz is not None and crz != "":
        try:
            crz_int = int(crz)
            if (vs < 0 and pred_alt < crz_int) or (vs > 0 and pred_alt > crz_int):
                pred_alt = crz_int
        except (ValueError, TypeError):
            pass

    pred_distance_covered = (gs * mins) / 60

    distance_to_next_wp = haversine_distance(lat, long, next_waypoints[0]['latitude'], next_waypoints[0]['longitude'])
    distance_remaining = pred_distance_covered - distance_to_next_wp

    if distance_remaining < 0:
        pred_lat, pred_long = great_circle_destination(lat, long, trk, pred_distance_covered)
        return pred_lat, pred_long, pred_alt

    lat = next_waypoints[0]['latitude']
    long = next_waypoints[0]['longitude']
    for i in range(1, len(next_waypoints)):
        future_waypoint = next_waypoints[i]
        distance = haversine_distance(lat, long, future_waypoint['latitude'], future_waypoint['longitude'])
        new_distance_remaining = distance_remaining - distance
        if new_distance_remaining < 0:
            bearing = track_between_points(lat, long, future_waypoint['latitude'], future_waypoint['longitude'])
            pred_lat, pred_long = great_circle_destination(lat, long, bearing, distance_remaining)
            return pred_lat, pred_long, pred_alt
        elif new_distance_remaining == 0:
            return future_waypoint['latitude'], future_waypoint['longitude'], pred_alt

        distance_remaining = new_distance_remaining

    return None, None, None