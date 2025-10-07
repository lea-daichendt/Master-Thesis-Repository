# Wetland Extent Extraction Scripts

This repository contains Python and ArcGIS Pro workflows used to extract and aggregate wetland extent data from multiple sources — **GSW**, **GWP**, **GIEMS2**, **WAD2M**, and **WaterGAP** — aligned to the **WaterGAP model grid cells**.  
All procedures were developed for the Master’s thesis:

> *Improving wetland dynamics modeling in Southern Africa based on remotely-sensed time series of wetland extent*  
> 2025 Lea Daichendt, Goethe University Frankfurt am Main

---

## Extraction of Monthly Data – General Workflow

1. All datasets were spatially aligned with **WaterGAP grid cells**.  
   Grid-cell coordinates (longitude / latitude / `Arc_ID`) were exported as CSV.  
2. For each dataset, relevant pixel values were extracted using Python scripts (see subsections below).  
3. Values were aggregated both **spatially** (per grid cell) and **temporally** (to monthly or daily resolution).  
4. Due to differing resolutions, temporal coverages, and formats (TIFF vs NetCDF), specific adjustments were implemented per dataset.

---

## GSW – Global Surface Water

**Input:** Monthly GSW maximum surface-water-extent GeoTIFFs (https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GSWE/MonthlyHistory/)
**Python script:** `Extraction_GSW.py`  
**Temporal resolution:** monthly (2003–2019)

### ArcGIS Pre-processing
1. Load maximum surface-water-extent rasters in ArcGIS Pro 3.3.2.  
2. Values: 0 = no water ever, 1 = water observed ≥ once, 2–255 = no value.  
3. Use **Extract by Attributes** to keep value = 1 only, then merge rasters (Data Management → Merge).  
4. Align raster to WaterGAP grid and clip lakes using **HydroLakes + Clip Raster**.  
5. Convert raster → points (**Raster to Points**) and assign grid cells via **Identity**.  
6. Export coordinates + `Arc_ID` as CSV.

### Python Extraction
- Loads the coordinate table and iterates over all monthly TIFFs.  
- Extracts pixel values (0 = no observation, 1 = no water, 2 = water detected).  
- Counts:
  - **Water pixels** (value = 2) per grid cell per month.  
  - **No-observation pixels** (value = 0).  
- Writes two CSV tables:
  - `GSW_water_values.csv` – monthly counts of water pixels.  
  - `GSW_no_observation.csv` – monthly counts of no-data pixels.  
- Using Excel, monthly percentages and areas (km²) were calculated by dividing pixel counts by the total number of pixels per grid cell.  
- Months with only no-data values were excluded.

### Output
- **Monthly time series** (2003–2019) of surface-water percentage and area (km²).  
- **Maximum surface-water extent** (% and km²) per WaterGAP grid cell.

---

## GWP – Global WaterPack

**Input:** Daily MODIS-based GWP water-classification GeoTIFFs  (https://download.geoservice.dlr.de/GWP/files/daily/)
**Python script:** `Extraction_GWP.py`  
**Temporal resolution:** daily (aggregated to monthly averages)

### ArcGIS Pre-processing
1. Load each daily TIFF in ArcGIS Pro.  
2. Assign every pixel to its WaterGAP grid cell (**Clip Raster**, **Identity**).  
3. Exclude lakes with HydroLakes (**Clip Raster**).  
4. Calculate geographic coordinates and export as CSV (`Arc_ID;longitude;latitude`).

### Python Extraction
- Iterates through all daily TIFF files (2003–2019).  
- For each `Arc_ID`, counts:
  - **Water pixels** (value = 1).  
  - **Land pixels** (value = 0).  
- Produces two daily CSV tables:
  - `GWP_water_values.csv` – daily sum of water pixels.  
  - `GWP_no_water_values.csv` – daily count of land pixels.  
- A post-processing step calculates the **percentage of water per day** and then averages by month to produce **monthly mean values** comparable to GSW and WaterGAP.

### Output
- **Daily and monthly time series** of surface water percentage per WaterGAP grid cell.  
- Lakes excluded; months with no valid pixels removed.

---

## GIEMS-2 – Global Inundation Extent from Multi-Satellites 2

**Input:** NetCDF (0.25° × 0.25°) with variables time, latitude, longitude, inundation fraction (`Fw`)  (https://zenodo.org/records/16530038)
**Python script:** `Extraction_GIEMS2.py`  
**Temporal resolution:** monthly (2003–2019)

### Method
1. Load NetCDF in ArcGIS and assign raster cells to WaterGAP grid cells.  
2. Convert to points and export coordinates + `Arc_ID`.  
3. Python script:
   - Loads the NetCDF and coordinate table.  
   - Extracts `Fw` for each coordinate.  
   - Averages all points per grid cell → monthly mean inundation fraction (%).  
4. Surface-water area (km²) = fraction × grid-cell area.

---

##  WAD2M – Wetland Area and Dynamics for Methane Modeling

**Input:** NetCDF (0.25° × 0.25°) with variables time, latitude, longitude, `fw` (inundated fraction)  (https://zenodo.org/records/3998454)
**Python script:** `Extraction_WAD2M.py`  
**Temporal resolution:** monthly (2003–2019)

### Method
- Identical workflow to GIEMS-2.  
- Extracts `fw` values, aggregates per WaterGAP grid cell, outputs monthly inundation fractions (%).  
- Converts fractions to areas (km²) using grid-cell size.

---

## WaterGAP – Model Output (Local & Global Wetlands)

**Input:** Two NetCDF files containing fraction of local (`locwet_extent`) and global (`glowet_extent`) wetlands  
**Python script:** `extract_watergap_points_daily.py`  
**Temporal resolution:** daily (2003–2019, aggregated to monthly data)

### Method
1. Extract centroid coordinates and `Arc_ID` for each WaterGAP grid cell.  
2. Python script:
   - Loads both NetCDF files and coordinate table.  
   - Extracts `locwet_extent` and `glowet_extent` values per grid cell.  
   - Aggregates to monthly means (2003–2019).  
   - Calculates surface-water area (km²) and percentage of total cell area.  
3. Outputs:
   - `locwet_extent_2003-2019.csv`  
   - `glowet_extent_2003-2019.csv`  
   - Each contains monthly wetland area (km²) and fraction (%).

---

## Software & Dependencies

| Tool | Purpose |
|------|----------|
| **ArcGIS** | Pre-processing, coordinate extraction, clipping lakes |
| **Python** | Automated pixel extraction & aggregation |
| **rasterio** | Reading GeoTIFFs |
| **netCDF4** | Reading NetCDF datasets |
| **pandas**, **numpy** | Data handling and aggregation |
| **tqdm**, **logging**, **multiprocessing** | Parallel processing and progress reporting |


## Output Summary

| Dataset | Resolution | Period | Unit | Output Files |
|----------|-------------|---------|------|---------------|
| GSW | Monthly | 2003–2019 | % / km² | `GSW_water_values.csv`, `GSW_no_observation.csv` |
| GWP | Daily → Monthly | 2003–2019 | % / km² | `GWP_water_values.csv`, `GWP_no_water_values.csv` |
| GIEMS-2 | Monthly | 2003–2019 | % / km² | `GIEMS2_inundation.csv` |
| WAD2M | Monthly | 2003–2019 | % / km² | `WAD2M_inundation.csv` |
| WaterGAP | Daily | 2003–2019 | % / km² | `locwet_extent_2003-2019.csv`, `glowet_extent_2003-2019.csv` |

---

## Notes
- All months with only **No-Data** values were excluded from the analysis.  
- Final monthly time series are spatially and temporally consistent across all datasets.

## How to Prepare and Run the Scripts

Before running any Python script, some preparation steps are required to ensure that all input data and file paths are correctly defined.

---

### Download Input Data
GSW: https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GSWE/MonthlyHistory/
GWP: https://download.geoservice.dlr.de/GWP/files/daily/
GIEMS2: https://zenodo.org/records/3998454
WAD2M: https://zenodo.org/records/16530038 

---

### Create Coordinate Files

All scripts rely on a **coordinate table** linking WaterGAP grid cells to their geographic positions.  
This file must contain the following columns:Arc_ID;longitude;latitude 

###  Define Input and Output Paths

Before execution, open the corresponding Python script (e.g., `extract_gsw_points.py`) and edit the path variables at the top of the file:

```python
coordinates_file = "path/to/coordinates.txt"
tif_folder = "path/to/tif_folder"       # or nc_file = "path/to/file.nc"
output_folder = "path/to/output_folder"

