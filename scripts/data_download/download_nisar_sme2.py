#!/usr/bin/env python
"""
Script to download NISAR soil moisture (SME2) data OR
update existing data as available.
"""
import os
import sys
import argparse

def check_existing_data(path):
  '''
  Check whether any nisar soil moisture
  data has already been downloaded. Data
  will be stacked and processed into a 
  particular style within a directory and
  this is what this function will search for.
  
  Return details on the existing data and the
  new available data on the server. E.g. date
  ranges, number of new files available, size
  of data, etc. 
  '''

  return

def download_data(date_from, date_to, all=True):
  '''
  This function will download new data files 
  as identified by check_existing_data.
  
  Arguments for a specific data range could be
  utilized here, and if none are provided, all
  data will be downloaded.

  This will return a list of downloaded file
  names
  '''

  return file_names

def might also want to think about downloading other ancillary data with this script.







# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmdline_define() -> argparse.ArgumentParser:
  """Define the command line interface and return the parser object."""
  parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent("""
      WIEMIP postprocessing for dvm-dos-tem outputs.

      Runs four stages in order:
        1. wetland merging
        2. unit conversion
        3. variable combination
        4. visuals production
    """),
  )
  parser.add_argument(
    "directory_a",
    type=Path,
    metavar="directoryA",
    help="First input directory (e.g. a model run or output tree).",
  )
  parser.add_argument(
    "directory_b",
    type=Path,
    metavar="directoryB",
    help="Second input directory (e.g. a model run or output tree).",
  )
  parser.add_argument(
    "wetland",
    type=Path,
    metavar="wetland",
    help=(
      "NetCDF with vegetation information (veg_pct_cov, veg_class) "
      "used to weight wetland merging."
    ),
  )
  parser.add_argument(
    "output_directory",
    type=Path,
    metavar="output_directory",
    help="Directory where postprocessed products will be written.",
  )
  return parser


def cmdline_parse(argv=None) -> argparse.Namespace:
  """Parse argv (or sys.argv[1:]) according to the CLI specification."""
  parser = cmdline_define()
  return parser.parse_args(argv)


def cmdline_run(args: argparse.Namespace) -> int:
  """Execute the four postprocessing sections from parsed CLI args."""
  directory_a = args.directory_a
  directory_b = args.directory_b
  wetland = args.wetland
  output_directory = args.output_directory

  output_directory.mkdir(parents=True, exist_ok=True)

  merged_directory = output_directory / 'merged'
  units_converted_directory = output_directory / 'units_converted'
  variable_combined_directory = output_directory / 'variable_combined'

  merged_directory.mkdir(parents=True, exist_ok=True)
  units_converted_directory.mkdir(parents=True, exist_ok=True)
  variable_combined_directory.mkdir(parents=True, exist_ok=True)

  wetland_merging(directory_a, directory_b, wetland, merged_directory)

  unit_conversion(merged_directory, units_converted_directory)

  variable_combination(directory_a, directory_b, variable_combined_directory)

  visuals_production(directory_a, directory_b, output_directory)

  return 0


def cmdline_entry(argv=None) -> int:
  """Parse CLI args and run; convenient for tests and ``main``."""
  args = cmdline_parse(argv)
  return cmdline_run(args)


def main(argv=None) -> int:
  return cmdline_entry(argv=argv)


if __name__ == "__main__":
  sys.exit(main())
