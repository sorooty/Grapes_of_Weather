"""ETL Grapes_of_Weather : des relevés quotidiens Météo-France aux indicateurs par station, par région et par millésime.

Étapes du pipeline :
    1. Extraction  : télécharger les fichiers bruts dans data/raw/
    2. Chargement  : lire les CSV d'un département
    3. Nettoyage   : codes qualité, valeurs manquantes, saison
    4. Indicateurs : métriques agro-climatiques par station et par année
    5. Agrégation  : par région et par millésime, puis écriture dans data/processed/
"""
from pathlib import Path

import pandas as pd
import requests

from src import config as cfg


# ---------------------------------------------------------------------------
# 1. Phase d'extraction
# ---------------------------------------------------------------------------
# La signature de la fonction précise les types attendus en entrée et en sortie.
def download_file(dep: str, period: str, force: bool = False) -> Path:
    """Télécharge le fichier RR-T-Vent d'un département et d'une période dans data/raw/.

    Renvoie le chemin local du fichier. Si le fichier existe déjà et que force=False, il n'est pas retéléchargé.
    """
    # Construction de l'URL distante.
    url = cfg.FILE_URL.format(period=period, dep=dep)
    
    # Construction du chemin local du fichier.
    filename = url.split("/")[-1]
    path = cfg.RAW_DIR / Path(filename)
    # print(path)
    
    # Fichier déjà présent : pas de nouveau téléchargement, sauf si force=True.
    if path.exists() and not force :
        print('deja la !')
        return path
    
    # Téléchargement par blocs : création du dossier, envoi de la requête, écriture du fichier.
    path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=60) as response :
        response.raise_for_status()
        with open(path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024): 
                f.write(chunk)
        return path


def download_all(force: bool = False) -> None:
    """Télécharge tous les départements de config.REGIONS pour toutes les périodes."""
    for dep in cfg.DEP_TO_REGION:
        for period in cfg.PERIODS:
            path = download_file(dep, period, force)
            print(f"  OK {path.name}")


# ---------------------------------------------------------------------------
# 2. Chargement
# ---------------------------------------------------------------------------
# Les fichiers RR-T-Vent comptent environ 60 colonnes : chaque mesure X est suivie de son
# code qualité QX (ex. TN puis QTN). On ne garde que ce qui sert aux indicateurs.
USECOLS: list[str] = [
    "NUM_POSTE", "NOM_USUEL", "LAT", "LON", "ALTI", "AAAAMMJJ",
    "RR", "QRR",   # précipitations (mm)
    "TN", "QTN",   # température minimale (degrés Celsius)
    "TX", "QTX",   # température maximale (degrés Celsius)
]


def load_department(dep: str) -> pd.DataFrame:
    """Lit et concatène toutes les périodes d'un département, avec une colonne DATE parsée."""
    frames = []
    for period in cfg.PERIODS:
        path = download_file(dep, period)  # réutilise le cache
        df = pd.read_csv(
            path,
            sep=";",
            usecols=USECOLS,
            dtype={"NUM_POSTE": str},  # garder les zéros de tête éventuels
            compression="gzip",
        )
        frames.append(df)

    df = pd.concat(frames, ignore_index=True)
    df["DATE"] = pd.to_datetime(df["AAAAMMJJ"].astype(str), format="%Y%m%d")
    df["DEP"] = dep
    df["REGION"] = cfg.DEP_TO_REGION[dep]
    return df.drop(columns="AAAAMMJJ")


# ---------------------------------------------------------------------------
# 3. Nettoyage
# ---------------------------------------------------------------------------
# Codes qualité Météo-France : 0 = protégée, 1 = validée, 9 = brute non encore validée.
# Les autres (2 = douteuse en vérification, ...) sont considérés comme invalides.
VALID_QUALITY = {0, 1, 9}
MEASURES = ["RR", "TN", "TX"]


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Masque les mesures de qualité douteuse et garde la saison viticole (d'avril à octobre)."""
    df = df.copy()
    for col in MEASURES:
        q = df[f"Q{col}"]
        bad = q.notna() & ~q.isin(VALID_QUALITY)
        df.loc[bad, col] = float("nan")
    df = df.drop(columns=[f"Q{c}" for c in MEASURES])

    month = df["DATE"].dt.month
    df = df[month.between(cfg.SEASON_START_MONTH, cfg.SEASON_END_MONTH)]
    df["YEAR"] = df["DATE"].dt.year
    return df[df["YEAR"].between(cfg.FIRST_VINTAGE, cfg.LAST_VINTAGE)]


# ---------------------------------------------------------------------------
# 4. Indicateurs par station et par année
# ---------------------------------------------------------------------------
GDD_BASE = 10.0          # zéro de végétation de la vigne, en degrés Celsius
HEAT_THRESHOLD = 35.0    # seuil d'un jour de canicule, en degrés Celsius
MIN_COVERAGE = 0.9       # part minimale de jours avec TN et TX valides dans la saison


def gdd_daily(tn: pd.Series, tx: pd.Series) -> pd.Series:
    """Degrés-jours de croissance (indice de Winkler) pour chaque jour."""
    # TODO(human)
    raise NotImplementedError


def station_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Une ligne par (station, année) avec les indicateurs agro-climatiques de la saison."""
    df = df.assign(
        GDD=gdd_daily(df["TN"], df["TX"]),
        FROST=(df["TN"] < 0) & df["DATE"].dt.month.isin([4, 5]),   # gel de printemps
        HEAT=df["TX"] > HEAT_THRESHOLD,
        TMEAN=(df["TN"] + df["TX"]) / 2,
        VALID_T=df["TN"].notna() & df["TX"].notna(),
    )
    keys = ["NUM_POSTE", "NOM_USUEL", "LAT", "LON", "ALTI", "DEP", "REGION", "YEAR"]
    out = df.groupby(keys, as_index=False).agg(
        gdd=("GDD", "sum"),
        frost_days=("FROST", "sum"),
        heat_days=("HEAT", "sum"),
        tmean=("TMEAN", "mean"),
        rain_mm=("RR", "sum"),
        n_valid=("VALID_T", "sum"),
    )
    season_days = 214  # du 1er avril au 31 octobre
    out["coverage"] = out["n_valid"] / season_days
    return out[out["coverage"] >= MIN_COVERAGE].drop(columns="n_valid")


# ---------------------------------------------------------------------------
# 5. Agrégation par région et millésime + écriture
# ---------------------------------------------------------------------------
INDICATORS = ["gdd", "frost_days", "heat_days", "tmean", "rain_mm"]


def region_year(stations: pd.DataFrame) -> pd.DataFrame:
    """Moyenne des stations de chaque région, par millésime."""
    out = stations.groupby(["REGION", "YEAR"], as_index=False).agg(
        **{c: (c, "mean") for c in INDICATORS},
        n_stations=("NUM_POSTE", "nunique"),
    )
    return out.round(2)


def run() -> None:
    """Pipeline complet : téléchargement, traitement, puis écriture de station_year.csv et region_year.csv."""
    download_all()
    parts = []
    for dep in cfg.DEP_TO_REGION:
        print(f"Traitement du département {dep}...")
        parts.append(station_indicators(clean(load_department(dep))))
    stations = pd.concat(parts, ignore_index=True)

    cfg.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    stations.to_csv(cfg.STATION_YEAR_CSV, index=False)
    regions = region_year(stations)
    regions.to_csv(cfg.REGION_YEAR_CSV, index=False)
    print(f"{len(stations)} lignes station-année, {len(regions)} lignes région-année.")


if __name__ == "__main__":
    run()
