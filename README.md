README for MMRV Project
===========================================
> [!NOTE]
> This repository is very much **Under Contruction** and not all features are be up
> and running yet.

This project concerns the development of data download, processing and analysis tools
to track soil moisture and assess it's efficacy as a metric of ecosystem health and
resilience to change. 

The `NISAR SME2` data product is the primary observational variable in this study, 
though as analysis continues more data will be added for predictive purposes.

## Setup
We have chosen to utilize the `conda` package manager to maintain a consistent environment
with that used in development. 

`conda` can be installed using these instructions for your specific operating system: 
- [Windows](https://docs.conda.io/projects/conda/en/latest/user-guide/install/windows.html)
- [macOS](https://docs.conda.io/projects/conda/en/latest/user-guide/install/macos.html)
- [Linux](https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html)

Or by following the instructions on the `conda` website if these are unavailable.

Once installed, create an environment for working with this project based on `environment.yml`:
```conda create --name <environment_name> --file environment.yml``` 

Activate your new environment with:
```conda activate <environment_name>```

## Quick Start
Below is a series of steps assuming this is the first time this repository and 
subsequent data has been downloaded.

> [!NOTE]
> Some paths are hard-coded (e.g. in `ismn_data_processing.py`) so it is best to run scripts
> i.e. `python ./scripts/ismn_data_processing.py` from the main repository directory.

### Downloading and processing NISAR data
In this example we are using the boundary of Boulder County, Colorado to query, download, and then process NISAR SME2
soil moisture data. This is from a geopackage file of US census county boundaries from:
https://geodata.colorado.gov/datasets/14c5450526a8430298b2fa74da12c2f4_0/explore?location=45.137928%2C-123.049258%2C3

> [!NOTE]
> We are working on making this more "generic" for different polygon file types (e.g. `.shp`, `.geojson`, etc.)
> as well as being more flexible with the polygon data (i.e. our example uses Boulder County, a `MultiPolygon`
> object as part of a large group of polygon data.

We have developed a command line tool which can be used to download and then process (pad, clip, and stack) the NISAR
data. It can be called from a terminal / cmd prompt once our `conda` environment has been activated. It looks something 
like this:

```
python ./scripts/nisar_download_and_processing.py --help
```
```

usage: nisar_download_and_processing.py [-h] [--processed_data_directory PROCESSED_DATA_DIRECTORY] [--polygon_file POLYGON_FILE] [--nisar_short_name NISAR_SHORT_NAME]
                                        [--variables VARIABLES [VARIABLES ...]] [--date_start DATE_START] [--date_end DATE_END] [--inspect] [--download]
                                        raw_data_directory

Tool for downloading and processing NISAR data.Still in development, but will likely need a few modifications to work with different NISAR productsand with shapefiles (being
consistent with how they are referenced in the code).

positional arguments:
  raw_data_directory    Directory path to store raw NISAR data.

options:
  -h, --help            show this help message and exit
  --processed_data_directory PROCESSED_DATA_DIRECTORY
                        Directory path to store processed NISAR data.
  --polygon_file POLYGON_FILE
                        File path to polygon of area of interest. This is currently in GeoPackage format.
  --nisar_short_name NISAR_SHORT_NAME
                        Short name for NISAR data download (default: NISAR_L3_SME2_PROVISIONAL_V1).
  --variables VARIABLES [VARIABLES ...]
                        Space-separated list of variables to process (default: ['soilMoisture', 'soilMoistureUncertainty'])
  --date_start DATE_START
                        Start of date window (default: 2025-07, i.e. launch date).
  --date_end DATE_END   End of date window (default: 2026-09 should be today's date, NOTE: this may be a large amount of data).
  --inspect             Print details of first downloaded file. Files must exist of be downloaded.
  --download            Download data, set to False if data is already downloaded.

```
Data can be downloaded and processed in independent call to this function provided by controlling the `--download` flag and providing the `--processed_data_directory`.
An example looks like this:
```
python3 ./scripts/nisar_download_and_processing.py ./data/raw_data/nisar_sme2/ --polygon_file ./data/raw_data/USA_Census_Counties_-2455842672934463084.gpkg --processed_data_directory ./data/processed_data/ --download
```

