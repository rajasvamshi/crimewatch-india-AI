import os

# Project root = folder that contains /data and /src
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Choose ONE primary India dataset first
INDIA_CRIME_FILE = os.path.join(
    PROJECT_ROOT, "data", "raw", "districtwise-ipc-crimes-2017-onwards.csv"
)

# Keep this for later (only if you add a global dataset file)
GLOBAL_HOMICIDE_FILE = os.path.join(
    PROJECT_ROOT, "data", "raw", "global_homicide.csv"
)
