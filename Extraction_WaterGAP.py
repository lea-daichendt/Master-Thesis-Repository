from netCDF4 import Dataset
import pandas as pd
import numpy as np
import os

# === User-defined paths ===
nc_path = ""  # Path to the WaterGAP NetCDF file
coordinates_file = ""  # Path to CSV file containing Arc_ID;longitude;latitude
output_folder = ""  # Folder to store the output CSV files

# === Time range (filtering window) ===
start_date = "2003-01-01"
end_date = "2019-12-31"

# === Variables to extract ===
variables = ["locwet_extent", "glowet_extent"]  # local and global wetlands

# === Open NetCDF dataset ===
ds = Dataset(nc_path, 'r')

# === Convert time to readable format ===
time_var = ds.variables['time']
start_year = 1901
time_index = pd.date_range(start=f"{start_year}-01", periods=len(time_var), freq='MS')

# === Filter time to 2003–2019 ===
mask = (time_index >= start_date) & (time_index <= end_date)
filtered_time_index = time_index[mask]

# === Load coordinate points ===
coordinates = pd.read_csv(coordinates_file, sep=';')  # Columns: Arc_ID;longitude;latitude
lats = ds.variables['lat'][:]
lons = ds.variables['lon'][:]

# === Extract data for each variable ===
for varname in variables:
    print(f"🔹 Extracting {varname} ...")

    var_data = ds.variables[varname]
    data_dict = {}

    for index, row in coordinates.iterrows():
        arc_id = str(row['Arc_ID'])
        lat = row['latitude']
        lon = row['longitude']

        # Find nearest grid cell
        lat_idx = (np.abs(lats - lat)).argmin()
        lon_idx = (np.abs(lons - lon)).argmin()

        # Extract time series for this point
        series = var_data[:, lat_idx, lon_idx]
        df = pd.DataFrame({arc_id: series}, index=time_index)

        # Filter to 2003–2019
        df = df.loc[start_date:end_date]

        data_dict[arc_id] = df

    # === Combine all DataFrames ===
    if data_dict:
        result_df = pd.concat(data_dict.values(), axis=1)
    else:
        result_df = pd.DataFrame(index=filtered_time_index)

    # === Save output ===
    output_file = os.path.join(output_folder, f"{varname}_2003-2019.csv")
    result_df.to_csv(output_file, sep=';')

    print(f"✅ {varname} saved to: {output_file}")

# === Close dataset ===
ds.close()
print("Extraction completed.")

