# Tests de fumée : on ouvre le jeu construit dans Chromium et on vérifie qu'il démarre
# et que la boucle de base (carte → fouille → établi) tourne sans erreur JavaScript.
#
# Lancement local :
#   python3 ci/build.py            # construit dist/ depuis le zip des sources
#   pytest tests/ -v
#
# Variables d'environnement :
#   DIST_DIR  dossier des fichiers construits (défaut : dist)
#   THREE_JS  copie locale de three.min.js r128 (sinon chargé depuis le CDN)
#   SHOTS_DIR dossier des captures d'écran (défaut : shots)
#   CHROMIUM  chemin d'un Chromium déjà installé (sinon celui de Playwright)
import os
import pathlib

import pytest
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = pathlib.Path(os.environ.get('DIST_DIR', ROOT / 'dist')).resolve()
SHOTS = pathlib.Path(os.environ.get('SHOTS_DIR', ROOT / 'shots')).resolve()
THREE_JS = os.environ.get('THREE_JS')
CHROMIUM = os.environ.get('CHROMIUM')

VIEWPORTS = {'mobile': (390, 844), 'desktop': (1280, 800)}


@pytest.fixture(scope='session')
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROMIUM, args=['--use-gl=swiftshader', '--enable-webgl',
                                                             '--ignore-gpu-blocklist',
                                                             '--autoplay-policy=no-user-gesture-required'])
        yield b
        b.close()


def open_page(browser, name, query='', size='mobile'):
    w, h = VIEWPORTS[size]
    pg = browser.new_page(viewport={'width': w, 'height': h})
    pg.errors = []
    pg.on('pageerror', lambda e: pg.errors.append(str(e)))
    pg.route('**/fonts.*/**', lambda r: r.abort())
    if THREE_JS:
        pg.route('**/three.min.js', lambda r: r.fulfill(path=THREE_JS, content_type='application/javascript'))
    pg.goto((DIST / name).as_uri() + query)
    pg.wait_for_timeout(1500)
    return pg


def shot(pg, name):
    SHOTS.mkdir(parents=True, exist_ok=True)
    pg.screenshot(path=str(SHOTS / f'{name}.png'))


def test_build_present():
    for f in ['carnet-de-fouille.html', 'preview.html', 'preview-debug.html']:
        assert (DIST / f).stat().st_size > 100_000, f


@pytest.mark.parametrize('size', VIEWPORTS)
def test_title_screen(browser, size):
    """La version publiée s'ouvre sur l'écran d'accueil, et toucher le carnet lance la partie."""
    pg = open_page(browser, 'preview.html', size=size)
    assert pg.title() == 'Carnet de Fouille'
    assert pg.evaluate('typeof THREE') == 'object', 'three.js non chargé'
    assert pg.locator('.title-screen').count() == 1
    shot(pg, f'{size}-accueil')
    pg.locator('.nb').click()
    pg.wait_for_timeout(2500)
    assert pg.locator('.title-screen').count() == 0
    shot(pg, f'{size}-apres-accueil')
    assert pg.errors == []
    pg.close()


@pytest.mark.parametrize('size', VIEWPORTS)
def test_dig_and_bench(browser, size):
    """Carte → on creuse une poche → la pierre arrive à l'établi 3D → on la fend."""
    pg = open_page(browser, 'preview-debug.html', size=size)
    assert pg.evaluate('typeof window.__dbg') == 'function'
    if pg.locator('#inSkip').count():
        pg.locator('#inSkip').click(force=True)
        pg.wait_for_timeout(400)
    pg.evaluate("() => { const d = window.__dbg(); if (d.tuto()) d.tutoFinish(); d.closeSay(); d.show('carte'); }")
    pg.wait_for_timeout(800)
    assert pg.evaluate('() => window.__dbg().G.site.poches.length') > 0
    shot(pg, f'{size}-carte')

    pg.evaluate("""() => { const d = window.__dbg(); d.G.notes.pierre = 1;
      const q = d.G.site.poches[0]; d.dig({ x: q.x, y: q.y }); }""")
    pg.wait_for_timeout(2500)
    pg.evaluate("() => { const d = window.__dbg(); d.closeSay(); if (d.G.stone && !d.Bench3D.debug().ST) d.show('etabli'); }")
    pg.wait_for_timeout(1200)
    assert pg.evaluate('() => !!window.__dbg().Bench3D.debug().ST'), "aucune pierre à l'établi"
    shot(pg, f'{size}-etabli')

    pg.evaluate("""() => { const d = window.__dbg(), D = d.Bench3D.debug(); d.closeSay();
      const pl = D.ST.planes[0]; D.tap(pl.contour.pts[D.hotIndex(pl)]); D.strike(pl.contour.pts[D.hotIndex(pl)], 1); }""")
    pg.wait_for_timeout(3000)
    shot(pg, f'{size}-pierre-fendue')
    assert pg.errors == []
    pg.close()
