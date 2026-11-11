# -*- coding: utf-8 -*-
"""Stagepulse student visual atlas: SPL model maps, dB relationships and realistic concept image."""
from pathlib import Path
import shutil
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image as PILImage
import cairosvg
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak,
                                Table, TableStyle, KeepTogether, HRFlowable)

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'ui'/'assets'
BUILD=ROOT/'.build_spl_visual_atlas'
BUILD.mkdir(parents=True,exist_ok=True)
EDU=ROOT/'egitim_paketleri'
OUT=EDU/'09_SPL_dB_3D_Gorsel_Atlasi.pdf'
ASSETS.mkdir(parents=True,exist_ok=True)
GOLD=colors.HexColor('#B99442'); GOLD2=colors.HexColor('#E6CC86'); DARK=colors.HexColor('#11151B')
FONT_REG=next((str(p) for p in [Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),Path('C:/Windows/Fonts/arial.ttf')] if p.exists()), '')
FONT_BOLD=next((str(p) for p in [Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),Path('C:/Windows/Fonts/arialbd.ttf')] if p.exists()), '')
if Path(FONT_REG).exists() and Path(FONT_BOLD).exists():
    pdfmetrics.registerFont(TTFont('SP', FONT_REG)); pdfmetrics.registerFont(TTFont('SP-Bold', FONT_BOLD)); REG='SP'; BOLD='SP-Bold'
else: REG='Helvetica'; BOLD='Helvetica-Bold'
GRAY=colors.HexColor('#647080'); LIGHT=colors.HexColor('#F2F4F7'); LINE=colors.HexColor('#D9DEE5')

# Render a crisp raster copy of the custom SVG wordmark for PDF.
logo_png=BUILD/'stagepulse-logo-pdf.png'
cairosvg.svg2png(url=str(ASSETS/'stagepulse-logo.svg'),write_to=str(logo_png),output_width=1040,output_height=232)

# The model intentionally represents ONE omnidirectional point source in free field.
width_m, depth_m, ref_db, ref_dist = 20.0, 30.0, 100.0, 1.0
x=np.linspace(-width_m/2,width_m/2,121)
y=np.linspace(0.5,depth_m,151)
X,Y=np.meshgrid(x,y)
R=np.maximum(ref_dist,np.hypot(X,Y))
L=ref_db-20*np.log10(R/ref_dist)

# 2D map: calculated and reproducible from the model stated on the page.
map2d=BUILD/'spl-map-2d-model.png'
fig,ax=plt.subplots(figsize=(8.8,5.2),dpi=180)
fig.patch.set_facecolor('#10151b'); ax.set_facecolor('#10151b')
mesh=ax.pcolormesh(X,Y,L,cmap='turbo',shading='auto',vmin=55,vmax=100)
cont=ax.contour(X,Y,L,levels=[60,65,70,75,80,85,90,95],colors='white',linewidths=.55,alpha=.65)
ax.clabel(cont,inline=True,fontsize=7,fmt='%d dB')
ax.add_patch(plt.Rectangle((-2, -1.4),4,1.2,facecolor='#212832',edgecolor='#f0d58d',linewidth=1.2))
ax.text(0,-.55,'SAHNE / TEK NOKTASAL KAYNAK',ha='center',va='center',fontsize=7,color='#f0d58d',fontweight='bold')
ax.set_xlim(-width_m/2,width_m/2); ax.set_ylim(depth_m,0)
ax.set_xlabel('Alan genişliği (m)',color='#e1e6ed'); ax.set_ylabel('Sahne önünden derinlik (m)',color='#e1e6ed')
ax.tick_params(colors='#c9d1dc',labelsize=8)
for sp in ax.spines.values(): sp.set_color('#566171')
cbar=fig.colorbar(mesh,ax=ax,pad=.02); cbar.set_label('Hesaplanan seviye (dB SPL modeli)',color='#e1e6ed'); cbar.ax.yaxis.set_tick_params(color='#c9d1dc'); plt.setp(cbar.ax.get_yticklabels(),color='#c9d1dc')
fig.tight_layout(); fig.savefig(map2d,facecolor=fig.get_facecolor(),bbox_inches='tight'); plt.close(fig)

# 3D surface: same calculation, z-axis is model SPL (not a physical room height).
map3d=BUILD/'spl-map-3d-model.png'
fig=plt.figure(figsize=(8.8,5.2),dpi=180); fig.patch.set_facecolor('#10151b')
ax=fig.add_subplot(111,projection='3d'); ax.set_facecolor('#10151b')
surf=ax.plot_surface(X,Y,L,cmap='turbo',vmin=55,vmax=100,linewidth=0,antialiased=True,rstride=3,cstride=3,alpha=.96)
ax.set_xlabel('Genişlik (m)',labelpad=5,color='#e1e6ed'); ax.set_ylabel('Derinlik (m)',labelpad=5,color='#e1e6ed'); ax.set_zlabel('dB SPL model',labelpad=5,color='#e1e6ed')
ax.tick_params(colors='#c9d1dc',labelsize=7); ax.view_init(elev=27,azim=-58); ax.set_zlim(55,100)
for axis in (ax.xaxis,ax.yaxis,ax.zaxis):
    try: axis.pane.set_facecolor((.06,.08,.1,1)); axis.pane.set_edgecolor((.25,.3,.36,1))
    except Exception: pass
cb=fig.colorbar(surf,ax=ax,shrink=.62,pad=.1); cb.set_label('dB SPL model',color='#e1e6ed'); plt.setp(cb.ax.get_yticklabels(),color='#c9d1dc')
fig.tight_layout(); fig.savefig(map3d,facecolor=fig.get_facecolor(),bbox_inches='tight'); plt.close(fig)

# Distance profile from the same exact model, to make the 20log relationship easy to teach.
distchart=BUILD/'spl-distance-curve.png'
distance=np.linspace(1,depth_m,120); level_curve=ref_db-20*np.log10(distance/ref_dist)
fig,ax=plt.subplots(figsize=(8.8,3.7),dpi=180); fig.patch.set_facecolor('#10151b'); ax.set_facecolor('#10151b')
ax.plot(distance,level_curve,color='#e4bf67',linewidth=2.6,label='Noktasal kaynak modeli')
for d in (1,5,10,20,30):
    lv=ref_db-20*np.log10(d/ref_dist); ax.scatter([d],[lv],color='#f4f0e4',s=18,zorder=3); ax.annotate(f'{lv:.1f} dB', (d,lv), xytext=(4,7),textcoords='offset points',fontsize=7,color='#f4f0e4')
ax.set_xlabel('Kaynağa uzaklık (m)',color='#e1e6ed'); ax.set_ylabel('Hesaplanan seviye (dB SPL)',color='#e1e6ed'); ax.tick_params(colors='#d4dbe4'); ax.grid(color='#3a434f',alpha=.65)
for sp in ax.spines.values(): sp.set_color('#566171')
fig.tight_layout(); fig.savefig(distchart,facecolor=fig.get_facecolor(),bbox_inches='tight'); plt.close(fig)

# dB ratio chart: pressure amplitude is 10^(dB/20); intensity/power is 10^(dB/10).
dbchart=BUILD/'db-physical-ratios.png'
deltas=np.array([3,6,10],dtype=float); pressure=10**(deltas/20); power=10**(deltas/10)
fig,ax=plt.subplots(figsize=(8.8,3.7),dpi=180); fig.patch.set_facecolor('#10151b'); ax.set_facecolor('#10151b')
ix=np.arange(3); bw=.34
b1=ax.bar(ix-bw/2,pressure,bw,label='Basınç genliği oranı',color='#d6b25d')
b2=ax.bar(ix+bw/2,power,bw,label='Yoğunluk / güç oranı',color='#318fa6')
ax.set_xticks(ix, ['+3 dB','+6 dB','+10 dB']); ax.set_ylabel('Kat oranı',color='#e1e6ed'); ax.tick_params(colors='#d4dbe4'); ax.set_ylim(0,11.5)
ax.grid(axis='y',color='#3a434f',alpha=.65); ax.set_axisbelow(True)
for sp in ax.spines.values(): sp.set_color('#566171')
leg=ax.legend(frameon=False,loc='upper left'); plt.setp(leg.get_texts(),color='#e1e6ed')
for bars in [b1,b2]:
    for bar in bars: ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+.18,f'{bar.get_height():.2f}×',ha='center',va='bottom',fontsize=8,color='#f5f1e7')
fig.tight_layout(); fig.savefig(dbchart,facecolor=fig.get_facecolor(),bbox_inches='tight'); plt.close(fig)

styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='CoverTitleSP',parent=styles['Title'],fontName=BOLD,fontSize=27,leading=32,textColor=colors.HexColor('#11151B'),alignment=TA_LEFT,spaceAfter=7))
styles.add(ParagraphStyle(name='SubSP',parent=styles['Normal'],fontName=REG,fontSize=11,leading=16,textColor=GRAY,spaceAfter=8))
styles.add(ParagraphStyle(name='H1SP',parent=styles['Heading1'],fontName=BOLD,fontSize=18,leading=23,textColor=colors.HexColor('#20262D'),spaceBefore=2,spaceAfter=10))
styles.add(ParagraphStyle(name='H2SP',parent=styles['Heading2'],fontName=BOLD,fontSize=12,leading=15,textColor=colors.HexColor('#8C6A24'),spaceBefore=8,spaceAfter=5))
styles.add(ParagraphStyle(name='BodySP',parent=styles['BodyText'],fontName=REG,fontSize=9,leading=13,textColor=colors.HexColor('#313944'),spaceAfter=7))
styles.add(ParagraphStyle(name='SmallSP',parent=styles['BodyText'],fontName=REG,fontSize=7.4,leading=10.5,textColor=GRAY,spaceAfter=4))
styles.add(ParagraphStyle(name='CalloutSP',parent=styles['BodyText'],fontName=BOLD,fontSize=8.5,leading=12,textColor=colors.HexColor('#3F3420'),backColor=colors.HexColor('#FBF4DF'),borderColor=GOLD,borderWidth=.6,borderPadding=8,spaceBefore=5,spaceAfter=8))
styles.add(ParagraphStyle(name='WhiteSP',parent=styles['BodyText'],fontName=REG,fontSize=9,leading=14,textColor=colors.white,spaceAfter=8))
from append_bilingual_glossary import bilingualize_markup
P=lambda x,style='BodySP':Paragraph(bilingualize_markup(x),styles[style])

def footer(canvas,doc):
    canvas.saveState(); w,h=A4
    canvas.setStrokeColor(GOLD);canvas.setLineWidth(.7);canvas.line(17*mm,15*mm,w-17*mm,15*mm)
    canvas.setFont(REG,7);canvas.setFillColor(GRAY);canvas.drawString(17*mm,9*mm,'STAGEPULSE  |  Öğrenci görsel atlası  |  v4.0.0')
    canvas.drawRightString(w-17*mm,9*mm,f'Sayfa {doc.page}')
    canvas.restoreState()

def img(path,width):
    im=Image(str(path),width=width,height=width*PILImage.open(str(path)).height/PILImage.open(str(path)).width)
    return im

story=[]
# Cover page
story += [Image(str(logo_png),width=155*mm,height=34.6*mm),Spacer(1,10*mm),P('SPL, dB ve 3D Görsel Atlası','CoverTitleSP'),P('Ses Mühendisliği Merkezi için görselleştirme rehberi · Öğrenci sürümü 4.0.0','SubSP'),HRFlowable(width='100%',thickness=1,color=GOLD,spaceBefore=2,spaceAfter=8),Spacer(1,3*mm)]
photo_path=ASSETS/'spl-3d-konsept.png'
with PILImage.open(photo_path) as photo_source:
    photo_ratio=photo_source.height/photo_source.width
photo=Image(str(photo_path),width=176*mm,height=176*mm*photo_ratio)
story += [photo,Spacer(1,3*mm),P('<b>Önemli:</b> Üstteki fotogerçekçi salon görseli konsept illüstrasyonudur. Üzerindeki renkler/sayılar gerçek bir hoparlör modeliyle hesaplanmış veya sahada ölçülmüş değer değildir. Teknik karar için sonraki sayfalardaki açıklamalı basit model ve saha ölçüm prosedürü ayrıdır.','CalloutSP'),P('Bu atlas; hesaplanan bir alan haritası, dB farklarının fiziksel karşılığı, gerçekçi görsel anlatım ve doğru yorumlama adımlarını birbirinden ayırır.','BodySP'),PageBreak()]

# page 2: exact simple model maps
story += [P('1. Hesaplanan SPL alan haritası','H1SP'),P('Bu örnek, sahnenin ön merkezinde tek bir ideal noktasal kaynak varsayar. Referans değer 1 m’de 100 dB SPL; serbest alan yaklaşımı ve geometrik yayılım kullanılmıştır: <b>Lp(r) = Lp(r₀) − 20 log₁₀(r/r₀)</b>. Alan 20 m × 30 m seçilmiştir. Bu grafik çizgi dizi (line array), çoklu hoparlör, yansıma, faz, yönlülük, limitör, hava soğurması veya kalabalığı modellemez.','BodySP')]
row=[img(map2d,87*mm),img(map3d,87*mm)]
t=Table([row],colWidths=[89*mm,89*mm]);t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),1),('RIGHTPADDING',(0,0),(-1,-1),1),('TOPPADDING',(0,0),(-1,-1),1),('BOTTOMPADDING',(0,0),(-1,-1),1)]));story += [t,Spacer(1,3*mm),P('<b>Okuma:</b> Renk, seçilen formül altındaki hesaplanan seviyeyi gösterir; aynı renk haritası gerçek salonda aynı dB SPL değerini garanti etmez. Dikey ekseni dB SPL olan 3D yüzeyin yüksekliği, fiziksel mekân yüksekliği değildir.','CalloutSP'),P('10 m örneği: 100 − 20 log₁₀(10/1) = 80 dB SPL. 20 m örneği: yaklaşık 73,98 dB SPL. Yansımalar veya hoparlörün yönlü yapısı nedeniyle gerçek değerler farklı olabilir.','BodySP'),P('Uzaklık arttıkça seviye profili','H2SP'),Image(str(distchart),width=174*mm,height=174*mm*3.7/8.8),PageBreak()]

# page 3: dB relationships
story += [P('2. dB farkının fiziksel karşılığı','H1SP'),P('Aynı ortam ve aynı tür fiziksel büyüklük karşılaştırılırken, seviye farkı ΔL için basınç genliği oranı 10^(ΔL/20), yoğunluk/güç oranı 10^(ΔL/10) olarak hesaplanır. dB, logaritmik bir oran birimidir; basınç oranı ile güç oranını aynı formülle hesaplama.','BodySP'),Image(str(dbchart),width=174*mm,height=174*mm*3.7/8.8),Spacer(1,3*mm)]
table_data=[['Seviye farkı','Basınç genliği oranı','Yoğunluk / güç oranı','Yorum'],['+3 dB','1,41×','2,00× (yaklaşık)','Güç/yoğunluk yaklaşık iki kat'],['+6 dB','2,00× (yaklaşık)','3,98× (yaklaşık)','Ses basıncı yaklaşık iki kat'],['+10 dB','3,16×','10,00×','Fiziksel oran; öznel algının evrensel yasası değil']]
t=Table([[P(str(c),'SmallSP') for c in row] for row in table_data],colWidths=[25*mm,39*mm,41*mm,71*mm],repeatRows=1)
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),DARK),('TEXTCOLOR',(0,0),(-1,0),colors.white),('BACKGROUND',(0,1),(-1,-1),LIGHT),('GRID',(0,0),(-1,-1),.4,LINE),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story += [t,Spacer(1,3*mm),P('Birleşik bağımsız kaynaklar için enerji toplamı <b>LΣ = 10 log₁₀(Σ 10^(Li/10))</b> formülüyle yapılır. Aynı seviyeli iki kaynağın ideal enerji toplamı yaklaşık +3 dB’dir; gerçek hoparlör dizilerinde faz ve girişim sebebiyle bu sonuç her noktada oluşmaz.','CalloutSP'),P('dB SPL (basınç seviyesi), dBA (A-ağırlıklı seviye), dBFS (dijital tam ölçeğe göre seviye) ve dBu (0,775 Vrms referanslı elektrik seviyesi) birbirinin yerine kullanılamaz.','BodySP'),PageBreak()]

# page 4: real use & safety
story += [P('3. Görseli sahada doğru kullanma','H1SP'),P('Bu uygulamadaki dinleyici alanı haritası yalnızca eğitim amaçlı noktasal kaynak / serbest alan modelidir. Gerçek PA tahmini için hoparlörün frekansa göre polar verisi, array kabin açıları, yükseklik ve eğim, yönlülük, sub yerleşimi, DSP, hedef bantlar, ortam geometresi ve yansıma koşulları gerekir. Ölçüm raporu için kalibre edilmiş cihaz ve yöntem ayrıca gereklidir.','BodySP'),P('SPL ölçümünde doğrulama listesi','H2SP')]
checks=[
['1','Cihaz ve ölçüm mikrofonu modelini; varsa IEC 61672 sınıfını ve kalibrasyon bilgisini kaydet.'],
['2','Ölçümün A/C/Z frekans ağırlığını, Fast/Slow zaman ağırlığını, LAeq/Lmax gibi metriğini ve süreyi kaydet.'],
['3','Mikrofon konumu, yükseklik, yön, sahne/PA mesafesi, rüzgâr ve arka plan koşullarını not et.'],
['4','RTA dBFS spektrumunu doğrudan dB SPL/dBA diye yorumlama. Kalibre edilmiş ses basıncı yolu veya uygun ses seviye ölçer olmadan mutlak SPL raporu yazma.'],
['5','3D konsept görselini pazarlama/öğretim için kullan; hesaplanmış ısı haritasıyla karıştırma. Haritadaki sayılar örnek illüstrasyon olarak değerlendirilmelidir.'],
['6','Array, sub hizalama, geri besleme veya mevzuat kararı için sadece bu uygulamanın tahminine dayanma; üretici verisi, ölçüm ve yetkin kişi kontrolü gerekir.'],
]
ct=Table([[P(a,'SmallSP'),P(b,'BodySP')] for a,b in checks],colWidths=[10*mm,166*mm])
ct.setStyle(TableStyle([('BACKGROUND',(0,0),(0,-1),colors.HexColor('#F8F0D9')),('GRID',(0,0),(-1,-1),.35,LINE),('VALIGN',(0,0),(-1,-1),'TOP'),('ALIGN',(0,0),(0,-1),'CENTER'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));story += [ct,Spacer(1,3*mm),P('Ölçüm raporunda kayıt altına alınacaklar','H2SP')]
fields=[['Alan','Kaydedilecek bilgi'],['Nokta','Konum kodu, PA mesafesi, mikrofon yüksekliği ve yönü'],['Cihaz','Ses seviye ölçer / mikrofon modeli, kalibrasyon kontrolü'],['Ayar','A/C/Z ağırlığı, Fast/Slow, LAeq/Lmax/Lpeak ve süre'],['Koşul','Program içeriği, arka plan, hava/rüzgâr ve kalabalık'],['Yorum','Ölçülen değer, model tahmini ve öznel gözlem ayrı ayrı']]
ft=Table([[P(str(v),'SmallSP') for v in row] for row in fields],colWidths=[30*mm,146*mm],repeatRows=1)
ft.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),DARK),('GRID',(0,0),(-1,-1),.35,LINE),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('BACKGROUND',(0,1),(-1,-1),LIGHT)]));story += [ft,Spacer(1,3*mm),P('Standart ve kaynak notları','H2SP'),P('IEC 61672-1:2013, ses seviye ölçerlerin zaman/ağırlıklandırma, zaman ortalaması ve ses maruziyeti performans özelliklerini tanımlar; sınıf 1 ve sınıf 2 kategorileri vardır. IEC 61260 ailesi oktav/kesirli oktav filtre performansını kapsar. NIOSH’un mesleki gürültü referansları işyeri işitme koruma programı bağlamındadır, genel halk/konser için doğrudan yasal sınır değildir.','SmallSP'),P('Kaynaklar: <link href="https://webstore.iec.ch/en/publication/5708" color="#8C6A24">IEC 61672-1</link> · <link href="https://www.cdc.gov/niosh/noise/prevent/understand.html" color="#8C6A24">CDC/NIOSH gürültü ölçümü</link> · <link href="https://aes.org/publications/standards-store/?id=72" color="#8C6A24">AES56 hoparlör polar radyasyonu</link>. Bu doküman standartların tam metni veya uygunluk sertifikası değildir.','SmallSP')]

# Build a polished, render-checked PDF.
doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=17*mm,leftMargin=17*mm,topMargin=13*mm,bottomMargin=21*mm,title='Stagepulse - SPL, dB ve 3D Görsel Atlası',author='Stagepulse',subject='Öğrenci eğitim görselleştirmeleri ve SPL model sınırlamaları')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
size=OUT.stat().st_size
shutil.rmtree(BUILD,ignore_errors=True)
print(f'{OUT} | {size} bytes')
