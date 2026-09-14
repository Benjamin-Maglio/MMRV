#!/usr/bin/env python
"""
Script to download NISAR soil moisture (SME2) data OR
update existing data as available.
"""
import os
import sys
import argparse
import matplotlib.pyplot as plt
from IPython import embed
import earthaccess
import geopandas as gpd
import xarray as xr
import numpy as np
import glob
import re
import pandas as pd
from datetime import date
import h5py

def inspect_h5_file(filepath):
    """Print structure and details of an HDF5 file: groups, datasets, shapes, dtypes, and attributes."""
    with h5py.File(filepath, 'r') as f:
        print(f"Inspecting: {filepath}\n" + "-" * 50)

        def visit(name, obj):
            indent = "  " * name.count("/")
            if isinstance(obj, h5py.Dataset):
                print(f"{indent}[Dataset] {name}")
                print(f"{indent}    shape: {obj.shape}, dtype: {obj.dtype}")
                if obj.size <= 10:
                    print(f"{indent}    values: {obj[()]}")
            elif isinstance(obj, h5py.Group):
                print(f"{indent}[Group] {name}")

            # Print attributes attached to this object
            for key, val in obj.attrs.items():
                print(f"{indent}    attr - {key}: {val}")

        # Print root-level attributes first
        for key, val in f.attrs.items():
            print(f"[Root attr] {key}: {val}")

        f.visititems(visit)

def find_corrupted_h5_files(path_to_raw_data):
    '''
    Check every .h5 file in the directory for readability.
    Returns a list of filepaths that fail to open cleanly.
    '''
    filepaths = [
        os.path.join(path_to_raw_data, f)
        for f in os.listdir(path_to_raw_data)
        if f.endswith(".h5")
    ]

    bad_files = []
    for fp in sorted(filepaths):
        try:
            with h5py.File(fp, "r") as f:
                if "science/LSAR/SME2/grids" not in f:
                    print(f"Missing expected group: {fp}")
                    bad_files.append(fp)
        except OSError as e:
            print(f"Corrupted/unreadable: {fp}\n  {e}")
            bad_files.append(fp)
    return bad_files

def download_data(path_to_raw_data, polygon_file, nisar_short_name, date_start, date_end, inspect=False):
  '''
  This function will download new data files 
  as identified by check_existing_data.
  
  Arguments for a specific data range could be
  utilized here, and if none are provided, all
  data will be downloaded.

  This will return a list of downloaded file
  names
  '''

  # Load area of interest - this could be make more generic for multiple polygon formats (e.g. .shp, .kml, .geojson, etc.)
  print("This workflow was initially developed using the following dataset in geopackage format:")
  print("https://geodata.colorado.gov/datasets/14c5450526a8430298b2fa74da12c2f4_0/explore?location=45.137928%2C-123.049258%2C3\n")
  print(polygon_file,"\n")
  gdf = gpd.read_file(polygon_file)
  

  # Select Boulder County geometry
  geom = gdf.geometry.iloc[gdf[gdf['NAME']=='Boulder County'].index[0]]

  # Authorize Earth Data account for data search and download
  earthaccess.login()

  # Query search Earth Data for NISAR SME2 data 
  # There is NISAR_L3_SME2_BETA_V1 and NISAR_L3_SME2_PROVISIONAL_V1 
  results = earthaccess.search_data(
    short_name=nisar_short_name,
    bounding_box=geom.bounds,
    temporal=(date_start, date_end)
  )

  print(results)

  files = earthaccess.download(results, path_to_raw_data)

  max_retries = 5

  for attempt in range(max_retries):
          bad_files = find_corrupted_h5_files(path_to_raw_data)
          if not bad_files:
              break
          print(f"Attempt {attempt+1}: re-downloading {len(bad_files)} corrupted file(s)")
          for f in bad_files:
              os.remove(f)
          earthaccess.download(results, path_to_raw_data)
  else:
      remaining = find_corrupted_h5_files(path_to_raw_data)
      if remaining:
          print(f"WARNING: {len(remaining)} file(s) still corrupted after {max_retries} attempts:")
          for f in remaining:
              print(" ", f)

  if inspect:
    inspect_h5_file(results[0])

  return 

def load_extend_and_clip_raw_nisar_data(filepath, polygon_file, variables=None):
    '''
    Load in, pad / extend, and then clip raw data
    to shapefile extent of bounding box.

    Parameters
    ----------
    filepath : str
        Path to the NISAR .h5 file.
    variables : list of str, optional
        Names of data variables to keep from the group. If None,
        all variables in the group are kept.
    '''
    ds = xr.open_dataset(filepath, group="science/LSAR/SME2/grids", engine="h5netcdf") # this would need to be made more flexible / automated
    ds = ds.rio.set_spatial_dims(x_dim="xCoordinates", y_dim="yCoordinates")
    ds = ds.rio.write_crs("EPSG:6933")

    # Subset to requested variables right after opening, so pad/clip only
    # ever touch what you actually want.
    if variables is not None:
        missing = set(variables) - set(ds.data_vars)
        if missing:
            raise ValueError(f"Requested variables not found in {filepath}: {missing}")
        ds = ds[variables]

    # Load area of interest - this could be make more generic for multiple polygon formats (e.g. .shp, .kml, .geojson, etc.)
    gdf = gpd.read_file(polygon_file).to_crs(ds.rio.crs)
    polygon = gdf[gdf["NAME"] == "Boulder County"]

    if gdf.crs != ds.rio.crs:
        gdf = gdf.to_crs(ds.rio.crs)

    minx, miny, maxx, maxy = polygon.total_bounds

    for var in ds.data_vars:
        if ds[var].rio.nodata is None:
            if np.issubdtype(ds[var].dtype, np.floating):
                ds[var] = ds[var].rio.write_nodata(np.nan)
            else:
                ds[var] = ds[var].rio.write_nodata(ds[var].rio.nodata)

    ds_extended = ds.rio.pad_box(minx=minx, miny=miny, maxx=maxx, maxy=maxy)
    ds_clipped = ds_extended.rio.clip(polygon.geometry, all_touched=True)

    return ds_clipped

def extract_datetime_from_filename(filepath):
    '''
    Extract acquisition start datetime from NISAR filename.
    e.g. ..._20260810T020535_20260810T020610_... -> first timestamp = start time
    '''
    match = re.search(r"_(\d{8}T\d{6})_(\d{8}T\d{6})_", filepath)
    if not match:
        raise ValueError(f"Could not parse datetime from filename: {filepath}")
    return pd.to_datetime(match.group(1), format="%Y%m%dT%H%M%S")

def build_nisar_timeseries(path_to_raw_data, processed_data_directory, polygon_file, nisar_short_name, variables=None, inspect=False):
    '''
    Loop through NISAR files, extend/clip each to polygon extent,
    and concatenate into a single Dataset along a time dimension.

    Parameters
    ----------
    path_to_raw_data : str
        Directory containing the raw .h5 NISAR files.
    variables : list of str, optional
        Names of data variables to keep. If None, all variables
        in the group are kept.
    '''
    ds_list = []

    filepaths = [os.path.join(path_to_raw_data, f) for f in os.listdir(path_to_raw_data) if f.endswith('.h5')]

    if inspect:
        inspect_h5_file(filepaths[0])

    for fp in sorted(filepaths):
        ds_clipped = load_extend_and_clip_raw_nisar_data(fp, polygon_file, variables=variables)
        timestamp = extract_datetime_from_filename(fp)

        ds_clipped = ds_clipped.expand_dims(time=[timestamp])
        ds_list.append(ds_clipped)

    for ds in ds_list:
        print(ds.rio.bounds(), {v: ds[v].shape for v in ds.data_vars})

    ref_x = ds_list[0]["xCoordinates"]
    ref_y = ds_list[0]["yCoordinates"]

    ds_list = [ds.assign_coords(xCoordinates=ref_x, yCoordinates=ref_y) for ds in ds_list]

    ds_combined = xr.concat(ds_list, dim="time", join="outer")
    ds_combined = ds_combined.sortby("time")

    print(f"{os.path.join(processed_data_directory, nisar_short_name)}.nc")

    ds_combined.to_netcdf(f"{os.path.join(processed_data_directory, nisar_short_name)}.nc", engine="netcdf4")

    return 

# download_data("../data/raw_data/nisar_sme2/")#"2025-09","2026-09",
# build_nisar_timeseries("../data/raw_data/nisar_sme2/", variables=['soilMoisture','soilMoistureUncertainty'])


def main(raw_data_directory, processed_data_directory, polygon_file,
         nisar_short_name, variables, date_start, date_end,
         inspect=False, download=False):

        if download:
            print('======================================')
            print('Initiating data search and download...\n')
            download_data(raw_data_directory, polygon_file, nisar_short_name, date_start, date_end, inspect=False)
        if processed_data_directory!=None:
                print('=======================================================')
                print('Initiating compiling of NISAR time series from raw data...\n')
                build_nisar_timeseries(raw_data_directory, processed_data_directory, polygon_file, nisar_short_name, variables, inspect=False)

DEFAULT_SHORT_NAME = "NISAR_L3_SME2_PROVISIONAL_V1"
DEFAULT_VARIABLES = ['soilMoisture', 'soilMoistureUncertainty']
DEFAULT_DATE_START = '2025-07'
DEFAULT_DATE_END = date.today().strftime("%Y-%m")
DEFAULT_INSPECT = False
DEFAULT_DOWNLOAD = False

# CLI
if __name__ == "__main__":
   parser = argparse.ArgumentParser(description="Tool for downloading and processing NISAR data." \
   "Still in development, but will likely need a few modifications to work with different NISAR products" \
   "and with shapefiles (being consistent with how they are referenced in the code).")

   parser.add_argument("raw_data_directory", type=str, help="Directory path to store raw NISAR data.")

   parser.add_argument("--processed_data_directory", type=str, help="Directory path to store processed NISAR data.")
   parser.add_argument("--polygon_file", type=str, help="File path to polygon of area of interest. This is currently in GeoPackage format.")

   parser.add_argument("--nisar_short_name", type=str, default=DEFAULT_SHORT_NAME,
                         help=f"Short name for NISAR data download (default: {DEFAULT_SHORT_NAME}).")
   parser.add_argument("--variables", nargs="+", default=DEFAULT_VARIABLES,
                         help=f"Space-separated list of variables to process (default: {DEFAULT_VARIABLES})")
   parser.add_argument("--date_start", type=str, default=DEFAULT_DATE_START,
                         help=f"Start of date window (default: {DEFAULT_DATE_START}, i.e. launch date).")
   parser.add_argument("--date_end", type=str, default=date.today().strftime("%Y-%m"),
                         help=f"End of date window (default: {DEFAULT_DATE_END} should be today's date, NOTE: this may be a large amount of data).")

   parser.add_argument("--inspect", action="store_true", help="Print details of first downloaded file. Files must exist of be downloaded.")
   parser.add_argument("--download", action="store_true", help="Download data, set to False if data is already downloaded.")

   args = parser.parse_args()
   
   main(args.raw_data_directory, args.processed_data_directory, args.polygon_file, args.nisar_short_name, args.variables, 
   args.date_start, args.date_end, inspect=args.inspect, download=args.download)