# Description

Relabels original NetCDF variables to match SWOT data description: width, slope2, wse. Creates and calculates the following variables: Qhat, d_x_area.

- 'input' directory contains original NetCDF files.
- 'output' directory contains output of relabel execution with one netcdf file per reach.

# Installation and Execution

1. Clone the relabel repo and place input files in the input directory.
2. Create a Python virtual environment `python3 -m venv env`
3. Activate the environment `source env/bin/activate`
3. Execute `pip3 install -r requirements.txt`
4. Execute relabel in virutal environemtn `python3 relabel.py`
5. Retrieve output from output directory.

**NOTE: relabel.py creates full data sets which when run with geobamdata may cause your system to crash due to memory constraints. Instead use relabel-small.py to create 5nx by 10nt datasets.**