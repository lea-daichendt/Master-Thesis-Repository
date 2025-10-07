import os
import rasterio
import pandas as pd
import numpy as np
from collections import defaultdict
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Paths
coordinates_file = ""
tif_folder = ""
output_txt = "GSW_water_values.csv"


def process_tif_file(tif_file, coordinate_rows):
    """Processes a single TIFF file and extracts pixel values."""
    try:
        with rasterio.open(os.path.join(tif_folder, tif_file)) as dataset:
            band_data = dataset.read(1)
            bounds = dataset.bounds

            arcid_pixel_map = defaultdict(list)

            for lon, lat, arc_id in coordinate_rows:
                arc_id_str = str(int(arc_id))  # Ensure Arc_ID is string (e.g., "63662")
                if not (bounds.left <= lon <= bounds.right and bounds.bottom <= lat <= bounds.top):
                    continue
                row, col = dataset.index(lon, lat)
                if 0 <= row < band_data.shape[0] and 0 <= col < band_data.shape[1]:
                    pixel_value = band_data[row, col]
                    arcid_pixel_map[arc_id_str].append(pixel_value)

        # Extract date (e.g. "2020-01-something.tif" → "2020")
        date = tif_file.split("-")[0]
        return {"Date": date, "ArcID_Values": dict(arcid_pixel_map)}

    except Exception as e:
        logging.error(f"Error processing {tif_file}: {e}")
        return None


def aggregate_results(results):
    """Aggregates pixel values == 2 per Arc_ID per date; also handles only-1 cases by returning 0."""
    combined_by_date = defaultdict(lambda: defaultdict(list))

    for result in results:
        if not result:
            continue
        date = result["Date"]
        for arc_id, values in result["ArcID_Values"].items():
            combined_by_date[date][arc_id].extend(values)

    final_rows = []
    for date, arcid_map in combined_by_date.items():
        row = {"Date": date}
        for arc_id, values in arcid_map.items():
            values = [v for v in values if v is not None]

            if not values:
                result = "na"
            elif any(v == 2 for v in values):
                result = sum(1 for v in values if v == 2)
            elif all(v in (0, 1) for v in values):
                result = 0
            else:
                result = "na"

            row[arc_id] = result
        final_rows.append(row)

    return final_rows


def generate_GSW_no_observation(results, output_path="GSW_no_observation.csv"):
    combined_by_date = defaultdict(lambda: defaultdict(list))

    for result in results:
        if not result:
            continue
        date = result["Date"]
        for arc_id, values in result["ArcID_Values"].items():
            combined_by_date[date][arc_id].extend(values)

    # Gather all Arc_IDs as strings
    all_arc_ids = sorted(set(str(k) for arcid_map in combined_by_date.values() for k in arcid_map.keys()))

    rows = []
    for date, arcid_map in combined_by_date.items():
        row = {"Date": date}
        for arc_id in all_arc_ids:
            values = arcid_map.get(arc_id, [])  # look up as str
            values = [v for v in values if v in (0, 1, 2)]

            if not values:
                row[arc_id] = "na"
            else:
                zero_count = sum(1 for v in values if v == 0)
                total_valid = len(values)
                percentage = round((zero_count / total_valid) * 100, 1)
                row[arc_id] = percentage
        rows.append(row)

    df = pd.DataFrame(rows).sort_values(by="Date")
    df.to_csv(output_path, sep=";", index=False)
    logging.info(f"GSW_no_observation saved to: {output_path}")


if __name__ == "__main__":
    # Read coordinates
    coordinates_df = pd.read_csv(coordinates_file, sep=";")
    coordinate_rows = coordinates_df[["longitude", "latitude", "Arc_ID"]].values

    # Process TIFF files
    tif_files = [f for f in os.listdir(tif_folder) if f.endswith(".tif")]
    results = [process_tif_file(tif_file, coordinate_rows) for tif_file in tif_files]

    # Aggregate analysis
    final_results = aggregate_results(results)
    final_df = pd.DataFrame(final_results)

    for col in final_df.columns:
        if col != "Date":
            final_df[col] = final_df[col].apply(lambda x: int(x) if isinstance(x, (float, int)) and not pd.isna(x) else x)

    # Save main table
    final_df.to_csv(output_txt, sep=";", index=False)
    logging.info(f"Results saved to {output_txt}.")

    # Save zero-percentage report
    generate_GSW_no_observation(results, output_path=" ") 
