import pandas as pd
from config import APT_FILE, FILE_READ_MODE, NAV_FILE, FIX_FILE, AWY_FILE
from utils.great_circle import great_circle_destination


def load_faa_nasr_data(path, data_type):
    if data_type == "feather":
        return pd.read_feather(path)
    elif data_type == "csv":
        return pd.read_csv(path)

    return None

apt = load_faa_nasr_data(APT_FILE, FILE_READ_MODE)
nav = load_faa_nasr_data(NAV_FILE, FILE_READ_MODE)
fix = load_faa_nasr_data(FIX_FILE, FILE_READ_MODE)
awy = load_faa_nasr_data(AWY_FILE, FILE_READ_MODE)

def deconstruct_awy(awy_id, from_fix, to_fix):
    awy_id = awy_id.upper()
    awy_row = awy[awy['AWY_ID'] == awy_id]

    if awy_row.empty:
        return []

    waypoints = awy_row.iloc[0]['AIRWAY_STRING'].split(' ')

    if from_fix:
        from_fix = from_fix.upper()
        if from_fix in waypoints:
            start_index = waypoints.index(from_fix) + 1
            waypoints = waypoints[start_index:]
        else:
            return []

    if to_fix:
        to_fix = to_fix.upper()
        if to_fix in waypoints:
            end_index = waypoints.index(to_fix)
            waypoints = waypoints[:end_index]
        else:
            return []

    return waypoints

def get_lat_lon(point):
    import re

    if re.match(r"^[A-Z]{3}\d{3}\d{3}$", point):
        navaid = point[:3].upper()

        lat_lon = get_lat_lon(navaid)
        if lat_lon is None:
            return None
        lat, lon = lat_lon

        radial_deg = int(point[3:6])
        distance_nm = int(point[6:])

        return great_circle_destination(lat, lon, radial_deg, distance_nm)

    entry = fix[fix['FIX_ID'] == point]

    if entry.empty:
        entry = nav[nav['NAV_ID'] == point]

    if entry.empty:
        entry = apt[apt['ARPT_ID'] == point]

    if entry.empty:
        return None

    lat = entry.iloc[0]['LAT_DECIMAL']
    lon = entry.iloc[0]['LONG_DECIMAL']
    return lat, lon