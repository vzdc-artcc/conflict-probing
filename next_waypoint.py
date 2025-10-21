import numpy as np

# -----------------------------
# 1. Helper conversions
# -----------------------------

def deg2rad(deg):
    return deg * np.pi / 180.0

def nm_to_radians(nm):
    # 1 NM = 1/60 degree = π / 10800 radians
    return nm * np.pi / 10800.0

def radians_to_nm(angle_rad):
    """Convert angular distance (radians) to nautical miles."""
    return angle_rad * (10800.0 / np.pi)

def latlon_to_unit(lat_deg, lon_deg):
    """Convert latitude/longitude (degrees) to 3D unit vector on the unit sphere"""
    lat = deg2rad(lat_deg)
    lon = deg2rad(lon_deg)
    x = np.cos(lat) * np.cos(lon)
    y = np.cos(lat) * np.sin(lon)
    z = np.sin(lat)
    v = np.array([x, y, z], dtype=float)
    return v / np.linalg.norm(v)

def angle_between(u, v):
    """Return the angle (radians) between two unit vectors"""
    d = np.dot(u, v)
    d = max(-1.0, min(1.0, d))  # clamp numerical error
    return np.arccos(d)

# -----------------------------
# 2. Main geometric test
# -----------------------------

def point_within_gc_arc_tol(u_latlon, w_latlon, p_latlon, tol_nm):
    """
    u_latlon: (lat_deg, lon_deg) of waypoint 1
    w_latlon: (lat_deg, lon_deg) of waypoint 2
    p_latlon: (lat_deg, lon_deg) of test point
    tol_nm: tolerance in nautical miles
    """
    tol_rad = nm_to_radians(tol_nm)

    # Convert all to 3D unit vectors
    u = latlon_to_unit(*u_latlon)
    w = latlon_to_unit(*w_latlon)
    p = latlon_to_unit(*p_latlon)

    # Build v (Gram–Schmidt orthonormal vector in the great-circle plane)
    proj = np.dot(u, w) * u
    v_raw = w - proj
    norm_v = np.linalg.norm(v_raw)
    if norm_v < 1e-12:
        # Waypoints are identical or opposite
        return ((angle_between(u, p) <= tol_rad) or (angle_between(w, p) <= tol_rad), 0.0)
    v = v_raw / norm_v

    # A, B for f(θ) = A cosθ + B sinθ
    A = np.dot(u, p)
    B = np.dot(v, p)
    C = np.hypot(A, B)
    C = min(1.0, max(-1.0, C))

    # Angle of closest approach on the infinite great circle
    theta_star = np.arctan2(B, A)

    # Angle along great circle from u to w
    Delta = np.arctan2(np.dot(w, v), np.dot(w, u))

    # Normalize to [0, 2π)
    norm2pi = lambda x: x % (2*np.pi)
    th = norm2pi(theta_star)
    d = norm2pi(Delta)

    # Check whether theta* lies on the shorter arc from u → w
    if d <= np.pi:
        in_arc = (0 <= th <= d)
    else:
        in_arc = not (d < th < 2*np.pi)

    # Compute perpendicular angular distance
    if in_arc:
        perp_angle = np.arccos(C)
        nm_dist = radians_to_nm(perp_angle)
        return perp_angle <= tol_rad + 1e-12, nm_dist
    else:
        # Closest point is one of the endpoints
        return None

# -----------------------------
# 3. Example usage
# -----------------------------

if __name__ == "__main__":
    # Example coordinates (in lat/lon)
    waypoint1 = (33.70735333,-82.16206444)
    waypoint2 = (38.75412463,-82.02616761)
    point = (36.31866,-82.09395)
    tolerance_nm = 4

    on_path, nm_dist = point_within_gc_arc_tol(waypoint1, waypoint2, point, tolerance_nm)

    print(f"Point {nm_dist} NM from the great-circle path (tolerance {tolerance_nm} NM): {on_path}")