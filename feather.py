from pathlib import Path
import pandas as pd

from config import FEATHER_DIR, NASR_REQUIRED_FILES, CSV_DIR
from utils.faa import update_navdata_csv, ensure_required_csv_files, ensure_navdata_directories

def convert_all_navdata_csv_to_feather():
    ensure_navdata_directories()
    ensure_required_csv_files()
    update_navdata_csv()

    for filename in NASR_REQUIRED_FILES:
        csv_path = Path(CSV_DIR) / filename
        feather_path = Path(FEATHER_DIR) / filename.replace(".csv", ".feather")

        print(filename)
        try:
            df = safe_read_csv(csv_path)
        except pd.errors.EmptyDataError:
            df = pd.DataFrame()
        df.to_feather(feather_path)
        print(f"Converted '{csv_path}' -> '{feather_path}'")

    print("All CSV files have been converted to Feather format.")

def safe_read_csv(path, encodings=("utf-8", "latin-1"), **kwargs):
    """Try multiple encodings when reading CSV; set low_memory=False by default."""
    kwargs.setdefault("low_memory", False)
    # Optionally force strings to avoid mixed-type warnings:
    # kwargs.setdefault("dtype", str)
    for enc in encodings:
        try:
            return pd.read_csv(path, encoding=enc, **kwargs)
        except UnicodeDecodeError:
            continue
    # final attempt with errors='replace' using python engine
    return pd.read_csv(path, encoding=encodings[-1], engine="python", encoding_errors="replace", **kwargs)