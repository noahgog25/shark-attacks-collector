"""
Etape de collecte.

Copie le fichier source vers data/raw/ avec un nom horodate. Cette copie
n'est plus jamais modifiee ensuite : c'est elle qui fait foi comme preuve
de collecte brute.

Pour l'instant la source est un fichier local (l'extrait Kaggle deja
telecharge dans data/source/). Le point d'entree est deliberement isole
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
DEFAULT_SOURCE = ROOT / "data" / "source" / "global_shark_attacks-selected-columns.csv"


def collect(source_path: str | Path | None = None) -> Path:
    """Copie le fichier source vers data/raw/<timestamp>.csv et retourne son chemin."""
    source = Path(source_path) if source_path else DEFAULT_SOURCE
    if not source.exists():
        raise FileNotFoundError(f"Source introuvable : {source}")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destination = RAW_DIR / f"shark_attacks_{stamp}.csv"
    shutil.copyfile(source, destination)
    return destination


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
