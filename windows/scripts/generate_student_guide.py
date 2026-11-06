# Stagepulse student guide source release 3.5.1
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'egitim_paketleri'/'00_Uygulama_Kullanimi_Ogrenci.pdf'
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
if Path(font).exists() and Path(bold).exists():
    pdfmetrics.registerFont(TTFont('Stage',font)); pdfmetrics.registerFont(TTFont('Stage-Bold',bold)); REG='Stage'; BOLD='Stage-Bold'
else: REG='Helvetica'; BOLD='Helvetica-Bold'
INK=colors.HexColor('#17191d'); GOLD=colors.HexColor('#b99143'); PALE=colors.HexColor('#f5f1e7'); GREY=colors.HexColor('#5d646d'); LIGHT=colors.HexColor('#e5e8ec')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='CoverTitle',fontName=BOLD,fontSize=25,leading=32,textColor=INK,alignment=TA_CENTER,spaceAfter=10))
styles.add(ParagraphStyle(name='CoverSub',fontName=REG,fontSize=12,leading=18,textColor=GREY,alignment=TA_CENTER,spaceAfter=10))
styles.add(ParagraphStyle(name='H1SP',fontName=BOLD,fontSize=17,leading=23,textColor=INK,spaceBefore=8,spaceAfter=8,keepWithNext=True))
styles.add(ParagraphStyle(name='H2SP',fontName=BOLD,fontSize=11.5,leading=15,textColor=GOLD,spaceBefore=7,spaceAfter=4,keepWithNext=True))
styles.add(ParagraphStyle(name='BodySP',fontName=REG,fontSize=9.3,leading=14,textColor=INK,spaceAfter=6))
styles.add(ParagraphStyle(name='SmallSP',fontName=REG,fontSize=7.6,leading=11,textColor=GREY,spaceAfter=4))
styles.add(ParagraphStyle(name='CalloutSP',fontName=REG,fontSize=9.2,leading=13.5,textColor=INK,backColor=PALE,borderColor=GOLD,borderWidth=0.6,borderPadding=8,spaceBefore=5,spaceAfter=8))
styles.add(ParagraphStyle(name='TableSP',fontName=REG,fontSize=8.1,leading=11,textColor=INK))
P=lambda t,style='BodySP': Paragraph(t,styles[style])
story=[]
# Cover
story += [Spacer(1,28*mm),P('STAGEPULSE','CoverSub'),P('SES MÜHENDİSLİĞİ MERKEZİ','CoverTitle'),P('Öğrenci Uygulama ve Sorun Giderme Rehberi','CoverSub'),Spacer(1,8*mm)]
cover=Table([[P('<b>TEK ÇALIŞMA ALANI</b><br/>Ses araçları, teknik hesaplar, RTA ve öğrenci PDF kitaplığı aynı uygulama penceresinde.','TableSP')], [P('<b>ÇEVRİMDIŞI ÖNCELİKLİ</b><br/>Yerel araçlar internet bağlantısı olmadan kullanılabilir. Yapay zekâ servisi çevrimiçi veya yerel servis gerektirir.','TableSP')], [P('<b>ÖLÇÜMDE DÜRÜSTLÜK</b><br/>Ekrandaki tahmin, kalibre edilmiş akustik ölçüm veya saha doğrulamasının yerine geçmez.','TableSP')]],colWidths=[145*mm])
cover.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('BOX',(0,0),(-1,-1),0.7,GOLD),('INNERGRID',(0,0),(-1,-1),0.4,LIGHT),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]))
story += [cover,Spacer(1,18*mm),P('Sürüm 3.5.1 · Öğrenci kullanım nüshası','CoverSub'),PageBreak()]
# 1
story += [P('1. Uygulamada öğrenme sırası','H1SP'),P('Her çalışma için aynı döngüyü uygula: konuyu oku, küçük bir örnek kur, tek bir değişkeni değiştir, sonucu dinle veya ölç, sonra gözlemini kaydet. Uygulamadaki araçlar eğitim ve ön çalışma içindir; kritik saha kararları üretici belgeleri, güvenlik prosedürleri ve gerçek ölçümlerle doğrulanmalıdır.')]
data=[[P('<b>Sıra</b>','TableSP'),P('<b>Öğrenci PDF / araç</b>','TableSP'),P('<b>Ne öğreneceksin?</b>','TableSP')],
[P('1','TableSP'),P('Ses Mühendisliği Öğrenci Ders Kitabı','TableSP'),P('Temel akustik, sinyal seviyesi, formüller ve uygulama düşüncesi.','TableSP')],
[P('2','TableSP'),P('Canlı Ses / Live Sound Öğrenci Dersleri','TableSP'),P('FOH, gain yapısı, patch, monitör/IEM, PA ve DSP iş akışları.','TableSP')],
[P('3','TableSP'),P('Dijital Ses Mikseri Çalışma Kitabı + Hızlı Başvuru','TableSP'),P('Gerçek konsolda kontrollü uygulama ve hızlı hatırlatma.','TableSP')],
[P('4','TableSP'),P('Stüdyo Ses Mühendisliği Öğrenci Dersleri','TableSP'),P('Kayıt, düzenleme, miks, kalite kontrol ve teslim.','TableSP')],
[P('5','TableSP'),P('Saha Ölçümü, SPL ve Raporlama Eğitimi','TableSP'),P('Veri toplama, ölçüm koşullarını kaydetme ve rapor sınırları.','TableSP')],
[P('6','TableSP'),P('Öğrenci Uygulama Formları','TableSP'),P('İşlemi, sonucu ve kanıtı kişisel olarak kayıt altına alma.','TableSP')],
[P('7','TableSP'),P('SPL, Alan Boyutlandırma ve RTA Teknik Uygulama Eki','TableSP'),P('dB/SPL, mesafe varsayımları, geometri, Sabine T60 ve RTA sınırları.','TableSP')],
[P('8','TableSP'),P('SPL, dB ve 3D Görsel Atlası','TableSP'),P('Hesaplanan 2D/3D model haritaları, dB basınç/güç oranları ve gerçekçi kavramsal PA illüstrasyonu.','TableSP')]]
t=Table(data,colWidths=[14*mm,58*mm,73*mm],repeatRows=1)
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('BOX',(0,0),(-1,-1),0.5,LIGHT),('INNERGRID',(0,0),(-1,-1),0.35,LIGHT),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
story += [t,Spacer(1,7),P('<b>Öneri:</b> Aynı gün içinde bütün araçları ezberlemeye çalışma. Bir konu seç, ilgili PDF bölümünü oku ve aracı yalnızca o konuyu anlamak için kullan.','CalloutSP'),P('2. Çalışma alanlarını doğru kullan','H1SP')]
for head,body in [
('Frekans Bulucu ve Kulak Eğitimi','Frekans/nota ilişkisini, oktavları ve EQ bölgelerini öğren. Kulak eğitimi örneği işitsel bir alıştırmadır; gerçek bir mikrofonun frekans yanıtını ölçmez.'),
('Teknik Hesaplayıcılar','dB, Vrms, gecikme, dalga boyu ve sistem ön hesabı gibi nicelikleri çalış. Girdilerin birimini ve formülün varsayımlarını kontrol et; tahmini sonucu doğrudan cihaz ayarı sayma.'),
('Ses Katmanı Atölyesi','Yerel medyayı aç, kanalları ayrı düzenle, cue ekle ve ön miks üret. Proje dosyası ayarları/işaretleri tutabilir; asıl ses ve video kaynaklarını tek başına içine gömmeyebilir. Kaynak medyayı ayrıca sakla.'),
('WAV ve LUFS araçları','PCM WAV kalite raporunda sample peak/RMS; loudness aracında ölçülen LUFS ve tahmini true peak bilgileri ayrı gösterilir. Normalizasyon işlemi limiter değildir; çıktıyı tekrar ölç ve dinle.'),
('Öğrenci profili ve uygulama formları','Her öğrenci kendi profiline ilerlemesini kaydetsin. Ortak bilgisayarda kullanıcı adını seçip doğru profile kaydedildiğini kontrol et; periyodik olarak verileri dışa aktar.')]:
    story += [P(head,'H2SP'),P(body)]
story += [P('SPL / alan planı hesaplayıcısı','H2SP'),P('Ses basıncı ↔ dB SPL aracı p0=20 µPa referansını kullanır. Mesafe hesabı sadece serbest alan noktasal kaynak yaklaşımıdır; çoklu kaynak toplaması fazı/array davranışını modellemez. Alan planı m², yaklaşık hacim, uzak köşe ve nominal yatay açıdan ideal geometrik genişlik çıkarır; gerçek akustik kapsama tahmini değildir. Maruziyet aracı NIOSH mesleki 85 dBA / 8 saat / 3 dB değişim oranı referansını kullanır; en fazla üç farklı LAeq/süre bloğunun dozunu toplar, dB düzeylerini ortalamaz ve genel halk veya yerel mevzuat sınırı değildir.'),P('Sabine ve eşdeğer soğurma alanı','H2SP'),P('Sabine ilk kestirimi T60 ≈ 0,161 × V/A formülünü kullanır. A = Σ(αᵢ × Sᵢ): her yüzey alanı S (m²), seçilen frekansta o malzemeye ait soğurma katsayısı α (0–1) ile çarpılır; katkılar toplanır. Yüzey hesaplayıcısındaki başlangıç katsayıları yalnızca örnektir, gerçek malzeme verisiyle değiştirilmeli. Bu sonuç ölçülmüş RT60 değildir.'),P('RTA öneri paneli','H2SP'),P('İsteğe bağlı optimizasyon paneli yalnızca pembe gürültü veya sabit bantlı test sinyali kullanımını onayladığında kararlı spektrum örneklerinden birkaç dar tepe için sınırlı EQ kesim adayı gösterir; müzik/konuşma spektrumundan oda EQ düzeltmesi yapmaz. EQ ayarını mikser veya DSP donanımına otomatik uygulamaz; ölçüm mikrofonu, birden fazla konum, dinleme ve gerektiğinde transfer-function ölçümü ile doğrulama gerekir.'),P('3. RTA: ne ölçülüyor, ne ölçülmüyor?','H1SP'),P('RTA, mikrofon ya da ses kartı girişinin örneklerini FFT ile frekans bileşenlerine ayırıp oktav veya 1/3 oktav bantlarında göreli güç gösterir. Bu uygulamadaki grafik eğitim amaçlı bir spektrum kestirimidir. IEC 61260 sınıf 1/2 analizörü olarak sertifikalandırılmış değildir; kalibre edilmiş dB SPL, faz veya transfer-function ölçümü yapmaz.'),P('Frekans sınırının matematiği','H2SP'),P('RTA başlarken uygulama, aygıt destekliyorsa 48 kHz mono PortAudio akışını tercih eder. Kullanılan değer aygıtın fiziksel kapsül örnekleme özelliği değil, açılan akışın örnekleme hızıdır. Örnekleme frekansı Fs ise teorik Nyquist sınırı Fs/2 olur. Bir bant merkezinin bu sınırın altında olması tek başına yeterli değildir; tam bant için üst bant kenarı da Nyquist altında olmalıdır. Uygulama, üst kenarı sınırı aşan bantları eksik ölçüm gibi göstermemek için dışarıda bırakır.')]
rows=[[P('<b>PortAudio akış hızı</b>','TableSP'),P('<b>Nyquist</b>','TableSP'),P('<b>20 Hz–20 kHz aralığında son tam 1/3 oktav merkezi</b>','TableSP')],
[P('16.000 Hz','TableSP'),P('8.000 Hz','TableSP'),P('6,3 kHz; 8 kHz bandının üst kenarı Nyquist sınırını aşar.','TableSP')],
[P('22.050 Hz','TableSP'),P('11.025 Hz','TableSP'),P('8 kHz; 10 kHz bandının üst kenarı sınırı aşar.','TableSP')],
[P('32.000 Hz','TableSP'),P('16.000 Hz','TableSP'),P('12,5 kHz; 16 kHz bandı tam değildir.','TableSP')],
[P('44.100 Hz','TableSP'),P('22.050 Hz','TableSP'),P('16 kHz; 20 kHz bandının üst kenarı yaklaşık 22.450 Hz.','TableSP')],
[P('48.000 Hz','TableSP'),P('24.000 Hz','TableSP'),P('20 kHz; üst kenar yaklaşık 22.450 Hz olduğundan tam banda sığar. Mikrofon cevabı garanti edilmez.','TableSP')],
[P('96.000 Hz','TableSP'),P('48.000 Hz','TableSP'),P('20 kHz; uygulamanın üst sınırı 20 kHz olarak kalır.','TableSP')]]
t=Table(rows,colWidths=[31*mm,25*mm,89*mm],repeatRows=1)
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('BOX',(0,0),(-1,-1),0.5,LIGHT),('INNERGRID',(0,0),(-1,-1),0.35,LIGHT),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
story += [t,Spacer(1,8),P('Özel frekans aralığı','H2SP'),P('RTA ekranında hazır aralıkların yanında özel alt/üst sınır girilebilir. Uygulama yalnızca seçilen aralıkta bulunan ve üst bandı Nyquist sınırının altında kalan tam bant merkezlerini çizer. Örneğin 44,1 kHz akışta 20 kHz 1/3 oktav bandı tam bant değildir; grafik bu nedenle 16 kHz üst merkezinde kesilir ve durum metninde nedenini bildirir. Bu, üst frekansların mikrofonda fiziksel olarak algılandığını garanti etmez.'),P('FFT boyutu seçimi','H2SP'),P('8192 daha düşük işlem maliyeti, 16384 dengeli çözünürlük, 32768 ise daha ince frekans aralığı sağlar ancak düşük güçlü bilgisayarda daha fazla CPU tüketebilir. FFT bin aralığı Fs / FFT boyutu ile yaklaşık hesaplanır. Dar bantlı düşük frekanslarda bir bant içine az sayıda bin düşebilir; daha büyük FFT bu çözünürlüğü artırır ama cihazın fiziksel frekans cevabını iyileştirmez.'),P('PC mikrofonu neden tizleri eksik gösterebilir?','H2SP'),P('Dizüstü mikrofonu konuşma anlaşılabilirliği için tasarlanmış olabilir; mikrofon kapsülü, mikrofon dizisi, fiziksel yerleşim, üretici eşitlemesi, gürültü bastırma ve otomatik kazanç yüksek frekansları azaltabilir veya güçlendirebilir. RTA yazılımı mikrofonun ölçülmemiş frekans cevabını geri getiremez. PortAudio üzerinden cihaz açılır ve uygulama içinde aygıt/örnekleme bilgileri gösterilir; bu değerler mikrofon kapsülünün kalibre edilmiş frekans cevabı değildir. Doğru RTA karşılaştırması için mümkünse kalibrasyonu ve frekans cevabı bilinen ölçüm mikrofonu, uygun ses kartı ve bilinen test sinyali kullan.'),P('Mikrofon sorunu giderme','H2SP')]
for item in [
'1. Windows Ayarlar → Sistem → Ses → Giriş bölümünde doğru mikrofonu seç; giriş seviyesi hareket ediyor mu kontrol et.',
'2. Windows Ayarlar → Gizlilik → Mikrofon kısmında mikrofon erişimi ve masaüstü uygulamalarının erişimi açık olsun.',
'3. RTA içinde Girişleri yenile düğmesine bas; cihazı seç ve Mikrofonu başlat. Başka bir uygulama mikrofonu kullanıyorsa onu kapat.',
'4. Ses Denetim Masası → Kayıt → mikrofon özellikleri altında varsa Ses geliştirmeleri / gürültü bastırma / otomatik seviye özelliklerini kapatıp yeniden dene. Sürücü bu özellikleri ayrıca uygulayabilir.',
'5. Giriş peak/RMS seviyesine bak. Seviye sürekli sıfıra yakınsa Windows giriş sesini ve donanım kazancını kontrol et; tepe 0 dBFS yakınındaysa kazancı düşür.',
'6. 16 kHz veya 20 kHz bandındaki düşüşü yazılımsal olarak düzeltmeye çalışmadan önce başka mikrofon/ses kartıyla karşılaştır. Mikrofonun gerçek frekans cevabı bilinmiyorsa grafiği kalibrasyon kanıtı sayma.'
]: story.append(P(item))
story += [P('4. Güvenlik, gizlilik ve raporlama','H1SP'),P('Mikrofon yalnızca RTA başlatıldığında açılır. RTA akışı uygulama tarafından ses kaydı dosyası olarak saklanmaz. Yerel ses ve video dosyaları kendiliğinden AI servisine gönderilmez. İsteğe bağlı AI bölümüne metin göndermeden önce onay kutusunu oku; gizli kişisel bilgi veya API anahtarını isteme yazma.'),P('Elektrik, rigging, RF frekans koordinasyonu, yüksek SPL ve kamuya sunulan akustik raporlar yetkin kişiler, güncel resmî kaynaklar, üretici kılavuzları ve gerçek saha ölçümleri gerektirir. Bu eğitim yazılımı yetki belgesi veya mevzuata uygunluk sertifikası değildir. Ölçüm raporunda cihaz, kalibrasyon, konum, süre, ayar, çevre koşulları, sonuç, sınırlama ve tekrar adımlarını yaz.')]

def footer(canvas,doc):
    canvas.saveState(); w,h=A4
    canvas.setStrokeColor(GOLD);canvas.setLineWidth(.6);canvas.line(18*mm,15*mm,w-18*mm,15*mm)
    canvas.setFont(REG,7.5);canvas.setFillColor(GREY);canvas.drawString(18*mm,9*mm,'STAGEPULSE · Öğrenci Uygulama Rehberi · v3.5.1')
    canvas.drawRightString(w-18*mm,9*mm,f'Sayfa {doc.page}')
    canvas.restoreState()

doc=SimpleDocTemplate(str(out),pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=17*mm,bottomMargin=21*mm,title='Stagepulse Ses Mühendisliği Merkezi - Öğrenci Uygulama Rehberi',author='Stagepulse')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(out, out.stat().st_size)
