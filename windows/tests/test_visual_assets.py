from pathlib import Path
from PIL import Image as PILImage
import pymupdf as fitz
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]


def test_brand_logo_and_realistic_concept_image_are_packaged():
    logo = ROOT / 'ui/assets/stagepulse-logo.svg'
    concept = ROOT / 'ui/assets/spl-3d-konsept.png'
    assert logo.is_file() and 'STAGEPULSE' in logo.read_text(encoding='utf-8')
    assert concept.is_file() and concept.stat().st_size > 500_000
    with PILImage.open(concept) as image:
        assert image.width >= 1200 and image.height >= 800


def test_spl_page_contains_dynamic_2d_and_3d_maps_and_explicit_concept_disclaimer():
    html = (ROOT / 'ui/index.html').read_text(encoding='utf-8')
    soup = BeautifulSoup(html, 'html.parser')
    assert soup.find('canvas', id='splMap2d') is not None
    assert soup.find('canvas', id='splMap3d') is not None
    assert soup.find('img', src='/ui/assets/spl-3d-konsept.png') is not None
    assert 'gerçek bir tahmin veya ölçüm değildir' in html
    app = (ROOT / 'ui/app.js').read_text(encoding='utf-8')
    assert 'function splMapLevel(x,y,p)' in app
    assert '20*Math.log10(r/p.refDistance)' in app
    assert 'splColor(L,min,max)' in app


def test_db_visual_shows_correct_pressure_and_power_ratios():
    html = (ROOT / 'ui/index.html').read_text(encoding='utf-8')
    for value in ('+3 dB', '+6 dB', '+10 dB', 'Basınç ×1,41', 'Yoğunluk/güç ×2', 'Basınç ×2', 'Yoğunluk/güç ×4', 'Basınç ×3,16', 'Yoğunluk/güç ×10'):
        assert value in html
    # Core physical ratios for pressure amplitude (20 log) and intensity/power (10 log).
    import math
    assert abs(10 ** (3 / 20) - 1.4125375) < 1e-5
    assert abs(10 ** (3 / 10) - 1.9952623) < 1e-5
    assert abs(10 ** (6 / 20) - 1.9952623) < 1e-5
    assert abs(10 ** (10 / 10) - 10) < 1e-9


def test_student_visual_atlas_is_renderable_four_page_pdf_with_technical_limits():
    path = ROOT / 'egitim_paketleri/09_SPL_dB_3D_Gorsel_Atlasi.pdf'
    assert path.read_bytes().startswith(b'%PDF-')
    pdf = fitz.open(path)
    assert len(pdf) == 7  # 4 özgün atlas sayfası + 3 terminoloji sözlüğü sayfası
    glossary_text = pdf[-1].get_text()
    assert 'Compressor' in glossary_text and 'Noise Gate' in glossary_text
    content = '\n'.join(page.get_text() for page in pdf)
    for phrase in ('SPL, dB ve 3D Görsel Atlası', 'Hesaplanan SPL alan haritası', 'Basınç genliği oranı', 'IEC 61672-1', 'konsept illüstrasyonudur'):
        assert phrase.lower() in content.lower(), phrase


def test_pdf_library_catalog_includes_visual_atlas_and_student_guide_mentions_it():
    import Merkez
    assert any(item['file'] == '09_SPL_dB_3D_Gorsel_Atlasi.pdf' for item in Merkez.STUDENT_PDFS)
    guide = fitz.open(ROOT / 'egitim_paketleri/00_Uygulama_Kullanimi_Ogrenci.pdf')
    content = '\n'.join(page.get_text() for page in guide)
    assert 'SPL, dB ve 3D Görsel Atlası' in content
