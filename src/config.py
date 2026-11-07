"""Configuration centrale de Grapes_of_Weather (chemins, régions, sources)."""
from pathlib import Path

# --- Projet --------------------------------------------------------------
APP_NAME = "Grapes of Weather"
AUTHOR = "Seyni Balde"
PROFESSOR = "Mano Mathew"
COURSE = "BDML1 – Data Visualization & Business Intelligence (EFREI)"

# --- Chemins ------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
STATION_YEAR_CSV = PROCESSED_DIR / "station_year.csv"
REGION_YEAR_CSV = PROCESSED_DIR / "region_year.csv"

# --- Source Météo-France (data.gouv.fr, Licence Ouverte 2.0) --------------
DATASET_URL = "https://www.data.gouv.fr/datasets/donnees-climatologiques-de-base-quotidiennes"
FILE_URL = (
    "https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/BASE/QUOT/"
    "Q_{dep}_{period}_RR-T-Vent.csv.gz"
)
PERIODS = ["previous-1950-2024", "latest-2025-2026"]

# --- Régions viticoles -> départements ----------------------------------
REGIONS: dict[str, list[str]] = {
    "Bordeaux": ["33"],
    "Champagne": ["51", "10"],
    "Alsace": ["67", "68"],
    "Bourgogne": ["21", "71"],
    "Vallée du Rhône": ["26", "84"],
    "Languedoc": ["34", "11"],
}
DEP_TO_REGION = {dep: reg for reg, deps in REGIONS.items() for dep in deps}

# --- Fenêtre d'analyse ---------------------------------------------------
FIRST_VINTAGE = 1950
LAST_VINTAGE = 2026
SEASON_START_MONTH = 4   # avril : débourrement
SEASON_END_MONTH = 10    # octobre : fin des vendanges
