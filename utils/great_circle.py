from functools import cache
import numpy as np

from config import WAYPOINT_TOLERANCE_NM
from utils.geo_constants import EARTH_RADIUS_NM

@cache
def deg2rad(deg):
    return deg * np.pi / 180.0

@cache
def nm_to_radians(nm):
    return nm * np.pi / 10800.0

@cache
def radians_to_nm(angle_rad):
    return angle_rad * (10800.0 / np.pi)

def latlon_to_unit(lat_deg, lon_deg):
    lat = deg2rad(lat_deg)
    lon = deg2rad(lon_deg)
    x = np.cos(lat) * np.cos(lon)
    y = np.cos(lat) * np.sin(lon)
    z = np.sin(lat)
    v = np.array([x, y, z], dtype=float)
    return v / np.linalg.norm(v)

def angle_between(u, v):
    d = np.dot(u, v)
    d = max(-1.0, min(1.0, d))  # clamp numerical error
    return np.arccos(d)

def great_circle_destination(lat, lon, bearing, distance_nm):
    bearing_rad = np.radians(bearing)
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    distance_rad = distance_nm / EARTH_RADIUS_NM

    new_lat_rad = np.arcsin(np.sin(lat_rad) * np.cos(distance_rad) +
                            np.cos(lat_rad) * np.sin(distance_rad) * np.cos(bearing_rad))

    new_lon_rad = lon_rad + np.arctan2(np.sin(bearing_rad) * np.sin(distance_rad) * np.cos(lat_rad),
                                       np.cos(distance_rad) - np.sin(lat_rad) * np.sin(new_lat_rad))

    new_lat = np.degrees(new_lat_rad)
    new_lon = np.degrees(new_lon_rad)

    return new_lat, new_lon


def haversine_distance(lat1, lon1, lat2, lon2):
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)

    a = np.sin(delta_phi / 2.0) ** 2 + \
        np.cos(phi1) * np.cos(phi2) * \
        np.sin(delta_lambda / 2.0) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    return EARTH_RADIUS_NM * c

WAYPOINT_TOLERANCE_RAD = nm_to_radians(WAYPOINT_TOLERANCE_NM)

def is_point_on_path(position_start, position_end, point):
    u = latlon_to_unit(*position_start)
    w = latlon_to_unit(*position_end)
    p = latlon_to_unit(*point)

    proj = np.dot(u, w) * u
    v_raw = w - proj
    norm_v = np.linalg.norm(v_raw)
    if norm_v < 1e-12:
        return (angle_between(u, p) <= WAYPOINT_TOLERANCE_RAD) or (angle_between(w, p) <= WAYPOINT_TOLERANCE_RAD), 0.0
    v = v_raw / norm_v

    A = np.dot(u, p)
    B = np.dot(v, p)
    C = np.hypot(A, B)
    C = min(1.0, max(-1.0, C))

    theta_star = np.arctan2(B, A)

    Delta = np.arctan2(np.dot(w, v), np.dot(w, u))

    norm2pi = lambda x: x % (2*np.pi)
    th = norm2pi(theta_star)
    d = norm2pi(Delta)

    if d <= np.pi:
        in_arc = (0 <= th <= d)
    else:
        in_arc = not (d < th < 2*np.pi)

    if in_arc:
        perp_angle = np.arccos(C)
        nm_dist = radians_to_nm(perp_angle)
        return perp_angle <= WAYPOINT_TOLERANCE_RAD + 1e-12, nm_dist
    else:
        return None