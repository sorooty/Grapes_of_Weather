"""ETL Grapes_of_Weather : Météo-France quotidien -> indicateurs par station, puis par région et par millésime.

Étapes (on les construit une par une) :
    1. Extraction  : télécharger les fichiers bruts dans data/raw/
    2. Chargement  : lire les CSV d'un département
    3. Nettoyage   : codes qualité, valeurs manquantes, saison
    4. Indicateurs : métriques agro-climatiques par station et par année
    5. Agrégation  : par région et par millésime, puis écriture dans data/processed/
"""
from pathlib import Path

import requests

from src import config as cfg


# ---------------------------------------------------------------------------
# 1. Extraction
# ---------------------------------------------------------------------------
def download_file(dep: str, period: str, force: bool = False) -> Path:
    """Télécharge le fichier RR-T-Vent d'un département et d'une période dans data/raw/.

    Renvoie le chemin local du fichier. Si le fichier existe déjà et que force=False, il n'est pas retéléchargé.
    """
    # TODO(human)
    raise NotImplementedError


def download_all(force: bool = False) -> None:
    """Télécharge tous les départements de config.REGIONS pour toutes les périodes."""
    for dep in cfg.DEP_TO_REGION:
        for period in cfg.PERIODS:
            path = download_file(dep, period, force)
            print(f"  ✓ {path.name}")


if __name__ == "__main__":
    download_all()
