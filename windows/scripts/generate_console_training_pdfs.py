from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, KeepTogether, HRFlowable, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'egitim_paketleri'
ASSETS = ROOT / 'ui' / 'assets'
OUT.mkdir(exist_ok=True)
FONT_CANDIDATES = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf',
    'C:/Windows/Fonts/arial.ttf',
]
BOLD_CANDIDATES = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf',
    'C:/Windows/Fonts/arialbd.ttf',
]
font_path = next((p for p in FONT_CANDIDATES if Path(p).exists()), None)
bold_path = next((p for p in BOLD_CANDIDATES if Path(p).exists()), None)
if not font_path or not bold_path:
    raise RuntimeError('Türkçe karakterleri destekleyen DejaVuSans/LiberationSans fontu bulunamadı.')
pdfmetrics.registerFont(TTFont('StageSans', font_path))
pdfmetrics.registerFont(TTFont('StageSans-Bold', bold_path))
GOLD = colors.HexColor('#D8B45D')
GOLD_DARK = colors.HexColor('#84682B')
INK = colors.HexColor('#151922')
MUTED = colors.HexColor('#5B6675')
PALE = colors.HexColor('#F4F1E8')
LINE = colors.HexColor('#D9DEE5')
WHITE = colors.white

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='CoverTitleSP', fontName='StageSans-Bold', fontSize=25, leading=31, textColor=WHITE, alignment=TA_LEFT, spaceAfter=12))
styles.add(ParagraphStyle(name='CoverSubSP', fontName='StageSans', fontSize=12, leading=18, textColor=colors.HexColor('#E5D7AF'), alignment=TA_LEFT, spaceAfter=8))
styles.add(ParagraphStyle(name='H1SP', fontName='StageSans-Bold', fontSize=18, leading=23, textColor=INK, spaceAfter=8, keepWithNext=True))
styles.add(ParagraphStyle(name='H2SP', fontName='StageSans-Bold', fontSize=12, leading=16, textColor=GOLD_DARK, spaceBefore=8, spaceAfter=5, keepWithNext=True))
styles.add(ParagraphStyle(name='BodySP', fontName='StageSans', fontSize=9.3, leading=14, textColor=INK, spaceAfter=7))
styles.add(ParagraphStyle(name='SmallSP', fontName='StageSans', fontSize=7.8, leading=11, textColor=MUTED, spaceAfter=4))
styles.add(ParagraphStyle(name='BulletSP', fontName='StageSans', fontSize=9, leading=13, leftIndent=12, firstLineIndent=-7, bulletIndent=1, textColor=INK, spaceAfter=4))
styles.add(ParagraphStyle(name='CalloutSP', fontName='StageSans-Bold', fontSize=9, leading=13, textColor=INK, backColor=PALE, borderColor=GOLD, borderWidth=0.7, borderPadding=8, spaceBefore=6, spaceAfter=10))
styles.add(ParagraphStyle(name='TableHeadSP', fontName='StageSans-Bold', fontSize=8.3, leading=11, textColor=WHITE))
styles.add(ParagraphStyle(name='TableCellSP', fontName='StageSans', fontSize=8.0, leading=11, textColor=INK))
styles.add(ParagraphStyle(name='TOCSP', fontName='StageSans', fontSize=9.2, leading=15, textColor=INK, leftIndent=8, spaceAfter=3))
styles.add(ParagraphStyle(name='CenterSP', fontName='StageSans', fontSize=10, leading=15, alignment=TA_CENTER, textColor=INK, spaceAfter=8))


def P(text, style='BodySP'):
    # Safe, intended markup only; escape ampersands in authored copy where needed.
    return Paragraph(text, styles[style])

def bullet(text):
    return Paragraph('• ' + bilingualize_markup(text), styles['BulletSP'])

def make_table(rows, widths=None):
    cooked=[]
    for ri,row in enumerate(rows):
        sty='TableHeadSP' if ri==0 else 'TableCellSP'
        cooked.append([Paragraph(bilingualize_markup(str(cell)), styles[sty]) for cell in row])
    t=Table(cooked, colWidths=widths, repeatRows=1, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),INK), ('TEXTCOLOR',(0,0),(-1,0),WHITE),
        ('GRID',(0,0),(-1,-1),0.45,LINE), ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),7), ('RIGHTPADDING',(0,0),(-1,-1),7),
        ('TOPPADDING',(0,0),(-1,-1),6), ('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE,colors.HexColor('#FAFAF8')]),
    ]))
    return t

def footer(canvas, doc):
    canvas.saveState()
    w,h=A4
    canvas.setFillColor(INK)
    canvas.rect(0,0,w,11*mm,fill=1,stroke=0)
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(1.1)
    canvas.line(16*mm,11*mm,w-16*mm,11*mm)
    canvas.setFont('StageSans',7.2)
    canvas.setFillColor(colors.HexColor('#E8EAF0'))
    canvas.drawString(16*mm,6.5*mm,'STAGEPULSE  |  SES MÜHENDİSLİĞİ MERKEZİ')
    canvas.drawRightString(w-16*mm,6.5*mm,f'Sayfa {doc.page}')
    canvas.restoreState()

def cover_flow(title, subtitle, console, duration, focus):
    flow=[]
    # Brand mark
    logo = ASSETS / 'stagepulse-icon.png'
    if logo.exists():
        im=Image(str(logo), width=36*mm, height=36*mm)
        flow += [Spacer(1,7*mm), im, Spacer(1,7*mm)]
    cover_rows=[
        [P('STAGEPULSE', 'CoverSubSP')],
        [P(title, 'CoverTitleSP')],
        [P(subtitle, 'CoverSubSP')],
        [Spacer(1,2*mm)],
        [P(f'<b>Konsol:</b> {console}<br/><b>Önerilen süre:</b> {duration}<br/><b>Eğitim tipi:</b> Tezgâh başı uygulama ve teknik çalışma', 'CoverSubSP')],
        [Spacer(1,2*mm)],
        [P(f'<b>Odak:</b> {focus}', 'CoverSubSP')],
    ]
    t=Table(cover_rows, colWidths=[169*mm])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),INK),('BOX',(0,0),(-1,-1),1.2,GOLD),('LEFTPADDING',(0,0),(-1,-1),13*mm),('RIGHTPADDING',(0,0),(-1,-1),12*mm),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    flow.append(t)
    flow += [Spacer(1,10*mm), P('Uygulama odaklı öğrenci çalışma kitabı', 'H1SP'),
      P('Bu kitap Stagepulse tarafından hazırlanmış özgün bir çalışma materyalidir. Menü adları ve özellik davranışları cihaz modeli, yazılım sürümü ve yapılandırmaya göre değişebilir. Sahada kullanılan konsolun üretici dokümanını ve güncel firmware notlarını kontrol edin.', 'BodySP'),
      P('Önemli sınır: Bu belge, üreticinin resmî kullanım kılavuzunun yerine geçmez. Mikrofon, phantom power, patch, scene recall, ağ ve RF işlemlerinde sahne sorumlusu ile onaylı çalışma prosedürünü izleyin.', 'CalloutSP'), PageBreak()]
    return flow

def lesson(title, objective, explain, practice, checklist, failure, question):
    flow=[P(title,'H1SP'), P('<b>Bu bölümün hedefi:</b> '+objective,'BodySP'), P('Teknik açıklama','H2SP'), P(explain,'BodySP'), P('Uygulama','H2SP')]
    flow += [bullet(x) for x in practice]
    flow += [P('Kontrol listesi','H2SP')]
    flow += [bullet('□ '+x) for x in checklist]
    flow += [P('Sahada sık görülen hata','H2SP'), P(failure,'BodySP'), P('<b>Kendini değerlendir:</b> '+question,'CalloutSP'), PageBreak()]
    return flow

MANUALS = [
  {
    'file':'10_Midas_M32_Live_Uygulamali_Egitim.pdf',
    'title':'Midas M32 Live Uygulamalı Eğitim',
    'subtitle':'Canlı ses, FOH, monitor ve sahne iş akışı',
    'console':'Midas M32 / M32 Live', 'duration':'12 ders saati (4 oturum önerisi)',
    'focus':'Gain staging, input ve output routing, bus/monitor, AES50 farkındalığı, efektler, scene güvenliği ve show günü disiplini',
    'concepts':[
      ('01 · Konsolu tanımak ve show dosyası','Fiziksel yüzey, katmanlar ve seçili kanal mantığını anlamak.',
       'M32 ailesinde kanal, bus, DCA, mute group ve efekt katmanları farklı görevler üstlenir. Önce mevcut show dosyasını yedekleyin; sonra kanal adlarını, patch listesini, bus kullanımını ve sahne adlarını doğrulayın. Fiziksel donanım sürümü ve yazılım/firmware uyumluluğu iş öncesinde kontrol edilmelidir.',
       ['Konsolu açmadan önce bağlı ekipmanı ve güç sırasını kontrol edin.','Mevcut sahne dosyasını yeni bir adla yedekleyin.','Kanal numaraları, isimler, renkler ve kaynak listesini sahne plotu ile eşleştirin.'],
       ['Orijinal show dosyasını koru.','Önemli sahne geçişini ayrı bir kopyada dene.','Yedek dosyanın gerçekten dışa aktarıldığını doğrula.'],
       'Başkasından alınmış show dosyasını incelemeden mevcut konsola yüklemek, kaynak patch’ini ve çıkış yönlendirmesini beklenmedik şekilde değiştirebilir.',
       'Yedekleme ile sahne geri çağırma neden aynı işlem değildir?'),
      ('02 · Input patch ve preamp','Fiziksel girişin doğru kanala ulaştığını doğrulamak.',
       'Kaynağın XLR girişi, local/AES50 kaynağı ve kanal input seçimi birbirinden farklı katmanlardır. “Sinyal yok” durumunda önce kaynağı, kabloyu, giriş kaynağı seçimini, preamp gain değerini ve meter hareketini ayrı ayrı kontrol edin. 48 V phantom power yalnızca ihtiyaç duyan kondansatör mikrofon veya aktif DI gibi donanımlara, bağlantı doğrulandıktan sonra uygulanmalıdır.',
       ['Bir mikrofonu tek kabloyla test girişine bağlayın.','Kanalın kaynak seçimini ve meter hareketini kontrol edin.','PFL ile kulaklıkta güvenli seviyede sinyali dinleyin.'],
       ['Kanal mute durumunu kontrol et.','Gain ile fader’ın farklı görevlerini ayırt et.','Phantom power öncesi kaynak tipini kontrol et.'],
       'Meter yoksa önce fader yükseltmek çoğu zaman çözüm değildir; sorun patch veya giriş kaynağında olabilir.',
       'Sinyal meter’a geliyor ancak ana çıkışta duyulmuyorsa sıradaki üç kontrolün nedir?'),
      ('03 · Gain staging ve headroom','Girişten çıkışa temiz seviye yapısı kurmak.',
       'Preamp seviyesini, kanal işleme aşamalarını ve master çıkış seviyesini tek “ses açma” kontrolü gibi düşünmeyin. PFL ile gerçek giriş seviyesini kontrol edin, ani transientler için headroom bırakın ve dijital clipping’e yaklaşan noktaları düzeltin. Düşük kaynak seviyesi sadece master fader’ı yükselterek her zaman sağlıklı biçimde giderilemez.',
       ['Konuşma ve enstrüman için gerçek performans seviyesinde kontrol yapın.','Peak meter’ları izleyin ve olağan dışı transientleri not edin.','Gain değişikliğinden sonra kompresör ve gate davranışını tekrar dinleyin.'],
       ['PFL ile kanal girişini kontrol et.','Clip göstergelerini gözle.','Gain değişikliğini kayıt altına al.'],
       'Soundcheck sırasında çok düşük seviyede yapılan gain ayarı, gerçek performans başladığında clipping yaratabilir.',
       'Giriş gain’i, kanal fader’ı ve DCA aynı şeyi mi değiştirir? Açıklayın.'),
      ('04 · Kanal işleme: HPF, EQ, gate, compressor','İşlemcileri amaca uygun ve ölçülü kullanmak.',
       'HPF gereksiz düşük frekans rumble’ını azaltabilir; EQ tonal denge ve sorun çözümü içindir; gate/expander arka planı kontrol edebilir; compressor dinamik aralığı yönetir. İşlemcileri görsel olarak değil, bypass A/B dinlemesi ve miks bağlamında karar vererek ayarlayın. Gate ayarı heceleri veya sustain’i kesmemeli; kompresörde gain reduction, attack/release ve makeup gain birlikte değerlendirilmelidir.',
       ['Konuşma kanalında HPF’yi kontrollü biçimde açın.','EQ öncesi ve sonrası aynı algılanan ses düzeyinde A/B yapın.','Kompressör gain reduction davranışını dinleyin.'],
       ['Aşırı EQ kesim/boost’tan kaçın.','Gate’i sessizlikte ve kelime başlarında dene.','İşlemci bypass denetimini kullan.'],
       'Daha yüksek seviyenin daha iyi duyulması, EQ ayarının daha iyi olduğu anlamına gelmez.',
       'Kötü mikrofon konumu sorununu neden ilk olarak ağır EQ ile çözmemelisiniz?'),
      ('05 · Bus, Main ve DCA','Ana miks ile yardımcı miksin farkını uygulamak.',
       'Main L/R izleyiciye giden ana miksin tipik hedefidir. Mix bus’lar monitör, kayıt, delay zone veya grup işlemesi gibi farklı amaçlar için kullanılabilir. DCA, atanan kanal seviyelerini toplu yönetir; tek başına yeni bir audio bus değildir. Bus pre/post fader ayarı, monitör miksinin FOH fader hareketinden etkilenip etkilenmeyeceğini belirler.',
       ['Vokal için ayrı monitor bus oluşturun.','Bus send seviyesini ve pre/post ayarını doğrulayın.','DCA atamasını kontrol ederek bir seferde yalnızca ilgili grubu yönetin.'],
       ['Bus çıkışının fiziksel porta patch edildiğini doğrula.','Pre/post fader mantığını not et.','DCA mute ile kanal mute farkını kontrol et.'],
       'Bus meter’ında sinyal olması, fiziksel XLR çıkışında mutlaka sinyal olduğu anlamına gelmez.',
       'DCA neden ayrı bir monitor miksinin yerine geçmez?'),
      ('06 · Monitor ve IEM güvenliği','Sahne miksini ve kulaklık risklerini yönetmek.',
       'Monitor miksini sahne üzerindeki kaynağın ihtiyacına göre kurun. IEM kullanımında peak seviyeleri ve kablosuz bağlantı kadar kulak sağlığı önemlidir. Sert geri besleme veya ani patch hatası kulaklıkta tehlikeli seviyeye çıkabilir. Soundcheck öncesinde tüm monitör/IEM seslerini minimumda tutan bir başlangıç disiplini belirleyin.',
       ['Her monitor bus’ı bir isim ve hedef ile eşleştirin.','Sanatçıdan gelen talepleri tek tek ekleyin.','Kulaklık vericilerini mutlak minimumdan başlatın.'],
       ['Monitor send kaynaklarını doğrula.','IEM sesini ani şekilde yükseltme.','Sahne sorumlusu ile değişiklikleri teyit et.'],
       'Tüm sanatçılara aynı monitor miksini vermek, sahne ihtiyaçlarına yanıt vermez.',
       'IEM’de geri beslemeden önce hangi elektriksel ve yönlendirme kontrolleri yapılmalıdır?'),
      ('07 · AES50 ve stagebox','Ağ tabanlı dijital stagebox bağlantısını yönetmek.',
       'AES50, uyumlu cihazlar arasında çok kanallı dijital ses ve kontrol taşımak için kullanılır. Kablo güzergâhı, uygun Cat kablo ve konnektör kalitesi, cihazların port eşlemesi ve clock durumları önemlidir. AES50’yi sıradan ofis Ethernet ağı gibi bir switch ağına bağlama varsayımıyla ele almayın; her sistemin üretici dokümantasyonu izlenmelidir.',
       ['Cihaz modelini ve port etiketlerini kontrol edin.','Kablonun hasarsız ve doğru uzunlukta olduğundan emin olun.','Stagebox giriş/çıkış patch’ini konsol planıyla karşılaştırın.'],
       ['Kabloyu fiziksel gerilimden koru.','Port yönünü doğru doğrula.','Clock/sync durumunu açılış kontrolüne ekle.'],
       'Yanlış port ya da uyumsuz patch, birden fazla kanalda sessizliğe veya beklenmedik kaynaklara neden olabilir.',
       'AES50 link ışığı tek başına tüm kanal patch’inin doğru olduğunu kanıtlar mı?'),
      ('08 · FX ve efekt send/return','Reverb ve delay’i yönlendirme hatası oluşturmadan kullanmak.',
       'Efekt bus/send ve return yolları ayrı kontrol edilmelidir. Send seviyesini artırmak, return kanalının mute veya patch durumunu düzeltmez. Reverb/delay miktarını bağlama göre ayarlayın; konuşmada anlaşılabilirliği koruyun, müzikte efekt kuyruklarının tempo ve aranjmanla ilişkisini dinleyin.',
       ['Bir reverb efektini uygun send/return yoluyla kurun.','Return kanalını mute ederek kontrol amaçlı A/B yapın.','FX send ve return seviyelerini ayrı ayrı kaydedin.'],
       ['Efekt return kanalını isimlendir.','Return’ün Main’e yönlendirildiğini doğrula.','Preset değiştirmeden önce kopya sahne oluştur.'],
       'Return kanalı Main’e gitmiyorsa send seviyesini artırmak yalnızca sinyalin efekt motoruna gittiğini gösterir.',
       'FX send meter hareket ediyor ama efekt duyulmuyorsa hangi dönüş yolunu izleyeceksiniz?'),
      ('09 · Scene, snippet ve recall güvenliği','Sahne değişikliklerini geri alınabilir ve kontrollü hale getirmek.',
       'Scene/snapshot yapıları kanal parametreleri, patch veya routing gibi farklı bilgileri kapsayabilir. Recall scope, safe ve filtreler sistemde hangi parametrelerin geri yükleneceğini belirleyebilir. Bir sahneyi çağırmadan önce hedef sahneyi, kapsamı ve değişecek çıkışları kontrol edin. Kritik show dosyasını yedeklemeden tek tuşla recall yapmayın.',
       ['Bir “soundcheck” sahnesi ve bir “show” sahnesi tanımlayın.','Recall scope/safe davranışını düşük riskli testte doğrulayın.','Sahne değişikliğinden sonra routing ve mute durumlarını kontrol edin.'],
       ['Her show için ayrı dosya kopyası sakla.','Sahne isimlerini açık yaz.','Recall sonrası mute ve bus kontrolü yap.'],
       'Snapshot’ın her parametreyi çağırdığı varsayımı da hiçbir parametreyi çağırmadığı varsayımı da tehlikelidir.',
       'Recall filtreleri neden sadece kayıt alırken değil gösteri sırasında da kritiktir?'),
      ('10 · Talkback, kayıt ve ölçüm','Operasyonel iletişim ve kayıt hatalarını azaltmak.',
       'Talkback routing’i sanatçıya veya ekibe giden hedeflerle eşleştirilmelidir. USB kayıt/playback veya dahili kayıt özellikleri model/firmware’e göre değişebilir; kanal kaynağı, sample rate, kayıt hedefi ve izleme yolu önceden doğrulanmalıdır. Ölçüm mikrofonunu referans/kalibrasyon gereklilikleriyle değerlendirin; telefon ölçümü sertifikalı SPL ölçerin yerine geçmez.',
       ['Talkback’i hedef bus’lara ayrı ayrı test edin.','Kısa test kaydı alıp dosyanın açıldığını doğrulayın.','Kayıt ve canlı çıkış yollarını birbirinden ayırın.'],
       ['Talkback yanlışlıkla Main’e gitmesin.','Kayıt başlat/durdur durumunu doğrula.','Kayıt dosyası yedekleme adımını ekle.'],
       'Kayıt göstergesinin çalışması, dosyanın doğru hedefe yazıldığı veya sonradan açılabildiği anlamına gelmez.',
       'Talkback sinyali yanlışlıkla Main’e gidiyorsa ilk güvenli müdahale nedir?'),
      ('11 · Soundcheck ve show akışı','Tekrarlanabilir iş akışı kurmak.',
       'Soundcheck sırası sahne plotu, line check, gain, monitor, FOH balansı, problem kaydı ve show dosyası yedeklemesini içerir. Büyük değişiklikleri sözlü teyit olmadan yapmak yerine patch tablosunu güncelleyin. Canlı olayda önce sesi güvenli biçimde kontrol altına alın, ardından kök nedeni izole edin.',
       ['Input list ile fiziksel girişleri sırayla kontrol edin.','Line check sorunlarını tabloya yazın.','Show öncesi dosya ve kritik çıkışları yedek planla doğrulayın.'],
       ['Sahne üzerinde kablo etiketleri kullan.','Problem/sorumlu/çözüm notu tut.','Show dosyasının yedeğini ayrı medyada sakla.'],
       'Aynı anda gain, EQ, routing ve bus değiştirirseniz hangi değişikliğin sorunu çözdüğünü bilemezsiniz.',
       'Show sırasında sorun çözme yaklaşımında neden tek değişken kuralı yararlıdır?'),
      ('12 · Arıza bulma ve teslim','Sinyal yolunda arızayı sistematik olarak daraltmak.',
       'Arıza izleme akışı kaynağı, kabloyu, input patch’i, kanal processing’i, send/bus, output patch’i ve fiziksel hedefi kapsamalıdır. Her adımda meter, PFL veya bilinen sağlam yedek kaynak kullanarak doğrulama yapın. Teslimde kullanılan show dosyası, patch listesi, bilinen arızalar ve geçici bypass’lar raporlanır.',
       ['“Sinyal yok” senaryosunda kaynaktan hoparlöre kadar blok diyagram çizerek ilerleyin.','Bir yedek mikrofon/kabloyla çapraz test yapın.','Teslim raporunda yapılan değişiklikleri yazın.'],
       ['Çıkış mute’larını kontrol et.','Known-good yedekle çapraz test yap.','Geçici değişiklikleri teslimde belirt.'],
       'Arıza giderilse bile geçici patch veya bypass belgelenmezse sonraki ekip aynı sorunu yeniden yaşayabilir.',
       'Bir sistemi teslim ederken hangi üç belge mutlaka aktarılmalıdır?'),
    ],
    'sources':[
      ('Midas M32 ürün ve destek sayfası','https://www.midasconsoles.com/en/products/0603-AEO'),
      ('M32 kullanıcı kılavuzu (üretici dokümanı)','https://cdn.mediavalet.com/aunsw/musictribe/yd140PNkGkipTcsODx8rQg/l7vFZzsCL0qGan2n4RQtbA/Original/M32_M_EN.pdf'),
      ('M32 Quick Start Guide','https://mediadl.musictribe.com/media/PLM/data/docs/P0B3I/M32_QSG_EN.pdf')]
  },
  {
    'file':'11_Yamaha_CL5_Uygulamali_Egitim.pdf',
    'title':'Yamaha CL5 Uygulamalı Eğitim',
    'subtitle':'Centralogic, Selected Channel, Dante ve show güvenliği',
    'console':'Yamaha CL5', 'duration':'12 ders saati (4 oturum önerisi)',
    'focus':'Input patch, HA/gain, Selected Channel, Centralogic, Mix/Matrix, Dante farkındalığı ve scene recall güvenliği',
    'concepts':[
      ('01 · CL5 yüzeyini tanımak','Selected Channel ve Centralogic çalışma mantığını öğrenmek.',
       'CL5 iş akışında Selected Channel, seçilen kanalın ayrıntılı kontrollerini; Centralogic ise kanal bankaları ve grup iş akışını destekler. Kanal seçimi, fader bankası ve ekran sayfası her zaman aynı nesneyi göstermeyebilir. İlk uygulamada kanal numarası, isim, renk ve seçili kaynak doğrulamasını birlikte yapın.',
       ['Masa yüzeyindeki kanal bankalarını model üzerinde tanımlayın.','Kanal seçimini değiştirip Selected Channel parametrelerini takip edin.','Fader bankasını ve seçilen kanal numarasını ses kaynağıyla doğrulayın.'],
       ['Kanal adlandırma ve renk kodu kullan.','Bank değişince seçili kanalı kontrol et.','Kullanılan show dosyasını yedekle.'],
       'Benzer isimli kanallar arasında bank değiştirirken yanlış kanalı işlemek sahnede beklenmedik seviyelere yol açar.',
       'Selected Channel görüntüsü ve fader bankasının farklı iş yapmasının avantajı nedir?'),
      ('02 · Input patch, HA ve gain','Fiziksel giriş ile kanal kaynağı ilişkisini kurmak.',
       'CL5 giriş patch’i, yerel girişler ve uygun Dante/remote kaynaklar arasında seçim yapılmasına imkân tanır. Head Amp kontrolü, sahne kutusunun veya lokal preamp’ın gain kontrolünü etkileyebilir. Birden çok konsolun aynı preamp’ı paylaştığı sistemlerde gain ownership ve paylaşım protokolünü doğrulamadan değişiklik yapmayın.',
       ['Bir lokal mikrofon kanalını patch edin.','Meter, PFL ve kulaklıkla sinyalin varlığını kontrol edin.','Remote HA/başka konsol kullanımında gain sorumlusunu belirleyin.'],
       ['Kanal kaynağını fiziksel girişle eşleştir.','Phantom power öncesi kaynak tipini doğrula.','Birden çok konsolda HA sahipliğini teyit et.'],
       'Kanalda meter hareketi olmaması, fader seviyesinden önce patch ve kaynak kontrolü gerektirir.',
       'Ortak head amp üzerinde iki operatör çalışırken gain paylaşımını nasıl yönetirsiniz?'),
      ('03 · Channel strip ve işleme','EQ, dynamics ve filtreleri işitsel hedefe göre kullanmak.',
       'Selected Channel, ilgili kanalın ayrıntılı işleme noktalarına erişimi hızlandırır. HPF, EQ, gate/expander ve compressor işlevlerini birbirinden ayırın; kararları eşit algılanan ses düzeyinde A/B dinlemeyle doğrulayın. Kademeler arasında clipping oluşabilir; giriş ve işlemci çıkış seviyelerini birlikte değerlendirin.',
       ['Konuşma mikrofonunda HPF ve ölçülü EQ uygulayın.','Kompresör gain reduction’ı ve bypass davranışını dinleyin.','İşleme sonrası meter değerlerini not edin.'],
       ['İşlemciyi bypass ederek A/B yap.','Aşırı boost yerine kaynak yerleşimini değerlendir.','Dinamik işlemde saldırı/bırakma davranışını dinle.'],
       'Görsel EQ eğrisi tek başına doğru tonal dengeyi kanıtlamaz.',
       'Bir konuşma mikrofonunda anlaşılabilirliği artırmak için hangi adımları sırayla denersiniz?'),
      ('04 · Mix bus, Matrix ve Main','Ana miks ve zone/dağıtım yollarını ayırmak.',
       'Mix bus’lar monitör, grup veya yardımcı miksler için; Matrix yolları ise Main/Bus mikslerini bölgelere veya farklı çıkışlara dağıtmak için kullanılabilir. Kurulumda bus yapılandırması ve kaynak ataması hedefe göre seçilir. Her bus/Matrix için kaynak send seviyeleri, master seviyesi ve fiziksel output patch doğrulanmalıdır.',
       ['Bir monitor Mix bus’ı hazırlayın.','Ana miksin bir Matrix çıkışına gidişini düşük seviyede test edin.','Bus/Matrix adlarını hedef bölgeyle eşleştirin.'],
       ['Bus ve Matrix görevlerini yaz.','Output patch’i fiziksel portla doğrula.','Meter hareketi sonrası gerçek çıkışı test et.'],
       'Matrix meter hareketi, hedef çıkışın doğru porta verildiğini tek başına kanıtlamaz.',
       'Monitor Mix bus ile gecikme bölgesi için Matrix kullanımı nasıl farklılaşabilir?'),
      ('05 · Centralogic ve kanal bankaları','Büyük kanal sayısında tutarlı dolaşım sağlamak.',
       'Centralogic bankaları ilgili kanallara hızlı erişim verir; bu erişim katmanlarını sahne plotu ile tutarlı isimlendirme ve renklerle destekleyin. Bankalar arasında geçiş yapan operatör, önemli kanalları fiziksel olarak etiketleyebilir ve show dosyasında organizasyon standartları kullanabilir.',
       ['Kanal grubunu vokal/enstrüman/FX gibi mantıklı adlarla düzenleyin.','Bank geçişinde doğru kanalın seçili olduğunu doğrulayın.','Önemli konuşma ve acil anons kanallarına hızlı erişim planlayın.'],
       ['Fiziksel etiketle yazılım adını eşleştir.','Acil kanalların konumunu ekip ile paylaş.','Bank geçişi sonrası fader kontrolü yap.'],
       'İsimlendirme standardı yoksa aynı kaynak farklı show dosyalarında farklı bankalarda bulunabilir.',
       'Büyük festival patch’inde bank düzeni neden operatör hatasını azaltır?'),
      ('06 · Dante ve ağ farkındalığı','Dante kaynaklarını ve sistem ağını temel seviyede doğrulamak.',
       'Dante, IP tabanlı dijital ses taşımacılığıdır; CL serisi konfigürasyonlarında cihazlar, abonelikler, clock ve ağ yapılandırması uygun şekilde eşleştirilmelidir. Konsol menüsü dışında Dante Controller gibi araçların gösterdiği abonelik ve saat kaynağı bilgisi de kontrol edilmelidir. Ağa bilinçsiz switch/port eklemeyin; üretici tavsiyesi ve sistem tasarımına uyun.',
       ['Cihaz adlarını ve kanal aboneliklerini listeleyin.','Primary/secondary ağ ayrımını sistem dokümanında kontrol edin.','Clock status ve ses aboneliklerini yetkili ekip ile doğrulayın.'],
       ['Ağ kablolarını etiketle.','Uygun switch ve QoS gerekliliklerini doğrula.','Clock uyuşmazlığını show başlamadan çöz.'],
       'Link ışığı yanıyor olabilir fakat yanlış abonelik veya clock durumu sesin geçmemesine neden olabilir.',
       'Dante cihazı görünür fakat kanal sessizse hangi kontroller yapılmalıdır?'),
      ('07 · Monitor, IEM ve pre/post','Sanatçı miksinin FOH seviyesinden bağımsızlığını yönetmek.',
       'Mix send noktaları, pre/post fader seçimi ve bus seviyeleri monitor davranışını değiştirir. FOH fader’ı hareket ettiğinde IEM miksinin etkilenip etkilenmediğini sistematik olarak test edin. IEM çıkış seviyesini güvenli bir alt seviyeden başlatın; birden fazla göndericide aynı RF/patch varsayımlarını kullanmayın.',
       ['Bir vokal monitor miksini kurun.','FOH fader’ını değiştirip pre/post etkisini doğrulayın.','Sanatçının isteklerini birer birer uygulayın.'],
       ['Mix send noktalarını kaydet.','IEM seviyesini minimumdan başlat.','Yanlış bus assignment kontrolü yap.'],
       'Monitor talebine hemen EQ ile cevap vermek yerine send kaynakları ve gain paylaşımı kontrol edilmelidir.',
       'Post-fader vokal send hangi durumda monitor miksini istenmeden değiştirebilir?'),
      ('08 · Efektler ve send/return','Efekt rotasını doğrulamak ve miks içinde dengeli tutmak.',
       'Efekt motoru, send bus, return kanalı ve Main/Matrix çıkışı tek zincirin parçalarıdır. Return fader’ı mute ise send meter hareketi duyulur efekt üretmez. Konuşma ve canlı müzikte efekt kararlarını kaynağın türü ve salon akustiğiyle birlikte verin; her preset’i önce düşük riskli sahnede test edin.',
       ['Reverb send ve return rotasını kurun.','Return’ü mute ederek A/B kontrolü yapın.','FX parametrelerini değiştirirken kaynağın anlaşılabilirliğini koruyun.'],
       ['FX return yönlendirmesini doğrula.','Preset adını ve amaçlanan kaynağı yaz.','Show dosyasına geri dönüş noktası koy.'],
       'Sahnede güvenli şekilde karşılaştırma yapmadan çok uzun reverb kuyruğu kullanmak konuşmayı anlaşılmaz hale getirebilir.',
       'Efektin dönmediği bir show’da send, return ve output patch kontrollerini sırala.'),
      ('09 · Scene, focus ve recall filtreleri','Sahne değişikliklerini kontrollü yapmak.',
       'CL show dosyası ve scene/recall iş akışı farklı durumları saklayabilir. Focus/recall filtreleri, hangi parametrelerin uygulanacağını etkiler. Kanal, input patch, output patch ve efekt kapsamlarını kopya show dosyasında doğrulamak gerekir. Kritik parametreleri sahne geçişinden koruyan güvenli durumları belgelenmiş şekilde yönetin.',
       ['A/B scene oluşturun.','Recall filtrelerini belirli bir kanal grubunda test edin.','Recall sonrası giriş, bus ve master mute durumlarını kontrol edin.'],
       ['Show dosyası yedeği al.','Recall kapsamını yaz.','Kritik output patch değişimini kontrol et.'],
       'Recall filtrelerini bilmeden sahne yüklemek, kayıtlı miksin yalnızca bir kısmının uygulanmasına neden olabilir.',
       'Scene recall sonrasında neden sadece sahne adını değil, çıkışları da kontrol etmelisiniz?'),
      ('10 · Talkback, oscillator ve line check','Kontrol sinyallerini izole ve güvenli kullanmak.',
       'Talkback yalnızca amaçlanan monitor veya iletişim hedeflerine yönlendirilmelidir. Test oscillator/ton jeneratörü kullanılıyorsa çıkış seviyesi düşükten başlamalı ve hoparlör/işitme güvenliği gözetilmelidir. Ton testi sırasında Main ve monitor bus hedeflerinin hangilerinin etkileneceğini önceden belirleyin.',
       ['Talkback hedefini tek bir monitor bus üzerinde test edin.','Test tonu için kısa ve düşük seviyeli deneme yapın.','Line check sonucunu yazılı tabloyla işaretleyin.'],
       ['Test tone öncesi mute/level kontrol et.','Talkback Main yönlendirmesini kontrol et.','Line check sonucunu raporla.'],
       'Ton jeneratörünün yanlışlıkla tüm sistemlere gönderilmesi ani ve tehlikeli ses seviyesine yol açabilir.',
       'Test tone üretmeden önce hangi iki kontrolü kesinlikle yaparsınız?'),
      ('11 · Show gününe hazırlık','Dosya, yedek ve ekip koordinasyonunu standartlaştırmak.',
       'Show-ready kontrolü; doğru show dosyası, input list, patch, bus/Matrix, scene, network status, kulaklık ve yedek planlarını kapsar. Soundcheck değişiklikleri tek yerde not alınmalı, son dakika yamaları sonraki operatöre aktarılmalıdır. Her büyük değişiklik sonrası ilgili kanallar ve çıkışlar kısa tekrar kontrolünden geçirilir.',
       ['Giriş listesi ile fiziksel patch’i karşılaştırın.','Yedek show dosyasını farklı bir lokasyonda tutun.','Soundcheck notlarını operatör tesliminde kullanın.'],
       ['Dosya ve sürüm adlandırması yap.','Önemli değişimleri kaydet.','Acil iletişim yollarını açık tut.'],
       'Birden çok sürümün “final”, “final2” şeklinde tutulması yanlış dosyanın çağrılması riskini yükseltir.',
       'Show dosyası sürümlendirmesinde hangi isimlendirme kuralını uygularsınız?'),
      ('12 · Sistematik arıza bulma ve teslim','Yönlendirme sorunlarını adım adım izlemek.',
       'Sinyal yolunu kaynak, input patch/HA, kanal, bus send, bus master, Matrix/Main, output patch, fiziksel bağlantı ve hedef ekipman sırasıyla izleyin. Her noktada meter ve uygun dinleme ile doğrulayın. Teslim raporu, hangi scene/show dosyasının kullanıldığını ve yapılan kalıcı/geçici değişiklikleri içermelidir.',
       ['Bir kanalda sinyal yok senaryosunu katman katman çözün.','Yedek kablo veya kaynakla çapraz test yapın.','Sahne sonunda kullanılan show dosyasını teslim edin.'],
       ['Tek seferde tek değişkeni değiştir.','Patch ve meter kontrolünü sırayla yap.','Geçici bypass’ları belgede belirt.'],
       'Belgesiz geçici yönlendirme, bir sonraki etkinlikte sessizlik ya da yanlış zon beslemesi olarak geri dönebilir.',
       'Sinyalin kanalda var ama Matrix çıkışında yok olduğu durumda sıradaki kontroller hangileridir?'),
    ],
    'sources':[
      ('Yamaha CL serisi resmî indirme ve destek sayfası','https://usa.yamaha.com/products/proaudio/mixers/cl_series/downloads.html'),
      ('Yamaha CL5 Owner’s Manual','https://my.yamaha.com/files/download/other_assets/3/329223/cl5_en_om_d0.pdf')]
  },
  {
    'file':'12_Allen_Heath_Avantis_Uygulamali_Egitim.pdf',
    'title':'Allen & Heath Avantis Uygulamalı Eğitim',
    'subtitle':'Continuity UI, I/O patch, bus, scene ve canlı sorun giderme',
    'console':'Allen & Heath Avantis', 'duration':'12 ders saati (4 oturum önerisi)',
    'focus':'Continuity kullanıcı arayüzü, kanal bankaları, I/O patch, mix bus, FX, scene/show yönetimi ve güvenli operasyon',
    'concepts':[
      ('01 · Avantis yüzeyine giriş','Continuity arayüzünü ve kanal erişimini anlamak.',
       'Avantis ailesinde Continuity UI, ekranda kanal/işlemci görünümünü ve fiziksel fader alanlarıyla ilişkisini kurar. İki ekran ve kanal bankaları arasında dolaşırken seçilen kanal, görünür katman ve fiziksel fader eşleşmesini doğrulayın. Kurulumdan önce kullanılan donanım varyantı, firmware ve lisans/opsiyon durumunu not edin.',
       ['Kanal bankalarını ve görünüm düzenini haritalayın.','Bir giriş kanalını seçip ilgili işlemciyi takip edin.','Kanal adlandırma ve renk standardı oluşturun.'],
       ['Mevcut show dosyası yedeği al.','Seçili kanal ile fader eşleşmesini doğrula.','Operatör düzenini not et.'],
       'Ekranda görülen bir kanalın fiziksel fader üzerinde olduğu varsayımı, bank değişiminde hatalı müdahaleye neden olabilir.',
       'Continuity UI ve kanal bankası ilişkisini sahne ekibine nasıl açıklarsınız?'),
      ('02 · I/O portları ve patch','Giriş/çıkış kaynağını ve soket rotasını eşleştirmek.',
       'Avantis I/O yapısı yerel I/O, genişletme kartları ve uyumlu stagebox/remote I/O kaynaklarını içerebilir. Patch düzeni fiziksel portu, kanal kaynağını ve hedef output’u birbirine bağlar. “Sinyal yok” durumunda kaynak, port, patch, kanal işleme ve output hedefini ayrı kontrol edin. Genişletme donanımı ve port uyumluluğu üretici dokümanıyla doğrulanmalıdır.',
       ['Bir fiziksel girişin kanal patch’ini doğrulayın.','Çıkış portu ile hedef amplifikatör/PA girişini eşleştirin.','Kanal etiketini stage plot üzerinde işaretleyin.'],
       ['Patch dosyasını yedekle.','Fiziksel soket etiketini kontrol et.','Output patch’i hoparlör yönlendirmesiyle karşılaştır.'],
       'Kanal meter’ında hareket görülmesi, doğru fiziksel çıkışa patch edildiği anlamına gelmez.',
       'Bir output bus çalışıyor ama PA girişinde sinyal yoksa hangi noktaları kontrol edersiniz?'),
      ('03 · Preamp, phantom ve gain staging','Giriş seviyesini kontrollü biçimde ayarlamak.',
       'Preamp gain, dijital kanal seviyesi ve bus master farklı aşamalardır. Kaynak türü ve phantom ihtiyacı doğrulanmadan 48 V açılmamalıdır. PFL ve meter kullanarak performansın gerçek seviyesini kontrol edin; dijital clipping’i işlemci ve bus aşamalarında da izleyin. Paylaşılan remote preamp varsa gain owner/HA paylaşımını belirleyin.',
       ['Mikrofon ve DI kaynaklarını ayrı ayrı test edin.','PFL üzerinden gerçek giriş seviyesini dinleyin.','Performans seviyesinde headroom’u gözleyin.'],
       ['Phantom power öncesi kablo/kaynak kontrolü yap.','Gain değişince işleme ayarlarını tekrar dinle.','Kırmızı peak göstergesini görmezden gelme.'],
       'Ana fader yükseltmek düşük giriş seviyesini telafi edebilir ama gürültü performansını düzeltmeyebilir.',
       'Giriş gain’i doğru olduğu halde miks zayıfsa hangi sonraki kademeler kontrol edilir?'),
      ('04 · Kanal işleme ve görünüm sayfaları','İşlemci ayarlarını hızlı ama kontrollü değiştirmek.',
       'HPF, EQ, gate/expander ve compressor farklı sorunları çözer. UI sayfaları işlemci parametrelerine hızlı erişim sağlar, ancak görsel eğri veya sayısal değer gerçek işitsel sonucu tek başına göstermez. A/B karşılaştırmasını aynı algılanan seviyede yapın. Ayar değişikliklerini show dosyasının kopyasında test edin.',
       ['Konuşma kaynağında HPF ve EQ uygulayın.','Kompressor gain reduction davranışını dinleyin.','Ayar öncesi/sonrası seviyeleri not alın.'],
       ['İşlemci bypass testi yap.','Aşırı boost’tan kaçın.','Ayar değişiminde komşu kanalı etkilemediğini doğrula.'],
       'Görünüm sayfası değişince yanlış kanal üzerinde işlem yapmadığınızı yeniden teyit edin.',
       'Gate eşiğini yükseltmek neden her zaman daha temiz sonuç vermez?'),
      ('05 · Mix bus, FX bus ve grup yapısı','Bus mimarisini show ihtiyacına göre kurmak.',
       'Mix bus’lar monitor, grup, efekt send veya bağımsız miksler için kullanılabilir. Pre/post send noktaları ve kanal/bus atamaları show tasarımının temelidir. FX send bus ile normal monitor mix’i aynı kavram değildir. İsimlendirmeyi hedef ve amaçla yapın, boş bus’ları kritik çıkışlara yanlışlıkla bağlamayın.',
       ['Monitor bus ve FX send’i ayrı kurun.','Bir bus’ın kanal send’lerini ve master çıkışını kontrol edin.','Grup işleme gereksinimini ayrı test sahnesinde inceleyin.'],
       ['Bus tipini ve kullanım amacını yaz.','Send noktalarını doğrula.','Bus master mute ve level kontrolü yap.'],
       'FX send kaynaklarının yanlışlıkla monitor bus’a gitmesi sahne miksini karıştırabilir.',
       'FX send ile IEM mix bus’ı farklı amaçlara nasıl hizmet eder?'),
      ('06 · DCA, mute group ve kontrol katmanı','Birden çok kanalın seviyesini ve durumunu güvenli yönetmek.',
       'DCA benzeri toplu kontrol ve mute group işlevleri, ilgili kanalları hızlı idare etmeyi kolaylaştırır; ancak audio routing yerine geçmez. Grubun hangi kanalları kapsadığını show dosyası üzerinde test edin. Acil anons, talkback ve kritik kaynakları yanlışlıkla aynı gruba atamayın.',
       ['Vokal DCA/grup oluşturun.','Mute grup kapsamını düşük riskli şekilde test edin.','Talkback ve acil kaynakların kapsam dışında olduğunu doğrulayın.'],
       ['Atama listesini kontrol et.','Toplu mute öncesi hedefi gözle.','Kritik kaynaklara ayrı güvenli davranış tanımla.'],
       'DCA fader’ının hareket etmesi, kanalın audio yolunun yeni bir bus’a yönlendirildiği anlamına gelmez.',
       'Kontrol grubu ile sinyal yönlendirmesi arasındaki fark nedir?'),
      ('07 · Monitor ve IEM iş akışı','Sahne miksini güvenli seviyede kurmak.',
       'Monitor miksini sanatçı ihtiyacına göre oluşturun, tek bir kaynağı diğerlerine göre dengeleyin ve send noktalarını kontrol edin. IEM’de ani yükselmeleri önlemek için başlatma prosedürü tanımlayın. Kulaklık seviyesi ve RF sorunları ses routing sorunlarından ayrı olarak incelenmelidir.',
       ['Bir vokal IEM miksini düşük seviyede oluşturun.','Sanatçı talebine göre kaynakları sırayla ekleyin.','PFL ve bus meter ile sinyali doğrulayın.'],
       ['IEM seviyesi minimumdan başlasın.','Bus output patch’i doğrula.','RF ve audio sorunlarını ayrı kaydet.'],
       'RF kesilmesi ile audio routing sessizliğini aynı sorun sanmak yanlış ekipmanı değiştirmeye yol açar.',
       'IEM’de audio var ancak kesintiler duyuluyorsa hangi RF kontrolleri gerekir?'),
      ('08 · FX motoru ve efekt return','Send/return rotasını uçtan uca doğrulamak.',
       'FX kaynağı, send seviyesi, FX motoru, return kanalı ve çıkış hedefi ayrı katmanlardır. Return kanalı mute olabilir veya Main/Matrix’e yönlendirilmemiş olabilir. Efekt seçimini akustik ortam ve program materyaline göre yapın; parametreleri kulakla doğrulayın, preset adından sonuç varsaymayın.',
       ['Bir reverb veya delay send/return zinciri kurun.','Return’ü mute ederek A/B testi yapın.','FX dönüşünü doğru Main/Matrix hedefinde doğrulayın.'],
       ['Return kanalını etiketle.','FX send/return seviyelerini ayrı izle.','Show dosyasını değiştirmeden önce kopya al.'],
       'FX return sinyali Main’e gitmiyorsa send seviyesini artırmak problemi çözmez.',
       'FX motoru meter hareketine rağmen duyulmuyorsa arıza ağacını sıralayın.'),
      ('09 · Scene/show yönetimi','Recall ve show dosyası değişikliklerini kontrollü tutmak.',
       'Scene/show kayıtları parametreleri ve bazı yapılandırma durumlarını saklayabilir. Recall safes/filtreler veya benzeri korumalar, hangi parametrelerin geri yüklendiğini etkiler. Herhangi bir show yüklemesinden önce sürüm, kaynak patch ve çıkış hedeflerini kontrol edin. Büyük değişiklikleri canlı performans yerine ayrı bir test kopyasında yapın.',
       ['Bir temel soundcheck sahnesi ve show sahnesi oluşturun.','Recall kapsamını düşük riskli bir kanalda test edin.','Show dosyasını versiyon ve tarih ile yedekleyin.'],
       ['Dosya yedeği al.','Recall kapsamını dokümante et.','Kritik çıkışlarda mute/level doğrula.'],
       'Başka show’dan alınmış dosya mevcut I/O patch’ini beklenmedik biçimde değiştirebilir.',
       'Show dosyası yüklemeden önce hangi üç alanı karşılaştırırsınız?'),
      ('10 · Ağ ve genişletme sistemi farkındalığı','Uzak I/O ve network sorunlarını doğru katmanda aramak.',
       'Dijital ses ağı veya genişletme bağlantısı; fiziksel kablo, cihaz portu, clock/sync, I/O patch ve uyumluluk bilgilerinin birlikte değerlendirilmesini gerektirir. Avantis yapılandırması içinde kullanılan kartlar ve remote I/O modeli değişebilir. Ağ bağlantısı var görünürken sesin gelmemesi abonelik/patch veya clock sorununa bağlı olabilir.',
       ['Kullanılan I/O cihaz modelini ve portları kaydedin.','Link ve clock/sync bilgilerini üretici dokümanına göre kontrol edin.','Yanlış patch olasılığını test ederek izole edin.'],
       ['Kablo/port etiketle.','Clock göstergesini kontrol et.','Uyumlu model ve firmware’i doğrula.'],
       'Ağ kablosunun takılı olması cihazlar arasındaki tüm ses kanallarının doğru atandığını göstermez.',
       'Uzak I/O cihazı görünür, fakat kaynak kanalda sessizlik varsa hangi kontrol sırası kullanılır?'),
      ('11 · Show öncesi doğrulama ve ekip teslimi','Show dosyası, scene ve patch’in son kontrolünü yapmak.',
       'Show öncesi line check; fiziksel giriş, kanal meter’ı, işleme, bus send, çıkış patch’i ve hedef cihazı doğrular. Ekip değişiminde notlar açık ve kısa olmalıdır. Son dakika yapılan patch değişikliklerini sahne plotuna ve kullanılan dosya sürümüne ekleyin. Acil durum planı ve yedek kablo/kaynak hazır olmalıdır.',
       ['Input list ile sahnedeki kaynakları karşılaştırın.','Her kritik bus için meter ve gerçek çıkışı test edin.','Değişiklik notlarını operatör ekibiyle paylaşın.'],
       ['Show dosyasının son sürümünü belirle.','Kritik route’ları sesli/ölçümsel doğrula.','Geçici değişiklikleri not et.'],
       'Bir kişinin bildiği ama dokümante etmediği yama, sonraki operatör için gizli risk oluşturur.',
       'Kısa, işe yarar teslim notunda hangi bilgiler bulunmalıdır?'),
      ('12 · Arıza giderme, yedekleme ve değerlendirme','Sinyal zincirindeki arızayı kanıta dayalı daraltmak.',
       'Kaynağı, kabloyu, I/O patch’ini, kanal işlemeyi, send/bus, Main/Matrix, output patch ve hedef cihazı sırasıyla test edin. Her noktada meter veya bilinen sağlam yedek kaynak kullanın. Sistem stabil hale geldikten sonra kalıcı değişiklikleri kaydedip kullanılan show dosyasını yeniden yedekleyin.',
       ['Bir sessiz kanal vakasını sinyal zinciri diyagramıyla çözün.','Bir yedek kabloyla çapraz test yapın.','Çözümü kısa teknik rapor halinde aktarın.'],
       ['Aynı anda bir parametreyi değiştir.','Bilinir sağlam kaynakla karşılaştır.','Geçici bypass ve riskleri raporla.'],
       'Çözümden sonra yedek alınmazsa sonraki açılışta hatalı yapılandırmaya geri dönülebilir.',
       'Arızanın çözüldüğünü kanıtlayan gözlem ve testler nasıl belgelenir?'),
    ],
    'sources':[
      ('Allen & Heath Avantis Solo / Avantis kaynak ve destek sayfası','https://www.allen-heath.com/hardware/avantis/avantis-solo/resources/'),
      ('Allen & Heath Avantis firmware reference guide','https://support.allen-heath.com/hc/en-gb/sections/39858119246737-Firmware-Reference-Guide'),
      ('Allen & Heath Avantis firmware release notes','https://support.allen-heath.com/hc/en-gb/articles/44018705862289-Avantis-Firmware-Release-Notes')]
  },
]

for m in MANUALS:
    story = cover_flow(m['title'], m['subtitle'], m['console'], m['duration'], m['focus'])
    story += [P('İçindekiler ve öğrenme rotası','H1SP'),
              P('Bu çalışma kitabı teorik açıklama ile ölçülebilir bir uygulama adımını eşleştirir. Eğitmen her bölüm sonunda öğrencinin doğru sinyal akışını açıklamasını, kritik kontrolleri yapmasını ve sonucu not etmesini ister.','BodySP')]
    toc_rows=[['Bölüm','Kazanım']]
    for title, objective, *_ in m['concepts']:
        toc_rows.append([title, objective])
    story.append(make_table(toc_rows, widths=[60*mm,109*mm]))
    story += [Spacer(1,6*mm), P('Önerilen ders planı','H2SP'), make_table([
        ['Oturum','İçerik','Önerilen süre'],
        ['1','Yüzey, input patch, preamp ve gain staging','3 saat'],
        ['2','Channel processing, bus, monitor ve FX','3 saat'],
        ['3','Dijital bağlantı, routing, scene/show yönetimi','3 saat'],
        ['4','Soundcheck simülasyonu, arıza bulma, değerlendirme','3 saat'],
    ], widths=[25*mm,104*mm,40*mm]), PageBreak()]
    story += [P('Temel kavramlar ve güvenlik ilkeleri','H1SP')]
    story += [bullet(x) for x in [
        '<b>Signal flow:</b> Kaynaktan hedef hoparlör/record çıkışına kadar her aşamayı ayrı doğrulayın.',
        '<b>Gain staging:</b> Tek bir fader ile bütün sinyal zincirini düzeltmeye çalışmayın; giriş, işlemci, bus ve çıkışı ayrı gözleyin.',
        '<b>Yedekleme:</b> Çalışan show dosyası korunur. Büyük değişiklikler yeni bir kopyada denenir.',
        '<b>Güvenli seviye:</b> Kulaklık, IEM ve PA testleri düşük seviyeden başlayıp kademeli artırılır.',
        '<b>Değişiklik disiplini:</b> Canlı show’da tek seferde tek ana değişken değiştirin ve sonucu not edin.',
        '<b>Sinyal ölçümü sınırı:</b> Konsol meter’ı elektriksel/dijital akışa ilişkin bilgi verir; salondaki dB SPL için uygun mikrofon ve kalibrasyonlu ölçüm gerekir.'
    ]]
    story += [P('İlk 10 dakikalık kontrol listesi','H2SP')]
    story += [bullet('□ Güç, kablo ve sistem açılış sırası doğrulandı.') for _ in range(1)]
    story += [bullet('□ Doğru show dosyası, sürüm adı ve yedek kopya hazır.')]
    story += [bullet('□ Input list / stage plot ile fiziksel kaynaklar eşleşiyor.')]
    story += [bullet('□ Ana çıkış, monitor, IEM ve talkback hedefleri doğrulandı.')]
    story += [bullet('□ Kritik çıkışlar düşük başlangıç seviyesiyle test edildi.')]
    story += [P('Üretici dokümanlarıyla birlikte kullanım','H2SP'), P('Bu eğitim kitabı genel iş akışını öğretir. Firmware sürümü, ek kartlar, port seçenekleri, bazı menüler ve lisans seçenekleri sürüme göre değişebilir. Aşağıdaki resmî üretici sayfaları, cihaz üzerinde uygulama yaparken başvurulacak güncel kaynaklardır.','BodySP'), PageBreak()]
    for section in m['concepts']:
        story += lesson(*section)
    story += [P('Uygulamalı bitirme görevi','H1SP'),
              P('Öğrenci, sahne plotu ve kanal listesini temel alarak 8 kaynaklı küçük bir show kurar. Girişleri isimlendirir, ana miks ile en az bir monitor bus’ı ayırır, sinyal akışını doğrular, kritik sahne dosyasını yedekler ve bir arıza senaryosunu sistematik biçimde çözer.','BodySP')]
    story += [make_table([
      ['Değerlendirme ölçütü','Puan','Gözlenebilir başarı ölçütü'],
      ['Patch ve kaynak doğruluğu','20','Kaynak ve kanal eşleştirmesi hatasız açıklanır.'],
      ['Gain staging / işitme güvenliği','20','Temiz seviye ve güvenli başlangıç uygulanır.'],
      ['Bus / monitor / output routing','20','Hedefe giden sinyal ve fiziksel çıkış doğrulanır.'],
      ['Scene/show yedekleme ve teslim','15','Doğru sürüm kaydedilir, değişiklikler yazılır.'],
      ['Arıza bulma yöntemi','25','Tek değişken ve kanıtla adım adım çözüm yapılır.'],
      ['Toplam','100','70/100 ve üstü önerilen başarılı tamamlama eşiğidir.'],
    ], widths=[54*mm,17*mm,98*mm]), Spacer(1,5*mm),
      P('Başarı eşiği eğitim önerisidir; Stagepulse tarafından bir resmî üretici sertifikası veya akredite yeterlilik belgesi anlamına gelmez.','CalloutSP'), PageBreak()]
    story += [P('Sahada arıza bulma çalışma formu','H1SP'),
      P('Bir problem gerçekleştiğinde önce belirtiyi yazın. Sonra kanıtlanan aşamaları işaretleyin. Aynı anda birden fazla ana parametreyi değiştirmeyin.','BodySP'),
      make_table([
        ['Kontrol noktası','Kontrol sorusu','Sonuç / not'],
        ['Kaynak','Kaynağın kendisi çalışıyor mu?','____________________________'],
        ['Kablo / port','Bilinen sağlam kablo veya port ile denendi mi?','____________________________'],
        ['Input patch','Kaynak doğru kanala mı atanmış?','____________________________'],
        ['Channel processing','Mute, gate, fader veya işlemci akışı kesiyor mu?','____________________________'],
        ['Bus / send','Sinyal bus’a ulaşıyor mu ve send noktası doğru mu?','____________________________'],
        ['Main / Matrix','Bus veya ana miks hedefe gidiyor mu?','____________________________'],
        ['Output patch','İşaretli fiziksel porta mı yönlendiriliyor?','____________________________'],
        ['Hedef cihaz','Amplifikatör/PA/record cihazı girişinde sinyal var mı?','____________________________'],
        ['Çözüm ve yedek','Yapılan kalıcı/geçici değişiklikler ve dosya yedeği','____________________________'],
      ], widths=[34*mm,74*mm,61*mm]), Spacer(1,6*mm),
      P('Eğitmen notu ve kişisel çalışma','H2SP'), P('Öğrencinin güçlü olduğu üç konu: ________________________________________________','BodySP'),
      P('Tekrar edilmesi gereken iki konu: _________________________________________________','BodySP'),
      P('Bir sonraki uygulama görevi: _____________________________________________________','BodySP'), PageBreak()]
    story += [P('Terimler sözlüğü','H1SP'), make_table([
      ['Terim','Kısa açıklama'],
      ['Gain / preamp','Kaynak sinyalini uygun giriş seviyesine getiren kontrol aşaması.'],
      ['Headroom','Sinyalin clipping olmadan artabileceği güvenli seviye payı.'],
      ['PFL / Solo','Kanalı ana miks yolundan bağımsız izlemek için kullanılan dinleme kontrolü.'],
      ['Bus / Mix','Birden fazla kaynağın ayrı bir çıkış/miks yolunda birleştirilmesi.'],
      ['Matrix','Mevcut miks veya bus kaynaklarını farklı çıkış hedeflerine dağıtmak için kullanılan katman.'],
      ['DCA','Atanmış kanalların seviyelerini toplu yönetir; kendi başına audio bus değildir.'],
      ['Patch','Fiziksel/dijital kaynağı kanal veya çıkış hedefine eşleştirme.'],
      ['Scene / snapshot','Konsol ayarlarının belli bir durumunu saklayan ve geri çağırabilen kayıt.'],
      ['AES50 / Dante','Üretici ve sistem koşullarına bağlı dijital ses/ağ taşıma teknolojileri.'],
      ['Recall safe/filter','Sahne geri çağırma sırasında korunacak veya çağrılacak parametreleri sınırlar.'],
      ['IEM','In-ear monitor; sanatçıya kulak içi kulaklık üzerinden verilen sahne miks sistemi.'],
    ], widths=[38*mm,131*mm]), PageBreak()]
    story += [P('Kaynaklar ve doküman kontrolü','H1SP'),
              P('Aşağıdaki üretici kaynaklarını kitap basım/uygulama tarihinde kontrol edin. İndirme sayfaları, kullanım kılavuzu ve firmware notlarının sürümleri değişebilir. Bu belge özgün bir eğitim kılavuzudur; üretici markaları ve modelleri burada yalnızca uyumluluk/öğretim hedefini belirtmek için anılmıştır.','BodySP')]
    for name,url in m['sources']:
        story += [P('<b>'+name+'</b>','H2SP'), P(url,'SmallSP')]
    story += [Spacer(1,5*mm), P('Eğitim setinin kullanım notu','H2SP'), P('Gerçek konsol üzerinde eğitim yapılırken donanıma erişim, sahne kablolaması, elektrik güvenliği ve ses seviyesi sorumluluğu eğitmen/sistem sorumlusundadır. Bu kitap menü isimlerini ezberlemekten çok, sinyal yolunu ölçerek ve dinleyerek doğrulama yaklaşımını öğretmek için hazırlanmıştır.','BodySP'),
              Spacer(1,7*mm), HRFlowable(width='100%', thickness=1, color=GOLD), Spacer(1,4*mm),
              P('STAGEPULSE  |  SESİN GÜCÜ, İŞİN KALİTESİ','CenterSP')]
    output=OUT/m['file']
    doc=SimpleDocTemplate(str(output), pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=17*mm, bottomMargin=17*mm,
                          title=m['title'], author='Stagepulse', subject='Türkçe uygulamalı dijital ses konsolu eğitimi', pageCompression=1)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f'{output.name}: {output.stat().st_size} bytes')
