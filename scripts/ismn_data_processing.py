import pandas as pd
import glob
import re
from IPython import embed
import pickle


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

# Load and merge all depths for this station
files = sorted(glob.glob("../data/raw_data/Data_separate_files_header_20251001_20260828_13850_i7SO_20260828/USCRN/Boulder-14-W/*Boulder-14-W*sm_*.stm"))
depth_dfs = [read_ismn_stm(f) for f in files]
sm = pd.concat(depth_dfs, axis=1)

# Quick look
print(sm.head())
print(sm.xs("value", axis=1, level=1).describe())  # just the values, all depths

# Static site metadata (soil texture, land cover, climate)
static = pd.read_csv(
    "../data/raw_data/Data_separate_files_header_20251001_20260828_13850_i7SO_20260828/USCRN/Boulder-14-W/USCRN_USCRN_Boulder-14-W_static_variables.csv",
    sep=";",
)
print(static)

sm.to_pickle("../data/processed_data/ismn/boulder_14_W.pkl")   # attrs included automatically
