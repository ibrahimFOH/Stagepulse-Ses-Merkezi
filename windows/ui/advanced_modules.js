(function(){
'use strict';
const $=id=>document.getElementById(id);
const esc=v=>String(v==null?'':v).replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const fmt=(v,d)=>Number(v).toLocaleString('tr-TR',{minimumFractionDigits:0,maximumFractionDigits:d==null?2:d});
const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
function calculatePower(x){
 const phase=x.phase==='three'?'three':'single',p=Number(x.powerW),v=Number(x.voltage),pf=Number(x.powerFactor),eff=Number(x.efficiency),reserve=Number(x.reserve||0),length=Number(x.lengthM||0),section=Number(x.sectionMm2),rho=x.material==='aluminium'?.0282:.0175;
 if(!(p>0&&p<=1e7))throw Error('Güç 1–10.000.000 W aralığında olmalı.');
 if(!(v>=50&&v<=1000))throw Error('Gerilim 50–1.000 V aralığında olmalı.');
 if(!(pf>.1&&pf<=1)||!(eff>.1&&eff<=1))throw Error('Güç faktörü ve verim 0,1–1 aralığında olmalı.');
 if(!(reserve>=0&&reserve<=100)||!(length>=0&&length<=5000)||!(section>0&&section<=1000))throw Error('Yedek payı, kablo uzunluğu veya kesiti geçersiz.');
 const designPowerW=p*(1+reserve/100),currentA=designPowerW/(v*pf*eff*(phase==='three'?Math.sqrt(3):1));
 const voltageDropV=(phase==='three'?Math.sqrt(3):2)*currentA*length*rho/section;
 return {phase,powerW:p,designPowerW,currentA,voltageDropV,voltageDropPercent:voltageDropV/v*100,receivingVoltage:Math.max(0,v-voltageDropV),material:x.material==='aluminium'?'Alüminyum':'Bakır',assumptions:'Dengeli yük, sabit güç faktörü, 20 °C iletken özdirenci ve dirençsel gerilim düşümü varsayımı.'};
}
function hasIntermodConflict(candidate,chosen,guard,min,max){
 const all=chosen.concat([candidate]);
 for(let i=0;i<all.length;i++)for(let j=i+1;j<all.length;j++)for(const product of [2*all[i]-all[j],2*all[j]-all[i]]){
  if(product<min||product>max)continue;
  for(const operating of all)if(Math.abs(product-operating)<guard)return true;
 }
 return false;
}
function coordinateRf(x){
 const min=Number(x.minMHz),max=Number(x.maxMHz),hand=Math.trunc(Number(x.handhelds)),iems=Math.trunc(Number(x.iems));
 const step=Number(x.stepMHz||.025),spacing=Number(x.spacingMHz||.3),guard=Number(x.guardMHz||.15),threshold=Number(x.noiseThresholdDbm==null?-70:x.noiseThresholdDbm),scan=Array.isArray(x.scan)?x.scan:[];
 if(!(min>0&&max>min&&max<=10000))throw Error('Frekans bandı geçersiz.');
 if(!(hand>=0&&iems>=0&&hand+iems>=1&&hand+iems<=32))throw Error('El mikrofonu + IEM toplamı 1–32 kanal olmalı.');
 if(!(step>=.005&&step<=1&&spacing>=step&&spacing<=20&&guard>=.01&&guard<=5))throw Error('Tarama adımı, kanal aralığı veya koruma aralığı geçersiz.');
 const count=hand+iems,center=(min+max)/2,candidates=[],nmax=Math.floor((max-min)/step);
 for(let n=0;n<=nmax;n++)candidates.push(Number((min+n*step).toFixed(4)));
 candidates.sort((a,b)=>Math.abs(a-center)-Math.abs(b-center)||a-b);
 const blocked=f=>scan.some(s=>Number.isFinite(s.frequencyMHz)&&Number.isFinite(s.levelDbm)&&s.levelDbm>=threshold&&Math.abs(s.frequencyMHz-f)<=Math.max(guard,step));
 const chosen=[];
 for(const f of candidates){if(blocked(f)||chosen.some(y=>Math.abs(y-f)<spacing)||hasIntermodConflict(f,chosen,guard,min,max))continue;chosen.push(f);if(chosen.length===count)break;}
 chosen.sort((a,b)=>a-b);
 const channels=chosen.map((frequencyMHz,i)=>({index:i+1,type:i<hand?'El mikrofonu':'IEM',label:i<hand?'El mikrofonu '+(i+1):'IEM '+(i-hand+1),frequencyMHz}));
 return {channels,requested:count,assigned:channels.length,missing:count-channels.length,scanCount:scan.length,warning:channels.length===count?'Ön koordinasyon tamamlandı. Cihaz modeli/firmware ve üretici intermod tablolarıyla sahada tekrar doğrula.':'Bu bant ve kısıtlarla istenen kanal sayısı bulunamadı. Kanal sayısını azalt, izinli bandı doğrula veya tarama verisini gözden geçir.'};
}
function parseRtaCandidates(text){
 const rows=String(text||'').split(/\r?\n/),found=[];
 for(let i=0;i<rows.length;i++){const m=rows[i].match(/([\d.,]+)\s*(kHz|Hz)/i);if(!m)continue;const v=Number(m[1].replace(',','.'));if(!Number.isFinite(v))continue;const hz=m[2].toLowerCase()==='khz'?v*1000:v,context=rows.slice(i,Math.min(rows.length,i+2)).join(' '),ex=context.match(/medyanından\s*\+([\d.,]+)\s*dB/i);found.push({frequencyHz:hz,excessDb:ex?Number(ex[1].replace(',','.')):null});}
 return found.filter((x,i,a)=>a.findIndex(y=>Math.abs(y.frequencyHz-x.frequencyHz)<1)===i).slice(0,5);
}
const videoLessons=[
{id:'gain',title:'Gain staging: doğru giriş seviyesi',duration:'3:10',script:'Gain staging, sinyal zincirindeki her aşamanın yeterli headroom ile çalışmasıdır. Önce kaynağı dinle ve mikrofon mesafesini düzelt. Ardından preamp kazancını, en yüksek beklenen performans anında kırpılma olmayacak şekilde ayarla. Dijital konsollarda ortalama seviyeyi yaklaşık -18 dBFS çevresinde tutmak pratik bir başlangıçtır; zorunlu standart değildir. Kanal faderını yükselterek kötü giriş kazancını düzeltme. Preamp, kanal işleme ve bus seviyelerini ayrı izle. Son kontrolü gerçek performans dinamiğiyle yap.',shots:['Sinyal zinciri animasyonu','Preamp ve meter yakın planı','Headroom karşılaştırması','Kırpılma örneği']},
{id:'hpf',title:'HPF ve LPF: ne zaman kullanılır?',duration:'2:45',script:'Yüksek geçiren filtre, seçilen kesim frekansının altındaki içeriği azaltır. Mikrofon ayağı titreşimi, rüzgâr ve gereksiz düşük frekans enerjisi için yararlıdır. Ancak her kanala aynı kesimi uygulamak doğru değildir. Bas gitar, kick ve derin erkek vokal gibi kaynaklarda temel frekansı yanlışlıkla zayıflatabilirsin. LPF üst frekansları sınırlar. Filtreyi solo dinlemekle kalma, tüm miks içindeki etkisini kontrol et.',shots:['HPF/LPF eğrisi','Vokal ve kick örnekleri','Kesim karşılaştırması','Miks içinde A/B']},
{id:'eq',title:'Parametrik EQ ile rezonans bulma',duration:'3:25',script:'Parametrik EQ merkez frekansı, kazanç ve Q kontrolleri sunar. Dar bir rezonansı ararken önce küçük bir boost ile bölgeyi bul, sonra kontrollü kesime dön. Canlı PA sisteminde ölçüm mikrofonu, pembe gürültü ve birden fazla konum kullan. Tek noktadaki çukur genellikle boost sebebi değildir; faz iptali olabilir. Geniş ve tekrarlanan birikimlerde küçük kesimler dene. Her değişikliği dinle ve geri alabileceğin şekilde çalış.',shots:['Parametrik EQ grafiği','Frekans tarama','Dar ve geniş Q','Ölçüm konumları']},
{id:'compressor',title:'Compressor: threshold, ratio ve attack',duration:'3:35',script:'Compressor, sinyal threshold seviyesini aştığında dinamik aralığı azaltır. Threshold başlangıcı, ratio sıkıştırma oranını belirler. Attack transientin ne kadarının geçeceğini, release ise kazanç azaltımının ne hızla bırakılacağını etkiler. Çok hızlı attack vuruşları söndürebilir; yanlış release pompalama oluşturabilir. Önce threshold ve ratioyu ayarla, ardından attack ve release değerlerini kaynağa göre dinle. Makeup gain ile seviye eşitlemeden A/B karşılaştırması yapma.',shots:['Compressor blok şeması','Gain reduction metre','Transient karşılaştırması','A/B seviye eşitleme']},
{id:'feedback',title:'Feedback anatomisi ve güvenli müdahale',duration:'3:00',script:'Feedback, mikrofonun hoparlörden çıkan sesi tekrar alıp döngüye sokmasıyla oluşur. Döngü kazancı belirli frekansta birin üzerine çıktığında dar bantlı çınlama duyulur. Önce mikrofon ve monitör konumunu, yönünü ve kazancını kontrol et. Sorunlu mikrofonun monitör gönderisini azaltmak geri alınabilir ilk adımdır. Frekansın sabit ve tekrarlanabilir olduğunu doğrula. Gerekirse dar parametrik kesim uygula. Tüm EQ bantlarını gelişigüzel kısmak miks kalitesini bozar.',shots:['Mikrofon-hoparlör döngüsü','Mikrofon yönü','Spektrum tepesi','Müdahale sırası']},
{id:'spl',title:'SPL kalibrasyonu ve ölçüm disiplini',duration:'3:40',script:'Ölçüm zincirini kalibre etmeden mikrofonun gösterdiği dBFS değerini dB SPL kabul etme. Uyumlu akustik kalibratörü mikrofon kapsülüne tak ve 94 veya 114 dB SPL, 1 kHz referansını kullan. Ardından uygun sınıf ölçüm cihazıyla A ağırlığı, Slow zaman ağırlığı ve LAeq koşullarını belirle. Ölçüm noktalarını, mikrofon yüksekliğini, mesafeyi ve süreyi kaydet. Telefon mikrofonu yasal veya standart uygunluk ölçümü için otomatik olarak yeterli değildir.',shots:['Akustik kalibratör','Mikrofon ve ölçüm cihazı','Ölçüm noktaları','LAeq raporu']},
{id:'rf',title:'Kablosuz mikrofon ve IEM koordinasyonu',duration:'3:30',script:'RF koordinasyonuna cihaz modelini, bölgeyi ve izinli frekans bandını doğrulayarak başla. Sahada RF taraması al ve yoğun taşıyıcıları kaydet. El mikrofonlarını ve IEM vericilerini aynı plan içinde değerlendir; ayrı ayrı temiz görünen frekanslar birlikte çalışırken intermodülasyon oluşturabilir. Anten dağıtımı, anten aralığı, koaksiyel kayıpları ve görüş hattı önemlidir. Planı üretici yazılımıyla ve gerçek sahada doğrulamadan kesin kabul etme. Yedek frekans ve pil hazırla.',shots:['RF spektrum taraması','Mikrofon ve IEM envanteri','Intermod şeması','Anten dağıtımı']},
{id:'power',title:'Tek/üç faz güç ve gerilim düşümü',duration:'3:15',script:'Elektrik hesabında aktif güç, gerilim, güç faktörü ve verim birlikte değerlendirilir. Tek fazda akım yaklaşık güç bölü gerilim, güç faktörü ve verimdir. Dengeli üç fazda kök üç çarpanı kullanılır. Kablo uzunluğu ve kesiti dirençsel gerilim düşümünü etkiler. Bu uygulamadaki hesap ön tasarım kontrolüdür; döşeme yöntemi, ortam sıcaklığı, kablo gruplaması, koruma elemanı, kısa devre akımı ve yerel mevzuat ayrıca yetkili elektrikçi tarafından doğrulanmalıdır.',shots:['Tek faz/üç faz şeması','Akım formülü','Kablo kesiti çizimi','Güvenlik kontrolü']}
];
function saveTextFile(name,mime,text){const blob=new Blob([text],{type:mime}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1500);}
function initPower(){
 const b=$('powerCalculate');if(!b||b.dataset.bound)return;b.dataset.bound='1';const phase=$('powerPhase'),voltage=$('powerVoltage');
 phase.addEventListener('change',()=>{voltage.value=phase.value==='three'?'400':'230';});
 b.addEventListener('click',()=>{try{const r=calculatePower({phase:phase.value,powerW:$('powerWatts').value,voltage:voltage.value,powerFactor:$('powerFactor').value,efficiency:$('powerEfficiency').value,reserve:$('powerReserve').value,lengthM:$('powerLength').value,sectionMm2:$('powerSection').value,material:$('powerMaterial').value});$('powerResult').textContent='Tasarım gücü: '+fmt(r.designPowerW,0)+' W · Hat akımı: '+fmt(r.currentA,2)+' A · Yaklaşık gerilim düşümü: '+fmt(r.voltageDropV,2)+' V ('+fmt(r.voltageDropPercent,2)+'%) · Uç gerilimi: '+fmt(r.receivingVoltage,2)+' V\n'+r.assumptions;$('powerResult').classList.toggle('notice-warn',r.voltageDropPercent>3);}catch(e){$('powerResult').textContent='Hesaplanamadı: '+e.message;}});
}
function initSplWizard(){
 const host=$('splWizardMeasurements');if(!host||host.dataset.bound)return;host.dataset.bound='1';let state={};try{state=JSON.parse(localStorage.getItem('stagepulse.splWizard.v1')||'{}');}catch(_){}
 let points=Array.isArray(state.points)?state.points:[];if(!points.length)points=[{name:'Ön sol',distance:5,laeq:'',lcpeak:''},{name:'Ön orta',distance:10,laeq:'',lcpeak:''},{name:'Ön sağ',distance:5,laeq:'',lcpeak:''},{name:'Orta alan',distance:20,laeq:'',lcpeak:''},{name:'Arka alan',distance:30,laeq:'',lcpeak:''}];
 const steps=$('splWizardSteps');if(steps)steps.querySelectorAll('input[type=checkbox]').forEach((el,i)=>{el.checked=!!(state.steps&&state.steps[i]);el.addEventListener('change',persist);});
 function render(){host.innerHTML=points.map((p,i)=>'<div class="spl-measure-row" data-index="'+i+'"><input data-point="name" aria-label="Ölçüm noktası" value="'+esc(p.name)+'"><input data-point="distance" type="number" min="0" step="0.1" aria-label="Mesafe metre" value="'+esc(p.distance)+'"><input data-point="laeq" type="number" min="0" max="160" step="0.1" aria-label="LAeq dBA" value="'+esc(p.laeq)+'" placeholder="LAeq dBA"><input data-point="lcpeak" type="number" min="0" max="180" step="0.1" aria-label="LCpeak dBC" value="'+esc(p.lcpeak)+'" placeholder="LCpeak dBC"><button type="button" class="btn btn-secondary btn-small" data-remove="'+i+'">Sil</button></div>').join('');}
 function persist(){host.querySelectorAll('.spl-measure-row').forEach((row,i)=>{const get=k=>row.querySelector('[data-point="'+k+'"]')?.value||'';points[i]={name:get('name'),distance:get('distance'),laeq:get('laeq'),lcpeak:get('lcpeak')};});state={steps:steps?Array.from(steps.querySelectorAll('input')).map(x=>x.checked):[],points};try{localStorage.setItem('stagepulse.splWizard.v1',JSON.stringify(state));}catch(_){}}
 host.addEventListener('input',persist);host.addEventListener('click',e=>{const r=e.target.closest('[data-remove]');if(r){points.splice(Number(r.dataset.remove),1);render();persist();}});
 $('splWizardAddPoint').addEventListener('click',()=>{persist();points.push({name:'Yeni nokta',distance:'',laeq:'',lcpeak:''});render();persist();});
 $('splWizardReport').addEventListener('click',()=>{persist();const rows=points.map(p=>({...p,laeq:Number(p.laeq)})).filter(p=>p.name&&Number.isFinite(p.laeq)&&p.laeq>0&&p.laeq<=160);if(rows.length<2){$('splWizardOutput').textContent='Rapor için en az iki ölçüm noktasında geçerli LAeq değeri gir.';return;}const values=rows.map(p=>p.laeq),avg=values.reduce((a,b)=>a+b,0)/values.length,min=Math.min(...values),max=Math.max(...values),target=Number($('splWizardTarget').value);$('splWizardOutput').textContent='Geçerli nokta: '+rows.length+' · Ortalama LAeq: '+fmt(avg,1)+' dBA · En düşük/en yüksek: '+fmt(min,1)+' / '+fmt(max,1)+' dBA · Noktalar arası aralık: '+fmt(max-min,1)+' dB'+(Number.isFinite(target)?' · Hedef farkı: '+fmt(avg-target,1)+' dB':'')+'\nBu özet girilen ölçüm değerlerinden hesaplandı. Ölçüm cihazı, kalibrasyon, zaman ağırlığı, mikrofon yüksekliği ve çevre koşulları rapora eklenmelidir.';});
 $('splWizardExport').addEventListener('click',()=>{persist();const lines=points.map(p=>[p.name,p.distance,p.laeq,p.lcpeak].map(v=>'"'+String(v||'').replace(/"/g,'""')+'"').join(','));saveTextFile('Stagepulse_SPL_saha_olcumleri.csv','text/csv;charset=utf-8','\uFEFF'+['point,distance_m,LAeq_dBA,LCpeak_dBC'].concat(lines).join('\n'));});
 render();
}
function initRfCoordinator(){
 const b=$('rfAdvancedGenerate');if(!b||b.dataset.bound)return;b.dataset.bound='1';let scan=[],last=[];
 const file=$('rfScanFile');if(file)file.addEventListener('change',async()=>{const f=file.files&&file.files[0];if(!f)return;try{const t=await f.text();scan=t.split(/\r?\n/).slice(1).map(line=>line.split(/[;,\t]/)).map(p=>({frequencyMHz:Number(String(p[0]||'').replace(',','.')),levelDbm:Number(String(p[1]||'').replace(',','.'))})).filter(x=>Number.isFinite(x.frequencyMHz)&&Number.isFinite(x.levelDbm));$('rfAdvancedStatus').textContent=scan.length+' tarama noktası koordinasyon filtresine alındı.';}catch(e){$('rfAdvancedStatus').textContent='Tarama dosyası okunamadı: '+e.message;}});
 b.addEventListener('click',()=>{try{const r=coordinateRf({minMHz:$('rfBandMin').value,maxMHz:$('rfBandMax').value,handhelds:$('rfHandheldCount').value,iems:$('rfIemCount').value,stepMHz:$('rfAdvancedStep').value,spacingMHz:$('rfAdvancedSpacing').value,guardMHz:$('rfAdvancedGuard').value,noiseThresholdDbm:$('rfNoiseLimit').value,scan});last=r.channels;$('rfAdvancedStatus').textContent=r.warning+'\nİstenen: '+r.requested+' · Atanan: '+r.assigned+' · Tarama noktası: '+r.scanCount;$('rfAdvancedTable').innerHTML=r.channels.map(c=>'<tr><td>'+c.index+'</td><td>'+esc(c.label)+'</td><td>'+fmt(c.frequencyMHz,3)+' MHz</td><td>Ön aday</td></tr>').join('');}catch(e){$('rfAdvancedStatus').textContent='Plan oluşturulamadı: '+e.message;$('rfAdvancedTable').innerHTML='';}});
 $('rfAdvancedExport').addEventListener('click',()=>{if(!last.length){$('rfAdvancedStatus').textContent='Önce kanal planı oluştur.';return;}const csv=['channel,type,label,frequency_MHz'].concat(last.map(c=>[c.index,c.type,'"'+c.label+'"',c.frequencyMHz].join(','))).join('\n');saveTextFile('Stagepulse_RF_IEM_koordinasyon.csv','text/csv;charset=utf-8','\uFEFF'+csv);});
}
let mixEngine=null,mixChannels=[],mixFrame=0;
const mixDb=db=>Math.pow(10,Number(db)/20);
function ensureMixEngine(){
 if(mixEngine)return mixEngine;const Audio=window.AudioContext||window.webkitAudioContext;if(!Audio)throw Error('Bu cihaz Web Audio API desteklemiyor.');
 const ctx=new Audio(),master=ctx.createGain();master.gain.value=mixDb(Number($('mixLabMaster')?.value||-24));master.connect(ctx.destination);
 mixChannels=Array.from({length:4},()=>{const input=ctx.createGain(),hpf=ctx.createBiquadFilter(),low=ctx.createBiquadFilter(),mid=ctx.createBiquadFilter(),high=ctx.createBiquadFilter(),comp=ctx.createDynamicsCompressor(),fader=ctx.createGain(),analyser=ctx.createAnalyser();
  hpf.type='highpass';hpf.frequency.value=80;hpf.Q.value=.707;low.type='lowshelf';low.frequency.value=120;mid.type='peaking';mid.frequency.value=1000;mid.Q.value=1;high.type='highshelf';high.frequency.value=8000;comp.threshold.value=-18;comp.ratio.value=3;comp.attack.value=.01;comp.release.value=.15;fader.gain.value=mixDb(-6);analyser.fftSize=1024;
  input.connect(hpf);hpf.connect(low);low.connect(mid);mid.connect(high);high.connect(comp);comp.connect(fader);fader.connect(analyser);analyser.connect(master);
  return {input,hpf,low,mid,high,comp,fader,analyser,source:null,buffer:null,muted:false,solo:false};});
 mixEngine={ctx,master};const host=$('mixLabChannels');if(host)host.querySelectorAll('[data-channel]').forEach((row,i)=>row.querySelectorAll('[data-mix-param]').forEach(input=>updateMixParam(i,input.dataset.mixParam,input.value)));return mixEngine;
}
function renderMixChannels(){
 const host=$('mixLabChannels');if(!host||host.dataset.rendered)return;host.dataset.rendered='1';
 host.innerHTML=Array.from({length:4},(_,i)=>'<article class="panel mixlab-strip" data-channel="'+i+'"><div class="panel-head"><div><span class="eyebrow">GİRİŞ '+(i+1)+'</span><h3>'+['Vokal','Kick / Davul','Bas','Enstrüman'][i]+'</h3></div><span class="chip" id="mixlabMeterText'+i+'">−∞ dBFS</span></div><label class="file-button mixlab-file">Ses dosyası yükle<input type="file" accept="audio/*,.wav,.mp3,.flac,.aiff,.ogg" data-mix-file="'+i+'" hidden></label><div class="field-row"><label>Preamp gain <b data-value="preamp">0 dB</b></label><input type="range" min="-12" max="36" step=".5" value="0" data-mix-param="preamp"></div><div class="field-row"><label>HPF <b data-value="hpf">80 Hz</b></label><input type="range" min="20" max="300" value="80" data-mix-param="hpf"></div><div class="field-row"><label>Low EQ <b data-value="low">0 dB</b></label><input type="range" min="-12" max="12" step=".5" value="0" data-mix-param="low"></div><div class="field-row"><label>Mid EQ <b data-value="mid">0 dB</b></label><input type="range" min="-12" max="12" step=".5" value="0" data-mix-param="mid"></div><div class="field-row"><label>High EQ <b data-value="high">0 dB</b></label><input type="range" min="-12" max="12" step=".5" value="0" data-mix-param="high"></div><div class="field-row"><label>Comp threshold <b data-value="threshold">−18 dB</b></label><input type="range" min="-40" max="0" value="-18" data-mix-param="threshold"></div><div class="field-row"><label>Comp ratio <b data-value="ratio">3:1</b></label><input type="range" min="1" max="12" step=".5" value="3" data-mix-param="ratio"></div><div class="field-row"><label>Channel fader <b data-value="fader">−6 dB</b></label><input type="range" min="-60" max="6" step=".5" value="-6" data-mix-param="fader"></div><div class="mixlab-meter"><i id="mixlabMeter'+i+'"></i></div><div class="row-actions"><button type="button" class="btn btn-secondary btn-small" data-mix-mute="'+i+'">MUTE</button><button type="button" class="btn btn-secondary btn-small" data-mix-solo="'+i+'">SOLO</button></div><small class="muted" id="mixlabFileName'+i+'">Test sinyali hazır</small></article>').join('');
}
function updateMixParam(i,param,value){
 const row=$('mixLabChannels')?.querySelector('[data-channel="'+i+'"]'),label=row&&row.querySelector('[data-value="'+param+'"]'),n=Number(value);
 if(label)label.textContent=param==='hpf'?fmt(n,0)+' Hz':param==='ratio'?fmt(n,1)+':1':fmt(n,1)+' dB';
 const ch=mixChannels[i];if(!ch)return;const now=ch.input.context.currentTime;
 if(param==='preamp')ch.input.gain.setTargetAtTime(mixDb(n),now,.015);if(param==='hpf')ch.hpf.frequency.setTargetAtTime(n,now,.015);
 if(param==='low')ch.low.gain.setTargetAtTime(n,now,.015);if(param==='mid')ch.mid.gain.setTargetAtTime(n,now,.015);if(param==='high')ch.high.gain.setTargetAtTime(n,now,.015);
 if(param==='threshold')ch.comp.threshold.setTargetAtTime(n,now,.015);if(param==='ratio')ch.comp.ratio.setTargetAtTime(n,now,.015);if(param==='fader')ch.fader.gain.setTargetAtTime(mixDb(n),now,.015);
}
function updateMixMuteSolo(){
 const active=mixChannels.some(c=>c.solo);mixChannels.forEach((ch,i)=>{const row=$('mixLabChannels').querySelector('[data-channel="'+i+'"]'),f=row.querySelector('[data-mix-param="fader"]'),db=Number(f?f.value:-6);ch.fader.gain.setTargetAtTime(!ch.muted&&(!active||ch.solo)?mixDb(db):0,ch.input.context.currentTime,.02);});
}
function stopMixLab(){
 mixChannels.forEach(ch=>{if(ch.source){try{ch.source.stop();ch.source.disconnect();}catch(_){}ch.source=null;}});if($('mixLabStop'))$('mixLabStop').disabled=true;if(mixFrame)cancelAnimationFrame(mixFrame);mixFrame=0;
}
function meterMixLab(){
 mixChannels.forEach((ch,i)=>{const data=new Float32Array(ch.analyser.fftSize);ch.analyser.getFloatTimeDomainData(data);let sum=0;for(const v of data)sum+=v*v;const rms=Math.sqrt(sum/data.length),db=rms>0?20*Math.log10(rms):-120,fill=$('mixlabMeter'+i),label=$('mixlabMeterText'+i);if(fill)fill.style.width=clamp((db+60),0,60)/60*100+'%';if(label)label.textContent=db<=-119?'−∞ dBFS':fmt(db,1)+' dBFS';});
 if(mixChannels.some(c=>c.source))mixFrame=requestAnimationFrame(meterMixLab);
}
async function playMixLab(){
 try{const e=ensureMixEngine();await e.ctx.resume();stopMixLab();const signal=$('mixLabSignal').value;
  mixChannels.forEach((ch,i)=>{let source;if(ch.buffer){source=e.ctx.createBufferSource();source.buffer=ch.buffer;source.loop=false;}
   else if(signal==='noise'){const buffer=e.ctx.createBuffer(1,e.ctx.sampleRate*2,e.ctx.sampleRate),data=buffer.getChannelData(0);let last=0;for(let n=0;n<data.length;n++){last=.985*last+.015*(Math.random()*2-1);data[n]=last*.15;}source=e.ctx.createBufferSource();source.buffer=buffer;source.loop=true;}
   else{source=e.ctx.createOscillator();source.type=signal==='voice'?'sawtooth':'sine';source.frequency.value=signal==='kick'?62:signal==='bass'?92:signal==='voice'?145:[220,330,440,550][i];}
   source.connect(ch.input);ch.source=source;source.onended=()=>{if(ch.source===source)ch.source=null;};source.start();
  });$('mixLabStop').disabled=false;meterMixLab();
 }catch(err){$('mixLabStatus').textContent='Miks laboratuvarı başlatılamadı: '+err.message;}
}
function applyMixScenario(){
 const presets={vocal:{preamp:18,hpf:100,low:-2,mid:1.5,high:2,threshold:-20,ratio:3,fader:-6},kick:{preamp:12,hpf:35,low:3,mid:-2,high:1,threshold:-14,ratio:4,fader:-8},bass:{preamp:12,hpf:40,low:2,mid:-1,high:0,threshold:-22,ratio:3,fader:-8},speech:{preamp:16,hpf:120,low:-2,mid:2,high:1,threshold:-24,ratio:3,fader:-6}};
 const preset=presets[$('mixLabScenario').value]||presets.vocal;
 $('mixLabChannels').querySelectorAll('[data-channel]').forEach((row,i)=>Object.entries(preset).forEach(([k,v])=>{const input=row.querySelector('[data-mix-param="'+k+'"]');if(input){input.value=v;updateMixParam(i,k,v);}}));
 $('mixLabStatus').textContent='Örnek ayar yüklendi. Bunlar başlangıç noktasıdır; kaynağa göre dinleyerek değiştir.';
}
function initMixLab(){
 const host=$('mixLabChannels');if(!host||host.dataset.bound)return;host.dataset.bound='1';renderMixChannels();
 host.addEventListener('input',e=>{const input=e.target.closest('[data-mix-param]');if(input)updateMixParam(Number(input.closest('[data-channel]').dataset.channel),input.dataset.mixParam,input.value);});
 host.addEventListener('change',async e=>{const f=e.target.closest('[data-mix-file]');if(!f||!f.files||!f.files[0])return;try{const engine=ensureMixEngine(),buffer=await engine.ctx.decodeAudioData(await f.files[0].arrayBuffer());mixChannels[Number(f.dataset.mixFile)].buffer=buffer;$('mixlabFileName'+f.dataset.mixFile).textContent=f.files[0].name+' · '+fmt(buffer.duration,1)+' s';$('mixLabStatus').textContent='Ses kaynağı yüklendi. Dosya yalnızca bu oturumda bellekte işlenir.';}catch(err){$('mixLabStatus').textContent='Ses dosyası çözümlenemedi: '+err.message;}});
 host.addEventListener('click',e=>{const m=e.target.closest('[data-mix-mute]'),s=e.target.closest('[data-mix-solo]');if(m){ensureMixEngine();const i=Number(m.dataset.mixMute);mixChannels[i].muted=!mixChannels[i].muted;m.classList.toggle('active',mixChannels[i].muted);updateMixMuteSolo();}if(s){ensureMixEngine();const i=Number(s.dataset.mixSolo);mixChannels[i].solo=!mixChannels[i].solo;s.classList.toggle('active',mixChannels[i].solo);updateMixMuteSolo();}});
 $('mixLabPlay').addEventListener('click',playMixLab);$('mixLabStop').addEventListener('click',stopMixLab);$('mixLabScenarioApply').addEventListener('click',()=>{ensureMixEngine();applyMixScenario();});
 $('mixLabMaster').addEventListener('input',e=>{if(mixEngine)mixEngine.master.gain.setTargetAtTime(mixDb(Number(e.target.value)),mixEngine.ctx.currentTime,.02);$('mixLabMasterValue').textContent=e.target.value+' dB';});
 document.addEventListener('click',e=>{const route=e.target.closest('[data-route]');if(route&&route.dataset.route!=='mixlab')stopMixLab();});
}
function renderRtaDecision(){
 const output=$('rtaOptimizerOutput'),host=$('rtaDecisionSteps');if(!output||!host)return;const table=output.querySelector('.report-table'),text=table?table.innerText:output.innerText||output.textContent||'',candidates=parseRtaCandidates(text);
 if(!candidates.length){host.textContent='Öneri için RTA ekranında pembe gürültü veya sabit bantlı test sinyaliyle kararlı örnekler topla. Müzik/konuşma spektrumundan oda EQ kararı çıkarılmaz.';return;}
 host.innerHTML=candidates.map(c=>{const hz=c.frequencyHz,band=hz<80?'sub-bass':hz<250?'bas / low-mid':hz<2000?'mid':'high-mid / tiz';
  const action=hz<80?'Sub yerleşimi, polarite, delay ve crossover noktasını kontrol et. İstenmeyen infrasonik gürültü varsa yalnızca ilgili kaynak kanalında uygun HPF değerlendir.':hz<250?'Sınır etkisi, sub-top crossover, polarite ve delay ilişkisini kontrol et. Birikim farklı ölçüm konumlarında tekrarlanıyorsa PA/DSP üzerinde küçük parametrik kesim dene; konsol kanalına gelişigüzel low-cut uygulama.':hz<2000?'Mikrofon/ölçüm konumu, yansımalar ve kaynak tonunu kontrol et. Birden fazla noktada aynı tepe kalıyorsa küçük ve dar bir kesimle başla.':'Hoparlör ekseni, mikrofonun yüksek frekans cevabı ve erken yansımaları kontrol et. Tek noktadaki tiz farkını sistem EQ’su olarak genelleme.';
  return '<div class="rta-decision-item"><strong>'+fmt(hz,0)+' Hz · '+band+'</strong><p>'+esc(action)+'</p><small>Gözlenen tepe farkı: '+(c.excessDb==null?'belirtilmedi':'+'+fmt(c.excessDb,1)+' dB')+'. İlk deneme en fazla 1–3 dB kesim; boost yok.</small></div>';
 }).join('')+'<ol class="plain-list"><li>Ölçüm mikrofonu ve kalibrasyonu doğrula.</li><li>En az 3–5 dinleme noktasında tekrar ölç.</li><li>Her değişiklikten sonra aynı koşullarda yeniden ölç ve dinle.</li></ol>';
}
function initRtaDecision(){
 const output=$('rtaOptimizerOutput');if(!output||output.dataset.decisionBound)return;output.dataset.decisionBound='1';new MutationObserver(renderRtaDecision).observe(output,{childList:true,subtree:true,characterData:true});renderRtaDecision();
 const b=$('rtaDecisionToAssistant');if(b)b.addEventListener('click',()=>{const context=$('promptContext'),type=$('promptType');if(context)context.value='RTA ölçüm adayları:\n'+($('rtaDecisionSteps')?.innerText||'Henüz aday yok.')+'\nBu veriler kesin teşhis değildir. Önce doğrulama ve güvenli müdahale sırası öner.';if(type)type.value='pa';document.querySelector('[data-route="assistant"]')?.click();});
}
async function copyText(text,status){try{if(navigator.clipboard&&navigator.clipboard.writeText)await navigator.clipboard.writeText(text);else{const a=document.createElement('textarea');a.value=text;document.body.appendChild(a);a.select();document.execCommand('copy');a.remove();}if(status)status.textContent='Metin panoya kopyalandı.';}catch(_){if(status)status.textContent='Kopyalama başarısız. Metni seçip elle kopyala.';}}
function initAcademy(){
 const list=$('videoLessonList');if(!list||list.dataset.bound)return;list.dataset.bound='1';
 list.innerHTML=videoLessons.map((l,i)=>'<button type="button" class="video-lesson-item'+(i===0?' active':'')+'" data-lesson="'+l.id+'"><strong>'+esc(l.title)+'</strong><small>'+l.duration+' · Senaryo hazır</small></button>').join('');
 let current=videoLessons[0];
 function show(l){current=l;list.querySelectorAll('[data-lesson]').forEach(b=>b.classList.toggle('active',b.dataset.lesson===l.id));$('videoLessonTitle').textContent=l.title+' · '+l.duration;$('videoLessonScript').textContent=l.script;$('videoLessonStoryboard').innerHTML=l.shots.map((s,i)=>'<li>Plan '+(i+1)+': '+esc(s)+'</li>').join('');$('videoLessonStatus').textContent='Türkçe anlatım metni ve sahne planı hazır. Gerçek video dosyası henüz eklenmedi.';$('videoLessonPrompt').value='Stagepulse için 2–4 dakikalık Türkçe ses mühendisliği eğitim videosu üret. İnsan eğitmen/kamera çekimi kullanma. Doğal Türkçe AI seslendirme, animasyonlu teknik grafikler ve altyazı kullan. Marka görünümü siyah, altın ve beyaz. Konu: '+l.title+'. Anlatım: '+l.script+'\nSahne planı: '+l.shots.join('; ')+'. Teknik değerleri uydurma; güvenlik ve ölçüm sınırlarını belirt.';}
 list.addEventListener('click',e=>{const b=e.target.closest('[data-lesson]');if(b){const l=videoLessons.find(x=>x.id===b.dataset.lesson);if(l)show(l);}});
 $('videoLessonCopyScript').addEventListener('click',()=>copyText(current.script,$('videoLessonStatus')));$('videoLessonCopyPrompt').addEventListener('click',()=>copyText($('videoLessonPrompt').value,$('videoLessonStatus')));
 $('videoLessonLoadUrl').addEventListener('click',()=>{const url=$('videoLessonUrl').value.trim();if(!/^https?:\/\//i.test(url)&&!/^\/(?!\/)/.test(url)){$('videoLessonStatus').textContent='Doğrudan MP4/WEBM adresi veya uygulama içi yol gir.';return;}$('videoLessonPlayer').src=url;$('videoLessonPlayer').load();$('videoLessonStatus').textContent='Video kaynağı yüklendi.';try{localStorage.setItem('stagepulse.video.url.'+current.id,url);}catch(_){}});
 $('videoLessonFile').addEventListener('change',()=>{const f=$('videoLessonFile').files&&$('videoLessonFile').files[0];if(!f)return;if(window.__stagepulseLessonObjectUrl)URL.revokeObjectURL(window.__stagepulseLessonObjectUrl);window.__stagepulseLessonObjectUrl=URL.createObjectURL(f);$('videoLessonPlayer').src=window.__stagepulseLessonObjectUrl;$('videoLessonStatus').textContent=f.name+' · bu oturumda oynatılıyor.';});
 show(current);
}
function certificatePdfBlob(canvas){
 const data=canvas.toDataURL('image/jpeg',.94),raw=atob(data.split(',')[1]),image=new Uint8Array(raw.length);for(let i=0;i<raw.length;i++)image[i]=raw.charCodeAt(i);
 const enc=new TextEncoder(),parts=[],offsets=[],size={n:0},add=s=>{const b=enc.encode(s);parts.push(b);size.n+=b.length;},bytes=b=>{parts.push(b);size.n+=b.length;};
 add('%PDF-1.4\n');offsets[1]=size.n;add('1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n');offsets[2]=size.n;add('2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n');offsets[3]=size.n;add('3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 842 595] /Resources << /XObject << /Im0 4 0 R >> >> /Contents 5 0 R >>\nendobj\n');
 offsets[4]=size.n;add('4 0 obj\n<< /Type /XObject /Subtype /Image /Width 1600 /Height 1131 /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length '+image.length+' >>\nstream\n');bytes(image);add('\nendstream\nendobj\n');
 const stream='q\n842 0 0 595 0 0 cm\n/Im0 Do\nQ\n';offsets[5]=size.n;add('5 0 obj\n<< /Length '+stream.length+' >>\nstream\n'+stream+'endstream\nendobj\n');
 const xref=size.n;add('xref\n0 6\n0000000000 65535 f \n');for(let i=1;i<=5;i++)add(String(offsets[i]).padStart(10,'0')+' 00000 n \n');add('trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n'+xref+'\n%%EOF');return new Blob(parts,{type:'application/pdf'});
}
function drawCertificate(name,program,level,hours,date,number){
 const canvas=document.createElement('canvas');canvas.width=1600;canvas.height=1131;const c=canvas.getContext('2d');c.fillStyle='#0b0d11';c.fillRect(0,0,1600,1131);c.strokeStyle='#c9a65b';c.lineWidth=10;c.strokeRect(35,35,1530,1061);c.lineWidth=2;c.strokeRect(58,58,1484,1015);c.textAlign='center';
 c.fillStyle='#c9a65b';c.font='bold 34px Arial';c.fillText('STAGEPULSE',800,150);c.fillStyle='#fff';c.font='bold 62px Georgia';c.fillText('KATILIM BELGESİ',800,285);c.fillStyle='#d7bd82';c.font='28px Arial';c.fillText('SES MÜHENDİSLİĞİ EĞİTİM PROGRAMI',800,350);
 c.fillStyle='#d8dde5';c.font='26px Arial';c.fillText('Aşağıda adı bulunan katılımcının',800,470);c.fillStyle='#fff';let fs=58;c.font='bold '+fs+'px Georgia';while(c.measureText(name).width>1300&&fs>30){fs-=2;c.font='bold '+fs+'px Georgia';}c.fillText(name,800,555);
 c.fillStyle='#d8dde5';c.font='27px Arial';c.fillText('Stagepulse eğitim programına katılım sağladığı belgelenir.',800,620);c.fillStyle='#c9a65b';c.font='bold 31px Arial';c.fillText(program.slice(0,80),800,710);
 c.fillStyle='#fff';c.font='24px Arial';c.fillText('Öğrenme yolu: '+level+'     ·     Katılım süresi: '+hours+' saat',800,775);c.fillStyle='#d8dde5';c.font='22px Arial';c.fillText('Tarih: '+date+'     ·     Belge No: '+number,800,845);
 c.strokeStyle='#c9a65b';c.lineWidth=2;c.beginPath();c.moveTo(240,910);c.lineTo(1360,910);c.stroke();c.fillStyle='#d7bd82';c.font='20px Arial';c.fillText('STAGEPULSE EĞİTİM PLATFORMU',800,950);c.fillStyle='#9ba4b2';c.font='18px Arial';c.fillText('Bu belge yalnızca katılımı gösterir; resmî yeterlilik, akreditasyon veya mesleki yetki sağlamaz.',800,1010);return canvas;
}
function initCertificate(){
 const b=$('certificateGenerate');if(!b||b.dataset.bound)return;b.dataset.bound='1';$('certificateDate').value=new Date().toISOString().slice(0,10);
 const number='SP-KB-'+new Date().toISOString().slice(0,10).replace(/-/g,'')+'-'+Math.random().toString(36).slice(2,7).toUpperCase();
 b.addEventListener('click',()=>{const name=$('certificateName').value.trim(),program=$('certificateProgram').value.trim(),hours=Number($('certificateHours').value),date=$('certificateDate').value,level=$('certificateLevel').value;
  if(!name||!program||!(hours>0&&hours<=1000)||!date){$('certificateStatus').textContent='Katılımcı, program, süre ve tarih alanlarını kontrol et.';return;}
  const canvas=drawCertificate(name,program,level,fmt(hours,1),new Date(date+'T12:00:00').toLocaleDateString('tr-TR'),number);
  $('certificatePreview').innerHTML='<div class="certificate-preview-inner"><strong>STAGEPULSE</strong><h2>KATILIM BELGESİ</h2><p>'+esc(name)+'</p><b>'+esc(program)+'</b><small>'+esc(level)+' · '+fmt(hours,1)+' saat · '+esc(date)+' · '+esc(number)+'</small><em>Bu belge yalnızca katılımı gösterir; resmî yeterlilik, akreditasyon veya mesleki yetki sağlamaz.</em></div>';
  const blob=certificatePdfBlob(canvas),android=window.StagepulseAndroid,desktop=window.pywebview&&window.pywebview.api;
  const asBase64=()=>blob.arrayBuffer().then(buffer=>{const bytes=new Uint8Array(buffer);let bin='';for(let i=0;i<bytes.length;i+=0x8000)bin+=String.fromCharCode.apply(null,bytes.subarray(i,i+0x8000));return btoa(bin);});
  if(android&&typeof android.saveBase64File==='function'){asBase64().then(encoded=>{const ok=android.saveBase64File('Stagepulse_Katilim_Belgesi.pdf','application/pdf',encoded);$('certificateStatus').textContent=ok?'PDF, İndirilenler/Stagepulse klasörüne kaydedildi.':'PDF kaydedilemedi.';});}
  else if(desktop&&typeof desktop.save_generated_pdf_dialog==='function'){asBase64().then(encoded=>desktop.save_generated_pdf_dialog('Stagepulse_Katilim_Belgesi.pdf',encoded)).then(result=>{$('certificateStatus').textContent=result&&result.ok?'PDF seçtiğin konuma kaydedildi.':result&&result.cancelled?'PDF kaydetme iptal edildi.':'PDF kaydedilemedi.';}).catch(error=>{$('certificateStatus').textContent='PDF kaydedilemedi: '+error.message;});}
  else{const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='Stagepulse_Katilim_Belgesi.pdf';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),2000);$('certificateStatus').textContent='Katılım belgesi PDF olarak dışa aktarıldı.';}
 });
}
function init(){initPower();initSplWizard();initRfCoordinator();initMixLab();initRtaDecision();initAcademy();initCertificate();}
if(typeof window!=='undefined')window.StagepulseAdvanced={calculatePower,coordinateRf,hasIntermodConflict,parseRtaCandidates,videoLessons};
if(typeof document!=='undefined'){if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();}
})();