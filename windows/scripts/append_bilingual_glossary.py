#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Her öğrenci PDF'sine ortak Türkçe-İngilizce ses mühendisliği terim tablosu ekler."""
from pathlib import Path
import pymupdf

ROOT = Path(__file__).resolve().parents[2]
WIN = ROOT / "windows" / "egitim_paketleri"
ANDROID = ROOT / "android" / "app" / "src" / "main" / "assets" / "egitim_paketleri"
PDF_NAMES = [
    "00_Uygulama_Kullanimi_Ogrenci.pdf",
    "01_Ses_Muhendisligi_Ogrenci_Ders_Kitabi.pdf",
    "02_Canli_Ses_Live_Sound_Ogrenci_Dersleri.pdf",
    "03_Studio_Ses_Muhendisligi_Ogrenci_Dersleri.pdf",
    "04_Dijital_Ses_Mikseri_Ogrenci_Calisma_Kitabi.pdf",
    "05_Canli_Ses_Mikseri_Hizli_Basvuru.pdf",
    "06_Ogrenci_Uygulama_Formlari.pdf",
    "07_Saha_Olcumu_SPL_Raporlama_Egitimi.pdf",
    "08_SPL_Alan_RTA_Teknik_Uygulama_Eki.pdf",
    "09_SPL_dB_3D_Gorsel_Atlasi.pdf",
    "10_Midas_M32_Live_Uygulamali_Egitim.pdf",
    "11_Yamaha_CL5_Uygulamali_Egitim.pdf",
    "12_Allen_Heath_Avantis_Uygulamali_Egitim.pdf",
]
TERMS = [
    ("Kompresör", "Compressor"), ("Gürültü kapısı", "Noise Gate"),
    ("Eşik", "Threshold"), ("Oran", "Ratio"), ("Diz", "Knee"),
    ("Atak", "Attack"), ("Bırakma", "Release"), ("Çıkış kazancı", "Makeup Gain"),
    ("Kısma aralığı", "Range"), ("Bekletme", "Hold"),
    ("Sinyal akışı", "Signal Flow"), ("Kazanç yapısı", "Gain Staging"),
    ("Giriş / Çıkış", "Input / Output"), ("Ön yükselteç", "Preamplifier"),
    ("Veriyolu", "Bus"), ("Ana çıkış", "Main Output"),
    ("Ses basınç seviyesi", "Sound Pressure Level"),
    ("Gerçek zamanlı analiz", "Real-Time Analysis"),
    ("Frekans yanıtı", "Frequency Response"), ("Gürültü tabanı", "Noise Floor"),
    ("Örnekleme hızı", "Sample Rate"), ("Nyquist frekansı", "Nyquist Frequency"),
    ("Süzgeç", "Filter"), ("Kesim frekansı", "Crossover Frequency"),
    ("Gecikme", "Delay"), ("Faz", "Phase"), ("Polarite", "Polarity"),
    ("Dinamik aralık", "Dynamic Range"), ("Sıkıştırma", "Compression"),
    ("Ses yüksekliği", "Loudness"), ("Tepe seviyesi", "Peak Level"),
    ("Gerçek tepe", "True Peak"), ("A/B karşılaştırma", "A/B Comparison"),
    ("Referans sinyal", "Reference Signal"), ("Kulak eğitimi", "Ear Training"),
    ("Mikrofon", "Microphone"), ("Anten", "Antenna"),
    ("Kablosuz sistem", "Wireless System"), ("Girişim ürünleri", "Intermodulation Products"),
    ("Dijital sinyal işleme", "Digital Signal Processing"),
    ("Hoparlör", "Loudspeaker"), ("Monitör", "Monitor"),
    ("Hat dizisi", "Line Array"), ("Subwoofer", "Subwoofer"),
]
FONT_CANDIDATES = [
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("C:/Windows/Fonts/arial.ttf"),
]
FONT = next((p for p in FONT_CANDIDATES if p.exists()), None)
if FONT is None:
    raise RuntimeError("PDF terminoloji eki için Türkçe karakter destekli font bulunamadı.")

def append_glossary(path: Path) -> None:
    doc = pymupdf.open(path)
    if doc.page_count and "TERİM SÖZLÜĞÜ / TECHNICAL GLOSSARY" in doc[-1].get_text():
        doc.close()
        return
    page = doc.new_page(width=595.28, height=841.89)
    page.insert_text((42, 42), "TERİM SÖZLÜĞÜ / TECHNICAL GLOSSARY", fontfile=str(FONT), fontsize=15, color=(0.12, 0.14, 0.17))
    page.insert_text((42, 62), "Teknik terimler tüm Stagepulse eğitimlerinde aynı karşılıklarla kullanılır.", fontfile=str(FONT), fontsize=8, color=(0.35, 0.38, 0.42))
    x0, x1, x2, x3 = 42, 292, 303, 553
    top, row_h = 88, 29
    page.draw_rect((x0, top, x3, top + row_h*22), color=(0.82,0.84,0.87), width=0.5)
    page.draw_line((x1, top, x1, top + 2*row_h*22), color=(0.82,0.84,0.87), width=0.5)
    page.draw_line((x2, top, x2, top + 2*row_h*22), color=(0.82,0.84,0.87), width=0.5)
    page.insert_text((x0+6, top+15), "Türkçe", fontfile=str(FONT), fontsize=8, color=(0.12,0.14,0.17))
    page.insert_text((x1+6, top+15), "English", fontfile=str(FONT), fontsize=8, color=(0.12,0.14,0.17))
    page.insert_text((x2+6, top+15), "Türkçe", fontfile=str(FONT), fontsize=8, color=(0.12,0.14,0.17))
    page.insert_text((x3-45, top+15), "English", fontfile=str(FONT), fontsize=8, color=(0.12,0.14,0.17))
    y = top + row_h
    half = (len(TERMS)+1)//2
    for i in range(half):
        pairs = [TERMS[i], TERMS[i+half] if i+half < len(TERMS) else ("","")]
        for col, (tr, en) in enumerate(pairs):
            left = x0 if col == 0 else x2
            right = x1 if col == 0 else x3
            yy = y + i*row_h
            page.insert_text((left+6, yy+15), tr, fontfile=str(FONT), fontsize=7.1, color=(0.12,0.14,0.17))
            page.insert_text((left+6, yy+25), en, fontfile=str(FONT), fontsize=6.8, color=(0.35,0.38,0.42))
            if i < half-1:
                page.draw_line((left, yy+row_h, right, yy+row_h), color=(0.9,0.91,0.93), width=0.35)
    page.insert_text((42, 812), "STAGEPULSE · Eğitim terminolojisi / Training terminology", fontfile=str(FONT), fontsize=7, color=(0.4,0.42,0.45))
    temp = path.with_suffix(".bilingual.tmp.pdf")
    doc.save(temp, garbage=4, deflate=True)
    doc.close()
    temp.replace(path)

def main():
    for name in PDF_NAMES:
        source = WIN / name
        if not source.is_file():
            raise FileNotFoundError(f"Eğitim PDF'si bulunamadı: {source}")
        append_glossary(source)
        target = ANDROID / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        with pymupdf.open(source) as check:
            if "TERİM SÖZLÜĞÜ / TECHNICAL GLOSSARY" not in check[-1].get_text():
                raise RuntimeError(f"Terim sözlüğü PDF'ye eklenemedi: {name}")
    print(f"OK: {len(PDF_NAMES)} PDF'ye ortak Türkçe-İngilizce sözlük eklendi; Android/Windows kopyaları eşitlendi.")

if __name__ == "__main__":
    main()
