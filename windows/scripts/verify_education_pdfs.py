#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""13 Stagepulse eğitim PDF'sinin ders içeriğini, görsel sözlüğünü ve platform eşitliğini denetler."""
from pathlib import Path
import sys
import pymupdf

ROOT = Path(__file__).resolve().parents[2]
WIN = ROOT / "windows" / "egitim_paketleri"
AND = ROOT / "android" / "app" / "src" / "main" / "assets" / "egitim_paketleri"

# append_bilingual_glossary.py: 98 terim, sayfa başına 44 terim, toplam 3 sözlük sayfası.
GLOSSARY_PAGE_COUNT = 3

# Anahtarlar yalnızca asıl ders sayfalarında aranır; ortak sözlük sayfaları kapsam kanıtı sayılmaz.
EXPECTED = {
    "00_Uygulama_Kullanimi_Ogrenci.pdf": ["Öğrenci", "RTA", "Nyquist", "kalibr"],
    "01_Ses_Muhendisligi_Ogrenci_Ders_Kitabi.pdf": ["Dalga", "dB SPL", "polarite", "Sabine"],
    "02_Canli_Ses_Live_Sound_Ogrenci_Dersleri.pdf": ["FOH", "monitör", "soundcheck", "sub", "intermodülasyon", "anten", "drop-out"],
    "03_Studio_Ses_Muhendisligi_Ogrenci_Dersleri.pdf": ["DAW", "LUFS", "true peak", "mono", "mastering", "dither"],
    "04_Dijital_Ses_Mikseri_Ogrenci_Calisma_Kitabi.pdf": ["routing", "DCA", "bus", "scene"],
    "05_Canli_Ses_Mikseri_Hizli_Basvuru.pdf": ["Gain", "phantom", "IEM", "arıza"],
    "06_Ogrenci_Uygulama_Formlari.pdf": ["kanıt", "eğitmen", "ölçüm", "rubrik"],
    "07_Saha_Olcumu_SPL_Raporlama_Egitimi.pdf": ["LAeq", "kalibrasyon", "belirsizlik", "LCpeak"],
    "08_SPL_Alan_RTA_Teknik_Uygulama_Eki.pdf": ["20 µPa", "Sabine", "Nyquist", "NIOSH"],
    "09_SPL_dB_3D_Gorsel_Atlasi.pdf": ["SPL", "3D", "IEC 61672-1", "konsept"],
    "10_Midas_M32_Live_Uygulamali_Egitim.pdf": ["Midas M32", "AES50", "DCA", "monitor"],
    "11_Yamaha_CL5_Uygulamali_Egitim.pdf": ["Yamaha CL5", "Dante", "Centralogic", "Scene"],
    "12_Allen_Heath_Avantis_Uygulamali_Egitim.pdf": ["Avantis", "Mix bus", "DCA", "Scene"],
}

def normalized(value: str) -> str:
    return " ".join(value.casefold().split())

def rendered_ink_ratio(page) -> float:
    """Metin katmanı font eşlemesinden bağımsız olarak sayfanın görünür içerik taşıdığını doğrular."""
    pix = page.get_pixmap(matrix=pymupdf.Matrix(0.5, 0.5), colorspace=pymupdf.csRGB, alpha=False)
    samples = pix.samples
    channels = pix.n
    dark_pixels = 0
    for offset in range(0, len(samples), channels):
        if min(samples[offset], samples[offset + 1], samples[offset + 2]) < 235:
            dark_pixels += 1
    return dark_pixels / max(1, pix.width * pix.height)

def inspect_pdf(path: Path, expected_terms: list[str], platform: str, errors: list[str]) -> tuple[int, int]:
    try:
        with pymupdf.open(path) as doc:
            if doc.is_encrypted:
                errors.append(f"{platform}: şifreli PDF açılamıyor: {path.name}")
                return 0, 0
            if doc.page_count <= GLOSSARY_PAGE_COUNT + 1:
                errors.append(f"{platform}: ders/sözlük sayfa sayısı yetersiz: {path.name} ({doc.page_count})")
                return doc.page_count, 0

            pages = [page.get_text("text").strip() for page in doc]
            content_pages = pages[:-GLOSSARY_PAGE_COUNT]
            main_text = "\n".join(content_pages)
            searchable = normalized(main_text)

            if len(main_text) < 1200:
                errors.append(f"{platform}: asıl ders metni 1.200 karakterin altında: {path.name} ({len(main_text)})")
            if len(content_pages) < 2:
                errors.append(f"{platform}: sözlük dışında yeterli ders sayfası yok: {path.name}")
            nonempty = sum(bool(text.strip()) for text in content_pages)
            if content_pages and nonempty / len(content_pages) < 0.80:
                errors.append(f"{platform}: ders bölümünde boş/metinsiz sayfa oranı yüksek: {path.name} ({nonempty}/{len(content_pages)})")

            missing = [term for term in expected_terms if normalized(term) not in searchable]
            if missing:
                errors.append(f"{platform}: kitaba özgü ders içeriği eksik {path.name}: {missing}")

            glossary_ratios = [
                rendered_ink_ratio(doc[index])
                for index in range(doc.page_count - GLOSSARY_PAGE_COUNT, doc.page_count)
            ]
            for offset, ratio in enumerate(glossary_ratios, start=1):
                if ratio < 0.001:
                    errors.append(
                        f"{platform}: sözlük sayfası görsel olarak boş: {path.name} "
                        f"(sözlük sayfası {offset}, görünür içerik oranı {ratio:.5f})"
                    )

            if "stagepulse" not in normalized("\n".join(pages)):
                errors.append(f"{platform}: marka/başlık metni eksik: {path.name}")

            print(
                f"OK {platform} {path.name}: {doc.page_count} sayfa; "
                f"{len(content_pages)} ders sayfası; {len(main_text)} ders karakteri; "
                f"sözlük görünürlük oranları={','.join(f'{x:.3f}' for x in glossary_ratios)}"
            )
            return doc.page_count, len(main_text)
    except Exception as exc:
        errors.append(f"{platform}: PDF açılamadı {path.name}: {type(exc).__name__}: {exc}")
        return 0, 0

def main() -> int:
    errors: list[str] = []
    for name, terms in EXPECTED.items():
        win_path = WIN / name
        android_path = AND / name
        if not win_path.is_file():
            errors.append(f"Windows PDF eksik: {name}")
            continue
        if not android_path.is_file():
            errors.append(f"Android PDF eksik: {name}")
            continue
        if win_path.stat().st_size < 1024 or android_path.stat().st_size < 1024:
            errors.append(f"PDF dosyası 1 KB altında: {name}")
            continue
        if win_path.read_bytes() != android_path.read_bytes():
            errors.append(f"Android/Windows PDF byte eşitliği bozuk: {name}")
        inspect_pdf(win_path, terms, "Windows", errors)
        inspect_pdf(android_path, terms, "Android", errors)

    expected_names = set(EXPECTED)
    for label, directory in (("Windows", WIN), ("Android", AND)):
        actual_names = {p.name for p in directory.glob("*.pdf")} if directory.is_dir() else set()
        missing = sorted(expected_names - actual_names)
        unexpected = sorted(actual_names - expected_names)
        if missing:
            errors.append(f"{label}: kitaplıkta eksik PDF: {missing}")
        if unexpected:
            errors.append(f"{label}: katalog dışı PDF dosyaları var: {unexpected}")

    if errors:
        print("PDF DENETİMİ BAŞARISIZ")
        for error in errors:
            print(" - " + error)
        return 1

    print(
        f"PDF DENETİMİ GEÇTİ: {len(EXPECTED)} özgün PDF; "
        "ders anahtarları sözlükten ayrı, üç sözlük sayfası görsel olarak, "
        "Android/Windows kopyaları byte düzeyinde doğrulandı."
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
