#!/usr/bin/env python3
"""Generate the student-facing SPL / audience geometry / RTA appendix."""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'egitim_paketleri' / '08_SPL_Alan_RTA_Teknik_Uygulama_Eki.pdf'
FONT = next((str(p) for p in [Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),Path('C:/Windows/Fonts/arial.ttf')] if p.exists()), '')
FONT_BOLD = next((str(p) for p in [Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),Path('C:/Windows/Fonts/arialbd.ttf')] if p.exists()), '')
if Path(FONT).exists() and Path(FONT_BOLD).exists():
    pdfmetrics.registerFont(TTFont('SP', FONT)); pdfmetrics.registerFont(TTFont('SP-Bold', FONT_BOLD))
    REG, BOLD = 'SP', 'SP-Bold'
else:
    REG, BOLD = 'Helvetica', 'Helvetica-Bold'
INK=colors.HexColor('#17191d'); GOLD=colors.HexColor('#b99143'); PALE=colors.HexColor('#f5f1e7')
GREY=colors.HexColor('#59616b'); LIGHT=colors.HexColor('#e1e5ea'); RED=colors.HexColor('#8c3027'); GREEN=colors.HexColor('#27634a')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Cover',fontName=BOLD,fontSize=25,leading=31,textColor=INK,alignment=TA_CENTER,spaceAfter=10))
styles.add(ParagraphStyle(name='Sub',fontName=REG,fontSize=11,leading=16,textColor=GREY,alignment=TA_CENTER,spaceAfter=7))
styles.add(ParagraphStyle(name='H1SP',fontName=BOLD,fontSize=16,leading=21,textColor=INK,spaceBefore=7,spaceAfter=7,keepWithNext=True))
styles.add(ParagraphStyle(name='H2SP',fontName=BOLD,fontSize=11,leading=14,textColor=GOLD,spaceBefore=6,spaceAfter=4,keepWithNext=True))
styles.add(ParagraphStyle(name='BodySP',fontName=REG,fontSize=8.7,leading=12.3,textColor=INK,spaceAfter=5))
styles.add(ParagraphStyle(name='SmallSP',fontName=REG,fontSize=7.1,leading=9.3,textColor=GREY,spaceAfter=3))
styles.add(ParagraphStyle(name='Callout',fontName=REG,fontSize=8.6,leading=12,textColor=INK,backColor=PALE,borderColor=GOLD,borderWidth=.65,borderPadding=7,spaceBefore=4,spaceAfter=7))
styles.add(ParagraphStyle(name='Danger',fontName=BOLD,fontSize=8.6,leading=12,textColor=RED,backColor=colors.HexColor('#f8eeec'),borderColor=colors.HexColor('#d8a49f'),borderWidth=.65,borderPadding=7,spaceBefore=4,spaceAfter=7))
styles.add(ParagraphStyle(name='Cell',fontName=REG,fontSize=7.2,leading=9.2,textColor=INK))
styles.add(ParagraphStyle(name='CellHead',fontName=BOLD,fontSize=7.2,leading=9.2,textColor=INK))
from append_bilingual_glossary import bilingualize_markup
P=lambda x,s='BodySP': Paragraph(bilingualize_markup(x),styles[s])
story=[]

def table(rows, widths, header=True):
    data=[]
    for ri,row in enumerate(rows):
        data.append([P(str(v),'CellHead' if header and ri==0 else 'Cell') for v in row])
    t=Table(data,colWidths=widths,repeatRows=1 if header else 0,hAlign='LEFT')
    cmds=[('BOX',(0,0),(-1,-1),.45,LIGHT),('INNERGRID',(0,0),(-1,-1),.35,LIGHT),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]
    if header: cmds.append(('BACKGROUND',(0,0),(-1,0),PALE))
    t.setStyle(TableStyle(cmds)); return t

# Cover
story += [Spacer(1,27*mm),P('STAGEPULSE','Sub'),P('SPL, ALAN BOYUTLANDIRMA<br/>VE GERÇEK ZAMANLI RTA','Cover'),P('Öğrenci teknik uygulama eki · Sürüm 4.0.2','Sub'),Spacer(1,8*mm)]
cover=Table([[P('<b>NE İÇİN?</b><br/>dB/SPL hesaplarını doğru yorumlamak, dinleyici alanını geometrik olarak değerlendirmek ve RTA grafiğini güvenli kullanmak.','Cell')],[P('<b>NE DEĞİL?</b><br/>Bu belge tek başına sistem tasarım raporu, kalibre edilmiş ses seviyesi ölçer, akustik simülasyon veya mevzuata uygunluk belgesi değildir.','Cell')],[P('<b>KULLANIM SIRASI</b><br/>Dersi oku → örnek hesabı elle kontrol et → uygulamada aynı girdileri kullan → varsayımları kontrol et → gerektiğinde gerçek ölçümle doğrula.','Cell')]],colWidths=[150*mm])
cover.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('BOX',(0,0),(-1,-1),.7,GOLD),('INNERGRID',(0,0),(-1,-1),.4,LIGHT),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9)]))
story += [cover,Spacer(1,15*mm),P('Sürüm 4.0.2 · Öğrenci çalışma nüshası · 29 Ekim 2026','Sub'),PageBreak()]

story += [P('1. dB, ses basıncı ve SPL','H1SP'),P('Desibel logaritmik bir oran gösterimidir. dB tek başına referansı söylemez: dBFS dijital tam ölçeğe, dBu 0,775 V RMS referansına, dB SPL ise havadaki ses basıncı referansına bağlıdır. Birimler birbirinin yerine kullanılamaz.'),P('Ses basıncı seviyesi formülü','H2SP'),P('<b>Lp = 20 × log10(pRMS / p0)</b><br/>Havada standart referans basınç p0 = 20 µPa = 0,00002 Pa RMS. Ters dönüşüm: <b>pRMS = p0 × 10^(Lp/20)</b>.'),table([
['Örnek','İşlem','Sonuç'],
['0,1 Pa RMS → dB SPL','20 log10(0,1 / 0,00002)','73,98 dB SPL'],
['94 dB SPL → Pa RMS','0,00002 × 10^(94/20)','1,002 Pa RMS (yaklaşık 1 Pa)'],
['20 µPa RMS → dB SPL','20 log10(20 µPa / 20 µPa)','0 dB SPL (referans tanımı)'],
],[38*mm,65*mm,45*mm]),Spacer(1,5),P('Önemli: 0 dB SPL sessizlik anlamına gelmez; referans ses basıncı seviyesidir. dB SPL ile A-ağırlıklı dBA, dBC veya dBZ aynı raporlama niteliğinde değildir. Ağırlık filtresi, zaman ağırlığı, ölçüm süresi ve cihaz sınıfı raporda belirtilmelidir.','Callout'),P('Birden fazla seviyeyi toplama','H2SP'),P('Bağımsız veya enerji toplamı varsayılabilecek kaynaklar için dB değerleri aritmetik toplanmaz. <b>Ltoplam = 10 × log10(Σ 10^(Li/10))</b>. Örneğin iki adet 90 dB kaynağın enerji toplamı 93,01 dB olur; 180 dB olmaz. Fazı eşleşmiş kaynaklarda, hoparlör dizilerinde ve aynı sinyalin koherent kopyalarında gerçek sonuç konuma ve faz ilişkisine bağlıdır; bu formül dizinin akustik toplamını tek başına çözmez.'),P('dB toplamı örnekleri','H2SP'),table([
['Girdiler','Enerji toplamı','Yorum'],
['90 dB + 90 dB','93,01 dB','Eşit seviyeli, enerji toplaması yaklaşımı'],
['90 dB + 87 dB','91,76 dB','Seviyesi 3 dB düşük ikinci katkı'],
['90 dB + 80 dB','90,41 dB','Düşük katkı toplamı az yükseltir'],
],[42*mm,34*mm,72*mm]),PageBreak()]

story += [P('2. Mesafeye göre seviye kestirimi','H1SP'),P('Serbest alan, noktasal kaynak ve doğrudan sesin baskın olduğu uzak alanda yaklaşık seviye farkı <b>ΔL = −20 × log10(r2/r1)</b>. Hedef seviye kestirimi <b>L2 = L1 − 20 × log10(r2/r1)</b>. Mesafe iki katına çıkarsa yaklaşık −6,02 dB; 10 katına çıkarsa −20 dB değişim beklenir. Bu, her PA sistemine uygulanacak evrensel kural değildir.'),table([
['Referans','Hedef mesafe','İdeal fark','100 dB @ 1 m örneği'],
['1 m','2 m','−6,02 dB','93,98 dB'],
['1 m','4 m','−12,04 dB','87,96 dB'],
['1 m','10 m','−20 dB','80 dB'],
['1 m','20 m','−26,02 dB','73,98 dB'],
],[28*mm,31*mm,31*mm,58*mm]),Spacer(1,6),P('Bu uygulamadaki hesaplayıcı aynı seviyedeki N kaynağı bağımsız enerji katkıları gibi ele alır ve 10 log10(N) ekler. Aynı programı çalan L/R hoparlörlerin veya subwoofer dizilerinin tüm dinleyici alanındaki katkısını güvenilir biçimde hesaplamaz. Array yönlülüğü, crossover, polarite/faz, kabin aralığı, duvar/yansımalar, atmosfer, limiter, güç sıkıştırması ve dinleyici yüksekliği modellenmiyor.','Danger'),P('Gerçek dış ortam yayılım modeli, kaynağın spektrumu ve yönlülüğü yanında geometri, zemin, engeller, yansımalar ve meteorolojik etkileri kapsayabilir. ISO 9613-2:2024 bu tür dış ortam tahmini için mühendislik yöntemidir; burada kullanılan basit mesafe denklemi bunun yerine geçmez.','BodySP'),P('Saha prosedürü','H2SP')]
for x in [
'1. Referans ölçümün mesafesini, yükseklik ve yönünü, test sinyalini, ağırlığı (A/C/Z) ve zaman parametresini kaydet.',
'2. Aynı sistem ayarıyla dinleyici alanında en az ön/orta/arka ve sol/merkez/sağ noktaları ölç; konumları işaretle.',
'3. LAeq, LAFmax/LASmax, LCpeak ve gerektiğinde SEL gibi metrikleri amaçlarına uygun ayrı değerlendir. Bir tepe değeri, ortalama maruziyetin yerine geçmez.',
'4. Sonuçları kalibrasyon öncesi/sonrası cihaz bilgisi ve belirsizlikle raporla; tahmini değer ile ölçümü ayrı etiketle.'
]: story.append(P(x))
story += [PageBreak(),P('3. Alan boyutlandırma ve kapsama geometrisi','H1SP'),P('Alan hesabı, izleyici alanının geometrik ilk adımıdır. Sesin yeterli seviyede veya homojen olduğu anlamına gelmez.'),P('Dikdörtgen dinleyici alanı','H2SP'),P('<b>Alan A = genişlik W × derinlik D</b><br/><b>Yaklaşık hacim V = W × D × yükseklik H</b><br/>PA’nın ön kenarın ortasında olduğu basit bir düzende, en uzak köşe uzaklığı <b>r = √(D² + (W/2)²)</b>.'),P('Örnek: W=20 m, D=30 m, H=6 m','H2SP'),table([
['Büyüklük','İşlem','Sonuç'],
['Düzlemsel alan','20 × 30','600 m²'],
['Yaklaşık hacim','20 × 30 × 6','3600 m³'],
['Merkezdeki ön kenardan uzak köşe','√(30² + 10²)','31,62 m'],
['Nominal 90° yatay açı ile arka çizgi geometrik genişliği','2 × 30 × tan(90°/2)','60 m'],
],[50*mm,62*mm,36*mm]),P('Nominal yatay açı θ için geometrik genişlik = <b>2 × D × tan(θ/2)</b>. Örnekte 60 m, 20 m’lik alandan daha geniş çıkar; ideal geometrik oran uygulamada %100 ile sınırlandırılır. Bu yalnızca geometrik örtüşmedir; gerçek hoparlör polar grafiği, frekansa bağlı directivity, dikey açı, yükseklik, down-tilt, rigging, balkon/engel veya ses seviyesi eşitliğini modellemez.','Callout'),P('Sistem seçimi için gereken ek veriler','H2SP')]
for x in [
'Üretici yatay/dikey kutup grafikleri veya doğrulanmış akustik model; her frekansta kapsama değişimi.',
'En uzak dinleyici noktası, en yakın dinleyici noktası, görüş çizgisi, yükseklik, eğim, sahne ve komşu yerleşimleri.',
'Sistem çıkış kapasitesi ve hedef LAeq/tepe şartı, limiter davranışı, program içeriği ve gereken headroom.',
'Ölçüm ızgarası ve saha doğrulaması. Sadece m² veya kişi sayısından gerekli hoparlör adedi ya da güvenli SPL belirlenemez.'
]: story.append(P(x))
story += [P('Açık alan ve kapalı oda farklıdır. Kapalı alanlarda erken/yankılı enerji, soğurma ve oda modları önemlidir. Dış ortamda da zemin yansıması, engel, atmosfer ve meteoroloji önemlidir; alan geometrisi bunların tamamı değildir.','Danger'),P('Oda eksenel modları','H2SP'),P('Dikdörtgen oda için temel eksenel modların ilk tahmini <b>fn = n × c/(2L)</b>; n=1,2,3… ve L ilgili uzunluk, genişlik veya yüksekliktir. Ses hızı c yaklaşık 343 m/s varsayılmıştır; sıcaklık ve ortam koşulları sonucu değiştirir. Bu hesap erken tanı içindir; tüm mod tiplerini veya gerçek oda cevabını içermez.')]

story.append(KeepTogether([
    P('Sabine yankılanma süresi: hacim ve yüzey soğurması','H2SP'),
    P('İlk yaklaşık değer <b>T60 ≈ 0,161 × V/A</b>; V oda hacmi (m³), A eşdeğer soğurma alanı (m² sabin). Her yüzey için <b>A = Σ(αᵢ × Sᵢ)</b>; αᵢ o yüzeyin seçilen frekanstaki soğurma katsayısı (0–1), Sᵢ yüzey alanıdır (m²). Zemin, tavan ve her duvarın alanını kendi katsayısıyla çarpıp katkıları toplarsın. Kaplama katsayıları frekansla değişir; tek bir katsayı tüm bantlar için doğru değildir.'),
    P('Çözümlü örnek: 6 × 4 × 2,8 m oda','H2SP'),
    table([['Yüzey','Alan','Örnek α','Eşdeğer A katkısı'],['Zemin','24,0 m²','0,20','4,8 m² sabin'],['Tavan','24,0 m²','0,50','12,0 m² sabin'],['Uzun duvarlar','22,4 m²','0,15','3,36 m² sabin'],['Kısa duvarlar','33,6 m²','0,15','5,04 m² sabin'],['Toplam','—','—','A = 25,2 m² sabin']],[37*mm,36*mm,27*mm,46*mm]),
    P('Oda hacmi 67,2 m³ ve bu örnek A değeriyle Sabine T60 ≈ 0,161 × 67,2 / 25,2 = 0,43 saniye. Katsayılar yalnızca örnek amaçlıdır; gerçek sonuç için ilgili frekanstaki üretici/veri kaynağı, insan/mobilya etkisi ve saha ölçümü gerekir. Sabine sonucu ölçülmüş RT60 değildir; açık alanlarda bu model uygun değildir.','Callout'),
]))

story += [PageBreak(),P('4. Maruziyet hesabı ve güvenli yorum','H1SP'),P('Bu ek, NIOSH mesleki işitme koruma referansını eğitim amacıyla gösterir. NIOSH REL, 85 dBA, 8 saat TWA ve 3 dB değişim oranını kullanır. Bu değer genel halk için konser sınırı veya Türkiye’deki yerel mevzuata ilişkin uygunluk kararı değildir.','Danger'),P('İzin verilen yaklaşık mesafe değil, süre hesabı: <b>T dakika = 480 / 2^((L − 85)/3)</b>. Tek maruziyet bloğunda <b>Doz % = 100 × t/T</b>. Farklı düzeylerdeki birden çok blok için dB değerlerinin aritmetik ortalaması alınmaz; her blok için süre/izin verilen süre oranı hesaplanır ve yüzdeler toplanır. Bu eğitim aracı en fazla üç bloğun dozunu biriktirir. Yalnızca uygun ölçümle elde edilmiş LAeq girdisi kullanılmalıdır; bilgisayar mikrofonunun dBFS değeri dBA değildir.'),table([
['Düzey (dBA)','NIOSH referans süresi','Örnek süre ile doz'],
['85','480 dakika (8 saat)','480 dk → %100'],
['88','240 dakika (4 saat)','240 dk → %100'],
['91','120 dakika (2 saat)','120 dk → %100'],
['94','60 dakika','60 dk → %100'],
['97','30 dakika','30 dk → %100'],
['100','15 dakika','15 dk → %100'],
],[36*mm,54*mm,58*mm]),P('Bu yalnızca mesleki maruziyet için referans hesabıdır; uygulama yasal uygunluk sertifikası vermez. İş yerinde geçerli iş sağlığı ve güvenliği gereklilikleri, ulusal mevzuat, doğru ölçüm cihazı ve yetkili profesyonel değerlendirmesi ayrıca uygulanmalıdır.','Callout'),PageBreak()]

story += [P('5. RTA’nın doğru kullanımı','H1SP'),P('RTA bu uygulamada yerel mikrofon/giriş akışından örnekleri FFT ile çözümler, oktav veya 1/3 oktav bantlarında göreli dBFS güç gösterir. Bu, IEC 61260-1’e uygunluğu doğrulanmış bir ölçüm cihazı veya IEC 61672 sınıf 1/2 ses seviye ölçeri değildir. RTA ekranı tek başına kalibre edilmiş dB SPL, faz ya da transfer-function göstermez.'),P('Örnekleme frekansı ve tiz sınırı','H2SP'),P('Fs örnekleme frekansı ise Nyquist frekansı Fs/2’dir. Bir 1/3 oktav bandını tam göstermek için bandın üst kenarı Nyquist sınırının altında kalmalıdır. 20 kHz merkezli üçüncü oktav bandının üst kenarı yaklaşık 22,45 kHz’tir. Bu nedenle 44,1 kHz akışta 20 kHz bandı tam ölçülemez; 16 kHz üst merkezli bantta sonlanır. 48 kHz akış teorik olarak bu bandın üst kenarına yer bırakır, ancak bu mikrofonun 20 kHz’deki duyarlılığını garanti etmez.'),table([
['Fs','Nyquist','1/3 oktavda son tam merkez (20 kHz üst limit içinde)'],
['16 kHz','8 kHz','Yaklaşık 6,3 kHz'],
['22,05 kHz','11,025 kHz','Yaklaşık 8 kHz'],
['32 kHz','16 kHz','Yaklaşık 12,5 kHz'],
['44,1 kHz','22,05 kHz','16 kHz'],
['48 kHz','24 kHz','20 kHz'],
['96 kHz','48 kHz','20 kHz (uygulamanın üst sınırı)'],
],[27*mm,29*mm,92*mm]),P('FFT boyutu ve yumuşatma','H2SP'),P('Frekans bin aralığı yaklaşık Δf = Fs/NFFT. 48 kHz örnekleme hızında NFFT=8192 için yaklaşık 5,86 Hz; 16384 için 2,93 Hz; 32768 için 1,46 Hz. Daha büyük FFT daha iyi frekans ayrımı sağlar ancak daha uzun örnekleme penceresi ve daha çok işlem/bellek ister. FFT kutu aralığı, mikrofonun fiziksel yanıtı veya analizörün standarda uygunluğuyla aynı şey değildir. Yumuşatma (Fast/Medium/Slow) grafiğin zaman içindeki tepkisini değiştirir; ölçüm kalibrasyonu yapmaz.'),P('Dizüstü / PC mikrofonu tizleri neden eksik veya fazla gösterebilir?','H2SP'),P('Dahili kapsülün frekans cevabı, mikrofon dizisi, üretici EQ’su, otomatik kazanç, gürültü bastırma, işletim sistemi efektleri, mesafe ve yön grafiği değiştirebilir. Yazılım bilinmeyen mikrofon cevabını düzeltemez. Bir 18 kHz test tonu girişte düşük görünüyorsa önce başka mikrofon, ses kartı ve bilinen sinyal ile karşılaştır; “EQ ile +12 dB düzelt” gibi genel bir çözüm uygulama. Kalibrasyon dosyası/duyarlılık verisi olmadan mutlak dB SPL sonucu çıkarma.','Danger'),P('Uygulamadaki gerçek zamanlı optimizasyon önerileri','H2SP'),P('İsteğe bağlı öneri modülü kullanıcı pembe gürültü veya sabit bantlı test sinyali kullandığını onayladıktan sonra son kararlı örneklerin medyanını kullanarak yerel bant tepelerini komşu bantlarla karşılaştırır. Müzik/konuşma programında öneri üretimi kapalıdır; içerikteki armonik yapı oda rezonansı sanılabilir. Eşik aşan birkaç dar tepe için en fazla −3 dB kesim adayı gösterir; otomatik EQ yazmaz, boost önermez ve gerçek transfer-function ölçümünün yerini almaz. Bu, “oda kalibrasyonu” değildir.'),P('Güvenli kullanım akışı','H2SP')]
for x in [
'1. Windows giriş aygıtının doğru seçildiğini ve giriş metrelerinin hareket ettiğini kontrol et. Mikrofon izinlerini, giriş kazancını ve diğer uygulamaların mikrofonu kullanıp kullanmadığını kontrol et.',
'2. RTA başlatıldığında cihaz adı, örnekleme hızı, FFT boyutu, bant türü ve frekans aralığı bilgisini kaydet. Giriş klipleniyorsa kazancı azalt.',
'3. İlk spektrumu temel olarak kaydet; aynı ayarla birden fazla konumda ölç. Tek noktadaki dar tepe oda veya mikrofon rezonansı olabilir.',
'4. Öneriyi EQ’ya aktarmadan önce dinleme, ölçüm mikrofonu ve gerekiyorsa transfer-function ile doğrula. Düşük frekans çukurlarını yüksek boost ile doldurmaya çalışma.',
'5. Gain, limiter, akustik geri besleme, sub hizalama veya yasal SPL sınırları için RTA önerisini otomatik donanım komutu gibi kullanma.'
]: story.append(P(x))

story += [PageBreak(),P('6. Uygulama ile çözümlü alıştırmalar','H1SP'),P('Alıştırma A — Mesafe','H2SP'),P('Bir referans ölçüm 1 m’de 100 dB SPL gösteriyor. Noktasal kaynak/serbest alan varsayımıyla 10 m sonucu: 100 − 20 log10(10/1) = 80 dB SPL. İki eşit, bağımsız kaynağın enerji toplamı varsayılırsa 10 log10(2) = 3,01 dB eklenir; kestirim 83,01 dB olur. Bu, L/R hoparlör dizisinin gerçek sonucu olarak okunmamalıdır.'),P('Alıştırma B — Alan','H2SP'),P('20 m genişlik ve 30 m derinlik için A=600 m². 6 m ortalama yükseklikle V=3600 m³. PA ön kenar ortasındaysa uzak köşe √(30²+10²)=31,62 m. Nominal yatay açı 90° için arka kenar teorik genişliği 2×30×tan45°=60 m; alan genişliği 20 m olduğundan hesaplayıcı geometrik kapsama oranını %100’e sınırlar. Gerçek kapsama bu sonuçtan çıkarılamaz.'),P('Alıştırma C — RTA tizleri','H2SP'),P('PC mikrofonla 48 kHz akışta 20 kHz bandı görünür olsa bile bu, 20 kHz ölçüm doğruluğu kanıtı değildir. 44,1 kHz akışta 20 kHz merkezli üçüncü oktav bandının üst kenarı Nyquist’in üstüne çıktığı için uygulama bu bandı göstermemelidir. İki akış ve bilinen test sinyali karşılaştırılır; donanım cevabı kontrol edilir.'),P('Alıştırma D — Maruziyet','H2SP'),P('NIOSH mesleki referansına göre 88 dBA ve 240 dakika için doz yaklaşık %100’dür. Girdi dBA olarak uygun cihazla ölçülmüş olmalıdır. RTA dBFS değeri veya bir telefon/PC mikrofonu okuması bu formüle doğrudan girilmez.'),P('Kontrol listesi: raporlamadan önce','H2SP'),table([
['Kontrol','Evet/Hayır'],
['Ölçüm cihazının modeli, sınıfı ve kalibrasyon kontrolü kaydedildi mi?','□ Evet  □ Hayır'],
['Mikrofon konumu, yüksekliği, yönü ve mesafesi kaydedildi mi?','□ Evet  □ Hayır'],
['dB SPL/dBA/dBFS ve süre/istatistikler birbirinden ayrıldı mı?','□ Evet  □ Hayır'],
['Sadece tahmin ile gerçek ölçüm açıkça ayrıldı mı?','□ Evet  □ Hayır'],
['En az birkaç dinleyici konumunda kontrol yapıldı mı?','□ Evet  □ Hayır'],
['Kullanılan formülün varsayımları ve sınırlamaları yazıldı mı?','□ Evet  □ Hayır'],
],[110*mm,42*mm]),P('Kaynaklar ve kapsam','H1SP'),P('NIOSH, “Understanding Noise Exposure Limits”: https://www.cdc.gov/niosh/bulletin/2016/noise.html (mesleki 85 dBA / 8 saat, 3 dB değişim oranı). OSHA Technical Manual, noise: https://www.osha.gov/otm/section-3-health-hazards/chapter-5 (serbest alanda noktasal kaynak için geometrik yayılım yaklaşımı). ASA/ANSI S1.11/IEC 61260-1, R2023: https://webstore.ansi.org/standards/asa/ASAANSIS111PartIEC612602014 (oktav ve kesirli oktav filtre performans gereklilikleri). IEC 61672-1 ses seviye ölçer şartları: https://webstore.iec.ch/en/publication/5708. ISO 9613-2:2024 dış ortam ses yayılımı mühendislik yöntemi: https://www.iso.org/standard/74047.html. Standartların tam metinlerine erişim ayrı olabilir; bu özet onların yerine geçmez.','SmallSP')]

def footer(canvas, doc):
    canvas.saveState(); w,h=A4
    canvas.setStrokeColor(GOLD); canvas.setLineWidth(.6); canvas.line(17*mm,15*mm,w-17*mm,15*mm)
    canvas.setFont(REG,7); canvas.setFillColor(GREY)
    canvas.drawString(17*mm,9*mm,'STAGEPULSE · SPL / ALAN / RTA · Öğrenci teknik eki · v4.0.2')
    canvas.drawRightString(w-17*mm,9*mm,f'Sayfa {doc.page}')
    canvas.restoreState()

OUT.parent.mkdir(parents=True,exist_ok=True)
doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=17*mm,leftMargin=17*mm,topMargin=15*mm,bottomMargin=21*mm,title='Stagepulse - SPL, Alan Boyutlandırma ve RTA Teknik Uygulama Eki',author='Stagepulse')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(f'{OUT} ({OUT.stat().st_size} bytes)')
