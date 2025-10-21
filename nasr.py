import pandas as pd

FIX_FILE = "navdata/FIX_BASE.csv"
NAV_FILE = "navdata/NAV_BASE.csv"
AWY_FILE = "navdata/AWY_BASE.csv"
APT_FILE = "navdata/APT_BASE.csv"

fix = pd.read_csv(FIX_FILE)
nav = pd.read_csv(NAV_FILE)
awy = pd.read_csv(AWY_FILE)
apt = pd.read_csv(APT_FILE, low_memory=False)


def get_lat_lon(point):
    point = point.upper()

    if is_radial(point):
        return get_lat_long_radial(point)

    row = fix[fix['FIX_ID'] == point]

    if row.empty:
        row = nav[nav['NAV_ID'] == point]

    if row.empty:
        if point.startswith('K') and len(point) == 4:
            point = point[1:]

        row = apt[apt['ARPT_ID'] == point]

    if row.empty:
        return None

    lat = row.iloc[0]['LAT_DECIMAL']
    lon = row.iloc[0]['LONG_DECIMAL']
    return lat, lon


def get_awy_points(awy_name, from_fix=None, to_fix=None):
    awy_name = awy_name.upper()
    awy_row = awy[awy['AWY_ID'] == awy_name]

    if awy_row.empty:
        return None

    waypoints = awy_row.iloc[0]['AIRWAY_STRING'].split(' ')

    if from_fix:
        from_fix = from_fix.upper()
        if from_fix in waypoints:
            start_index = waypoints.index(from_fix) + 1
            waypoints = waypoints[start_index:]
        else:
            return None

    if to_fix:
        to_fix = to_fix.upper()
        if to_fix in waypoints:
            end_index = waypoints.index(to_fix)
            waypoints = waypoints[:end_index]
        else:
            return None

    return waypoints

def get_lat_long_radial(radial):
    import math

    # Parse the input string: assume format like "SJC085002" -> navaid, radial, distance
    navaid = radial[:3].upper()  # e.g., "SJC"
    radial_deg = int(radial[3:6])  # e.g., 085
    distance_nm = int(radial[6:])  # e.g., 002

    # Get navaid lat/lon
    lat_lon = get_lat_lon(navaid)
    if lat_lon is None:
        return None
    lat1, lon1 = lat_lon

    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    bearing_rad = math.radians(radial_deg)

    # Earth's radius in NM
    R = 3440.065  # nautical miles

    # Distance in radians
    d_rad = distance_nm / R

    # Calculate destination lat/lon
    lat2_rad = math.asin(math.sin(lat1_rad) * math.cos(d_rad) + math.cos(lat1_rad) * math.sin(d_rad) * math.cos(bearing_rad))
    lon2_rad = lon1_rad + math.atan2(math.sin(bearing_rad) * math.sin(d_rad) * math.cos(lat1_rad), math.cos(d_rad) - math.sin(lat1_rad) * math.sin(lat2_rad))

    # Convert back to degrees
    lat2 = math.degrees(lat2_rad)
    lon2 = math.degrees(lon2_rad)

    return lat2, lon2

def is_radial(waypoint):
    import re
    return bool(re.match(r"^[A-Z]{3}\d{3}\d{3}$", waypoint.upper()))