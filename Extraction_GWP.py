import os
import rasterio
import pandas as pd
import numpy as np
from collections import defaultdict
from multiprocessing import Pool, cpu_count
import logging
from datetime import datetime
import gc

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# File paths
coordinates_file = ""
tif_folder = ""
output_folder = ""
os.makedirs(output_folder, exist_ok=True)

sum_file = os.path.join(output_folder, "GWP_water_values.csv")
zero_file = os.path.join(output_folder, " GWP_no_water_values.csv")

# Load coordinates
coordinates_df = pd.read_csv(coordinates_file, sep=";")
coordinate_rows = coordinates_df[["longitude", "latitude", "Arc_ID"]].values


def extract_date_from_filename(filename):
    """Extracts date from filename if it contains an 8-digit date (YYYYMMDD)."""
    for part in filename.split("."):
        if part.isdigit() and len(part) == 8:
            return datetime.strptime(part, "%Y%m%d")
    return None


def process_tif(tif_file):
    """Processes a single TIFF file and extracts values for predefined coordinate points."""
    try:
        filepath = os.path.join(tif_folder, tif_file)
        with rasterio.open(filepath) as dataset:
            band = dataset.read(1)
            bounds = dataset.bounds
            arcid_map = defaultdict(list)
            date = extract_date_from_filename(tif_file)

            for lon, lat, arc_id in coordinate_rows:
                if not (bounds.left <= lon <= bounds.right and bounds.bottom <= lat <= bounds.top):
                    continue
                row, col = dataset.index(lon, lat)
                if 0 <= row < band.shape[0] and 0 <= col < band.shape[1]:
                    val = band[row, col]
                    arcid_map[int(arc_id)].append(val)

        return {"Date": date.strftime("%Y-%m-%d"), "ArcID_Values": arcid_map}

    except Exception as e:
        logging.error(f"Error processing file {tif_file}: {e}")
        return None


def write_result_row(result):
    """Writes one result row (sum and 0-count) for a single date to output files."""
    date = result["Date"]
    arcid_map = result["ArcID_Values"]

    row_sum = {"Date": date}
    row_zero = {"Date": date}

    for arc_id, values in arcid_map.items():
        filtered = [v for v in values if v in (0, 1)]
        if not filtered:
            row_sum[arc_id] = "na"
            row_zero[arc_id] = "na"
        else:
            row_sum[arc_id] = sum(filtered)
            row_zero[arc_id] = filtered.count(0)

    pd.DataFrame([row_sum]).to_csv(sum_file, sep=";", index=False, mode='a', header=not os.path.exists(sum_file))
    pd.DataFrame([row_zero]).to_csv(zero_file, sep=";", index=False, mode='a', header=not os.path.exists(zero_file))


if __name__ == "__main__":
    from tqdm import tqdm

    tif_files = sorted([f for f in os.listdir(tif_folder) if f.endswith(".tif")])

    for tif_file in tqdm(tif_files, desc="Processing TIFF files"):
        result = process_tif(tif_file)
        if result:
            write_result_row(result)
        gc.collect()

    logging.info("Processing completed. Daily values saved to GWP_water_values.csv and GWP_no_water_values.csv.")
