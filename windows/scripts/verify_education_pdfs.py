#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""13 Stagepulse eğitim PDF'sinin açılabilirliğini, metin kapsamını ve kopya eşitliğini denetler."""
from pathlib import Path
import sys
import pymupdf

ROOT=Path(__file__).resolve().parents[2]
WIN=ROOT/'windows'/'egitim_paketleri'
AND=ROOT/'android'/'app'/'src'/'main'/'assets'/'egitim_paketleri'
EXPECTED={
'00_Uygulama_Kullanimi_Ogrenci.pdf':['Öğrenci','RTA','Nyquist','kalibr'],
'01_Ses_Muhendisligi_Ogrenci_Ders_Kitabi.pdf':['Dalga','dB SPL','polarite','Sabine'],
'02_Canli_Ses_Live_Sound_Ogrenci_Dersleri.pdf':['FOH','monitör','soundcheck','sub','intermodülasyon','anten','drop-out'],
'03_Studio_Ses_Muhendisligi_Ogrenci_Dersleri.pdf':['DAW','LUFS','true peak','mono','mastering','dither'],
'04_Dijital_Ses_Mikseri_Ogrenci_Calisma_Kitabi.pdf':['routing','DCA','bus','scene'],
'05_Canli_Ses_Mikseri_Hizli_Basvuru.pdf':['Gain','phantom','IEM','arıza'],
'06_Ogrenci_Uygulama_Formlari.pdf':['kanıt','eğitmen','ölçüm','rubrik'],
'07_Saha_Olcumu_SPL_Raporlama_Egitimi.pdf':['LAeq','kalibrasyon','belirsizlik','LCpeak'],
'08_SPL_Alan_RTA_Teknik_Uygulama_Eki.pdf':['20 µPa','Sabine','Nyquist','NIOSH'],
'09_SPL_dB_3D_Gorsel_Atlasi.pdf':['SPL','3D','IEC 61672-1','konsept'],
'10_Midas_M32_Live_Uygulamali_Egitim.pdf':['Midas M32','AES50','DCA','monitor'],
'11_Yamaha_CL5_Uygulamali_Egitim.pdf':['Yamaha CL5','Dante','Centralogic','Scene'],
'12_Allen_Heath_Avantis_Uygulamali_Egitim.pdf':['Avantis','Mix bus','DCA','Scene'],
}
errors=[]
for name,terms in EXPECTED.items():
 wp=WIN/name; ap=AND/name
 if not wp.is_file(): errors.append(f'Windows PDF eksik: {name}'); continue
 if not ap.is_file(): errors.append(f'Android PDF eksik: {name}'); continue
 if wp.read_bytes()!=ap.read_bytes(): errors.append(f'Android/Windows PDF farklı: {name}')
 try:
  doc=pymupdf.open(wp)
  if not doc.page_count: errors.append(f'Sayfa yok: {name}')
  pages=[p.get_text().strip() for p in doc]
  text='\n'.join(pages)
  if not pages or 'TERİM SÖZLÜĞÜ / TECHNICAL GLOSSARY' not in pages[-1]:
   errors.append(f'Türkçe-İngilizce terim sözlüğü eksik: {name}')
  for term in ['Compressor','Noise Gate','Threshold','Ratio','Attack','Release']:
   if term not in text: errors.append(f'İki dilli teknik terim eksik {name}: {term}')
  if len(text)<1200: errors.append(f'Metin hacmi yetersiz: {name} ({len(text)} karakter)')
  if sum(bool(x) for x in pages)<max(2,doc.page_count//2): errors.append(f'Boş sayfa oranı yüksek: {name}')
  missing=[t for t in terms if t.casefold() not in text.casefold()]
  if missing: errors.append(f'İçerik anahtarları eksik {name}: {missing}')
  if 'STAGEPULSE' not in text.upper(): errors.append(f'Marka/başlık metni eksik: {name}')
  print(f'OK {name}: {doc.page_count} sayfa, {len(text)} metin karakteri')
 except Exception as exc: errors.append(f'PDF açılamadı {name}: {exc}')
if errors:
 print('PDF DENETİMİ BAŞARISIZ')
 for e in errors: print(' - '+e)
 sys.exit(1)
print(f'PDF DENETİMİ GEÇTİ: {len(EXPECTED)} özgün PDF; Android/Windows kopyaları birebir.')
