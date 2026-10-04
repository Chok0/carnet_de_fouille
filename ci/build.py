"""Construit le jeu depuis carnet-de-fouille-sources.zip, comme en local.

    python3 ci/build.py           # → dist/carnet-de-fouille.html, dist/preview.html, dist/preview-debug.html
    python3 ci/build.py --check   # échoue si carnet-de-fouille.html (racine) ne correspond plus aux sources
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
ZIP = ROOT / 'carnet-de-fouille-sources.zip'
DIST = ROOT / 'dist'
PUBLISHED = ROOT / 'carnet-de-fouille.html'

with tempfile.TemporaryDirectory() as tmp:
    work = pathlib.Path(tmp)
    zipfile.ZipFile(ZIP).extractall(work)
    (work / 'dist').mkdir(exist_ok=True)
    subprocess.run([sys.executable, 'build.py'], cwd=work, check=True)
    shutil.rmtree(DIST, ignore_errors=True)
    shutil.copytree(work / 'dist', DIST)

if '--check' in sys.argv:
    if (DIST / 'preview.html').read_bytes() != PUBLISHED.read_bytes():
        sys.exit(f'{PUBLISHED.name} ne correspond pas aux sources du zip : reconstruisez-le et recommitez les deux.')
    print(f'{PUBLISHED.name} est à jour avec les sources.')
