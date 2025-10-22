import numpy as np

from config import VS_ZERO_RANGE
from utils.great_circle import great_circle_destination, haversine_distance

def track_between_points(lat1, lon1, lat2, lon2):
    return np.degrees(np.arctan2(np.sin(lon2 - lon1) * np.cos(lat2), np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(lon2 - lon1)))

def predict_lat_long_alt(lat, long, alt, vs, gs, trk, next_waypoint, waypoints, crz, mins):
    next_waypoints = waypoints[waypoints.index(next_waypoint):]

    if not next_waypoints:
        return None, None, None

    if VS_ZERO_RANGE[0] <= vs <= VS_ZERO_RANGE[1]:
        vs = 0

    pred_alt = alt + (vs * mins)

    if crz is not None and isinstance(crz, int):
        if (vs < 0 and pred_alt < crz) or (vs > 0 and pred_alt > crz):
            pred_alt = crz

    pred_distance_covered = (gs * mins) / 60

    distance_to_next_wp = haversine_distance(lat, long, next_waypoints[0][1][0], next_waypoints[0][1][1])
    distance_remaining = pred_distance_covered - distance_to_next_wp

    if distance_remaining < 0:
        pred_lat, pred_long = great_circle_destination(lat, long, trk, pred_distance_covered)
        return pred_lat, pred_long, pred_alt

    lat = next_waypoints[0][1][0]
    long = next_waypoints[0][1][1]
    for i in range(1, len(next_waypoints)):
        future_waypoint = next_waypoints[i]
        distance = haversine_distance(lat, long, future_waypoint[1][0], future_waypoint[1][1])
        new_distance_remaining = distance_remaining - distance
        if new_distance_remaining < 0:
            bearing = track_between_points(lat, long, future_waypoint[1][0], future_waypoint[1][1])
            pred_lat, pred_long = great_circle_destination(lat, long, bearing, distance_remaining)
            return pred_lat, pred_long, pred_alt
        elif new_distance_remaining == 0:
            return future_waypoint[1][0], future_waypoint[1][1], pred_alt

        distance_remaining = new_distance_remaining

    return None, None, None