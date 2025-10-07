import xarray as xr
import pandas as pd
from collections import defaultdict

# === File paths ===
nc_file = ""
coordinates_file = ""
output_csv = ""
variable_name = "Fw"

# === Open NetCDF dataset ===
ds = xr.open_dataset(nc_file)

# === Load coordinates ===
coordinates_df = pd.read_csv(coordinates_file, sep=";")  # Columns: Arc_ID;longitude;latitude

# === Dictionary: Arc_ID → list of time series for all coordinates in that Arc_ID
arcid_series_map = defaultdict(list)

# === Iterate over coordinates
for _, row in coordinates_df.iterrows():
    arc_id = str(int(row["Arc_ID"]))  # Convert Arc_ID to string for use as column name
    lat = row["latitude"]
    lon = row["longitude"]

    try:
        # Extract the nearest grid cell time series for each coordinate
        series = ds[variable_name].sel(latitude=lat, longitude=lon, method="nearest")
        arcid_series_map[arc_id].append(series)
    except Exception as e:
        print(f"Error with coordinates Arc_ID {arc_id} ({lat}, {lon}): {e}")

# === Output: Which Arc_IDs were processed?
print(f"Processed Arc_IDs: {list(arcid_series_map.keys())}")

# === Aggregate by Arc_ID: average over all coordinates
arcid_df_map = {}

for arc_id, series_list in arcid_series_map.items():
    if not series_list:
        continue
    combined = xr.concat(series_list, dim="points").mean(dim="points", skipna=True)
    df = combined.to_dataframe().reset_index()
    df = df[["time", variable_name]].rename(columns={variable_name: arc_id})
    
    # Skip if all values are NaN
    if df[arc_id].isnull().all():
        print(f"All values for Arc_ID {arc_id} are NaN – skipping.")
        continue

    arcid_df_map[arc_id] = df

# === Output: Which Arc_IDs contain valid data?
print(f"Arc_IDs with valid data: {list(arcid_df_map.keys())}")

# === Merge all Arc_ID DataFrames
merged_df = None
for arc_id, df in arcid_df_map.items():
    if merged_df is None:
        merged_df = df
    else:
        merged_df = pd.merge(merged_df, df, on="time", how="outer")

# === Sort and export final DataFrame
if merged_df is None:
    print("No valid time series found – writing an empty file.")
    pd.DataFrame(columns=["Date"] + list(arcid_series_map.keys())).to_csv(output_csv, sep=";", index=False)
else:
    merged_df = merged_df.sort_values("time")
    merged_df.rename(columns={"time": "Date"}, inplace=True)
    merged_df = merged_df.round(4)
    merged_df.to_csv(output_csv, sep=";", index=False)
    print(f"Final time series table saved to: {output_csv}") 
