# Carnet de Fouille

Jeu de fouille paléontologique en un seul fichier HTML.

- `carnet-de-fouille-sources.zip` : les sources (`src/`, `build.py`, outils)
- `carnet-de-fouille.html` : le jeu construit, à ouvrir dans un navigateur

## GitHub Actions

Le workflow `.github/workflows/ci.yml` tourne à chaque push et pull request :

1. **Build** : dézippe les sources et lance `build.py`. Échoue si `carnet-de-fouille.html`
   ne correspond plus au zip (penser à recommiter les deux ensemble).
2. **Tests de fumée** dans Chromium, en mobile et en desktop : écran d'accueil, carte,
   coup de pelle, pierre à l'établi 3D, pierre fendue, sans aucune erreur JavaScript.
   Les captures d'écran sont téléchargeables dans l'onglet *Actions* (artefact `captures`).
3. **Publication** sur GitHub Pages (branche `main` uniquement, si les tests passent) :
   - `/` : le jeu
   - `/debug.html` : la préversion avec `window.__dbg()` dans la console

> À faire une fois : *Settings → Pages → Build and deployment → Source : **GitHub Actions***.

## En local

```sh
pip install -r tests/requirements.txt
python -m playwright install chromium
python3 ci/build.py --check   # → dist/
python3 -m pytest tests -v    # → shots/
```
