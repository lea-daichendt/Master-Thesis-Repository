import xarray as xr
import pandas as pd
from collections import defaultdict

# === Paths ===
nc_file = ""
coordinates_file = ""
output_csv = ""
variable_name = "Fw"

# === Open NetCDF ===
ds = xr.open_dataset(nc_file)

# === Load coordinates ===
coordinates_df = pd.read_csv(coordinates_file, sep=";")  # Columns: Arc_ID;longitude;latitude

# === Dictionary: Arc_ID → list of point time series
arcid_series_map = defaultdict(list)

# === Loop through points
for _, row in points_df.iterrows():
    arc_id = str(int(row["Arc_ID"]))  # Use string for column name
    lat = row["latitude"]
    lon = row["longitude"]

    try:
        # Extract point (nearest)
        series = ds[variable_name].sel(lat=lat, lon=lon, method="nearest")
        arcid_series_map[arc_id].append(series)
    except Exception as e:
        print(f"Error at point Arc_ID {arc_id} ({lat}, {lon}): {e}")

# === Aggregation: average per Arc_ID
arcid_df_map = {}

for arc_id, series_list in arcid_series_map.items():
    if not series_list:
        continue
    combined = xr.concat(series_list, dim="points").mean(dim="points")
    df = combined.to_dataframe().reset_index()
    df = df[["time", variable_name]].rename(columns={variable_name: arc_id})
    arcid_df_map[arc_id] = df

# === Merge all DataFrames based on time
merged_df = None
for arc_id, df in arcid_df_map.items():
    if merged_df is None:
        merged_df = df
    else:
        merged_df = pd.merge(merged_df, df, on="time", how="outer")

# === Sort & Save
merged_df = merged_df.sort_values("time")
merged_df.rename(columns={"time": "Date"}, inplace=True)
merged_df.to_csv(output_csv, sep=";", index=False)

print(f"WAD2M time series saved at: {output_csv}")
