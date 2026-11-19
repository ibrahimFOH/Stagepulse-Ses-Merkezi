#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""13 Stagepulse eğitim PDF'sinin gerçek ders içeriğini, sayfalarını ve platform eşitliğini denetler."""
from pathlib import Path
import sys
import pymupdf

ROOT = Path(__file__).resolve().parents[2]
WIN = ROOT / "windows" / "egitim_paketleri"
AND = ROOT / "android" / "app" / "src" / "main" / "assets" / "egitim_paketleri"
GLOSSARY_MARKER = "TERİM SÖZLÜĞÜ / TECHNICAL GLOSSARY"

# Bu anahtarlar ortak sözlük sayfalarından değil, kitabın asıl ders sayfalarından aranır.
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
GLOSSARY_TERMS = [
    "Compressor", "Noise Gate", "Threshold", "Ratio", "Attack", "Release",
    "Makeup Gain", "Sound Pressure Level", "Real-Time Analysis",
    "Frequency Response", "Sample Rate", "Signal Flow", "Gain Staging",
    "Line Array", "Subwoofer", "Transfer Function", "Impulse Response",
]

def normalized(value: str) -> str:
    return " ".join(value.casefold().split())

def inspect_pdf(path: Path, expected_terms: list[str], platform: str, errors: list[str]) -> tuple[int, int]:
    try:
        with pymupdf.open(path) as doc:
            if doc.is_encrypted:
                errors.append(f"{platform}: şifreli PDF açılamıyor: {path.name}")
                return 0, 0
            if doc.page_count < 2:
                errors.append(f"{platform}: sayfa sayısı yetersiz: {path.name} ({doc.page_count})")
                return doc.page_count, 0

            pages = [page.get_text("text").strip() for page in doc]
            marker_pages = [i for i, text in enumerate(pages) if GLOSSARY_MARKER in text]
            if not marker_pages:
                errors.append(f"{platform}: iki dilli teknik sözlük bölümü bulunamadı: {path.name}")
                content_pages = pages
                glossary_text = ""
            else:
                first_glossary = marker_pages[0]
                content_pages = pages[:first_glossary]
                glossary_text = "\n".join(pages[first_glossary:])

            main_text = "\n".join(content_pages)
            searchable = normalized(main_text)
            glossary_searchable = normalized(glossary_text)

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

            missing_glossary = [term for term in GLOSSARY_TERMS if normalized(term) not in glossary_searchable]
            if missing_glossary:
                errors.append(f"{platform}: iki dilli sözlük terimleri eksik {path.name}: {missing_glossary}")

            all_text = normalized("\n".join(pages))
            if "stagepulse" not in all_text:
                errors.append(f"{platform}: marka/başlık metni eksik: {path.name}")

            print(
                f"OK {platform} {path.name}: {doc.page_count} sayfa; "
                f"{len(content_pages)} ders sayfası; {len(main_text)} ders karakteri"
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
        "Windows/Android kopyaları birebir; ders anahtarları sözlük sayfalarından ayrı doğrulandı."
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
