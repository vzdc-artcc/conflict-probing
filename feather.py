import pandas as pd
import os

csv_dir = "navdata_csv"
feather_dir = "navdata_feather"

def convert_all_navdata_csv_to_feather():
    os.makedirs(feather_dir, exist_ok=True)

    # Loop over CSV files
    for filename in os.listdir(csv_dir):
        if filename.endswith(".csv"):
            csv_path = os.path.join(csv_dir, filename)
            feather_path = os.path.join(feather_dir, filename.replace(".csv", ".feather"))

            print(filename)
            # Read CSV and write Feather
            df = pd.read_csv(csv_path)
            df.to_feather(feather_path)

            print(f"Converted '{csv_path}' -> '{feather_path}'")

    print("All CSV files have been converted to Feather format.")