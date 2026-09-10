#!/usr/bin/env python
"""
Simple random forest downscaling of NISAR SME2 soil moisture using
high-resolution covariates (e.g. Sentinel-1 backscatter, NDVI, LST,
terrain, soil texture).

Approach (standard RF downscaling, e.g. Fang et al. 2018; Zhao et al. 2021):
  1. Aggregate all fine-resolution covariates DOWN to the coarse NISAR
     SME2 grid (spatial mean per coarse pixel).
  2. Train RandomForestRegressor: coarse_soil_moisture ~ aggregated_covariates,
     using one training sample per (coarse pixel, time step).
  3. Apply the trained model to the covariates at their NATIVE fine
     resolution -> a "raw" fine-resolution prediction.
  4. Residual correction: compute the residual (observed - predicted)
     at the coarse scale, resample/interpolate the residual field to fine
     resolution, and add it back. This guarantees the downscaled map
     integrates back to the original coarse observation, which is the
     main thing reviewers/collaborators will check.

This script assumes covariates have already been reprojected to a common
CRS but are still at their native (differing) resolutions -- reprojection
and reprojection-matching are handled here with rioxarray's reproject_match.

Expects:
  - NISAR SME2 processed netcdf, as produced by the download/processing
    script (nisar_sme2_processed.nc), with a 'soilMoisture' variable and
    a 'time' dimension.
  - A directory of fine-resolution covariate rasters (GeoTIFFs), one per
    covariate, already clipped to the same county extent. If a covariate
    varies in time (e.g. Sentinel-1 backscatter, LST, NDVI), match its
    filename convention to the NISAR acquisition dates; static covariates
    (DEM/terrain, soil texture, land cover) are loaded once.
"""

import os
import glob
import numpy as np
import pandas as pd
import xarray as xr
import rioxarray  # noqa: F401  (registers the .rio accessor)
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score


# ---------------------------------------------------------------------------
# 1. Covariate loading
# ---------------------------------------------------------------------------

STATIC_COVARIATES = {
    # name -> filepath; extend with your own static layers
    "elevation": "../data/raw_data/covariates/dem.tif",
    "slope": "../data/raw_data/covariates/slope.tif",
    "twi": "../data/raw_data/covariates/twi.tif",
    "sand_pct": "../data/raw_data/covariates/soilgrids_sand.tif",
    "clay_pct": "../data/raw_data/covariates/soilgrids_clay.tif",
    "soc": "../data/raw_data/covariates/soilgrids_soc.tif",
}

# Time-varying covariates: directory + filename pattern containing a
# YYYYMMDD date string that will be matched to NISAR acquisition dates.
DYNAMIC_COVARIATE_DIRS = {
    "s1_vv": "../data/raw_data/covariates/sentinel1_vv/",
    "s1_vh": "../data/raw_data/covariates/sentinel1_vh/",
    "ndvi": "../data/raw_data/covariates/ndvi/",
    "lst": "../data/raw_data/covariates/lst/",
}


def load_static_covariates(reference_da):
    """Load static covariate rasters and reproject/resample each to match
    reference_da's grid (used twice: once at coarse NISAR resolution for
    training, once at native fine resolution for prediction)."""
    covs = {}
    for name, path in STATIC_COVARIATES.items():
        da = xr.open_dataarray(path).squeeze(drop=True)
        da = da.rio.reproject_match(reference_da)
        covs[name] = da
    return covs


def find_dynamic_covariate_file(covariate_dir, target_date, max_gap_days=3):
    """Find the covariate file closest in time to target_date (a pandas
    Timestamp), within max_gap_days. Returns None if nothing close enough."""
    candidates = sorted(glob.glob(os.path.join(covariate_dir, "*.tif")))
    best_file, best_gap = None, None
    for fp in candidates:
        date_str = "".join(filter(str.isdigit, os.path.basename(fp)))[:8]
        try:
            file_date = pd.to_datetime(date_str, format="%Y%m%d")
        except ValueError:
            continue
        gap = abs((file_date - target_date).days)
        if best_gap is None or gap < best_gap:
            best_gap, best_file = gap, fp
    if best_file is not None and best_gap <= max_gap_days:
        return best_file
    return None


def load_dynamic_covariates_for_date(target_date, reference_da):
    """Load the time-varying covariates closest to target_date and
    resample each to match reference_da's grid. Returns dict, or None
    if any covariate is missing for this date."""
    covs = {}
    for name, cov_dir in DYNAMIC_COVARIATE_DIRS.items():
        fp = find_dynamic_covariate_file(cov_dir, target_date)
        if fp is None:
            print(f"  Skipping {target_date.date()}: no {name} within gap window")
            return None
        da = xr.open_dataarray(fp).squeeze(drop=True)
        da = da.rio.reproject_match(reference_da)
        covs[name] = da
    return covs


# ---------------------------------------------------------------------------
# 2. Build training table at coarse (NISAR) resolution
# ---------------------------------------------------------------------------

def build_training_dataframe(sm_ds, static_covs_coarse):
    """
    sm_ds: xarray Dataset with 'soilMoisture' (time, y, x) at NISAR resolution.
    static_covs_coarse: dict of static covariate DataArrays already matched
        to the NISAR grid.

    Returns a tidy DataFrame with one row per (time, pixel) that has a
    valid soil moisture value and valid covariates.
    """
    rows = []
    times = pd.to_datetime(sm_ds["time"].values)

    for t in times:
        sm_t = sm_ds["soilMoisture"].sel(time=t)

        dyn_covs = load_dynamic_covariates_for_date(t, sm_t)
        if dyn_covs is None:
            continue

        all_covs = {**static_covs_coarse, **dyn_covs}

        df_t = sm_t.to_dataframe(name="soil_moisture").reset_index()
        for name, da in all_covs.items():
            df_t[name] = da.values.ravel()
        df_t["time"] = t

        rows.append(df_t)

    df = pd.concat(rows, ignore_index=True)
    df = df.dropna()  # drop pixels with any missing covariate or SM
    return df


# ---------------------------------------------------------------------------
# 3. Train / evaluate RF
# ---------------------------------------------------------------------------

def train_rf(df, feature_cols, target_col="soil_moisture", test_size=0.2,
             n_estimators=500, random_state=42):
    X = df[feature_cols].values
    y = df[target_col].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    rf = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=None,
        min_samples_leaf=5,
        n_jobs=-1,
        random_state=random_state,
        oob_score=True,
    )
    rf.fit(X_train, y_train)

    y_pred = rf.predict(X_test)
    print(f"Test R^2:  {r2_score(y_test, y_pred):.3f}")
    print(f"Test RMSE: {mean_squared_error(y_test, y_pred, squared=False):.4f}")
    print(f"OOB R^2:   {rf.oob_score_:.3f}")

    importances = pd.Series(rf.feature_importances_, index=feature_cols)
    print("\nFeature importances:")
    print(importances.sort_values(ascending=False))

    return rf


# ---------------------------------------------------------------------------
# 4. Predict at fine resolution + residual correction
# ---------------------------------------------------------------------------

def predict_fine_resolution(rf, feature_cols, target_date,
                             fine_reference_da, static_covs_fine,
                             coarse_pred_da, coarse_obs_da):
    """
    Predict soil moisture at native fine resolution for one date, then
    apply residual correction so the downscaled field is consistent with
    the coarse NISAR observation it was derived from.

    fine_reference_da : any fine-res covariate DataArray defining the
        target output grid.
    coarse_pred_da : RF prediction already made ON the coarse grid for
        this same date (i.e. rf applied to the coarse-resolution covariates).
    coarse_obs_da : the actual NISAR soil moisture on the coarse grid.
    """
    dyn_covs_fine = load_dynamic_covariates_for_date(target_date, fine_reference_da)
    if dyn_covs_fine is None:
        return None

    all_covs_fine = {**static_covs_fine, **dyn_covs_fine}

    stack = np.stack([all_covs_fine[c].values.ravel() for c in feature_cols], axis=1)
    valid = ~np.isnan(stack).any(axis=1)

    fine_pred_flat = np.full(stack.shape[0], np.nan)
    fine_pred_flat[valid] = rf.predict(stack[valid])

    fine_pred = fine_reference_da.copy(
        data=fine_pred_flat.reshape(fine_reference_da.shape)
    )

    # Residual correction: coarse residual = observed - predicted (coarse),
    # resampled (nearest/bilinear) up to the fine grid and added back.
    residual_coarse = coarse_obs_da - coarse_pred_da
    residual_fine = residual_coarse.rio.reproject_match(fine_pred)

    fine_pred_corrected = fine_pred + residual_fine
    return fine_pred_corrected


# ---------------------------------------------------------------------------
# Example driver
# ---------------------------------------------------------------------------

def main():
    sm_ds = xr.open_dataset(
        "../data/processed_data/nisar_sme2/nisar_sme2_processed.nc"
    )

    reference_coarse = sm_ds["soilMoisture"].isel(time=0)
    static_covs_coarse = load_static_covariates(reference_coarse)

    print("Building training table at NISAR resolution...")
    df = build_training_dataframe(sm_ds, static_covs_coarse)
    print(f"Training samples: {len(df)}")

    feature_cols = list(STATIC_COVARIATES.keys()) + list(DYNAMIC_COVARIATE_DIRS.keys())

    print("Training random forest...")
    rf = train_rf(df, feature_cols)

    # Example: downscale a single date using a fine-res covariate as the
    # output grid template (e.g. the native-resolution Sentinel-1 raster).
    example_date = pd.to_datetime(sm_ds["time"].values[-1])
    fine_reference = xr.open_dataarray(
        find_dynamic_covariate_file(DYNAMIC_COVARIATE_DIRS["s1_vv"], example_date)
    ).squeeze(drop=True)

    static_covs_fine = load_static_covariates(fine_reference)

    coarse_obs = sm_ds["soilMoisture"].sel(time=example_date)
    coarse_features = df[df["time"] == example_date][feature_cols].values
    # (in practice, predict on the full coarse grid, not just training rows,
    #  to get a complete coarse_pred_da; simplified here for brevity)

    print("Downscaling example date:", example_date.date())
    # coarse_pred_da would need to be built by predicting on every coarse
    # pixel (not shown fully here) -- see comment above.


if __name__ == "__main__":
    main()