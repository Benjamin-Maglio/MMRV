import pandas as pd
from pathlib import Path
import glob
import re
from IPython import embed
import pickle
import os

def read_ismn_stm(filepath):
    """Read a single ISMN .stm soil moisture file into a DataFrame."""
    with open(filepath) as f:
        header = f.readline().split()
    
    network, station = header[0], header[1]
    lat, lon, elevation = map(float, header[3:6])
    depth_from, depth_to = float(header[6]), float(header[7])
    sensor = header[8].strip("'")

    df = pd.read_csv(
        filepath,
        skiprows=1,
        sep=r"\s+",
        header=None,
        names=["date", "time", "value", "ismn_flag", "provider_flag"],
    )
    df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"])
    df = df.set_index("datetime")[["value", "ismn_flag", "provider_flag"]]
    df.columns = pd.MultiIndex.from_tuples(
        [(f"{depth_from}-{depth_to}m", c) for c in df.columns]
    )
    df.attrs.update(
        network=network, station=station, lat=lat, lon=lon,
        elevation=elevation, sensor=sensor,
    )
    return df

rel_dir = "./data/raw_data/international_soil_moisture_data/Data_separate_files_header_20251001_20260828_13850_i7SO_20260828/"

ismn_dirs = [
    "USCRN/Boulder-14-W",
    "SNOTEL/Sawtooth",
    "SNOTEL/WildBasin"
]

results = {key: [] for key in ismn_dirs}

for i, site in enumerate(ismn_dirs):

    site_name = site.split("/")[1]

    # Load and merge all depths for this station
    files = sorted(glob.glob(os.path.join(rel_dir+site, "*.stm")))
    
    depth_dfs = [read_ismn_stm(f) for f in files]
    
    sm = pd.concat(depth_dfs, axis=1)

    var_file = [name for name in os.listdir(rel_dir+site) if os.listdir(rel_dir+site) and ".csv" in name][0]

    # Static site metadata (soil texture, land cover, climate)
    static = pd.read_csv(os.path.join(rel_dir+site, var_file), sep=";")

    # save to Pickle for quick review of data
    sm.to_pickle(f"./data/processed_data/international_soil_moisture_data/{site_name}.pkl")   # attrs included automatically
