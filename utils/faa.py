from datetime import datetime, timezone
import shutil
import zipfile
from pathlib import Path
from functools import lru_cache

import pandas as pd
import requests

from config import APT_FILE, NAV_FILE, FIX_FILE, AWY_FILE, SID_FILE, STAR_FILE, NASR_DOWNLOAD_URL, CSV_DIR, FEATHER_DIR, \
    NASR_REQUIRED_FILES, NASR_REQUIRED_FILES_SET
from utils.great_circle import great_circle_destination

# Cache loaded DataFrames at module level
_navdata_cache = {}



def get_nasr_zip_name(date):
    return date.strftime("%d_%b_%Y_CSV.zip")

def save_current_nasr_zip(temp_zip_path):
    for days_back in range(0, 28):
        date = datetime.now(timezone.utc) - pd.Timedelta(days=days_back)
        zip_name = get_nasr_zip_name(date)
        test_url = NASR_DOWNLOAD_URL + zip_name
        response = requests.get(test_url, timeout=10)
        print(f"Testing NASR URL: {test_url} - Status Code: {response.status_code}")
        if response.status_code == 200 and response.headers.get('Content-Type') == 'application/zip':
            temp_zip_path.touch(exist_ok=True)

            with open(temp_zip_path, "wb") as f:
                f.write(response.content)
            print(f"Downloaded NASR zip file: {zip_name}")
            return

    raise RuntimeError("Could not find a valid NASR zip file in the last 28 days.")


def ensure_navdata_directories() -> None:
    Path(CSV_DIR).mkdir(parents=True, exist_ok=True)
    Path(FEATHER_DIR).mkdir(parents=True, exist_ok=True)

def ensure_required_csv_files() -> None:
    ensure_navdata_directories()
    missing = []
    for filename in NASR_REQUIRED_FILES:
        target = Path(CSV_DIR) / filename
        if not target.exists():
            target.touch()
            missing.append(filename)
    if missing:
        print(
            "Created placeholder CSV files for missing NASR datasets: "
            + ", ".join(missing)
        )

def update_navdata_csv():
    ensure_navdata_directories()
    ensure_required_csv_files()
    zip_path = Path(CSV_DIR) / "latest_nasr_download.zip"

    try:
        save_current_nasr_zip(zip_path)

        with zipfile.ZipFile(zip_path) as archive:
            csv_members = [m for m in archive.namelist() if m.lower().endswith(".csv")]
            if not csv_members:
                raise RuntimeError("No CSV files found inside NASR archive.")

            for member in csv_members:
                if Path(member).name.upper() not in NASR_REQUIRED_FILES_SET:
                    continue

                target_path = Path(CSV_DIR) / Path(member).name
                with archive.open(member) as src, open(target_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                print(f"Saved {target_path}")

    finally:
        if zip_path.exists():
            zip_path.unlink()
            pass

def load_faa_nasr_data(path):
    if path not in _navdata_cache:
        _navdata_cache[path] = pd.read_feather(path)
    return _navdata_cache[path]

def clear_navdata_cache():
    """Call this after nightly refresh to reload fresh data."""
    _navdata_cache.clear()
    get_lat_lon.cache_clear()

def deconstruct_procedure(procedure, transition):

    if (not procedure) or (not transition):
        return []

    sid = load_faa_nasr_data(SID_FILE)
    star = load_faa_nasr_data(STAR_FILE)
    procedure = procedure.upper()
    transition = transition.upper()

    star_points = star[star['TRANSITION_COMPUTER_CODE'] == f"{transition}.{procedure}"]
    sid_points = sid[sid['TRANSITION_COMPUTER_CODE'] == f"{procedure}.{transition}"]

    if sid_points.empty and star_points.empty:
        if procedure.startswith(transition):
            return [transition]
        return []

    sid_p = sort_points_by_seq(sid_points)
    star_p = sort_points_by_seq(star_points)

    if len(sid_p) > 0 and sid_p[len(sid_p) - 1] == transition:
        sid_p = sid_p[:-1]
    elif len(star_p) > 0 and star_p[0] == transition:
        star_p = star_p[1:]

    return sid_p + star_p

def sort_points_by_seq(points):
    if points.empty:
        return []
    sorted_points = points.sort_values('POINT_SEQ', ascending=False)
    return sorted_points['POINT'].tolist()

def deconstruct_awy(awy_id, from_fix, to_fix):
    awy = load_faa_nasr_data(AWY_FILE)

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

@lru_cache(maxsize=10000)
def get_lat_lon(point):
    import re

    apt = load_faa_nasr_data(APT_FILE)
    nav = load_faa_nasr_data(NAV_FILE)
    fix = load_faa_nasr_data(FIX_FILE)

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
        if len(point) == 4 and point[0] == 'K':
            entry = apt[apt['ARPT_ID'] == point[1:]]

    if entry.empty:
        return None

    lat = entry.iloc[0]['LAT_DECIMAL']
    lon = entry.iloc[0]['LONG_DECIMAL']
    return lat, lon