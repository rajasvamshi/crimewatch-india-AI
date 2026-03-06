import pandas as pd
from pathlib import Path
import sys

# Add project root to Python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from src.config import INDIA_CRIME_FILE, GLOBAL_HOMICIDE_FILE


def load_india_crime():
    """
    Load India crime dataset (NCRB).
    """
    df = pd.read_csv(INDIA_CRIME_FILE)
    return df


def load_global_homicide():
    """
    Load global homicide dataset.
    """
    df = pd.read_csv(GLOBAL_HOMICIDE_FILE)
    return df
