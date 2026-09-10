#!/usr/bin/env python
"""
Download the minimal covariate set for RF downscaling of NISAR SME2
soil moisture:

  - Sentinel-1 backscatter -> OPERA RTC-S1 (via earthaccess / ASF)
  - NDVI                   -> HLS (Harmonized Landsat Sentinel-2, via earthaccess)
  - Land surface temp      -> MODIS MOD11A2 (via earthaccess)
  - Terrain (DEM)          -> Copernicus DEM GLO-30 (AWS Open Data, no login needed)
  - Soil texture           -> SoilGrids 250m (ISRIC file server, no login needed)

The first three go through NASA Earthdata / earthaccess, same login you're
already using for NISAR. The last two aren't in the Earthdata catalog, so
they're pulled directly with plain HTTP(S) requests instead.
"""

import os
import geopandas as gpd
import earthaccess
import requests
from datetime import date


def get_boulder_county_bounds():
    """Reuse the same county polygon as the NISAR download script."""
    gdf = gpd.read_file(
        "../data/raw_data/usa_census_counties/USA_Census_Counties_-2455842672934463084.gpkg"
    )
    geom = gdf.geometry.iloc[gdf[gdf["NAME"] == "Boulder County"].index[0]]
    return geom.bounds  # (minx, miny, maxx, maxy) in EPSG:4326


# ---------------------------------------------------------------------------
# 1. Sentinel-1 backscatter -> OPERA RTC-S1
# ---------------------------------------------------------------------------

def download_rtc_s1(path_to_raw_data, bounds, date_from, date_to):
    """
    OPERA RTC-S1 (radiometrically terrain corrected Sentinel-1 backscatter),
    archived at ASF and searchable through the standard Earthdata/CMR
    interface earthaccess already uses for NISAR.
    """
    results = earthaccess.search_data(
        short_name="OPERA_L2_RTC-S1_V1",
        bounding_box=bounds,
        temporal=(date_from, date_to),
    )
    print(f"Found {len(results)} OPERA RTC-S1 granules")
    files = earthaccess.download(results, path_to_raw_data)
    return files


# ---------------------------------------------------------------------------
# 2. NDVI -> HLS (Harmonized Landsat Sentinel-2)
# ---------------------------------------------------------------------------

def download_hls(path_to_raw_data, bounds, date_from, date_to, max_cloud_cover=30):
    """
    HLS provides 30 m surface reflectance harmonized across Landsat and
    Sentinel-2, so you only need to manage one product family. Two
    collections cover the two source sensors: HLSL30 (Landsat) and
    HLSS30 (Sentinel-2). Query both and combine.
    """
    all_files = []
    for short_name in ["HLSL30", "HLSS30"]:
        results = earthaccess.search_data(
            short_name=short_name,
            bounding_box=bounds,
            temporal=(date_from, date_to),
            cloud_cover=(0, max_cloud_cover),
        )
        print(f"Found {len(results)} {short_name} granules")
        files = earthaccess.download(results, path_to_raw_data)
        all_files.extend(files)
    return all_files
    # Note: HLS granules are delivered as separate per-band COGs
    # (e.g. ...B04.tif, ...B08.tif for red/NIR). Compute NDVI yourself:
    #   ndvi = (nir - red) / (nir + red)


# ---------------------------------------------------------------------------
# 3. Land surface temperature -> MODIS MOD11A2
# ---------------------------------------------------------------------------

def download_modis_lst(path_to_raw_data, bounds, date_from, date_to):
    """
    MOD11A2: 1 km, 8-day composite LST. An 8-day composite is a reasonable
    match for the ~12-day NISAR repeat and smooths out daily cloud gaps.
    Use MYD11A2 (Aqua) as well if you want twice-daily coverage.
    """
    results = earthaccess.search_data(
        short_name="MOD11A2",
        version="061",
        bounding_box=bounds,
        temporal=(date_from, date_to),
    )
    print(f"Found {len(results)} MOD11A2 granules")
    files = earthaccess.download(results, path_to_raw_data)
    return files
    # Note: MODIS granules are delivered as .hdf with sinusoidal
    # projection; reproject to your working CRS (e.g. with rioxarray/GDAL
    # warp) before use.


# ---------------------------------------------------------------------------
# 4. Terrain -> Copernicus DEM GLO-30 (AWS Open Data, public, no login)
# ---------------------------------------------------------------------------

def download_copernicus_dem(path_to_raw_data, bounds):
    """
    Copernicus DEM GLO-30 is public on AWS, tiled in 1x1 degree cells named
    by their lower-left corner, e.g. Copernicus_DSM_COG_10_N40_00_W106_00_DEM.
    Boulder County spans roughly one or two tiles; this loops over the
    tiles needed to cover the bounding box.
    """
    minx, miny, maxx, maxy = bounds
    os.makedirs(path_to_raw_data, exist_ok=True)
    downloaded = []

    for lat in range(int(miny) - 1, int(maxy) + 1):
        for lon in range(int(minx) - 1, int(maxx) + 1):
            lat_tag = f"N{abs(lat):02d}_00" if lat >= 0 else f"S{abs(lat):02d}_00"
            lon_tag = f"E{abs(lon):03d}_00" if lon >= 0 else f"W{abs(lon):03d}_00"
            tile_name = f"Copernicus_DSM_COG_10_{lat_tag}_{lon_tag}_DEM"
            url = (
                f"https://copernicus-dem-30m.s3.amazonaws.com/"
                f"{tile_name}/{tile_name}.tif"
            )
            out_path = os.path.join(path_to_raw_data, f"{tile_name}.tif")

            resp = requests.head(url)
            if resp.status_code != 200:
                continue  # tile doesn't exist (e.g. over ocean) -> skip

            print(f"Downloading {tile_name}")
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(out_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            downloaded.append(out_path)

    return downloaded
    # Alternative: use `aws s3 cp` / boto3 against s3://copernicus-dem-30m
    # if you prefer the AWS CLI over plain HTTP requests.


# ---------------------------------------------------------------------------
# 5. Soil texture -> SoilGrids 250m (ISRIC file server, public, no login)
# ---------------------------------------------------------------------------

def download_soilgrids(path_to_raw_data, bounds, variables=("sand", "clay", "soc"),
                        depth="0-5cm", stat="mean"):
    """
    Full-resolution SoilGrids tiles are global and large, so for a
    single-county area of interest it's much more practical to use the
    WCS (Web Coverage Service) endpoint, which supports a bounding-box
    GetCoverage request, instead of downloading the global GeoTIFFs.

    variables here follow ISRIC's naming, e.g. 'sand', 'clay', 'soc', 'bdod'.
    """
    minx, miny, maxx, maxy = bounds
    os.makedirs(path_to_raw_data, exist_ok=True)
    downloaded = []

    for var in variables:
        wcs_url = (
            f"https://maps.isric.org/mapserv?map=/map/{var}.map"
            f"&SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage"
            f"&COVERAGEID={var}_{depth}_{stat}"
            f"&FORMAT=image/tiff"
            f"&SUBSET=X({minx},{maxx})&SUBSET=Y({miny},{maxy})"
            f"&SUBSETTINGCRS=http://www.opengis.net/def/crs/EPSG/0/4326"
            f"&OUTPUTCRS=http://www.opengis.net/def/crs/EPSG/0/4326"
        )
        out_path = os.path.join(path_to_raw_data, f"soilgrids_{var}_{depth}.tif")

        print(f"Downloading SoilGrids {var} ({depth})")
        resp = requests.get(wcs_url)
        resp.raise_for_status()
        with open(out_path, "wb") as f:
            f.write(resp.content)
        downloaded.append(out_path)

    return downloaded
    # Note: double-check the exact COVERAGEID / map file naming at
    # https://www.isric.org/explore/soilgrids/faq-soilgrids -- ISRIC has
    # changed endpoint details before, so if a request 404s, confirm the
    # current layer names there rather than assuming this is still exact.


# ---------------------------------------------------------------------------
# Example driver
# ---------------------------------------------------------------------------

def main():
    bounds = get_boulder_county_bounds()
    date_from, date_to = "2025-08", date.today().strftime("%Y-%m")

    earthaccess.login()  # same login used for the NISAR download script

    download_rtc_s1("../data/raw_data/covariates/sentinel1_rtc/", bounds, date_from, date_to)
    download_hls("../data/raw_data/covariates/hls/", bounds, date_from, date_to)
    download_modis_lst("../data/raw_data/covariates/modis_lst/", bounds, date_from, date_to)

    # Static layers -- only need to be pulled once, not per date range
    download_copernicus_dem("../data/raw_data/covariates/dem/", bounds)
    download_soilgrids("../data/raw_data/covariates/soilgrids/", bounds)


if __name__ == "__main__":
    main()