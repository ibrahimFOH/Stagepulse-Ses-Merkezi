#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Her öğrenci PDF'sine ortak Türkçe-İngilizce ses mühendisliği terim tablosu ekler."""
from pathlib import Path
import re
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
    ("Kompresör", "Compressor"),
    ("Gürültü kapısı", "Noise Gate"),
    ("Eşik", "Threshold"),
    ("Oran", "Ratio"),
    ("Diz", "Knee"),
    ("Atak", "Attack"),
    ("Atak süresi", "Attack Time"),
    ("Bırakma", "Release"),
    ("Bırakma süresi", "Release Time"),
    ("Çıkış kazancı", "Makeup Gain"),
    ("Kısma aralığı", "Range"),
    ("Bekletme", "Hold"),
    ("Ham sinyal", "Dry Signal"),
    ("İşlenmiş sinyal", "Processed Signal"),
    ("Test sinyali", "Test Signal"),
    ("Konuşma benzeri sinyal", "Speech-like Signal"),
    ("Vurmalı sinyal", "Drum Signal"),
    ("Bas sinyali", "Bass Signal"),
    ("Sinyal akışı", "Signal Flow"),
    ("Kazanç yapısı", "Gain Staging"),
    ("Giriş / Çıkış", "Input / Output"),
    ("Ön yükselteç", "Preamplifier"),
    ("Kazanç", "Gain"),
    ("Kazanç azaltımı", "Gain Reduction"),
    ("Baş boşluğu", "Headroom"),
    ("Kırpılma", "Clipping"),
    ("Veriyolu", "Bus"),
    ("Ana çıkış", "Main Output"),
    ("Gönderim", "Send"),
    ("Dönüş", "Return"),
    ("Ekleme", "Insert"),
    ("Yan zincir", "Sidechain"),
    ("Kaydırma", "Pan"),
    ("Susturma", "Mute"),
    ("Tek başına dinleme", "Solo"),
    ("Sürgü", "Fader"),
    ("Ses basınç seviyesi", "Sound Pressure Level"),
    ("Gerçek zamanlı analiz", "Real-Time Analysis"),
    ("Frekans yanıtı", "Frequency Response"),
    ("Gürültü tabanı", "Noise Floor"),
    ("Örnekleme hızı", "Sample Rate"),
    ("Örnekleme frekansı", "Sampling Frequency"),
    ("Bit derinliği", "Bit Depth"),
    ("Nyquist frekansı", "Nyquist Frequency"),
    ("Süzgeç", "Filter"),
    ("Yüksek geçiren filtre", "High-Pass Filter"),
    ("Alçak geçiren filtre", "Low-Pass Filter"),
    ("Bant geçiren filtre", "Band-Pass Filter"),
    ("Bant durduran filtre", "Band-Stop Filter"),
    ("Kesim frekansı", "Crossover Frequency"),
    ("Merkez frekans", "Center Frequency"),
    ("Faz", "Phase"),
    ("Polarite", "Polarity"),
    ("Gecikme", "Delay"),
    ("Gecikme telafisi", "Latency Compensation"),
    ("Dinamik aralık", "Dynamic Range"),
    ("Sıkıştırma", "Compression"),
    ("Genişletici", "Expander"),
    ("Sınırlayıcı", "Limiter"),
    ("Ses yüksekliği", "Loudness"),
    ("Tepe seviyesi", "Peak Level"),
    ("Örnek tepe", "Sample Peak"),
    ("Gerçek tepe", "True Peak"),
    ("A/B karşılaştırma", "A/B Comparison"),
    ("Referans sinyal", "Reference Signal"),
    ("Kalibrasyon", "Calibration"),
    ("Ağırlıklandırma", "Weighting"),
    ("Zaman ağırlıklandırma", "Time Weighting"),
    ("Mikrofon", "Microphone"),
    ("Anten", "Antenna"),
    ("Kablosuz sistem", "Wireless System"),
    ("Frekans koordinasyonu", "Frequency Coordination"),
    ("RF taraması", "RF Scan"),
    ("Girişim ürünleri", "Intermodulation Products"),
    ("Dijital sinyal işleme", "Digital Signal Processing"),
    ("Hoparlör", "Loudspeaker"),
    ("Monitör", "Monitor"),
    ("Hat dizisi", "Line Array"),
    ("Alt frekans hoparlörü", "Subwoofer"),
    ("Çapraz geçiş", "Crossover"),
    ("Darbe yanıtı", "Impulse Response"),
    ("Aktarım işlevi", "Transfer Function"),
    ("Tutarlılık", "Coherence"),
    ("Genlik", "Magnitude"),
    ("Spektrum", "Spectrum"),
    ("Oktav bandı", "Octave Band"),
    ("Üçte bir oktav", "One-Third Octave"),
    ("Hızlı Fourier dönüşümü", "Fast Fourier Transform"),
    ("Pencere işlevi", "Window Function"),
    ("Yankı", "Reverb"),
    ("Ses kontrolü", "Soundcheck"),
    ("Sahne planı", "Stage Plot"),
    ("Giriş listesi", "Input List"),
    ("Teknik şartname", "Technical Rider"),
    ("Ön alan", "Front of House"),
    ("Kulak içi monitör", "In-Ear Monitor"),
    ("Ölçüm mikrofonu", "Measurement Microphone"),
    ("Yankılanma süresi", "Reverberation Time"),
]
def bilingualize_markup(value):
    """Metindeki Türkçe teknik terimleri İngilizce endüstri karşılığıyla birlikte yazar."""
    text = str(value)
    for tr, en in sorted(TERMS, key=lambda pair: len(pair[0]), reverse=True):
        pattern = r"(?<![\wğüşöçıİĞÜŞÖÇ])" + re.escape(tr) + r"(?![\wğüşöçıİĞÜŞÖÇ])(?!\s*\()"
        text = re.sub(pattern, lambda match, label=f"{tr} ({en})": label, text, flags=re.IGNORECASE)
    return text

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
    # Her sayfada en fazla 44 terim; iki sütunlu sözlük taşma yapmadan bölünür.
    for offset in range(0, len(TERMS), 44):
        batch = TERMS[offset:offset + 44]
        page = doc.new_page(width=595.28, height=841.89)
        page.insert_text((42, 42), "TERİM SÖZLÜĞÜ / TECHNICAL GLOSSARY", fontfile=str(FONT), fontsize=15, color=(0.12, 0.14, 0.17))
        page.insert_text((42, 62), "Türkçe teknik terimlerin İngilizce endüstri karşılıkları", fontfile=str(FONT), fontsize=8, color=(0.35, 0.38, 0.42))
        x0, x1, x2, x3 = 42, 292, 303, 553
        half = (len(batch) + 1) // 2
        row_h, top = 29, 88
        page.draw_rect((x0, top, x3, top + row_h * (half + 1)), color=(0.82,0.84,0.87), width=0.5)
        page.draw_line((x1, top), (x1, top + row_h * (half + 1)), color=(0.82,0.84,0.87), width=0.5)
        page.draw_line((x2, top), (x2, top + row_h * (half + 1)), color=(0.82,0.84,0.87), width=0.5)
        for left, right in ((x0,x1),(x2,x3)):
            page.insert_text((left+6, top+15), "Türkçe", fontfile=str(FONT), fontsize=8, color=(0.12,0.14,0.17))
            page.insert_text((right-45, top+15), "English", fontfile=str(FONT), fontsize=8, color=(0.12,0.14,0.17))
        for i in range(half):
            for col, (tr, en) in enumerate((batch[i], batch[i+half] if i+half < len(batch) else ("",""))):
                left = x0 if col == 0 else x2
                yy = top + row_h * (i + 1)
                page.insert_text((left+6, yy+15), tr, fontfile=str(FONT), fontsize=7.1, color=(0.12,0.14,0.17))
                page.insert_text((left+6, yy+25), en, fontfile=str(FONT), fontsize=6.8, color=(0.35,0.38,0.42))
                if i < half-1:
                    page.draw_line((left, yy+row_h), (left + (x1-x0), yy+row_h), color=(0.9,0.91,0.93), width=0.35)
        page.insert_text((42, 812), f"STAGEPULSE · Eğitim terminolojisi / Training terminology · {offset//44 + 1}", fontfile=str(FONT), fontsize=7, color=(0.4,0.42,0.45))
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
            if check.page_count < 2:
                raise RuntimeError(f"PDF sayfası üretilemedi: {name}")
    print(f"OK: {len(PDF_NAMES)} PDF'ye ortak Türkçe-İngilizce sözlük eklendi; Android/Windows kopyaları eşitlendi.")

if __name__ == "__main__":
    main()
