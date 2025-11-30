import shutil
import zipfile
from pathlib import Path
import pandas as pd

import requests
from datetime import datetime

csv_dir = "navdata_csv"
feather_dir = "navdata_feather"
NASR_DOWNLOAD_URL = "https://nfdc.faa.gov/webContent/28DaySub/extra/"
NASR_REQUIRED_FILES = [
    "APT_BASE.csv",
    "AWY_BASE.csv",
    "DP_RTE.csv",
    "FIX_BASE.csv",
    "NAV_BASE.csv",
    "STAR_RTE.csv",
]
NASR_REQUIRED_FILES_SET = {name.upper() for name in NASR_REQUIRED_FILES}

def get_nasr_zip_name(date):
    return date.strftime("%d_%b_%Y_CSV.zip")

def save_current_nasr_zip(temp_zip_path):
    for days_back in range(0, 28):
        date = datetime.utcnow() - pd.Timedelta(days=days_back)
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
    Path(csv_dir).mkdir(parents=True, exist_ok=True)
    Path(feather_dir).mkdir(parents=True, exist_ok=True)

def ensure_required_csv_files() -> None:
    ensure_navdata_directories()
    missing = []
    for filename in NASR_REQUIRED_FILES:
        target = Path(csv_dir) / filename
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
    zip_path = Path(csv_dir) / "latest_nasr_download.zip"

    try:
        save_current_nasr_zip(zip_path)

        with zipfile.ZipFile(zip_path) as archive:
            csv_members = [m for m in archive.namelist() if m.lower().endswith(".csv")]
            if not csv_members:
                raise RuntimeError("No CSV files found inside NASR archive.")

            for member in csv_members:
                if Path(member).name.upper() not in NASR_REQUIRED_FILES_SET:
                    continue

                target_path = Path(csv_dir) / Path(member).name
                with archive.open(member) as src, open(target_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                print(f"Saved {target_path}")

    finally:
        if zip_path.exists():
            zip_path.unlink()
            pass

def convert_all_navdata_csv_to_feather():
    ensure_navdata_directories()
    update_navdata_csv()
    ensure_required_csv_files()

    for filename in NASR_REQUIRED_FILES:
        csv_path = Path(csv_dir) / filename
        feather_path = Path(feather_dir) / filename.replace(".csv", ".feather")

        print(filename)
        try:
            df = pd.read_csv(csv_path)
        except pd.errors.EmptyDataError:
            df = pd.DataFrame()
        df.to_feather(feather_path)
        print(f"Converted '{csv_path}' -> '{feather_path}'")

    print("All CSV files have been converted to Feather format.")