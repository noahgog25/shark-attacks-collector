"""
Etape de collecte.

Copie le fichier source vers data/raw/ avec un nom horodate. Cette copie
n'est plus jamais modifiee ensuite : c'est elle qui fait foi comme preuve
de collecte brute.

Pour l'instant la source est un fichier local (l'extrait Kaggle conserve
dans data/raw/). Le point d'entree est deliberement isole
dans cette fonction pour pouvoir, plus tard, le remplacer par un appel a
une API sans toucher au reste du pipeline.
"""

from __future__ import annotations

import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
RAW_PATH = RAW_DIR / "global_shark_attacks_raw.csv"
DEFAULT_SOURCE = RAW_PATH
SAMPLE_SOURCE = ROOT / "data" / "samples" / "sample_source.csv"


def collect(source_path: str | Path | None = None) -> Path:
    """Conserve une copie brute horodatee de la source et la retourne."""
    source = Path(source_path) if source_path else DEFAULT_SOURCE
    if source_path is None and not source.is_file() and SAMPLE_SOURCE.is_file():
        source = SAMPLE_SOURCE
    if not source.is_file():
        raise FileNotFoundError(f"Source introuvable : {source}")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    suffix = source.suffix or ".csv"
    snapshot = RAW_DIR / f"source_{timestamp}{suffix}"
    shutil.copyfile(source, snapshot)
    return snapshot


def sha256_file(path: str | Path) -> str:
    """Retourne l'empreinte SHA-256 d'un fichier pour sa traçabilité."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    import sys

    arg = sys.argv[1] if len(sys.argv) > 1 else None
    path = collect(arg)
    print(f"Collecte terminee -> {path}")
