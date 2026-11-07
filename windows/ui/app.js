// Stagepulse UI release 3.8.10
'use strict';
const $ = (id) => document.getElementById(id);
const routes = {
  home:'Ana sayfa', frequency:'Frekans bulucu', ear:'Kulak eğitimi', calculators:'Hesaplayıcılar', acoustics:'SPL / alan planı', systemplan:'Sahne ve ses-görüntü planı', patch:'Mikser kanal bağlantı raporu', rf:'Kablosuz frekans planı', distribution:'70/100 V hoparlör hattı', roommap:'Oda ses basınç seviyesi haritası', speaker:'Hoparlör ve sayısal sinyal işleme', wavelab:'Dalga / faz / gecikme laboratuvarı',
  rta:'Gerçek zamanlı analiz (RTA)', mixer:'Ses katmanı atölyesi', wav:'Ses dosyası kalite analizi (WAV)', lufs:'Ses yüksekliği normalizasyonu (LUFS)',
  cues:'Sahne ipucu (Cue) ve video notları', checklists:'Kontrol listeleri', docs:'Ders kılavuzları', pdf:'Öğrenci PDF kitaplığı',
  curriculum:'Eğitim dalları / ustalık yolu', student:'Öğrenci ilerlemesi', assistant:'Yapay zekâ / çalışma asistanı', account:'Hesap / lisans', settings:'Ayarlar ve gizlilik'
};
const progressModules = [
  ['frequency','Frekans ve nota'],['ear','Kulak eğitimi'],['calculators','Teknik hesaplar'],['acoustics','SPL ve alan planı'],['rta','RTA ve ölçüm sınırları'],
  ['mixer','Çok katmanlı ses'],['wav','WAV kalite kontrolü'],['lufs','Loudness normalizasyonu'],['cues','Cue planlama'],
  ['checklists','Saha kontrol listeleri'],['docs','Ders kılavuzları']
];
const checklistData = {
  show:['Teknik rider, stageplot ve input list eşleştirildi.','Güç, topraklama ve kablo yolları yetkili ekipçe kontrol edildi.','Array/hoparlör donanımı ve rigging güvenliği kontrol edildi.','Konsol patch, phantom power ve sinyal akışı doğrulandı.','Ana PA, sub, fill, monitör ve IEM yolları ayrı test edildi.','RF taraması ve kablosuz koordinasyon kaydedildi.','Soundcheck ve sahne değişimleri ekipçe onaylandı.','Yedek mikrofon, DI, pil ve konsol sahnesi hazırlandı.','Güvenli ses seviyesi ve işitme koruması planlandı.','Etkinlik sonu kapatma ve arşivleme sorumlusu belirlendi.'],
  qc:['Dosya sürümü, format, kanal sayısı ve teslim standardı doğrulandı.','Başlangıç/bitiş, sessizlik ve tüm kanallar dinlendi.','Clipping, tıklama, uğultu, bozulma ve istenmeyen gürültü kontrol edildi.','Mono uyumu, polarite ve stereo alanı kontrol edildi.','Tonal denge, rezonans ve düşük frekans birikimi dinlendi.','Kompresyon artefaktları ve otomasyon kontrol edildi.','Peak/RMS ile teslim gerektiriyorsa LUFS/true-peak ayrı ölçüldü.','Son dışa aktarılan dosya yeniden açılıp dinlendi.'],
  recording:['Metin, özel adlar ve alternatif telaffuzlar hazırlandı.','Fan, HVAC, trafik ve oda yansımaları dinlendi.','Mikrofon mesafesi, açı, pop filtre ve shock mount kontrol edildi.','Örnekleme, bit derinliği ve giriş/çıkış yönlendirmesi eşleşti.','Normal ve yüksek ifadelerde gain/headroom doğrulandı.','Deneme kaydı ve oda tonu alındı.','Ham kaynak ve işlenmiş teslim ayrı saklandı.','Gürültü azaltma ve kompresyon artefaktları dinlendi.'],
  rf:['Bölge ve cihaz varyantının izinli frekans aralığı doğrulandı.','Ortam RF taraması kaydedildi.','Mikrofon ve IEM vericileri ortak koordinasyon planına eklendi.','Anten, dağıtıcı, kablo ve görüş hattı kontrol edildi.','Kanallar tek tek ve birlikte kesilme/girişim için test edildi.','Yedek frekans, cihaz ve pil planlandı.'],
  noise:['Kaynak, zaman aralığı ve etkilenen alan tanımlandı.','Cihaz modeli, kalibrasyon ve yöntem kaydedildi.','Mikrofon konumu, yüksekliği, süre ve çevre koşulları kaydedildi.','Ölçümler ile işitsel gözlemler ayrı yazıldı.','Oda yankısı ile dışarıdan ses geçişi ayırt edildi.','Mevzuat ve standart iddiaları güncel resmi kaynaktan doğrulandı.','İyileştirme sonrası aynı koşullarda tekrar ölçüm planlandı.']
};
const prompts = {
  live:'Canlı ses arızasını güvenli şekilde sınıflandır. Belirti, olası neden, en geri alınabilir test sırası ve durdurma koşulu başlıklarını kullan. Görmediğin ekipman ayarlarını uydurma.',
  wav:'Ses dosyasını yalnızca gerçekten ölçülen özelliklerle değerlendir. Format, sample peak, RMS, clipping riski, dinleme kontrolleri ve sınırlamaları ayrı belirt. Ölçülmemiş LUFS, true-peak veya dB SPL değeri üretme.',
  mix:'Miksi düşük frekans, orta alan netliği, üst frekans, stereo, transient/dinamik ve kaynak dengesi olarak değerlendir. En fazla beş öncelikli değişiklik öner; olası yan etkileri de yaz.',
  pa:'Hoparlör modeli, fiziksel mesafe, işlemci/preset, crossover, polarite ve ölçüm koşulları olmadan kesin ayar verme. Teorik hesap ile saha ölçümünü ayır. Güvenli ölçüm adımlarını sırala.',
  noise:'Ölçüm aracı, kalibrasyon, yer, saat, süre ve kaynak koşullarını raporla. Ölçülen bulguları hipotezlerden ayır. Mevzuat uygunluğu hakkında güncel resmi kaynak olmadan kesin hüküm verme.',
  speech:'Anlaşılabilirlik, telaffuz, vurgu, ritim, sibilans, tını sürekliliği ve artefaktları ayrı değerlendir. Ses dinlenmediyse yalnızca metinden ses kalitesi ölçülmüş gibi davranma.'
};
let activeRoute = 'home';
let apiReady = false;
let nativeInitStarted = false;
let appAuthorized = false;
let licenseGatePending = true;
let currentRole = 'guest';
let currentAccountContext = null;
let remoteProgress = {};
let teacherStudents = [];
let selectedTeacherStudentId = '';
let latestUpdateManifest = null;
let profiles = {};
let profilesLoaded = false;
let profilesLoadPromise = null;
let activeStudent = '';
let studentData = {completedModules:[], checklists:{}, cues:[]};
let lastWavReport = null;
let cueRows = [];
let audioContext = null;
let earTarget = 500;
let earRound = 0;
let earCorrect = 0;
let earAnswered = 0;
let eqTarget = 'low';
let eqBuffer = null;
let mixerTracks = [];
const MAX_DECODED_AUDIO_BYTES = 512 * 1024 * 1024;
const MAX_RENDER_AUDIO_BYTES = 320 * 1024 * 1024;
const MAX_AUDIO_WORK_BYTES = 1024 * 1024 * 1024;
let lastMasterGainDb = 0;
let nextTrackId = 1;
let mixerAudioContext = null;
let mixerPreviewSource = null;
let videoObjectUrl = null;
let rtaPollTimer = 0;
let rtaRunning = false;
let rtaBusy = false;
let rtaGeneration = 0;
let rtaCommandQueue = Promise.resolve();
let rtaLastTime = 0;
let rtaSampleRate = 0;
let rtaFftSize = 16384;
let rtaSmoothed = null;
let rtaPeak = null;
let rtaTraceHistory = [];
let rtaFreqs = [];
let rtaOptimizerHistory = [];
let rtaDeviceName = '';
let videoSceneMarkers = [];
let audioEvidenceData = null;
let soundLibraryIndex = [];
let pendingMixProject = null;
let editDraft = [];
let curriculumCatalog = null;
const curriculumQuizBank = {
 live_sound:[['Gain staging neyi amaçlar?',['Sinyal seviyelerini kırpılma olmadan uygun aralıkta tutmak','Tüm kanalları kırmızıya sürmek','Her girişte aynı kazancı kullanmak'],0],['Phantom power ne zaman açılır?',['Her XLR girişinde koşulsuz','Yalnızca ihtiyaç duyan uyumlu mikrofon/cihaz için kontrol edilerek','Hoparlör çıkışında'],1],['Soundcheck öncesi kritik güvenlik adımı hangisidir?',['Rigging ve güç güvenliğini yetkili ekiple kontrol etmek','PA’yı seyirciye bakmadan maksimuma almak','Kabloyu yük altında sökmek'],0]],
 rf_wireless:[['Frekans koordinasyonunda önce ne doğrulanır?',['Cihaz modeli, bölge ve izinli bant aralığı','Sadece cihazın rengi','Yalnızca pil markası'],0],['Drop-out teşhisinde iyi yaklaşım hangisidir?',['Rastgele frekans değiştirip bırakmak','Tarama, anten/koaksiyel kontrolü ve kayıtlı test','Gücü sürekli maksimum yapmak'],1],['RF planında yedek kanal neden gerekir?',['Girişim veya arıza halinde kontrollü geçiş için','Ses seviyesini artırmak için','Mikrofonu stereo yapmak için'],0]],
 pa_system:[['İki kaynak arasındaki delay nasıl belirlenmelidir?',['Sadece oda alanına bakarak','Mesafe/ölçüm ve sistem konfigürasyonuna göre doğrulayarak','Her zaman sıfır'],1],['SPL tahmininde hangi yaklaşım doğrudur?',['Varsayımları ve üretici verisini açıkça belirtip sahada doğrulamak','Alan m² değerinden kesin SPL çıkarmak','RTA dBFS değerini dB SPL kabul etmek'],0],['Limiter/preset seçimi neye dayanmalı?',['Üretici verisi ve sistem bileşenlerine','Rastgele internet ayarına','Yalnızca sub sayısına'],0]],
 studio_post:[['Teslim edilen ses dosyası için son kontrol nedir?',['Sadece dışa aktarma düğmesine basmak','Dosyayı yeniden açıp dinlemek ve QC yapmak','Kaynak oturumu silmek'],1],['Clipping neyi ifade eder?',['Sinyalin dijital tam ölçeği aşması/kırpılma oluşması','Her zaman doğru loudness','Stereo genişliği'],0],['Loudness hedefi nasıl seçilir?',['Her işte tek evrensel değer','Müşteri/platform teslim şartına göre','Dosya adına göre'],1]],
 spl_acoustics:[['Kalibre edilmemiş PC mikrofonu neyi kanıtlamaz?',['Göreli spektrum gösterebilir','Mutlak dB SPL ve standart uygunluğu','Ses girişinin varlığını'],1],['Ölçüm raporunda hangisi bulunmalı?',['Cihaz, kalibrasyon, yer, süre ve koşullar','Sadece en yüksek sayı','Yalnızca oda fotoğrafı'],0],['dB toplamı enerji kaynaklarında nasıl hesaplanır?',['Aritmetik ortalama','Enerji toplamı, logaritmik biçimde','Her zaman iki kat dB'],1]],
 digital_console:[['DCA genellikle ne yapar?',['Atanmış kanalların seviyelerini topluca kontrol eder','Her zaman fiziksel audio bus üretir','RF taraması yapar'],0],['Scene recall öncesi neden scope/safe kontrol edilir?',['İstenmeyen parametrelerin değişmesini önlemek için','Mikrofon frekansını değiştirmek için','Örnekleme hızını artırmak için'],0],['Show dosyası güvenli iş akışında nasıl yönetilir?',['Yedek alınır ve geri yükleme doğrulanır','Tek kopya tutulur','Dosya adı önemsizdir'],0]],
 speech_broadcast:[['Mix-minus ne sağlar?',['Uzak katılımcıya kendi sesinin geri beslemesini göndermemek','Tüm kanalları mute etmek','Loudness ölçmek'],0],['Konuşma kaydında ilk öncelik nedir?',['Mikrofon yerleşimi, oda ve temiz kayıt seviyesi','Her zaman ağır gürültü azaltma','Maksimum kompresyon'],0],['De-esser hangi sorunu hedefler?',['Sibilansın aşırılığını','Şebeke frekansını','Stereo fazını'],0]],
 maintenance:[['XLR mikrofon kablosu standart pin sayısı kaçtır?',['2','3','4'],1],['Arızalı kabloyu test etmeden önce ne yapılır?',['Güvenli şekilde sistemden ayırmak','Phantom açıkken uçları kısa devre etmek','Hoparlör çıkışına bağlamak'],0],['Hum/buzz teşhisinde doğru ilke hangisidir?',['Güvenli, adım adım izolasyon ve test','Toprak hattını rastgele kaldırmak','Şebeke panosunu yetkisiz açmak'],0]]
};


const extraCurriculumQuestions = {
 live_sound:[
  ['Compressor threshold neyi belirler?',['İşlemcinin ses dosyası adını','Sinyalin sıkıştırmaya girmeye başladığı seviyeyi','Mikrofonun polaritesini'],1],
  ['Make-up gain ne yapar?',['Sıkıştırma sonrası seviyeyi yükseltir','Attack süresini kapatır','Frekans taraması yapar'],0],
  ['Gain reduction göstergesi neyi gösterir?',['Uygulanan kazanç azaltımını','Mikrofon kapsül sıcaklığını','Kablo uzunluğunu'],0]
 ],
 rf_wireless:[
  ['Anten dağıtıcı seçerken ne kontrol edilir?',['Bant uyumu, port izolasyonu ve üretici şartları','Yalnızca rengi','Sadece pil voltajı'],0],
  ['Intermodülasyon riski hangi durumda artabilir?',['Birbirine uyumsuz/koordinasyonsuz RF taşıyıcılarında','Konsol faderları kapalıyken','XLR pin sayısı üçken'],0],
  ['IEM RF planında ne yapılmalıdır?',['Verici ve alıcıların uyumlu bantları koordine edilir','Tüm vericiler aynı frekansa konur','Antenler metal kutuya kapatılır'],0]
 ],
 pa_system:[
  ['Crossover ayarı neyi yönetir?',['Frekans bantlarının sistem bileşenlerine dağıtımını','Mikrofonun kayıt dosya adını','Kablosuz pil durumunu'],0],
  ['Sub polaritesi neden kontrol edilir?',['Crossover bölgesindeki birleşim ve iptalleri etkileyebildiği için','Dijital dosya boyutunu azaltmak için','Sahne ışığını eşlemek için'],0],
  ['Line array kapsamı hangi verilerle doğrulanır?',['Üretici verisi, geometri ve sahada ölçümle','Sadece kabin rengiyle','Yalnızca toplam watt sayısıyla'],0]
 ],
 studio_post:[
  ['Attack çok hızlı olduğunda ne olabilir?',['Transient başlangıcı bastırılabilir','Sample rate otomatik iki katına çıkar','Stereo dosya mono olur'],0],
  ['Noise floor neyi ifade eder?',['İstenen sinyal dışındaki arka plan gürültü seviyesini','Dosya adındaki karakter sayısını','EQ merkez frekansını'],0],
  ['De-esser hangi prensiple çalışır?',['Sibilans bandını algılayıp kontrollü azaltarak','Tüm basları kaldırarak','Stereo kanalları geciktirerek'],0]
 ],
 spl_acoustics:[
  ['dB SPL ölçümünde mikrofon kalibrasyonu neden önemlidir?',['Mutlak ses basıncı seviyesinin güvenilirliği için','FFT boyutunu seçmek için tek başına','Dosyayı MP3 yapmak için'],0],
  ['Ters kare yasası yaklaşımı hangi koşulda daha uygundur?',['Serbest alana yakın, noktasal kaynak varsayımında','Her odada ve her array konfigürasyonunda','Yalnızca kulaklıkla dinlerken'],0],
  ['RT60 hangi özelliği tanımlar?',['Ses enerjisinin 60 dB azalması için tahmini süreyi','Hoparlörün maksimum wattını','Mikrofonun RF kanalını'],0]
 ],
 digital_console:[
  ['Pre-fader AUX ne anlama gelir?',['Gönderim seviyesinin kanal faderından bağımsız olması','Her zaman post-EQ olması garantisi','DCA grubunun fiziksel çıkış olması'],0],
  ['PFL ne için kullanılır?',['Kanalı ana miks dışında ön dinlemek için','Hoparlör polaritesini çevirmek için','RF taraması başlatmak için'],0],
  ['Scene recall öncesi hangi adım güvenlidir?',['Recall scope ve safe parametrelerini kontrol etmek','Tüm çıkışları maksimuma almak','Yedeği silmek'],0]
 ],
 speech_broadcast:[
  ['Limiter ve compressor arasındaki temel fark genellikle nedir?',['Limiter daha yüksek oranlarla tepe seviyelerini daha sıkı sınırlar','Limiter sadece pan kontrolüdür','Compressor yalnızca stereo dosyada çalışır'],0],
  ['Room tone neden kaydedilir?',['Kurgu ve gürültü değerlendirmesi için oda arka planını belgelemek','Mikrofon frekansını değiştirmek','Kompresör ratio değerini ölçmek'],0],
  ['Loudness hedefi hangi kritere göre belirlenir?',['Teslim standardı ve platform şartlarına','Her zaman tek evrensel LUFS değerine','Dosyanın süresine tek başına'],0]
 ],
 maintenance:[
  ['XLR kablosunda pin 1 genel olarak ne taşır?',['Ekran/şase bağlantısı','Sağ kanal sinyali','Phantom anahtarı'],0],
  ['Phantom power açıkken kablo sökmeden önce ne yapılır?',['Güvenli prosedüre göre phantom kapatılır ve seviye düşürülür','Kablo uçları kısa devre edilir','Hoparlör çıkışı bağlanır'],0],
  ['Kablo arızasında ilk güvenli adım hangisidir?',['Sistemi güvenli duruma alıp kabloyu test cihazıyla kontrol etmek','Yük altındayken konnektörü açmak','Toprak pinini kesmek'],0]
 ]
};
for (const [track, questions] of Object.entries(extraCurriculumQuestions)) curriculumQuizBank[track].push(...questions);

function api() { return window.pywebview && window.pywebview.api ? window.pywebview.api : null; }
function enqueueRtaCommand(task){const next=rtaCommandQueue.then(task,task);rtaCommandQueue=next.catch(()=>{});return next;}
function setStatus(message) { $('footerStatus').textContent = message; $('connectionText').textContent = message; }
function fmt(value, digits=2) { return Number(value).toLocaleString('tr-TR',{minimumFractionDigits:digits,maximumFractionDigits:digits}); }
function safeText(value) { return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function downloadBlob(blob, filename) { const url=URL.createObjectURL(blob); const a=document.createElement('a');a.href=url;a.download=filename;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1500); }
function setPage(route) {
  if (!routes[route]) route='home';
  if (!appAuthorized && currentRole !== 'owner' && route !== 'account') route='account';
  if (activeRoute==='rta' && route!=='rta') stopRta();
  if (activeRoute==='wavelab' && route!=='wavelab') window.StagepulseWaveLabStop?.();
  activeRoute=route;
  setMobileMenu(false);
  document.querySelectorAll('.page').forEach(page=>page.classList.toggle('active',page.dataset.page===route));
  if (route==='wavelab') window.requestAnimationFrame(()=>window.StagepulseWaveLabRefresh?.());
  document.querySelectorAll('.nav-item').forEach(btn=>btn.classList.toggle('active',btn.dataset.route===route));
  $('pageHeading').textContent=routes[route];
  if (route==='docs') loadDocs();
  if (route==='student') { ensureProfilesLoaded().catch(()=>{}); refreshProfiles(); }
  if (route==='checklists') renderChecklist();
  if (route==='cues') renderCueRows();
  if (route==='rta') { drawRtaPlaceholder(); refreshRtaDevices(); }
  if (route==='acoustics') requestAnimationFrame(()=>{try{drawSplCoverageMaps();}catch(err){const el=$('splMapSummary');if(el)el.textContent='Harita hesaplanamadı: '+err.message;}});
  if (route==='settings') loadAppInfo();
  if (route==='account') refreshAccountUi();
  if (route==='student') { renderStudentModules(); if (currentRole==='student') refreshStudentProgress().catch(()=>{}); }
  if (route==='pdf') { loadStudentPdfs(); setStatus('Öğrenci PDF kitaplığı aynı uygulama penceresinde.'); }
  if (route==='curriculum') { loadCurriculumWorkshop().catch(err=>{const el=$('curriculumTrackDetails');if(el)el.textContent='Eğitim kataloğu yüklenemedi: '+err.message;}); }
  if (route==='frequency') setStatus('Frekans Bulucu: tamamen yerel.');
  if (route==='mixer') renderTracks();
}
document.addEventListener('click', e => { const btn=e.target.closest('[data-route]'); if(btn) setPage(btn.dataset.route); });
function setMobileMenu(open){
 document.body.classList.toggle('mobile-menu-open',!!open);
 const toggle=$('mobileMenuToggle');
 if(toggle)toggle.setAttribute('aria-expanded',String(!!open));
}
$('mobileMenuToggle')?.addEventListener('click',()=>setMobileMenu(!document.body.classList.contains('mobile-menu-open')));
$('mobileMenuClose')?.addEventListener('click',()=>setMobileMenu(false));
$('mobileMenuBackdrop')?.addEventListener('click',()=>setMobileMenu(false));
document.addEventListener('keydown',e=>{if(e.key==='Escape')setMobileMenu(false);});

window.addEventListener('online',()=>{ $('runtimeBadge').innerHTML='<i></i>İnternet erişimi var'; setStatus('İnternet erişimi var · yerel araçlar çalışmaya devam ediyor'); });
window.addEventListener('offline',()=>{ $('runtimeBadge').innerHTML='<i></i>Çevrimdışı'; setStatus('Çevrimdışı · temel araçlar kullanılabilir'); });

async function loadCurriculumWorkshop(){
 if(!curriculumCatalog){const r=await fetch('/egitim_paketleri/stagepulse_egitim_katalogu_v1.json');if(!r.ok)throw new Error('Katalog HTTP '+r.status);curriculumCatalog=await r.json();}
 const sel=$('curriculumTrackSelect'); if(!sel)return;
 if(!sel.dataset.bound){sel.dataset.bound='1';sel.addEventListener('change',renderCurriculumWorkshop);$('saveCurriculumPractice').addEventListener('click',saveCurriculumPractice);$('curriculumQuizButton').addEventListener('click',renderCurriculumQuiz);}
 renderCurriculumWorkshop();
}
function renderCurriculumWorkshop(){
 const id=$('curriculumTrackSelect').value, track=curriculumCatalog?.tracks?.find(x=>x.id===id); if(!track)return;
 const saved=(studentData.practiceTasks||{})[id]||{};
 $('curriculumTrackDetails').innerHTML=`<h3>${safeText(track.name)}</h3><p>${safeText(track.audience)}</p><strong>Modüller</strong><ol>${track.modules.map(x=>`<li>${safeText(x)}</li>`).join('')}</ol><strong>Uygulama görevleri</strong><div class="checklist-items">${track.practicals.map((x,i)=>`<label class="check-item"><input type="checkbox" data-practice-task="${i}" ${saved[i]?'checked':''}><span>${safeText(x)}</span></label>`).join('')}</div><div class="notice"><strong>Usta onay kapısı</strong><span>${safeText(track.master_gate)}</span></div>`;
 $('curriculumEvidence').value=saved.evidence||'';
}
async function saveCurriculumPractice(){
 const id=$('curriculumTrackSelect').value;studentData.practiceTasks=studentData.practiceTasks||{};const checks={};$('curriculumTrackDetails').querySelectorAll('[data-practice-task]').forEach(x=>checks[x.dataset.practiceTask]=x.checked);checks.evidence=$('curriculumEvidence').value.trim();studentData.practiceTasks[id]=checks;
 if(activeStudent){try{await saveStudentProfile(false);$('curriculumTrackDetails').insertAdjacentHTML('beforeend','<p class="feedback">Kişisel çalışma profiline kaydedildi.</p>');}catch(e){$('curriculumTrackDetails').insertAdjacentHTML('beforeend',`<p class="feedback">Yerel profil kaydı başarısız: ${safeText(e.message)}</p>`);}}
 else {$('curriculumTrackDetails').insertAdjacentHTML('beforeend','<p class="feedback">Bu oturumda tutuldu. Kalıcı yerel kayıt için Öğrenci ilerlemesi bölümünden profil oluşturup kaydet.</p>');}
}
function renderCurriculumQuiz(){
 const id=$('curriculumTrackSelect').value, pool=curriculumQuizBank[id]||[], qs=pool.slice().sort(()=>Math.random()-.5).slice(0,Math.min(5,pool.length));const host=$('curriculumQuizArea');if(!qs.length){host.textContent='Bu dal için test sorusu bulunamadı.';host.classList.remove('hidden');return;}
 host.classList.remove('hidden');host.innerHTML=`<h3>${safeText($('curriculumTrackSelect').selectedOptions[0].textContent)} · Bilgi testi</h3><form id="curriculumQuizForm">${qs.map((q,i)=>`<fieldset class="panel"><legend>${i+1}. ${safeText(q[0])}</legend>${q[1].map((a,j)=>`<label class="check-item"><input type="radio" name="cq${i}" value="${j}" required><span>${safeText(a)}</span></label>`).join('')}</fieldset>`).join('')}<button class="btn btn-gold" type="submit">Testi değerlendir</button></form><div id="curriculumQuizResult" class="report-box">Üç soruyu yanıtla. Bu test yalnızca ön değerlendirmedir.</div>`;
 host.querySelector('#curriculumQuizForm').addEventListener('submit',e=>{e.preventDefault();let score=0;qs.forEach((q,i)=>{const v=host.querySelector(`input[name="cq${i}"]:checked`);if(v&&Number(v.value)===q[2])score++;});const pass=score===qs.length;host.querySelector('#curriculumQuizResult').textContent=`Sonuç: ${score}/${qs.length}. ${pass?'Bu kısa ön testi geçtin. Uygulama sınavı ve öğretmen onayı yine gereklidir.':'Başarısız maddeleri ders kılavuzundan tekrar et ve testi yeniden çöz.'}`;const again=document.createElement('button');again.className='btn btn-secondary';again.type='button';again.textContent='Yeni soru seti';again.addEventListener('click',renderCurriculumQuiz);host.querySelector('#curriculumQuizResult').after(again);});
}
function runInitStep(name, initialize, errors){
  try { initialize(); }
  catch(err) {
    const message=(err&&err.message)||String(err);
    console.error('Stagepulse başlatma hatası ['+name+']:',err);
    errors.push(name+': '+message);
  }
}
function initShell(){
  const initErrors=[];
  runInitStep('Ana ekran',()=>{
    const wave=$('heroWave');
    if(wave&&!wave.children.length){for(let i=0;i<47;i++){const b=document.createElement('span');b.style.height=(8+Math.abs(Math.sin(i*.47)*Math.cos(i*.17))*34)+'px';wave.appendChild(b);}}
    $('runtimeBadge').innerHTML='<i></i>'+(navigator.onLine?'Yerel motor':'Çevrimdışı');
    setStatus('Yerel çalışma alanı açılıyor…');
  },initErrors);
  const initSteps=[
    ['Hesaplayıcılar',initCalculators],['SPL / alan planı',initAcoustics],
    ['Kulak eğitimi',initEarTraining],['Ses katmanı atölyesi',initMixer],
    ['Canlı RTA arayüzü',initRtaControls],['Akustik sistem analizi',initAcousticAnalyzer],['Canlı stereo Transfer Function',initLiveTfControls],['WAV analizi',initWav],
    ['LUFS normalizasyonu',initLufs],['Cue notları',initCues],
    ['Kontrol listeleri',initChecklists],['Öğrenci profilleri',initStudent],
    ['Ders kılavuzları',initDocs],['AI asistanı',initAssistant],
    ['Hesap ve lisans',initAccount],['Ayarlar',initSettings],['Stagepulse özgün yerel araçları',()=>window.StagepulseFirstPartyTools.initAll()]
  ];
  // İlk pencere çizildikten sonra her başlatma adımını ayrı görevde çalıştır.
  // Düşük güçlü bilgisayarlarda tek uzun JS görevi Windows'un "Yanıt vermiyor"
  // durumuna geçmesini önler; bir özellik hata verse bile diğerleri başlatılır.
  const runNext=(index)=>{
    if(index>=initSteps.length){
      runInitStep('Ana sayfa göstergeleri',updateHomeMetrics,initErrors);
      if(initErrors.length)setStatus('Bazı özellikler başlatılamadı; diğer menüler çalışmaya devam ediyor. '+initErrors.join(' | ').slice(0,360));
      else setStatus('Yerel çalışma alanı hazır.');
      return;
    }
    const [name,initialize]=initSteps[index];
    runInitStep(name,initialize,initErrors);
    window.setTimeout(()=>runNext(index+1),12);
  };
  runInitStep('Masaüstü bağlantısı',()=>{
    if(api()){apiReady=true;initializeNativeData();}
    else $('settingsInfo').textContent='Yerel geliştirme/önizleme modu. Dosya seçme, profil saklama ve masaüstü normalizasyonu ana uygulama köprüsü olmadan devre dışıdır.';
  },initErrors);
  if(window.requestAnimationFrame)window.requestAnimationFrame(()=>window.setTimeout(()=>runNext(0),0));
  else window.setTimeout(()=>runNext(0),30);
}
window.addEventListener('error',event=>{const message=(event.error&&event.error.message)||event.message||'Bilinmeyen JavaScript hatası';console.error('Stagepulse yakalanan JavaScript hatası:',event.error||event.message);if($('footerStatus'))setStatus('Arayüz hatası: '+String(message).slice(0,180));});
window.addEventListener('unhandledrejection',event=>{const reason=event.reason,message=(reason&&reason.message)||String(reason||'Bilinmeyen asenkron hata');console.error('Stagepulse yakalanan asenkron hata:',reason);if($('footerStatus'))setStatus('Arka plan işlemi başarısız: '+String(message).slice(0,180));});

window.addEventListener('DOMContentLoaded',initShell);
window.addEventListener('pywebviewready',()=>{apiReady=true;initializeNativeData();});
async function initializeNativeData(){
  if(nativeInitStarted || !api())return;
  nativeInitStarted = true;
  setPage('account');
  try { await ensureProfilesLoaded(); }
  catch(err) { setStatus('Profil deposu okunamadı. Veriler sıfırlanmadı: '+err.message); }

  // Ağ yanıtı yerel araçların açılmasını bekletmez; geç yanıtlar arka planda uygulanır.
  if (typeof api().auth_restore === 'function') {
    const authPromise = api().auth_restore().catch(err=>{
      setStatus('Kayıtlı hesap çevrimiçi doğrulanamadı; yerel araçlar kullanılabilir. ' + String(err.message || err).slice(0, 160));
      return null;
    });
    Promise.race([authPromise,new Promise(resolve=>setTimeout(()=>resolve(null),3000))]).then(restored=>{
      if(restored&&restored.authenticated&&restored.context)applyAccountContext(restored.context);
    });
  }
  if (typeof api().app_info === 'function') {
    api().app_info().then(info=>{
      const cached=info&&info.cached_license;
      if(cached&&cached.active)appAuthorized=true;
      if(licenseGatePending){licenseGatePending=false;setPage(appAuthorized?'home':'account');}
      refreshAccountUi();
    }).catch(()=>{});
  }
  loadAppInfo();
  refreshAccountUi();
}

// --- Teknik hesaplar ---
function val(id){return Number($(id).value)}
const AcousticMath=window.StagepulseAcousticMath;
function showCalcError(id,err){$(id).textContent='Hesaplanamadı: '+(err&&err.message||String(err));}
function initCalculators(){
 $('fromDbU').addEventListener('click',()=>{try{const d=val('dbuInput');if(!Number.isFinite(d)||Math.abs(d)>200)throw new Error('dBu -200 ile +200 arasında olmalı.');$('vrmsInput').value=(.775*Math.pow(10,d/20)).toPrecision(6);$('dbuResult').textContent=`${fmt(d,1)} dBu = ${fmt(val('vrmsInput'),4)} Vrms`;}catch(e){showCalcError('dbuResult',e);}});
 $('fromVrms').addEventListener('click',()=>{try{const v=val('vrmsInput');if(!(v>0)||v>1e8)throw new Error('Vrms 0 ile 100.000.000 arasında olmalı.');const d=20*Math.log10(v/.775);$('dbuInput').value=d.toFixed(3);$('dbuResult').textContent=`${fmt(v,4)} Vrms = ${fmt(d,2)} dBu`;}catch(e){showCalcError('dbuResult',e);}});
 $('sumDb').addEventListener('click',()=>{try{const a=val('dbA'),b=val('dbB');if(!Number.isFinite(a)||!Number.isFinite(b)||Math.abs(a)>300||Math.abs(b)>300)throw new Error('Her iki seviye -300 ile +300 dB arasında sonlu olmalı.');$('dbSumResult').textContent=fmt(AcousticMath.dbSum([a,b]),2)+' dB';}catch(e){showCalcError('dbSumResult',e);}});
 $('calcDelay').addEventListener('click',()=>{try{const d=val('distanceM'),c=val('soundSpeed');if(!Number.isFinite(d)||d<0||d>10000||!Number.isFinite(c)||c<250||c>380)throw new Error('Mesafe 0-10000 m, ses hızı 250-380 m/s olmalı.');$('delayResult').textContent=fmt(d/c*1000,2)+' ms';}catch(e){showCalcError('delayResult',e);}});
 $('calcEndfire').addEventListener('click',()=>{try{const v=AcousticMath.wavelength(val('efFreq'),val('efSpeed'));$('endfireResult').textContent=`λ = ${fmt(v.wavelengthM,3)} m · λ/4 = ${fmt(v.quarterWaveM,3)} m · λ/2 = ${fmt(v.halfWaveM,3)} m · periyot = ${fmt(v.periodMs,3)} ms. ${v.note}`;}catch(e){showCalcError('endfireResult',e);}});
 const ohm=(parallel)=>{try{const a=val('ohmA'),b=val('ohmB');if(!(a>0&&b>0)||a>100000||b>100000)throw new Error('Her iki empedans 0-100000 Ω arasında pozitif olmalı.');const r=parallel?(a*b)/(a+b):a+b;$('ohmResult').textContent=`${parallel?'Paralel':'Seri'} eşdeğer: ${fmt(r,2)} Ω (ideal direnç varsayımı)`;}catch(e){showCalcError('ohmResult',e);}};
 $('ohmSeries').addEventListener('click',()=>ohm(false));$('ohmParallel').addEventListener('click',()=>ohm(true));
 $('calcBpm').addEventListener('click',()=>{const bpm=val('bpm'),div=val('noteDivision');$('bpmResult').textContent=Number.isFinite(bpm)&&bpm>=1&&bpm<=400&&div>0?fmt(60000/bpm*div,2)+' ms':'BPM 1-400, nota bölümü pozitif olmalı.';});
 $('calcNote').addEventListener('click',()=>{const n=val('noteName'),a=val('referenceA');if(!Number.isInteger(n)||n<0||n>127||!Number.isFinite(a)||a<400||a>480){$('noteResult').textContent='MIDI numarası 0-127 tam sayı, referans A4 400-480 Hz olmalı.';return;}const hz=a*Math.pow(2,(n-69)/12);const noteNames=['C','C♯','D','D♯','E','F','F♯','G','G♯','A','A♯','B'];$('noteResult').textContent=`${noteNames[n%12]}${Math.floor(n/12)-1} · ${fmt(hz,2)} Hz`;});
 $('calcModes').addEventListener('click',()=>{try{const modes=AcousticMath.axialModes(val('roomLength'),val('roomWidth'),val('roomHeight'),343,4);$('roomResult').textContent='Dikdörtgen oda için yaklaşık eksenel modlar (ölçüm değil):\n'+modes.map(m=>`${fmt(m.frequencyHz,1)} Hz · ${m.axis} · n=${m.order} · ${fmt(m.dimensionM,2)} m`).join('\n');}catch(e){showCalcError('roomResult',e);}});
}

function initAcoustics(){
 let lastFarthestDistance=null,lastAudienceVolume=null,lastEquivalentAbsorption=null;
 const redrawMap=()=>{try{drawSplCoverageMaps();}catch(err){const el=$('splMapSummary');if(el)el.textContent='Harita hesaplanamadı: '+err.message;}};
 ['splReferenceLevel','splReferenceDistance','splSourceCount','audienceWidth','audienceDepth','speakerCoverageAngle'].forEach(id=>$(id).addEventListener('input',redrawMap));
 window.addEventListener('resize',()=>{if($('splMap2d'))redrawMap();});

 $('useFarDistance').addEventListener('click',()=>{if(lastFarthestDistance!==null){$('splTargetDistance').value=lastFarthestDistance.toFixed(2);setStatus('Alan planındaki uzak köşe mesafesi SPL hedef mesafesine aktarıldı; varsayımları yeniden kontrol et.');}});
 $('useAudienceVolume').addEventListener('click',()=>{if(lastAudienceVolume!==null){$('rt60Volume').value=lastAudienceVolume.toFixed(1);setStatus('Alan planındaki hacim Sabine hesabına aktarıldı; soğurma alanını doğrula.');}});
 $('calcSplDistance').addEventListener('click',()=>{try{const r=AcousticMath.distanceSpl(val('splReferenceLevel'),val('splReferenceDistance'),val('splTargetDistance'),val('splSourceCount'));$('splDistanceResult').textContent=`Tek kaynak kestirimi: ${fmt(r.singleSourceDbSpl,2)} dB SPL\n${val('splSourceCount')} eşit kaynak için enerji toplamı kestirimi: ${fmt(r.combinedEnergyEstimateDbSpl,2)} dB SPL\nMesafe düzeltmesi: ${fmt(r.distanceCorrectionDb,2)} dB · kaynak toplamı: +${fmt(r.sourceCountEnergyCorrectionDb,2)} dB\nVarsayımlar: ${r.assumptions.join(' ')}`;redrawMap();}catch(e){showCalcError('splDistanceResult',e);}});
 $('calcAudienceArea').addEventListener('click',()=>{try{const r=AcousticMath.areaPlan(val('audienceWidth'),val('audienceDepth'),val('audienceHeight'),val('speakerCoverageAngle'));lastFarthestDistance=r.farthestCornerDistanceM;lastAudienceVolume=r.volumeM3;$('useFarDistance').disabled=false;$('useAudienceVolume').disabled=false;$('audienceAreaResult').textContent=`Alan: ${fmt(r.areaM2,1)} m²\nYaklaşık hacim: ${fmt(r.volumeM3,1)} m³\nÖn kenar merkezi kabulüyle uzak köşe: ${fmt(r.farthestCornerDistanceM,2)} m\nArka kenarda ideal açı genişliği: ${fmt(r.idealWidthAtRearM,2)} m\nGeometrik genişlik oranı: ${fmt(r.idealWidthCoveragePercent,1)}%\n${r.assumptions.join(' ')}`;redrawMap();}catch(e){showCalcError('audienceAreaResult',e);}});
 $('calcRt60').addEventListener('click',()=>{try{const r=AcousticMath.sabineRt60(val('rt60Volume'),val('rt60Absorption'));$('rt60Result').textContent=`Yaklaşık T60: ${fmt(r.rt60Seconds,2)} saniye\nT60 ≈ 0,161 × ${fmt(r.volumeM3,1)} / ${fmt(r.equivalentAbsorptionM2,1)}. ${r.note}`;}catch(e){showCalcError('rt60Result',e);}});
 $('calcAbsorption').addEventListener('click',()=>{try{const r=AcousticMath.equivalentAbsorption(val('absWidth'),val('absDepth'),val('absHeight'),val('absFloorAlpha'),val('absCeilingAlpha'),val('absLongWallAlpha'),val('absShortWallAlpha'),val('absFrequency'));lastEquivalentAbsorption=r;$('absorptionResult').textContent=`Zemin: ${fmt(r.areasM2.floor,1)} m² × α ${fmt(r.coefficients.floor,2)} = ${fmt(r.contributionsM2Sabin.floor,1)} m² sabin\nTavan: ${fmt(r.areasM2.ceiling,1)} m² × α ${fmt(r.coefficients.ceiling,2)} = ${fmt(r.contributionsM2Sabin.ceiling,1)} m² sabin\nUzun duvarlar: ${fmt(r.areasM2.longWalls,1)} m² × α ${fmt(r.coefficients.longWalls,2)} = ${fmt(r.contributionsM2Sabin.longWalls,1)} m² sabin\nKısa duvarlar: ${fmt(r.areasM2.shortWalls,1)} m² × α ${fmt(r.coefficients.shortWalls,2)} = ${fmt(r.contributionsM2Sabin.shortWalls,1)} m² sabin\nEşdeğer toplam A @ ${fmt(r.selectedFrequencyHz,0)} Hz: ${fmt(r.equivalentAbsorptionM2,2)} m² sabin · Hacim: ${fmt(r.volumeM3,1)} m³\n${r.note}`;$('useAbsorptionResult').disabled=false;}catch(e){lastEquivalentAbsorption=null;$('useAbsorptionResult').disabled=true;showCalcError('absorptionResult',e);}});
 $('useAbsorptionResult').addEventListener('click',()=>{if(!lastEquivalentAbsorption)return;$('rt60Volume').value=lastEquivalentAbsorption.volumeM3.toFixed(2);$('rt60Absorption').value=lastEquivalentAbsorption.equivalentAbsorptionM2.toFixed(2);setStatus('Yüzeylerden hesaplanan hacim ve eşdeğer soğurma Sabine alanına aktarıldı. Katsayıları doğrula.');});
 $('calcPressureSpl').addEventListener('click',()=>{try{$('pressureSplResult').textContent=`${fmt(val('pressurePa'),6)} Pa RMS = ${fmt(AcousticMath.pressureToSpl(val('pressurePa')),2)} dB SPL (referans 20 µPa)`;}catch(e){showCalcError('pressureSplResult',e);}});
 $('calcSplPressure').addEventListener('click',()=>{try{$('splPressureResult').textContent=`${fmt(val('pressureSplLevel'),2)} dB SPL = ${fmt(AcousticMath.splToPressure(val('pressureSplLevel')),6)} Pa RMS (referans 20 µPa)`;}catch(e){showCalcError('splPressureResult',e);}});
 $('calcExposure').addEventListener('click',()=>{try{
   const segments=[];
   for(let i=1;i<=3;i++){
     const levelEl=$('exposureLevel'+(i===1?'':i)),minutesEl=$('exposureMinutes'+(i===1?'':i));
     const levelText=levelEl.value.trim(),minutesText=minutesEl.value.trim();
     if(i>1&&!levelText&&!minutesText)continue;
     if(!levelText||!minutesText)throw new Error(`Blok ${i}: LAeq ve süre ikisi birlikte girilmeli.`);
     segments.push({levelDba:Number(levelText),durationMinutes:Number(minutesText)});
   }
   const r=AcousticMath.nioshDose(segments);
   const detail=r.segments.map((x,i)=>`Blok ${i+1}: ${fmt(x.levelDba,1)} dBA · ${fmt(x.durationMinutes,1)} dk · blok dozu ${fmt(x.dosePercent,1)}%`).join('\n');
   $('exposureResult').textContent=`Toplam süre: ${fmt(r.totalDurationMinutes,1)} dakika\nToplam hesaplanan NIOSH referans dozu: ${fmt(r.dosePercent,1)}%\n${detail}\n${r.referenceDoseReached?'UYARI: Birikimli NIOSH mesleki referans dozu %100’e ulaştı veya aştı. Maruziyeti azalt ve yetkili İSG uzmanına danış; bu sonuç mevzuat uygunluk kararı değildir.\n':''}${r.note}`;
 }catch(e){showCalcError('exposureResult',e);}});
 redrawMap();
}

// --- SPL görselleştirme: hesaplanan sade model, gerçek array simülasyonu değildir ---
function splColor(level,low=50,high=110){
 const palette=[[25,42,122],[0,111,190],[0,174,187],[65,180,110],[237,222,45],[244,137,35],[207,39,34]];
 const t=Math.max(0,Math.min(1,(level-low)/Math.max(.001,high-low)))*(palette.length-1),i=Math.min(palette.length-2,Math.floor(t)),f=t-i;
 const rgb=palette[i].map((v,k)=>Math.round(v+(palette[i+1][k]-v)*f));return `rgb(${rgb[0]},${rgb[1]},${rgb[2]})`;
}
function splMapParams(){
 const width=val('audienceWidth'),depth=val('audienceDepth');
 if(!Number.isFinite(width)||width<0.1||width>1000||!Number.isFinite(depth)||depth<0.1||depth>1000)throw new Error('Alan genişliği ve derinliği 0,1–1000 m aralığında olmalı.');
 const refLevel=val('splReferenceLevel'),refDistance=val('splReferenceDistance');
 if(!Number.isFinite(refLevel)||refLevel < -20||refLevel>160)throw new Error('Referans seviye -20–160 dB SPL aralığında olmalı.');
 if(!Number.isFinite(refDistance)||refDistance<=0||refDistance>10000)throw new Error('Referans mesafe 0–10000 m aralığında pozitif olmalı.');
 if(!Number.isFinite(width)||!Number.isFinite(depth))throw new Error('Alan boyutları geçerli sayısal değer olmalı.');
 return {width,depth,refLevel,refDistance};
}
function splMapLevel(x,y,p){const r=Math.max(p.refDistance,Math.hypot(x,y));return p.refLevel-20*Math.log10(r/p.refDistance);}
function prepareHiDPICanvas(canvas,minW=520,minH=300){
 const rect=canvas.getBoundingClientRect(),dpr=Math.max(1,window.devicePixelRatio||1),w=Math.max(minW,rect.width||minW),h=Math.max(minH,Number(canvas.getAttribute('height'))||minH);
 if(canvas.width!==Math.round(w*dpr)||canvas.height!==Math.round(h*dpr)){canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);}const ctx=canvas.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);return {ctx,w,h};
}
function drawSplCoverageMaps(){
 const c2=$('splMap2d'),c3=$('splMap3d');if(!c2||!c3)return;
 const p=splMapParams();const lvals=[];for(let j=0;j<55;j++){const y=(j+.5)/55*p.depth;for(let i=0;i<72;i++){const x=((i+.5)/72-.5)*p.width;lvals.push(splMapLevel(x,y,p));}}
 const min=Math.floor(Math.min(...lvals)/5)*5,max=Math.ceil(Math.max(...lvals)/5)*5;const span=Math.max(1,max-min);
 $('splMapRange').textContent=`${fmt(min,0)}–${fmt(max,0)} dB SPL`;
 // 2D plan heat map; values are evaluated from the stated free-field point-source model.
 let q=prepareHiDPICanvas(c2,560,330),ctx=q.ctx,w=q.w,h=q.h;ctx.fillStyle='#0b1016';ctx.fillRect(0,0,w,h);
 const pad={l:46,r:72,t:32,b:48},pw=w-pad.l-pad.r,ph=h-pad.t-pad.b;
 ctx.fillStyle='#111a22';ctx.fillRect(pad.l,pad.t,pw,ph);
 const nx=70,ny=50,cw=pw/nx,ch=ph/ny;
 for(let j=0;j<ny;j++)for(let i=0;i<nx;i++){
  const x=((i+.5)/nx-.5)*p.width,y=(j+.5)/ny*p.depth,L=splMapLevel(x,y,p);
  ctx.fillStyle=splColor(L,min,max);ctx.fillRect(pad.l+i*cw,pad.t+j*ch,Math.ceil(cw+.5),Math.ceil(ch+.5));
 }
 ctx.strokeStyle='rgba(255,255,255,.25)';ctx.lineWidth=1;
 for(let m=0;m<=4;m++){const xx=pad.l+pw*m/4;ctx.beginPath();ctx.moveTo(xx,pad.t);ctx.lineTo(xx,pad.t+ph);ctx.stroke();ctx.fillStyle='#bac4d1';ctx.font='10px Segoe UI';ctx.textAlign='center';ctx.fillText(`${fmt(-p.width/2+p.width*m/4,1)} m`,xx,h-28);}
 for(let m=0;m<=5;m++){const yy=pad.t+ph*m/5;ctx.beginPath();ctx.moveTo(pad.l,yy);ctx.lineTo(pad.l+pw,yy);ctx.stroke();ctx.textAlign='right';ctx.fillStyle='#bac4d1';ctx.fillText(`${fmt(p.depth*m/5,0)} m`,pad.l-8,yy+3);}
 ctx.fillStyle='#252a30';ctx.fillRect(pad.l-8,pad.t-19,pw+16,16);ctx.fillStyle='#e7c778';ctx.textAlign='center';ctx.font='bold 10px Segoe UI';ctx.fillText('SAHNE / PA KAYNAĞI (noktasal model)',pad.l+pw/2,pad.t-7);
 ctx.fillStyle='#dce2e9';ctx.textAlign='left';ctx.font='10px Segoe UI';ctx.fillText('dB SPL',pad.l+pw+12,pad.t+2);
 const grad=ctx.createLinearGradient(0,pad.t,0,pad.t+ph);for(let v=0;v<=1;v+=.1)grad.addColorStop(v,splColor(max-v*span,min,max));ctx.fillStyle=grad;ctx.fillRect(pad.l+pw+12,pad.t+10,15,ph-10);
 [max,max-span*.25,max-span*.5,max-span*.75,min].forEach((v,i)=>{const yy=pad.t+10+(ph-10)*i/4;ctx.fillStyle='#cad3de';ctx.fillText(fmt(v,0),pad.l+pw+32,yy+4);});
 // 3D isometric view of the same numeric surface: the height is a plot axis, not physical room height.
 q=prepareHiDPICanvas(c3,560,330);ctx=q.ctx;w=q.w;h=q.h;ctx.fillStyle='#0b1016';ctx.fillRect(0,0,w,h);
 const cols=42,rows=26,baseY=h-44,centerX=w*.48,scaleX=Math.min(w*.55/p.width,12),depthY=Math.min(h*.5/p.depth,6.2),skewX=Math.min(w*.2/p.depth,3.0),zScale=Math.min(2.2,180/span);
 const point=(ix,iy)=>{const xn=ix/cols,yn=iy/rows,xm=(xn-.5)*p.width,ym=yn*p.depth,L=splMapLevel(xm,ym,p);return {x:centerX+xm*scaleX+ym*skewX,y:baseY-ym*depthY-(L-min)*zScale,L};};
 // Draw back-to-front quads, keeping each patch in the exact same model as the plan map.
 for(let j=rows-1;j>=0;j--)for(let i=0;i<cols;i++){
  const pts=[point(i,j),point(i+1,j),point(i+1,j+1),point(i,j+1)];ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);for(let k=1;k<pts.length;k++)ctx.lineTo(pts[k].x,pts[k].y);ctx.closePath();const avg=pts.reduce((a,b)=>a+b.L,0)/4;ctx.fillStyle=splColor(avg,min,max);ctx.globalAlpha=.96;ctx.fill();ctx.globalAlpha=1;ctx.strokeStyle='rgba(8,12,18,.38)';ctx.lineWidth=.55;ctx.stroke();
 }
 ctx.fillStyle='#d9c080';ctx.font='bold 10px Segoe UI';ctx.textAlign='center';ctx.fillText('dB SPL / seviye yüzeyi',w*.5,17);
 ctx.fillStyle='#9daaba';ctx.font='10px Segoe UI';ctx.fillText(`Genişlik ${fmt(p.width,1)} m`,w*.27,h-14);ctx.fillText(`Derinlik ${fmt(p.depth,1)} m`,w*.74,h-14);
 const Lrear=splMapLevel(0,p.depth,p);$('splMapSummary').textContent=`Model: ${fmt(p.refLevel,1)} dB SPL @ ${fmt(p.refDistance,2)} m · uzak merkez ${fmt(Lrear,1)} dB SPL · ${fmt(p.width*p.depth,1)} m². İdeal noktasal kaynak, serbest alan ve mesafeyle 20 log kaybı varsayımı; gerçek array/oda tahmini değildir.`;
}

// --- Kulak eğitimi ---
function getAudioContext(){if(!audioContext){const AudioContextCtor=window.AudioContext||window.webkitAudioContext;if(typeof AudioContextCtor!=='function')throw new Error('Bu WebView ortamında Web Audio desteklenmiyor. WebView2 Runtime güncellenmeli.');audioContext=new AudioContextCtor();}return audioContext;}
const earFrequencies=[63,80,100,125,160,200,250,315,400,500,630,800,1000,1250,1600,2000,2500,3150,4000,5000,6300,8000];
const freqBands=[['20–80 Hz',20,80],['81–160 Hz',81,160],['161–315 Hz',161,315],['316–630 Hz',316,630],['631–1.25 kHz',631,1250],['1.26–2.5 kHz',1251,2500],['2.51–5 kHz',2501,5000],['5.01–12 kHz',5001,12000]];
function randomChoice(xs){return xs[Math.floor(Math.random()*xs.length)];}
function newEarQuestion(){earTarget=randomChoice(earFrequencies);earRound++;$('earRound').textContent='Tur '+earRound;$('earToneLabel').textContent='? Hz';$('earFeedback').textContent='Tonu dinle ve frekans aralığını seç.';$('earFeedback').className='feedback';const correct=freqBands.findIndex(b=>earTarget>=b[1]&&earTarget<=b[2]);let choices=[correct];while(choices.length<4){const n=Math.floor(Math.random()*freqBands.length);if(!choices.includes(n))choices.push(n);}choices.sort(()=>Math.random()-.5);$('earChoices').innerHTML='';choices.forEach(index=>{const b=freqBands[index],btn=document.createElement('button');btn.className='choice';btn.textContent=b[0];btn.dataset.band=index;btn.addEventListener('click',()=>answerEar(Number(btn.dataset.band),correct));$('earChoices').appendChild(btn);});}
async function playTone(freq,duration=1){const ctx=getAudioContext();if(ctx.state!=='running')await ctx.resume();const osc=ctx.createOscillator(),gain=ctx.createGain();osc.type='sine';osc.frequency.value=freq;gain.gain.setValueAtTime(0.0001,ctx.currentTime);gain.gain.linearRampToValueAtTime(.055,ctx.currentTime+.025);gain.gain.setValueAtTime(.055,ctx.currentTime+Math.max(.04,duration-.06));gain.gain.linearRampToValueAtTime(.0001,ctx.currentTime+duration);osc.connect(gain).connect(ctx.destination);osc.start();osc.stop(ctx.currentTime+duration+.02);}

function answerEar(chosen,correct){if($('earFeedback').dataset.answered===String(earRound))return;$('earFeedback').dataset.answered=String(earRound);earAnswered++;const ok=chosen===correct;if(ok)earCorrect++;document.querySelectorAll('#earChoices .choice').forEach(b=>{b.disabled=true;if(Number(b.dataset.band)===correct)b.classList.add('correct');else if(Number(b.dataset.band)===chosen)b.classList.add('wrong');});$('earFeedback').textContent=ok?'Doğru. Frekansın bulunduğu bölgeyi iyi ayırt ettin.':`Bu soru ${freqBands[correct][0]} aralığındaydı.`;$('earFeedback').className='feedback '+(ok?'good':'bad');$('earScore').textContent=`${earCorrect} / ${earAnswered}`;}
function initEarTraining(){
  // Web Audio is created only after a deliberate user click, never during app startup.
  $('playEarTone').addEventListener('click',async()=>{try{await playTone(earTarget,1.25);}catch(err){$('earFeedback').textContent='Ses başlatılamadı: '+(err.message||String(err));}});
  $('newEarTone').addEventListener('click',newEarQuestion);
  newEarQuestion();
  document.querySelectorAll('[data-eq]').forEach(btn=>btn.addEventListener('click',()=>{const answer=btn.dataset.eq;if($('eqFeedback').dataset.answered==='yes')return;const ok=answer===eqTarget;$('eqFeedback').dataset.answered='yes';$('eqFeedback').textContent=ok?'Doğru. Seçtiğin bölge A ve B arasında değişti.':('Bu örnekte değişen bölge: '+(eqTarget==='low'?'bas':eqTarget==='mid'?'orta frekans':eqTarget==='high'?'tiz':'belirgin değişim yok')+'.');$('eqFeedback').className='feedback '+(ok?'good':'bad');document.querySelectorAll('[data-eq]').forEach(b=>{b.disabled=true;if(b.dataset.eq===eqTarget)b.classList.add('correct');else if(b===btn)b.classList.add('wrong');});earAnswered++;if(ok)earCorrect++;$('earScore').textContent=earCorrect+' / '+earAnswered;}));
  document.getElementById('playEqA').addEventListener('click',async()=>{try{await playNoise(false);}catch(err){$('eqFeedback').textContent='Ses başlatılamadı: '+(err.message||String(err));}});
  document.getElementById('playEqB').addEventListener('click',async()=>{try{await playNoise(true);}catch(err){$('eqFeedback').textContent='Ses başlatılamadı: '+(err.message||String(err));}});
  $('newEqQuestion').addEventListener('click',newEqQuestion);
  newEqQuestion();
}

function newEqQuestion(){eqTarget=randomChoice(['low','mid','high','flat']);$('eqFeedback').dataset.answered='no';$('eqFeedback').textContent='A ve B örneklerini dinle, farkın bulunduğu bölgeyi seç.';$('eqFeedback').className='feedback';document.querySelectorAll('[data-eq]').forEach(b=>{b.disabled=false;b.classList.remove('correct','wrong');});const path=eqTarget==='low'?'M20 94 Q150 10 240 65 T580 80':eqTarget==='mid'?'M20 80 Q150 80 250 25 T400 80 T580 80':eqTarget==='high'?'M20 80 Q380 80 450 50 T580 25':'M20 80 Q140 80 210 80 T580 80';$('eqCurve').setAttribute('d',path);}
async function playNoise(isB){const ctx=getAudioContext();if(ctx.state!=='running')await ctx.resume();if(!eqBuffer){const noise=ctx.createBuffer(1,ctx.sampleRate*2,ctx.sampleRate),data=noise.getChannelData(0);let seed=23871;for(let i=0;i<data.length;i++){seed=(seed*16807)%2147483647;data[i]=(seed/1073741823.5)-1;}eqBuffer=noise;}const src=ctx.createBufferSource();src.buffer=eqBuffer;const gain=ctx.createGain();gain.gain.value=.10;src.connect(gain);if(isB&&eqTarget!=='flat'){const filter=ctx.createBiquadFilter();filter.type=eqTarget==='low'?'lowshelf':eqTarget==='high'?'highshelf':'peaking';filter.frequency.value=eqTarget==='low'?180:eqTarget==='high'?4200:1000;filter.Q.value=0.85;filter.gain.value=7;gain.connect(filter).connect(ctx.destination);}else gain.connect(ctx.destination);src.start();src.stop(ctx.currentTime+1.6);}



function drawAcousticChart(canvasId, frequencies, values, minValue, maxValue, unit) {
 const canvas=$(canvasId);if(!canvas||!Array.isArray(frequencies)||!Array.isArray(values)||frequencies.length!==values.length)return;
 const width=Math.max(320,Math.floor(canvas.getBoundingClientRect().width||640)),height=210,dpr=window.devicePixelRatio||1;
 canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);
 const ctx=canvas.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,width,height);
 ctx.fillStyle='#0c1117';ctx.fillRect(0,0,width,height);
 const left=54,right=12,top=12,bottom=29,plotW=width-left-right,plotH=height-top-bottom;
 ctx.font='10px Segoe UI,sans-serif';ctx.fillStyle='#9ba5b1';ctx.strokeStyle='#303944';ctx.lineWidth=1;
 for(let tick=0;tick<=4;tick++){const y=top+plotH*tick/4;ctx.beginPath();ctx.moveTo(left,y);ctx.lineTo(width-right,y);ctx.stroke();ctx.fillText((maxValue-(maxValue-minValue)*tick/4).toFixed(0)+unit,3,y+3);}
 const minF=Math.max(10,frequencies.find(v=>v>0)||20),maxF=frequencies[frequencies.length-1]||20000,logMin=Math.log10(minF),logMax=Math.log10(maxF);
 [20,50,100,200,500,1000,2000,5000,10000,20000].filter(v=>v>=minF&&v<=maxF).forEach(v=>{const x=left+(Math.log10(v)-logMin)/(logMax-logMin)*plotW;ctx.beginPath();ctx.moveTo(x,top);ctx.lineTo(x,top+plotH);ctx.stroke();ctx.fillText(v>=1000?(v/1000)+'k':String(v),x-10,height-9);});
 ctx.strokeStyle='#d7ad58';ctx.lineWidth=1.6;ctx.beginPath();let started=false;const stride=Math.max(1,Math.floor(frequencies.length/2400));
 for(let i=1;i<frequencies.length;i+=stride){const freq=frequencies[i],value=values[i];if(!Number.isFinite(freq)||!Number.isFinite(value)||freq<=0)continue;const x=left+(Math.log10(freq)-logMin)/(logMax-logMin)*plotW,y=top+(maxValue-value)/(maxValue-minValue)*plotH;if(!started){ctx.moveTo(x,y);started=true;}else ctx.lineTo(x,y);}
 if(started)ctx.stroke();
}
let liveTfRunning=false,liveTfBusy=false,liveTfTimer=null,liveTfGeneration=0;
async function refreshLiveTfDevices(){
 const select=$('liveTfDevice');if(!select)return;
 if(!api()||typeof api().list_tf_devices!=='function'){
  select.innerHTML='<option value="">Yalnızca Windows masaüstü EXE</option>';
  $('liveTfStatus').textContent='Canlı stereo TF, Windows masaüstü EXE içinde kullanılabilir.';
  return;
 }
 try{
  const devices=await api().list_tf_devices();
  select.innerHTML='';
  if(!Array.isArray(devices)||!devices.length){
   select.innerHTML='<option value="">Stereo giriş aygıtı bulunamadı</option>';
   $('liveTfStatus').textContent='En az iki eşzamanlı giriş kanalı olan bir ses kartı bağla.';
   return;
  }
  devices.forEach(device=>{
   const option=document.createElement('option');option.value=String(device.index);
   option.textContent=String(device.name)+' · '+String(device.host_api||'Ses aygıtı')+' · '+device.max_input_channels+' giriş';
   select.appendChild(option);
  });
  $('liveTfStatus').textContent=devices.length+' stereo giriş aygıtı bulundu. CH0 referans, CH1 ölçüm mikrofonu.';
 }catch(error){$('liveTfStatus').textContent='Stereo girişler listelenemedi: '+(error.message||String(error));}
}
async function stopLiveTf(showMessage=true){
 liveTfGeneration++;liveTfRunning=false;liveTfBusy=false;
 if(liveTfTimer!==null){clearTimeout(liveTfTimer);liveTfTimer=null;}
 $('startLiveTf').disabled=false;$('stopLiveTf').disabled=true;
 if(api()&&typeof api().stop_tf==='function'){
  try{await api().stop_tf();}catch(error){if(showMessage)$('liveTfStatus').textContent='TF durdurma uyarısı: '+(error.message||String(error));}
 }
 if(showMessage)$('liveTfStatus').textContent='Canlı TF durduruldu.';
}
async function tickLiveTf(token){
 if(!liveTfRunning||token!==liveTfGeneration)return;
 if(liveTfBusy){liveTfTimer=setTimeout(()=>tickLiveTf(token),120);return;}
 liveTfBusy=true;
 try{
  const snapshot=await api().get_tf_snapshot('third',20,20000);
  if(!liveTfRunning||token!==liveTfGeneration)return;
  if(!snapshot||!snapshot.ok)throw new Error(snapshot?.error||'TF verisi alınamadı.');
  const age=Number(snapshot.seconds_since_last_callback||0);
  if(snapshot.ready){
   drawAcousticChart('acousticMagnitudeChart',snapshot.centers,snapshot.mag_db,-36,18,' dB');
   drawAcousticChart('acousticPhaseChart',snapshot.centers,snapshot.phase_deg,-180,180,'°');
   drawAcousticChart('acousticCoherenceChart',snapshot.centers,snapshot.coherence,0,1,'');
  }
  const streamNote=snapshot.stream_stale||age>2?'\nUYARI: Ses akışı durdu veya iki saniyeden uzun süredir veri gelmiyor.':'';
  $('liveTfStatus').textContent='Canlı H1 · '+snapshot.device+'\n'+Number(snapshot.sample_rate).toLocaleString('tr-TR')+' Hz · FFT '+snapshot.fft_size+' · Ortalama '+snapshot.averages+'/'+snapshot.averages_target+'\nCH0 referans: '+Number(snapshot.peak_ref_dbfs).toFixed(1)+' dBFS peak · CH1 ölçüm: '+Number(snapshot.peak_mic_dbfs).toFixed(1)+' dBFS peak'+streamNote+(snapshot.callback_status?'\nSürücü: '+snapshot.callback_status:'');
 }catch(error){
  $('liveTfStatus').textContent='Canlı TF hatası: '+(error.message||String(error));
 }finally{
  liveTfBusy=false;
  if(liveTfRunning&&token===liveTfGeneration)liveTfTimer=setTimeout(()=>tickLiveTf(token),120);
 }
}
function initLiveTfControls(){
 const start=$('startLiveTf');if(!start)return;
 $('refreshLiveTfDevices').addEventListener('click',refreshLiveTfDevices);
 start.addEventListener('click',async()=>{
  if(!api()||typeof api().start_tf!=='function'){ $('liveTfStatus').textContent='Canlı stereo TF yalnızca Windows masaüstü EXE içinde kullanılabilir.';return;}
  start.disabled=true;
  try{
   await stopLiveTf(false);
   const device=$('liveTfDevice').value||'default';
   const result=await api().start_tf(device,Number($('liveTfFft').value||16384),Number($('liveTfAverages').value||8));
   if(!result||!result.ok)throw new Error(result?.error||'Stereo ses akışı başlatılamadı.');
   liveTfRunning=true;liveTfGeneration++;const token=liveTfGeneration;
   $('stopLiveTf').disabled=false;start.disabled=true;
   $('liveTfStatus').textContent=result.message||'Stereo TF başlatıldı; ilk ortalamalar bekleniyor.';
   tickLiveTf(token);
  }catch(error){
   liveTfRunning=false;start.disabled=false;$('stopLiveTf').disabled=true;
   $('liveTfStatus').textContent='Canlı TF başlatılamadı: '+(error.message||String(error));
  }
 });
 $('stopLiveTf').addEventListener('click',()=>stopLiveTf(true));
 if(api())refreshLiveTfDevices();
 window.addEventListener('pywebviewready',refreshLiveTfDevices,{once:true});
 window.addEventListener('pagehide',()=>{if(liveTfRunning)stopLiveTf(false);});
}

function initAcousticAnalyzer(){
 const run=$('acousticAnalyze');if(!run)return;
 run.addEventListener('click',async()=>{
  if(!api()){ $('acousticAnalysisStatus').textContent='Bu özellik masaüstü EXE içinde çalışır.';return;}
  run.disabled=true;$('acousticAnalysisStatus').textContent='Stereo WAV dosyası seçiliyor…';
  try{
   const path=await api().pick_wav();if(!path){$('acousticAnalysisStatus').textContent='Dosya seçimi iptal edildi.';return;}
   $('acousticAnalysisStatus').textContent='Stereo WAV okunuyor ve yerel DSP motorunda analiz ediliyor…';
   const size=Number($('acousticSegmentSize').value||8192),overlap=Number($('acousticOverlap').value||0.5);
   const result=await api().analyze_stereo_wav(path,size,overlap);
   if(!result||!result.ok)throw new Error(result?.error||'Analiz sonucu alınamadı.');
   const tf=result.transfer_function,delay=result.delay,ir=result.impulse_response;
   drawAcousticChart('acousticMagnitudeChart',tf.frequency_hz,tf.magnitude_db,-36,18,' dB');
   drawAcousticChart('acousticPhaseChart',tf.frequency_hz,tf.phase_deg,-180,180,'°');
   drawAcousticChart('acousticCoherenceChart',tf.frequency_hz,tf.coherence,0,1,'');
   $('acousticDelayResult').textContent='DELAY FINDER\n'+delay.delay_samples.toFixed(2)+' örnek · '+delay.delay_ms.toFixed(3)+' ms\nKorelasyon: '+delay.correlation_peak.toFixed(4)+' · '+(delay.polarity_inverted?'Polarite ters':'Polarite normal');
   const peakIndex=ir.impulse_response.reduce((best,v,i,a)=>Math.abs(v)>Math.abs(a[best])?i:best,0);
   $('acousticIrResult').textContent='IMPULSE RESPONSE / ETC\n'+ir.impulse_response.length+' örnek · tepe '+(peakIndex*1000/result.sample_rate).toFixed(3)+' ms\nWelch ortalaması: '+tf.averages+' · segment: '+size;
   $('acousticAnalysisStatus').textContent='Analiz tamamlandı: '+result.file_name+'\n'+result.channels+' kanal · '+result.sample_rate.toLocaleString('tr-TR')+' Hz · '+result.duration_seconds.toFixed(2)+' sn\nH1 Transfer Function, Phase, Coherence, Delay ve Impulse Response hesaplandı. Sonuçlar dB SPL değildir.';
  }catch(err){$('acousticAnalysisStatus').textContent='Analiz başarısız: '+(err.message||String(err));}
  finally{run.disabled=false;}
 });
}

// --- RTA: yerel PortAudio mikrofonu + test edilmiş FFT güç bantları ---
const RtaMath=window.StagepulseRtaMath;
const rtaTicks=[20,25,31.5,40,50,63,80,100,125,160,200,250,315,400,500,630,800,1000,1250,1600,2000,2500,3150,4000,5000,6300,8000,10000,12500,16000,20000];
let rtaViewMin=20, rtaViewMax=20000, rtaAvailableMax=20000;
function rtaRatio(){return RtaMath.ratio($('rtaBands').value);}
function rtaCenters(){return RtaMath.centers($('rtaBands').value);}
function rtaEffectiveSampleRate(){return rtaSampleRate||48000;}
function rtaFullBandCenters(){return RtaMath.supportedCenters(rtaEffectiveSampleRate(),$('rtaBands').value,20,20000);}
function rtaBounds(){const opts={'20-20000':[20,20000],'31.5-16000':[31.5,16000],'63-8000':[63,8000],'125-4000':[125,4000]};const v=$('rtaRange')?.value||'auto';const bands=rtaFullBandCenters();const supportedMax=bands.length?bands[bands.length-1]:8000;let range;if(v==='auto')range=[20,Math.max(20,supportedMax)];else if(v==='custom'){let low=Number($('rtaCustomMin')?.value||20),high=Number($('rtaCustomMax')?.value||20000);low=Math.max(20,Math.min(20000,Number.isFinite(low)?low:20));high=Math.max(20,Math.min(20000,Number.isFinite(high)?high:20000));if(high<=low)high=Math.min(20000,low*2);if(high<=low){low=Math.max(20,high/2);}range=[low,high];}else range=opts[v]||[20,20000];return rtaSampleRate>0?RtaMath.clampRangeToSupported(rtaSampleRate,$('rtaBands').value,range[0],range[1]):range;}
function rtaFormatHz(f){return f>=1000?(f/1000).toLocaleString('tr-TR',{maximumFractionDigits:1})+' kHz':f.toLocaleString('tr-TR',{maximumFractionDigits:1})+' Hz';}
function resetRtaHistory(){rtaSmoothed=null;rtaPeak=null;rtaTraceHistory=[];rtaLastTime=0;rtaOptimizerHistory=[];if($('rtaOptimizerOutput'))$('rtaOptimizerOutput').textContent='Kararlı spektrum örneği bekleniyor.';}
function initRtaControls(){
 $('rtaStart').addEventListener('click',startRta);$('rtaStop').addEventListener('click',()=>stopRta(true));
 $('rtaCalibrate').addEventListener('click',async()=>{
  if(!api()||typeof api().calibrate_rta_spl!=='function'){$('rtaStatus').textContent='Fiziksel kalibratörle SPL kalibrasyonu bu Windows masaüstü sürümünde kullanılabilir.';return;}
  const button=$('rtaCalibrate');button.disabled=true;
  try{
   const result=await api().calibrate_rta_spl(Number($('rtaCalibratorLevel').value||94));
   $('rtaStatus').textContent=result.message||'SPL kalibrasyonu tamamlandı.';
   if(rtaRunning)tickRta(rtaGeneration);
  }catch(error){$('rtaStatus').textContent='SPL kalibrasyonu yapılamadı: '+(error.message||String(error));}
  finally{button.disabled=false;}
 });
 $('rtaResetPeak').addEventListener('click',()=>{rtaPeak=null;if(rtaSmoothed)drawRta(rtaSmoothed);});
 $('rtaRefreshDevices').addEventListener('click',refreshRtaDevices);
 $('rtaDevice').addEventListener('change',()=>{if(rtaRunning)startRta();});
 $('rtaBands').addEventListener('change',()=>{resetRtaHistory();updateRtaRangeInfo();});
 $('rtaRange').addEventListener('change',()=>{const custom=$('rtaRange').value==='custom';$('rtaCustomRangeFields').classList.toggle('hidden',!custom);resetRtaHistory();updateRtaRangeInfo();});
 ['rtaCustomMin','rtaCustomMax'].forEach(id=>$(id).addEventListener('change',()=>{if(Number($('rtaCustomMax').value)<=Number($('rtaCustomMin').value))$('rtaCustomMax').value=Math.min(20000,Math.max(Number($('rtaCustomMin').value)+1,Number($('rtaCustomMin').value)*2));resetRtaHistory();updateRtaRangeInfo();}));
 $('rtaSmooth').addEventListener('change',resetRtaHistory);
 $('rtaFftSize').addEventListener('change',()=>{resetRtaHistory();if(rtaRunning)startRta();else{rtaFftSize=Number($('rtaFftSize').value);updateRtaRangeInfo();}});
 $('rtaOffset').addEventListener('input',()=>{if(rtaSmoothed)drawRta(rtaSmoothed);});
 $('rtaOptimizeEnabled').addEventListener('change',()=>{rtaOptimizerHistory=[];if(!$('rtaOptimizeEnabled').checked)$('rtaOptimizerOutput').textContent='Canlı öneriler kapalı. Grafik çalışmaya devam eder.';else $('rtaOptimizerOutput').textContent='Öneri için pembe gürültü veya kararlı bantlı test sinyali onayı gerekir.';});
 $('rtaOptimizerTestSignalConfirm').addEventListener('change',()=>{rtaOptimizerHistory=[];$('rtaOptimizerOutput').textContent=$('rtaOptimizerTestSignalConfirm').checked?'Test sinyali onaylandı; 8 kararlı spektrum örneği bekleniyor.':'Test sinyali onayı kaldırıldı; EQ önerileri durduruldu.';});
 $('rtaPeakThreshold').addEventListener('change',()=>{rtaOptimizerHistory=[];$('rtaOptimizerOutput').textContent='Eşik değişti; yeni kararlı örnekler toplanıyor.';});
 $('rtaClearOptimize').addEventListener('click',()=>{rtaOptimizerHistory=[];$('rtaOptimizerOutput').textContent='Öneri geçmişi sıfırlandı; yeni örnekler bekleniyor.';});
 window.addEventListener('resize',()=>{if(activeRoute==='rta')drawRtaPlaceholder();});
 updateRtaRangeInfo();
}
async function refreshRtaDevices(){
 const select=$('rtaDevice');if(!select)return;
 if(!api()){select.innerHTML='<option value="">Mikrofon listesi için masaüstü uygulamasını aç</option>';return;}
 const current=select.value;select.innerHTML='<option value="">Varsayılan Windows giriş aygıtı</option>';
 try{
  const devices=await api().list_rta_devices();
  for(const d of devices){const option=document.createElement('option');option.value=String(d.index);option.textContent=`${d.name} · ${d.host_api||'Ses sürücüsü'} · ${d.default_sample_rate||'?' } Hz${d.is_default?' · varsayılan':''}`;select.appendChild(option);}
  if(devices.some(d=>String(d.index)===current))select.value=current;else select.value='';
  if(!devices.length)$('rtaCaptureInfo').textContent='Windows giriş aygıtı bulunamadı. Sistem aygıtı/driver ve mikrofon iznini kontrol et.';
  else if(!rtaRunning)$('rtaCaptureInfo').textContent=`${devices.length} yerel giriş aygıtı bulundu. İstenen mikrofonu seçip Mikrofonu başlat düğmesine bas.`;
 }catch(err){$('rtaCaptureInfo').textContent='Yerel giriş listesi alınamadı: '+(err.message||String(err))+'\nWindows mikrofon izinlerini, ses sürücüsünü ve uygulamanın yeniden derlenmiş olup olmadığını kontrol et.';}
}
function rtaMicError(err){const msg=String(err&&err.message||err||'Bilinmeyen hata');if(/permission|access denied|erişim engellendi|izin/i.test(msg))return msg+'\nWindows Ayarlar → Gizlilik → Mikrofon bölümünde masaüstü uygulamalarına izin ver.';if(/device|input|aygıt|PortAudio|no default/i.test(msg))return msg+'\nWindows Ayarlar → Sistem → Ses → Giriş bölümünde mikrofon seçildiğini doğrula.';if(/busy|unavailable|kullanılıyor|device unavailable/i.test(msg))return msg+'\nTeams/Zoom/kayıt uygulamalarını kapatıp tekrar dene.';return msg;}
async function startRta(){
 if(!api()){$('rtaStatus').textContent='Yerel mikrofon RTA için paketlenmiş Stagepulse uygulaması gerekir; tarayıcı önizlemesinde donanım yakalama başlatılmaz.';return;}
 const token=++rtaGeneration; if(rtaPollTimer)clearTimeout(rtaPollTimer);rtaPollTimer=0;rtaRunning=false;rtaBusy=false;
 $('rtaStart').disabled=true;$('rtaStop').disabled=true;$('rtaStatus').textContent='Yerel ses sürücüsü açılıyor…';$('rtaInputMeter').textContent='Giriş seviyesi: ölçüm bekleniyor.';
 try{
  const rawDevice=$('rtaDevice').value;const selected=rawDevice===''?null:Number(rawDevice);const fftSize=Number($('rtaFftSize').value||16384);
  const result=await enqueueRtaCommand(async()=>{
   await api().stop_rta();
   if(token!==rtaGeneration)return {stale:true};
   const started=await api().start_rta(selected,fftSize);
   if(token!==rtaGeneration){await api().stop_rta();return {stale:true};}
   return started;
  });
  if(token!==rtaGeneration||result&&result.stale)return;
  if(!result||!result.ok)throw new Error(result&&result.error||'Mikrofon başlatılamadı.');
  rtaRunning=true;rtaSampleRate=Number(result.sample_rate)||0;rtaFftSize=Number(result.fft_size)||fftSize;rtaDeviceName=result.device||'Varsayılan giriş';resetRtaHistory();
  $('rtaStart').disabled=true;$('rtaStop').disabled=false;if($('homeMicStatus'))$('homeMicStatus').textContent='Aktif';
  updateRtaRangeInfo();$('rtaStatus').textContent=`Yerel mikrofon açıldı · ${rtaSampleRate.toLocaleString('tr-TR')} Hz · ${rtaFftSize} FFT. İlk spektrum penceresi hazırlanıyor…`;tickRta(token);
 }catch(err){if(token!==rtaGeneration)return;rtaRunning=false;rtaSampleRate=0;$('rtaStart').disabled=false;$('rtaStop').disabled=true;if($('homeMicStatus'))$('homeMicStatus').textContent='Kapalı';$('rtaCaptureInfo').textContent='Sorun giderme: 1) Windows giriş aygıtını seç ve sistem testinde seviye hareketini doğrula. 2) Masaüstü uygulamalarının mikrofon erişimini aç. 3) Başka uygulamanın mikrofonu kullanmadığını kontrol et. 4) Girişleri yenile ve yeniden dene.';updateRtaRangeInfo();$('rtaStatus').textContent='RTA başlatılamadı: '+rtaMicError(err);}
}
async function stopRta(showStatus=true){
 rtaGeneration++;if(rtaPollTimer)clearTimeout(rtaPollTimer);rtaPollTimer=0;rtaRunning=false;rtaBusy=false;
 try{if(api())await enqueueRtaCommand(()=>api().stop_rta());}catch(_){}
 rtaSampleRate=0;rtaDeviceName='';resetRtaHistory();
 if($('rtaStart'))$('rtaStart').disabled=false;if($('rtaStop'))$('rtaStop').disabled=true;
 if($('homeMicStatus'))$('homeMicStatus').textContent='Kapalı';
 if($('rtaInputMeter'))$('rtaInputMeter').textContent='Giriş seviyesi: ölçüm durduruldu.';
 updateRtaRangeInfo();if(showStatus&&$('rtaStatus'))$('rtaStatus').textContent='Yerel mikrofon yakalama kapatıldı.';if(activeRoute==='rta')drawRtaPlaceholder();
}
function updateRtaRangeInfo(){
 const bounds=rtaBounds(),full=rtaFullBandCenters();rtaViewMin=bounds[0];rtaViewMax=bounds[1];rtaAvailableMax=full.length?full[full.length-1]:0;
 $('rtaAxisMin').textContent=rtaFormatHz(rtaViewMin);$('rtaAxisMax').textContent=rtaFormatHz(rtaViewMax);
 const availableInView=full.filter(f=>f>=rtaViewMin&&f<=rtaViewMax),fftSize=rtaFftSize||Number($('rtaFftSize').value||16384),bin=rtaSampleRate?rtaSampleRate/fftSize:0;
 let note=`Tam bant merkezleri: ${availableInView.length} · FFT: ${fftSize} · bin aralığı: ${bin?bin.toFixed(2)+' Hz':'mikrofon açılınca hesaplanır'}`;
 if(!rtaSampleRate)note+=' · örnekleme hızı mikrofon açılınca belirlenir';
 const rangeOptions={'20-20000':[20,20000],'31.5-16000':[31.5,16000],'63-8000':[63,8000],'125-4000':[125,4000]};const requested=$('rtaRange')?.value||'auto';const customMin=Number($('rtaCustomMin')?.value||20),customMax=Number($('rtaCustomMax')?.value||20000);const requestedRange=requested==='custom'?[customMin,customMax]:(rangeOptions[requested]||[20,rtaAvailableMax]);const requestedMax=requested==='auto'?rtaAvailableMax:requestedRange[1];
 if(rtaSampleRate&&requestedMax>rtaAvailableMax)note+=` · seçilen üst sınır örnekleme/Nyquist nedeniyle ${rtaFormatHz(rtaAvailableMax)} olarak daraltıldı.`;if(rtaSampleRate&&requested==='custom'&&requestedRange[0]>=rtaAvailableMax)note+=` · alt sınırın üzerinde tam bant kalmadı; grafik kullanılabilir bandı göstermek için ${rtaFormatHz(rtaViewMin)} değerine genişletildi.`;
 if(!rtaRunning&&rtaSampleRate===0)note+=' · önizleme 48 kHz varsayımıdır, ölçüm değildir.';
 $('rtaStatus').textContent=note;
 if(rtaSmoothed&&rtaFreqs.length)drawRta(rtaSmoothed);
}
function updateRtaOptimizer(centers, values){
 const out=$('rtaOptimizerOutput');if(!out)return;
 if(!$('rtaOptimizeEnabled').checked){out.textContent='Canlı öneriler kapalı. Grafik çalışmaya devam eder.';return;}
 if(!$('rtaOptimizerTestSignalConfirm').checked){rtaOptimizerHistory=[];out.textContent='EQ adayı üretmek için pembe gürültü veya sabit bantlı test sinyali kullanımını onayla. Müzik/konuşma programında öneri üretilmez.';return;}
 if(!Array.isArray(centers)||!Array.isArray(values)||centers.length!==values.length||!values.length){out.textContent='Geçerli spektrum yok.';return;}
 rtaOptimizerHistory.push(values.slice());if(rtaOptimizerHistory.length>12)rtaOptimizerHistory.shift();
 if(rtaOptimizerHistory.length<8){out.textContent=`Kararlı örnekler toplanıyor: ${rtaOptimizerHistory.length}/8. Bu sırada EQ önerisi üretilmez.`;return;}
 const median=(a)=>{const s=a.slice().sort((x,y)=>x-y);return s.length%2?s[(s.length-1)/2]:(s[s.length/2-1]+s[s.length/2])/2;};
 const robust=centers.map((_,i)=>median(rtaOptimizerHistory.map(row=>row[i]).filter(Number.isFinite)));
 let cuts=[];try{cuts=AcousticMath.recommendCuts(centers,robust,Number($('rtaPeakThreshold').value||6));}catch(e){out.textContent='Öneriler hesaplanamadı: '+e.message;return;}
 if(!cuts.length){out.textContent=`Son ${rtaOptimizerHistory.length} yumuşatılmış örnekte eşik üzerinde dar bantlı tepe bulunmadı. Bu durum sistemin düz olduğunu kanıtlamaz; ölçüm mikrofonu/konum yanıtı bilinmiyor.`;return;}
 out.innerHTML='<p>Son '+rtaOptimizerHistory.length+' örneğin medyanından adaylar. Kesim miktarı en fazla 3 dB ile sınırlandırıldı; otomatik uygulanmaz.</p><div class="report-table">'+cuts.map(x=>`<div>${rtaFormatHz(x.frequencyHz)}</div><div>Komşu bant medyanından +${fmt(x.excessDb,1)} dB · aday kesim ${x.suggestedCutDb} dB · yaklaşık Q ${fmt(x.qApprox,1)}</div>`).join('')+'</div><p class="muted">Önce mikrofon konumunu değiştirip tekrarla. Aynı tepe birden fazla konumda görünmeli ve dinleme/transfer-function ölçümüyle doğrulanmalı. Oda kaynaklı çukurlara boost uygulanmaz.</p>';
}

async function tickRta(token){
 if(!rtaRunning||activeRoute!=='rta'||token!==rtaGeneration)return;
 if(rtaBusy){rtaPollTimer=setTimeout(()=>tickRta(token),120);return;}
 rtaBusy=true;
 try{
  const bounds=rtaBounds();rtaViewMin=bounds[0];rtaViewMax=bounds[1];
  const snapshot=await api().get_rta_snapshot($('rtaBands').value,rtaViewMin,rtaViewMax);
  if(!rtaRunning||token!==rtaGeneration||activeRoute!=='rta')return;
  if(!snapshot||!snapshot.ok){$('rtaStatus').textContent='RTA veri hatası: '+(snapshot&&snapshot.error||'bilinmeyen durum');}
  else{
   rtaSampleRate=Number(snapshot.sample_rate)||rtaSampleRate;rtaFftSize=Number(snapshot.fft_size)||rtaFftSize;
   const centers=snapshot.centers||[],values=snapshot.band_dbfs||[];
   const changed=centers.length!==rtaFreqs.length||centers.some((f,i)=>f!==rtaFreqs[i]);
   if(changed){rtaFreqs=centers.slice();resetRtaHistory();}
   if(snapshot.ready){const now=performance.now(),dt=rtaLastTime?Math.max(.001,(now-rtaLastTime)/1000):.1;rtaLastTime=now;const tau={fast:.12,medium:.18,slow:.5}[$('rtaSmooth').value]||.18;rtaSmoothed=RtaMath.smooth(rtaSmoothed,values,dt,tau);rtaPeak=rtaPeak&&rtaPeak.length===rtaSmoothed.length?rtaPeak.map((v,i)=>Math.max(v,rtaSmoothed[i])):rtaSmoothed.slice();rtaTraceHistory.push(rtaSmoothed.slice());if(rtaTraceHistory.length>4)rtaTraceHistory.shift();drawRta(rtaSmoothed);updateRtaOptimizer(centers,rtaSmoothed);}
   const peak=Number(snapshot.peak_dbfs??-120),rms=Number(snapshot.rms_dbfs??-120),peakWarn=snapshot.stream_stale?' · AKIŞ DURDU; son örnek değerleri':peak>-1?' · Kırpılmaya çok yakın!':peak<-60?' · Çok düşük giriş; kazancı kontrol et.':' · Giriş alınıyor.';
   const splNote=snapshot.calibrated_spl&&Number.isFinite(Number(snapshot.spl_db))?' · '+Number(snapshot.spl_db).toFixed(1)+' dB SPL Z (kalibre)':'';
   $('rtaInputMeter').textContent=`Giriş peak: ${peak.toFixed(1)} dBFS · RMS: ${rms.toFixed(1)} dBFS${splNote}${peakWarn}`;updateRtaMeters(peak,rms);
   const bin=snapshot.sample_rate/snapshot.fft_size;
   const status=snapshot.stream_status?`\nSürücü uyarısı: ${snapshot.stream_status}`:'';
   const bandNote=rtaAvailableMax&&rtaViewMax>rtaAvailableMax?`\nTam bandın üst merkezi: ${rtaFormatHz(rtaAvailableMax)}; daha üst bantlar akış örnekleme hızında eksik kalır.`:'';
   const splCalibrationNote=snapshot.calibrated_spl?`\nSPL kalibrasyonu: 1 kHz / ${Number(snapshot.spl_calibration_reference_db).toFixed(1)} dB SPL referansı · Z ağırlıksız · offset ${Number(snapshot.spl_calibration_offset_db).toFixed(1)} dB. Mikrofon frekans düzeltmesi/IEC sınıfı sağlamaz.`:'\nSPL kalibrasyonu yok; grafik dBFS RMS gösterir.';
   $('rtaCaptureInfo').textContent=`Aygıt: ${snapshot.device||rtaDeviceName}\nYerel PortAudio akışı: ${Number(snapshot.sample_rate).toLocaleString('tr-TR')} Hz · FFT: ${snapshot.fft_size} · bin aralığı: ${bin.toFixed(2)} Hz · Nyquist: ${rtaFormatHz(snapshot.sample_rate/2)}\nBant grafiği dBFS RMS gösterir.${splCalibrationNote}${bandNote}${status}`;
   if(snapshot.ready)$('rtaStatus').textContent=`${centers.length} bant · ${snapshot.sample_rate.toLocaleString('tr-TR')} Hz yerel giriş · FFT ${snapshot.fft_size}${snapshot.stream_status?' · sürücü uyarısını kontrol et.':''}`;
   else if(snapshot.stream_stale||Number(snapshot.seconds_since_last_callback||0)>2)$('rtaStatus').textContent='Mikrofon akışından yeni örnek gelmiyor. Grafikteki son spektrum güncel değil; giriş aygıtını, izinleri ve sürücüyü kontrol et.';else $('rtaStatus').textContent='Mikrofondan örnekler alınıyor; ilk FFT penceresi hazırlanıyor…';
  }
 }catch(err){$('rtaStatus').textContent='RTA okuması başarısız: '+(err.message||String(err));}
 finally{rtaBusy=false;if(rtaRunning&&activeRoute==='rta'&&token===rtaGeneration)rtaPollTimer=setTimeout(()=>tickRta(token),100);}
}
function drawRtaPlaceholder(){const c=$('rtaCanvas');if(!c)return;const rect=c.getBoundingClientRect();if(rect.width<32)return;const dpr=Math.min(2,Math.max(1,window.devicePixelRatio||1)),ctx=c.getContext('2d');c.width=Math.max(280,Math.floor(rect.width*dpr));c.height=Math.floor(Math.max(240,rect.height)*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);const w=c.width/dpr,h=c.height/dpr;drawRtaGrid(ctx,w,h);if(rtaSmoothed)drawRta(rtaSmoothed);}
function drawRta(values){
 const c=$('rtaCanvas');if(!c||!Array.isArray(values)||!rtaFreqs.length)return;
 const ctx=c.getContext('2d'),dpr=Math.min(2,Math.max(1,window.devicePixelRatio||1)),rect=c.getBoundingClientRect();
 if(rect.width<32)return;
 const w=Math.max(320,rect.width),h=Math.max(300,rect.height);
 if(c.width!==Math.floor(w*dpr)||c.height!==Math.floor(h*dpr)){c.width=Math.floor(w*dpr);c.height=Math.floor(h*dpr);}
 ctx.setTransform(dpr,0,0,dpr,0,0);
 const pad={l:54,r:18,t:24,b:42},floor=-96,ceil=0,offset=Math.max(-60,Math.min(60,Number($('rtaOffset').value||0)));
 const x=f=>pad.l+Math.log(Math.max(rtaViewMin,f)/rtaViewMin)/Math.log(rtaViewMax/rtaViewMin)*(w-pad.l-pad.r);
 const y=v=>pad.t+(ceil-Math.max(floor,Math.min(ceil,v+offset)))/(ceil-floor)*(h-pad.t-pad.b);
 drawRtaGrid(ctx,w,h);
 const valid=rtaFreqs.map((f,i)=>({f,v:Number(values[i])})).filter(p=>p.f>=rtaViewMin&&p.f<=rtaViewMax&&Number.isFinite(p.v));
 if(!valid.length)return;
 const colors=['#42d6b0','#78a9ff','#e77be7','#ff9c57'];
 rtaTraceHistory.slice(-4).forEach((row,ri)=>{
  if(row.length!==rtaFreqs.length)return;
  ctx.beginPath();ctx.strokeStyle=colors[ri%colors.length];ctx.globalAlpha=.58;ctx.lineWidth=1.35;
  row.forEach((v,i)=>{const px=x(rtaFreqs[i]);if(i===0)ctx.moveTo(px,y(v));else ctx.lineTo(px,y(v));});ctx.stroke();
 });
 ctx.globalAlpha=1;
 const step=valid.length>1?Math.max(2,(x(valid[1].f)-x(valid[0].f))*.78):8;
 valid.forEach(p=>{
  const px=x(p.f),py=y(p.v),base=y(floor),grad=ctx.createLinearGradient(0,py,0,base);
  grad.addColorStop(0,'#ffe6a0');grad.addColorStop(.42,'#d7ad50');grad.addColorStop(1,'rgba(211,163,61,.12)');
  ctx.fillStyle=grad;ctx.fillRect(px-step/2,py,Math.max(2,step),Math.max(1,base-py));
 });
 ctx.beginPath();ctx.strokeStyle='#f5d98d';ctx.lineWidth=2.15;ctx.lineJoin='round';
 valid.forEach((p,i)=>{if(i===0)ctx.moveTo(x(p.f),y(p.v));else ctx.lineTo(x(p.f),y(p.v));});ctx.stroke();
 if(rtaPeak&&rtaPeak.length===rtaFreqs.length){
  ctx.beginPath();ctx.strokeStyle='#e9f1ff';ctx.lineWidth=1.1;ctx.setLineDash([4,4]);
  rtaFreqs.forEach((f,i)=>{if(i===0)ctx.moveTo(x(f),y(rtaPeak[i]));else ctx.lineTo(x(f),y(rtaPeak[i]));});
  ctx.stroke();ctx.setLineDash([]);
 }
 const peakPoint=valid.reduce((best,p)=>p.v>best.v?p:best,valid[0]);
 if(peakPoint){
  const px=x(peakPoint.f),py=y(peakPoint.v);ctx.fillStyle='#ffbd66';ctx.beginPath();ctx.arc(px,py,3.2,0,Math.PI*2);ctx.fill();
  ctx.font='600 10px Segoe UI';ctx.textAlign=px>w*.72?'right':'left';ctx.fillStyle='#fff0c9';
  ctx.fillText(rtaFormatHz(peakPoint.f)+' · '+peakPoint.v.toFixed(1)+' dBFS',px+(px>w*.72?-7:7),Math.max(14,py-9));
 }
}
function drawRtaGrid(ctx,w,h){
 ctx.clearRect(0,0,w,h);
 const bg=ctx.createLinearGradient(0,0,0,h);bg.addColorStop(0,'#101d32');bg.addColorStop(1,'#09111f');ctx.fillStyle=bg;ctx.fillRect(0,0,w,h);
 const pad={l:54,r:18,t:24,b:42},floor=-96,ceil=0;
 ctx.strokeStyle='rgba(117,151,194,.18)';ctx.lineWidth=1;ctx.fillStyle='#a9bad0';ctx.font='10px Segoe UI';ctx.textAlign='right';
 for(let db=0;db>=floor;db-=12){const yy=pad.t+(ceil-db)/(ceil-floor)*(h-pad.t-pad.b);ctx.beginPath();ctx.moveTo(pad.l,yy);ctx.lineTo(w-pad.r,yy);ctx.stroke();ctx.fillText(String(db),pad.l-8,yy+3);}
 ctx.textAlign='center';
 for(const f of rtaTicks.filter(f=>f>=rtaViewMin&&f<=rtaViewMax)){const xx=pad.l+Math.log(f/rtaViewMin)/Math.log(rtaViewMax/rtaViewMin)*(w-pad.l-pad.r);ctx.beginPath();ctx.moveTo(xx,pad.t);ctx.lineTo(xx,h-pad.b);ctx.stroke();ctx.fillStyle='#a9bad0';ctx.fillText(f>=1000?(f/1000).toLocaleString('tr-TR',{maximumFractionDigits:1})+'k':String(f).replace('.',','),xx,h-17);}
 ctx.textAlign='left';ctx.fillStyle='#9db2ce';ctx.font='9px Segoe UI';ctx.fillText('dBFS',8,14);
}
function updateRtaMeters(peak,rms){
 const p=Math.max(0,Math.min(100,(Number(peak)+72)/72*100)),r=Math.max(0,Math.min(100,(Number(rms)+72)/72*100));
 const pf=$('rtaPeakMeterFill'),rf=$('rtaRmsMeterFill');
 if(pf)pf.style.width=p.toFixed(1)+'%';if(rf)rf.style.width=r.toFixed(1)+'%';
 if($('rtaPeakMeterValue'))$('rtaPeakMeterValue').textContent=Number(peak).toFixed(1)+' dBFS';
 if($('rtaRmsMeterValue'))$('rtaRmsMeterValue').textContent=Number(rms).toFixed(1)+' dBFS';
}

// --- WAV local native analysis ---
function initWav(){$('wavChoose').addEventListener('click',async()=>{if(!api()){ $('wavReport').textContent='Bu düğme masaüstü EXE içinde çalışır. Tarayıcı önizlemesinde native dosya iletişim kutusu bulunmaz.';return;}try{const path=await api().pick_wav();if(!path)return;$('wavReport').textContent='Analiz ediliyor…';const r=await api().analyze_wav(path);lastWavReport=r;renderWavReport(r);$('wavSaveReport').disabled=false;setStatus('WAV analizi tamamlandı: '+r.file);}catch(err){$('wavReport').textContent='Analiz başarısız: '+(err.message||String(err));}});$('wavSaveReport').addEventListener('click',()=>{if(!lastWavReport)return;const text=Object.entries(lastWavReport).map(([k,v])=>`${k}: ${v===null?'ölçülmedi':typeof v==='number'?fmt(v,3):v}`).join('\n');downloadBlob(new Blob([text],{type:'text/plain;charset=utf-8'}),'WAV_Analiz_Raporu.txt');});}
function renderWavReport(r){const rows=[['Dosya',r.file],['Kanal sayısı',r.channels],['Örnekleme',r.sample_rate_hz+' Hz'],['Bit derinliği',r.bits_per_sample+' bit PCM'],['Süre',fmt(r.duration_seconds,3)+' s'],['Sample peak',r.sample_peak_dbfs===null?'Sessiz':fmt(r.sample_peak_dbfs,2)+' dBFS'],['RMS',r.rms_dbfs===null?'Sessiz':fmt(r.rms_dbfs,2)+' dBFS'],['Crest factor',r.crest_factor_db===null?'Hesaplanmadı':fmt(r.crest_factor_db,2)+' dB'],['Tam ölçeğe yakın örnekler',`${r.near_full_sample_count} (${fmt(r.near_full_sample_percent,5)}%)`]];$('wavReport').innerHTML='<div class="report-table">'+rows.map(([a,b])=>`<div>${safeText(a)}</div><div>${safeText(b)}</div>`).join('')+'</div><p style="margin:14px 0 0;color:#8e9baa">'+safeText(r.scope_note)+'</p>';}

// --- Offline LUFS normalization via bundled Python DSP dependencies ---
function initLufs(){$('runLufs').addEventListener('click',async()=>{if(!api()){ $('lufsReport').textContent='Bu özellik paketlenmiş masaüstü uygulamasının yerel API özelliğini gerektirir.';return;}const target=Number($('lufsTarget').value),tp=Number($('tpTarget').value);if(!Number.isFinite(target)||target< -70||target>0||!Number.isFinite(tp)||tp< -20||tp>0){$('lufsReport').textContent='Hedef LUFS -70..0, true-peak tavanı -20..0 aralığında olmalı.';return;}try{$('runLufs').disabled=true;$('lufsReport').textContent='Kaynak/çıktı seçimi ve loudness işlemi sürüyor…';const r=await api().normalize_lufs_dialog(target,tp);if(r.cancelled){$('lufsReport').textContent='İşlem iptal edildi.';return;}$('lufsReport').textContent=Object.entries(r).map(([k,v])=>`${k}: ${typeof v==='number'?fmt(v,3):typeof v==='object'?JSON.stringify(v):v}`).join('\n');setStatus('LUFS işlemi tamamlandı. Çıktıyı tekrar kontrol et.');}catch(err){$('lufsReport').textContent='Normalizasyon başarısız: '+(err.message||String(err));}finally{$('runLufs').disabled=false;}});}

// --- Multitrack mix lab ---
function initMixer(){ $('trackFiles').addEventListener('change',e=>loadTrackFiles(e.target.files));$('mixPreview').addEventListener('click',previewMix);$('mixStop').addEventListener('click',stopMixerPreview);$('mixRender').addEventListener('click',renderAndDownloadMix);$('mixExportProject').addEventListener('click',exportMixProject);$('mixLoadProject').addEventListener('click',()=>$('mixProjectFile').click());$('mixProjectFile').addEventListener('change',loadMixProject);$('exportEvidenceReport').addEventListener('click',exportEvidenceReport);$('addCue').addEventListener('click',()=>addCue({time:0,type:'Efekt',text:'Yeni ses işareti'}));$('videoFile').addEventListener('change',loadLocalVideo);$('captureVideoFrame').addEventListener('click',captureFrame);$('addVideoCue').addEventListener('click',()=>addCue({time:$('localVideo').currentTime||0,type:'Video notu',text:'Video zamanındaki ses/görüntü notunu yaz.'}));$('analyzeVideoLocal').addEventListener('click',analyzeVideoLocal);$('stageSceneCues').addEventListener('click',stageSceneCues);$('buildAutonomousEdit').addEventListener('click',buildLocalSoundPlan);$('applyPlanCues').addEventListener('click',applyPlanCues);$('exportPlanJSON').addEventListener('click',exportPlanJSON);$('exportPlanCSV').addEventListener('click',exportPlanCSV);$('evidenceAudioFile').addEventListener('change',()=>{audioEvidenceData=null;$('audioEvidenceReport').textContent=$('evidenceAudioFile').files[0]?'Dosya seçildi. Ölçüm için düğmeye bas.':'Dosya seçilmedi.';});$('analyzeAudioEvidence').addEventListener('click',analyzeAudioEvidence);$('clearAudioEvidence').addEventListener('click',()=>{audioEvidenceData=null;$('evidenceAudioFile').value='';$('audioEvidenceReport').textContent='Temizlendi.';});$('soundLibraryFiles').addEventListener('change',()=>{$('soundLibraryResults').textContent=`${$('soundLibraryFiles').files.length} yerel dosya seçildi.`;});$('indexSoundLibrary').addEventListener('click',indexSoundLibrary);$('matchSoundCues').addEventListener('click',matchSoundCues);$('clearSoundLibrary').addEventListener('click',()=>{soundLibraryIndex=[];$('soundLibraryFiles').value='';renderSoundLibrary();});$('soundLibrarySearch').addEventListener('input',renderSoundLibrary);$('sceneMarkerList').addEventListener('click',async e=>{const b=e.target.closest('[data-seek-scene]');if(b){try{await seekLocalVideo(videoSceneMarkers[Number(b.dataset.seekScene)]||0);}catch(err){$('videoAnalysisReport').textContent=err.message;}}});$('trackList').addEventListener('input',onTrackControl);$('trackList').addEventListener('change',onTrackControl);renderTracks();renderMixerCues();}
function decodedAudioBytes(){return mixerTracks.reduce((sum,t)=>sum+t.buffer.length*t.buffer.numberOfChannels*4,0);}
async function readAudioDuration(file){const url=URL.createObjectURL(file),media=document.createElement('audio');media.preload='metadata';try{return await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(new Error('Dosya süresi okunamadı; daha kısa bir WAV/PCM dosyası dene.')),8000);media.onloadedmetadata=()=>{clearTimeout(timer);Number.isFinite(media.duration)&&media.duration>0?resolve(media.duration):reject(new Error('Ses süresi geçersiz.'));};media.onerror=()=>{clearTimeout(timer);reject(new Error('Bu biçimin ses süresi okunamadı.'));};media.src=url;});}finally{media.removeAttribute('src');URL.revokeObjectURL(url);}}
async function loadTrackFiles(files){if(!files||!files.length)return;const ctx=mixerAudioContext||(mixerAudioContext=new (window.AudioContext||window.webkitAudioContext)());let added=0;for(const file of Array.from(files).slice(0,12-mixerTracks.length)){try{$('mixStatus').textContent=`Dosya inceleniyor: ${file.name}`;const duration=await readAudioDuration(file),estimatedBytes=duration*Math.max(48000,ctx.sampleRate)*2*4;if(decodedAudioBytes()+estimatedBytes>MAX_DECODED_AUDIO_BYTES)throw new Error('RAM koruması: çözümlenmiş ses belleği 512 MiB sınırını aşabilir. Daha kısa veya daha az sayıda dosya seç.');const bytes=await file.arrayBuffer();const buffer=await ctx.decodeAudioData(bytes.slice(0));const actualBytes=buffer.length*buffer.numberOfChannels*4;if(decodedAudioBytes()+actualBytes>MAX_DECODED_AUDIO_BYTES)throw new Error('RAM koruması: toplam çözümlenmiş ses belleği 512 MiB sınırını aşıyor.');mixerTracks.push({id:nextTrackId++,name:file.name,buffer,bytes:file.size,channels:buffer.numberOfChannels,sampleRate:buffer.sampleRate,duration:buffer.duration,category:guessAudioCategory(file.name),gain:1,pan:0,start:0,trimIn:0,trimOut:buffer.duration,fadeIn:0,fadeOut:0,hpf:25,low:0,high:0,compress:false,compThreshold:-24,compRatio:3,compAttack:0.008,compRelease:0.18,gate:-70,muted:false});added++;}catch(err){console.error(err);alert(`${file.name} eklenemedi: ${err.message}`);}}$('trackFiles').value='';if(pendingMixProject&&added)applyPendingProject();renderTracks();$('mixStatus').textContent=`${mixerTracks.length} katman · ${added} yeni dosya eklendi · RAM koruması etkin.`;setStatus('Yerel ses dosyaları yüklendi.');}
function renderTracks(){const list=$('trackList');if(!mixerTracks.length){list.innerHTML='<div class="empty-state"><div class="empty-symbol">＋</div><strong>Ses katmanı ekle</strong><p>Bir veya daha fazla yerel ses dosyası seç. Her dosya ayrı bir kanal şeridi olur.</p></div>';return;}list.innerHTML=mixerTracks.map((t,i)=>`<article class="track-card" data-track="${t.id}"><header class="track-head"><span class="track-index">${String(i+1).padStart(2,'0')}</span><strong title="${safeText(t.name)}">${safeText(t.name)}</strong><small>${t.channels} ch · ${fmt(t.sampleRate,0)} Hz · ${fmt(t.duration,2)} s</small></header><div class="track-role field"><label>Kaynak türü</label><select data-prop="category"><option ${t.category==='Diyalog'?'selected':''}>Diyalog</option><option ${t.category==='Müzik'?'selected':''}>Müzik</option><option ${t.category==='Efekt'?'selected':''}>Efekt</option><option ${t.category==='Ambiyans'?'selected':''}>Ambiyans</option><option ${t.category==='Diğer'?'selected':''}>Diğer</option></select><label>Konuşma başlangıç ayarı</label><select data-action="preset"><option value="">Hazır ayar seç…</option><option value="natural">Doğal ses</option><option value="rumble">Dip gürültüsü azaltma</option><option value="clarity">Anlaşılırlık</option><option value="dynamic">Dinamik kontrol</option></select></div><div class="track-body"><div class="track-knob"><label>Gain ${fmt(20*Math.log10(Math.max(t.gain,.00001)),1)} dB</label><input type="range" min="0" max="2" step="0.01" value="${t.gain}" data-prop="gain"></div><div class="track-knob"><label>Pan ${fmt(t.pan,2)}</label><input type="range" min="-1" max="1" step="0.02" value="${t.pan}" data-prop="pan"></div><div class="track-knob"><label>Başlangıç (s)</label><input type="number" min="0" max="3600" step="0.05" value="${t.start}" data-prop="start"></div><div class="track-knob"><label>Trim in (s)</label><input type="number" min="0" max="${t.duration}" step="0.02" value="${t.trimIn}" data-prop="trimIn"></div><div class="track-knob"><label>Trim out (s)</label><input type="number" min="0.05" max="${t.duration}" step="0.02" value="${t.trimOut}" data-prop="trimOut"></div><div class="track-knob"><label>Fade in (s)</label><input type="number" min="0" max="${t.duration}" step="0.05" value="${t.fadeIn}" data-prop="fadeIn"></div><div class="track-knob"><label>Fade out (s)</label><input type="number" min="0" max="${t.duration}" step="0.05" value="${t.fadeOut}" data-prop="fadeOut"></div><div class="track-knob"><label>HPF (Hz)</label><input type="number" min="20" max="20000" step="5" value="${t.hpf}" data-prop="hpf"></div><div class="track-knob"><label>Low shelf (dB)</label><input type="number" min="-12" max="12" step="0.5" value="${t.low}" data-prop="low"></div><div class="track-knob"><label>High shelf (dB)</label><input type="number" min="-12" max="12" step="0.5" value="${t.high}" data-prop="high"></div><div class="track-knob"><label>Gate threshold (dBFS)</label><input type="number" min="-70" max="0" step="1" value="${t.gate}" data-prop="gate"></div><div class="track-knob"><label>Dinamik</label><label class="consent-line"><input type="checkbox" data-prop="compress" ${t.compress?'checked':''}> Hafif comp.</label></div><div class="track-knob"><label>Comp threshold (dB)</label><input type="number" min="-60" max="0" step="1" value="${t.compThreshold??-24}" data-prop="compThreshold"></div><div class="track-knob"><label>Comp ratio</label><input type="number" min="1" max="20" step="0.5" value="${t.compRatio??3}" data-prop="compRatio"></div><div class="track-knob"><label>Attack (ms)</label><input type="number" min="0.1" max="100" step="0.1" value="${(t.compAttack??0.008)*1000}" data-prop="compAttackMs"></div><div class="track-knob"><label>Release (ms)</label><input type="number" min="10" max="1000" step="10" value="${(t.compRelease??0.18)*1000}" data-prop="compReleaseMs"></div></div><footer class="track-actions"><button class="tiny-btn" data-action="mute">${t.muted?'Muted':'Mute'}</button><button class="tiny-btn" data-action="up" ${i===0?'disabled':''}>↑</button><button class="tiny-btn" data-action="down" ${i===mixerTracks.length-1?'disabled':''}>↓</button><button class="tiny-btn danger" data-action="remove">Katmanı kaldır</button><span class="muted">Kaynak değiştirilmez</span></footer></article>`).join('');}
function onTrackControl(e){const el=e.target.closest('[data-prop],[data-action]');if(!el)return;const card=el.closest('[data-track]');if(!card)return;const t=mixerTracks.find(x=>x.id===Number(card.dataset.track));if(!t)return;if(el.dataset.prop){const prop=el.dataset.prop;if(prop==='category'){t.category=el.value;return;}if(el.type==='checkbox')t[prop]=el.checked;else{let n=Number(el.value);if(!Number.isFinite(n))return;if(prop==='trimIn')n=Math.max(0,Math.min(t.duration-.05,n));if(prop==='trimOut')n=Math.max(t.trimIn+.05,Math.min(t.duration,n));if(prop==='fadeIn'||prop==='fadeOut')n=Math.max(0,Math.min(t.duration,n));if(prop==='start')n=Math.max(0,n);if(prop==='gate')n=Math.max(-70,Math.min(0,n));if(prop==='compThreshold')n=Math.max(-60,Math.min(0,n));if(prop==='compRatio')n=Math.max(1,Math.min(20,n));if(prop==='compAttackMs'){t.compAttack=Math.max(0.0001,Math.min(0.1,n/1000));return;}if(prop==='compReleaseMs'){t.compRelease=Math.max(0.01,Math.min(1,n/1000));return;}t[prop]=n;}if(el.type==='range'&&el.dataset.prop==='gain')el.previousElementSibling.textContent=`Gain ${fmt(20*Math.log10(Math.max(t.gain,.00001)),1)} dB`;else if(el.type==='range'&&el.dataset.prop==='pan')el.previousElementSibling.textContent=`Pan ${fmt(t.pan,2)}`;if(e.type==='change'||el.type==='checkbox')renderTracks();return;}if(el.dataset.action==='preset'&&el.value){applyDialoguePreset(t,el.value);renderTracks();setStatus('Hazır konuşma ayarı uygulandı; kritik teslimden önce dinle.');return;}if(el.dataset.action==='mute'){t.muted=!t.muted;renderTracks();}if(el.dataset.action==='remove'){mixerTracks=mixerTracks.filter(x=>x.id!==t.id);renderTracks();}if(el.dataset.action==='up'||el.dataset.action==='down'){const index=mixerTracks.indexOf(t),target=el.dataset.action==='up'?index-1:index+1;if(target>=0&&target<mixerTracks.length){[mixerTracks[index],mixerTracks[target]]=[mixerTracks[target],mixerTracks[index]];renderTracks();}}}
function validateTrack(t){const start=Math.max(0,Number(t.start)||0),trimIn=Math.max(0,Math.min(t.duration-.05,Number(t.trimIn)||0)),trimOut=Math.max(trimIn+.05,Math.min(t.duration,Number(t.trimOut)||t.duration));return {start,trimIn,trimOut,dur:trimOut-trimIn};}
function gateBuffer(buffer,thresholdDb){if(thresholdDb<=-69.9)return buffer;const ctx=new OfflineAudioContext(buffer.numberOfChannels,buffer.length,buffer.sampleRate);const out=ctx.createBuffer(buffer.numberOfChannels,buffer.length,buffer.sampleRate);const win=Math.max(1,Math.round(buffer.sampleRate*.01));const attack=Math.exp(-1/(buffer.sampleRate*.008)),release=Math.exp(-1/(buffer.sampleRate*.08));const thr=Math.pow(10,thresholdDb/20);for(let ch=0;ch<buffer.numberOfChannels;ch++){const input=buffer.getChannelData(ch),dest=out.getChannelData(ch);let gain=0;for(let start=0;start<input.length;start+=win){const end=Math.min(input.length,start+win);let sum=0;for(let i=start;i<end;i++)sum+=input[i]*input[i];const rms=Math.sqrt(sum/Math.max(1,end-start));const goal=rms>=thr?1:.04;const coeff=goal>gain?attack:release;for(let i=start;i<end;i++){gain=goal+(gain-goal)*coeff;dest[i]=input[i]*gain;}}}return out;}

const gateCache = new WeakMap();
function gateBufferCached(track, buffer, thresholdDb){
 const key=`${thresholdDb}:${track.trimIn}:${track.trimOut}:${buffer.sampleRate}:${buffer.length}`;
 const cached=gateCache.get(track);
 if(cached&&cached.buffer===buffer&&cached.key===key)return cached.result;
 const result=gateBuffer(buffer,thresholdDb);
 gateCache.set(track,{buffer,key,result});
 return result;
}
async function renderMix(){if(!mixerTracks.length)throw new Error('Önce ses dosyası ekle.');const enabled=mixerTracks.filter(t=>!t.muted);if(!enabled.length)throw new Error('Tüm katmanlar sessize alınmış.');const specs=enabled.map(t=>({t,...validateTrack(t)}));const length=Math.max(...specs.map(x=>x.start+x.dur));if(length<=0||length>3600)throw new Error('Miks süresi 0-3600 saniye aralığında olmalı.');const rate=48000,frames=Math.ceil(length*rate),outputBytes=frames*2*4,wavBytes=frames*2*2+44,sourceBytes=decodedAudioBytes(),gateBytes=enabled.filter(t=>t.gate>-69.9).reduce((sum,t)=>sum+t.buffer.length*t.buffer.numberOfChannels*4,0);if(outputBytes>MAX_RENDER_AUDIO_BYTES||sourceBytes+gateBytes+outputBytes+wavBytes>MAX_AUDIO_WORK_BYTES)throw new Error('RAM koruması: bu miksin tahmini çalışma belleği sınırı aşıyor. Daha kısa bölüm, az katman veya gate kapalı ayarlarla dene.');const off=new OfflineAudioContext(2,frames,rate);for(const s of specs){const t=s.t;let buffer=t.gate>-69.9?gateBufferCached(t,t.buffer,t.gate):t.buffer;const src=off.createBufferSource();src.buffer=buffer;let node=src;const hp=off.createBiquadFilter();hp.type='highpass';hp.frequency.value=Math.max(20,Math.min(20000,t.hpf));node.connect(hp);node=hp;if(Math.abs(t.low)>.01){const f=off.createBiquadFilter();f.type='lowshelf';f.frequency.value=180;f.gain.value=t.low;node.connect(f);node=f;}if(Math.abs(t.high)>.01){const f=off.createBiquadFilter();f.type='highshelf';f.frequency.value=5000;f.gain.value=t.high;node.connect(f);node=f;}if(t.compress){const comp=off.createDynamicsCompressor();comp.threshold.value=t.compThreshold??-24;comp.knee.value=20;comp.ratio.value=t.compRatio??3;comp.attack.value=t.compAttack??.008;comp.release.value=t.compRelease??.18;node.connect(comp);node=comp;}const gain=off.createGain();const base=Math.max(0,Math.min(2,t.gain));const fs=Math.min(s.dur/2,Math.max(0,t.fadeIn)),fe=Math.min(s.dur/2,Math.max(0,t.fadeOut));gain.gain.setValueAtTime(fs>0?.0001:base,s.start);if(fs>0)gain.gain.linearRampToValueAtTime(base,s.start+fs);if(fe>0){gain.gain.setValueAtTime(base,s.start+s.dur-fe);gain.gain.linearRampToValueAtTime(.0001,s.start+s.dur);}node.connect(gain);node=gain;const pan=off.createStereoPanner();pan.pan.value=Math.max(-1,Math.min(1,t.pan));node.connect(pan).connect(off.destination);src.start(s.start,s.trimIn,s.dur);}const rendered=await off.startRendering();let peak=0;for(let ch=0;ch<rendered.numberOfChannels;ch++){const data=rendered.getChannelData(ch);for(let i=0;i<data.length;i++)peak=Math.max(peak,Math.abs(data[i]));}const ceiling=Math.pow(10,-1/20);lastMasterGainDb=peak>ceiling?20*Math.log10(ceiling/peak):0;if(lastMasterGainDb<0){const gain=Math.pow(10,lastMasterGainDb/20);for(let ch=0;ch<rendered.numberOfChannels;ch++){const data=rendered.getChannelData(ch);for(let i=0;i<data.length;i++)data[i]*=gain;}}return rendered;}
function audioBufferToWav(buffer){const channels=2,rate=buffer.sampleRate,len=buffer.length;const out=new ArrayBuffer(44+len*channels*2),view=new DataView(out);const writeString=(off,s)=>{for(let i=0;i<s.length;i++)view.setUint8(off+i,s.charCodeAt(i));};writeString(0,'RIFF');view.setUint32(4,36+len*channels*2,true);writeString(8,'WAVE');writeString(12,'fmt ');view.setUint32(16,16,true);view.setUint16(20,1,true);view.setUint16(22,channels,true);view.setUint32(24,rate,true);view.setUint32(28,rate*channels*2,true);view.setUint16(32,channels*2,true);view.setUint16(34,16,true);writeString(36,'data');view.setUint32(40,len*channels*2,true);const left=buffer.getChannelData(0),right=buffer.getChannelData(1);let off=44;for(let i=0;i<len;i++){for(const v0 of [left[i],right[i]]){const v=Math.max(-1,Math.min(1,v0));view.setInt16(off,v<0?v*32768:v*32767,true);off+=2;}}return new Blob([out],{type:'audio/wav'});}
async function previewMix(){try{stopMixerPreview();$('mixStatus').textContent='Miks hazırlanıyor…';const rendered=await renderMix();mixerAudioContext=mixerAudioContext||(new AudioContext());await mixerAudioContext.resume();mixerPreviewSource=mixerAudioContext.createBufferSource();mixerPreviewSource.buffer=rendered;mixerPreviewSource.connect(mixerAudioContext.destination);mixerPreviewSource.onended=()=>{$('mixStop').disabled=true;$('mixPreview').disabled=false;};mixerPreviewSource.start();$('mixStop').disabled=false;$('mixPreview').disabled=true;$('mixStatus').textContent=`Önizleme çalıyor · ${fmt(rendered.duration,2)} s · ${rendered.sampleRate} Hz · ana kazanç ${fmt(lastMasterGainDb,2)} dB`; }catch(err){$('mixStatus').textContent='Miks önizleme hatası: '+err.message;}}
function stopMixerPreview(){if(mixerPreviewSource){try{mixerPreviewSource.stop();}catch(_){ }mixerPreviewSource.disconnect();mixerPreviewSource=null;}if($('mixStop'))$('mixStop').disabled=true;if($('mixPreview'))$('mixPreview').disabled=false;}
async function renderAndDownloadMix(){try{$('mixRender').disabled=true;$('mixStatus').textContent='Stereo WAV render ediliyor…';const rendered=await renderMix();const blob=audioBufferToWav(rendered);downloadBlob(blob,'Stagepulse_Miks.wav');$('mixStatus').textContent=`WAV hazır · ${fmt(rendered.duration,2)} s · 48 kHz / 16-bit PCM · ana kazanç ${fmt(lastMasterGainDb,2)} dB · tepe güvenliği -1 dBFS`;setStatus('Yeni stereo WAV üretildi.');}catch(err){$('mixStatus').textContent='Render başarısız: '+err.message;}finally{$('mixRender').disabled=false;}}
function exportMixProject(){downloadBlob(new Blob([JSON.stringify(mixProjectPayload(),null,2)],{type:'application/json'}),'Stagepulse_Ses_Projesi.json');$('projectStatus').textContent='Proje ayarları JSON olarak dışa aktarıldı. Medya dosyaları gömülmedi.';}
async function loadMixProject(e){const f=e.target.files&&e.target.files[0];if(!f)return;try{const p=JSON.parse(await f.text());if(!p||typeof p!=='object'||!Array.isArray(p.tracks)||!Array.isArray(p.cues))throw new Error('Proje biçimi tanınmadı.');if(p.tracks.length>12||p.cues.length>10000)throw new Error('Proje sınırları aşıyor.');pendingMixProject=p;cueRows=p.cues.filter(c=>c&&Number.isFinite(Number(c.time))).map(c=>({id:c.id||Date.now()+Math.random(),time:Math.max(0,Number(c.time)),type:String(c.type||'Teknik not').slice(0,80),text:String(c.text||'').slice(0,2000)})).sort((a,b)=>a.time-b.time);videoSceneMarkers=Array.isArray(p.sceneMarkers)?p.sceneMarkers.map(Number).filter(n=>Number.isFinite(n)&&n>=0).slice(0,1000):[];editDraft=Array.isArray(p.editDraft)?p.editDraft:[];if(mixerTracks.length)applyPendingProject();renderCueRows();renderMixerCues();renderSceneMarkers();$('projectStatus').textContent=mixerTracks.length?'Proje ayarları yüklendi; eşleşen katmanlar güncellendi.':'Proje ayarları yüklendi. Şimdi aynı ses kaynaklarını seç; isimleri eşleşen kanallara ayarlar uygulanacak.';setStatus('Proje JSON yüklendi.');}catch(err){$('projectStatus').textContent='Proje yüklenemedi: '+err.message;}finally{$('mixProjectFile').value='';}}
function applyPendingProject(){if(!pendingMixProject)return;const defs=Array.isArray(pendingMixProject.tracks)?pendingMixProject.tracks:[];let matched=0;for(const t of mixerTracks){const d=defs.find(x=>String(x.name).toLocaleLowerCase('tr')===String(t.name).toLocaleLowerCase('tr'));if(!d)continue;matched++;for(const key of ['gain','pan','start','trimIn','trimOut','fadeIn','fadeOut','hpf','low','high','gate','compThreshold','compRatio','compAttack','compRelease']){if(Number.isFinite(Number(d[key])))t[key]=Number(d[key]);}for(const key of ['compress','muted'])if(typeof d[key]==='boolean')t[key]=d[key];if(['Diyalog','Müzik','Efekt','Ambiyans','Diğer'].includes(d.category))t.category=d.category;t.trimIn=Math.max(0,Math.min(t.duration-.05,t.trimIn));t.trimOut=Math.max(t.trimIn+.05,Math.min(t.duration,t.trimOut));t.start=Math.max(0,t.start);t.fadeIn=Math.max(0,Math.min(t.duration,t.fadeIn));t.fadeOut=Math.max(0,Math.min(t.duration,t.fadeOut));}if(matched){pendingMixProject=null;$('projectStatus').textContent=`Proje ayarları ${matched} ses katmanına uygulandı. Kaynak dosyalar yerelde kaldı.`;}}
async function analyzeAudioEvidence(){const file=$('evidenceAudioFile').files&&$('evidenceAudioFile').files[0];if(!file){$('audioEvidenceReport').textContent='Önce bir ses dosyası seç.';return;}try{$('analyzeAudioEvidence').disabled=true;$('audioEvidenceReport').textContent='Dosya yerel olarak çözümlenip ölçülüyor…';const ctx=mixerAudioContext||(mixerAudioContext=new (window.AudioContext||window.webkitAudioContext)());const buffer=await ctx.decodeAudioData((await file.arrayBuffer()).slice(0));let peak=0,squares=0,count=0,near=0,dcSum=0,channelStats=[];for(let ch=0;ch<buffer.numberOfChannels;ch++){const a=buffer.getChannelData(ch);let cp=0,cs=0,dc=0,cn=0;for(let i=0;i<a.length;i++){const v=a[i],av=Math.abs(v);cp=Math.max(cp,av);cs+=v*v;dc+=v;cn+=av>=.999?1:0;}peak=Math.max(peak,cp);squares+=cs;count+=a.length;near+=cn;dcSum+=dc;channelStats.push({peakDbfs:cp?20*Math.log10(cp):null,rmsDbfs:cs&&a.length?20*Math.log10(Math.sqrt(cs/a.length)):null,dc:a.length?dc/a.length:0});}let corr=null;if(buffer.numberOfChannels>=2){const a=buffer.getChannelData(0),b=buffer.getChannelData(1),stride=Math.max(1,Math.floor(a.length/100000));let aa=0,bb=0,ab=0,n=0;for(let i=0;i<Math.min(a.length,b.length);i+=stride){aa+=a[i]*a[i];bb+=b[i]*b[i];ab+=a[i]*b[i];n++;}corr=aa&&bb?ab/Math.sqrt(aa*bb):null;}audioEvidenceData={file:file.name,fileBytes:file.size,channels:buffer.numberOfChannels,sampleRate:buffer.sampleRate,frames:buffer.length,duration:buffer.duration,peakDbfs:peak?20*Math.log10(peak):null,rmsDbfs:squares&&count?20*Math.log10(Math.sqrt(squares/count)):null,nearClipSamples:near,nearClipPercent:count?100*near/count:0,channelStats,stereoCorrelation:corr,scope:'Tarayıcı kod çözücüsünün PCM örnekleri üzerinde sample peak/RMS/DC/kanal korelasyonu. LUFS, oversampled true peak veya kalibreli dB SPL değildir.'};renderAudioEvidence();setStatus('Yerel ses kanıt analizi tamamlandı.');}catch(err){$('audioEvidenceReport').textContent='Dosya çözümlenemedi: '+err.message+'\nBu tarayıcı ses biçimini desteklemeyebilir.';}finally{$('analyzeAudioEvidence').disabled=false;}}
function renderAudioEvidence(){if(!audioEvidenceData){$('audioEvidenceReport').textContent='Ölçüm yok.';return;}const r=audioEvidenceData;const rows=[['Dosya',r.file],['Kanal / örnekleme',`${r.channels} ch · ${r.sampleRate} Hz`],['Süre',fmt(r.duration,3)+' s'],['Sample peak',r.peakDbfs===null?'Sessiz':fmt(r.peakDbfs,2)+' dBFS'],['RMS',r.rmsDbfs===null?'Sessiz':fmt(r.rmsDbfs,2)+' dBFS'],['Yakın clipping örneği',`${r.nearClipSamples} · ${fmt(r.nearClipPercent,5)}%`],['Stereo korelasyonu',r.stereoCorrelation===null?'Uygulanamaz':fmt(r.stereoCorrelation,3)],['DC offset / kanal',r.channelStats.map((x,i)=>`CH${i+1}: ${fmt(x.dc,5)}`).join(' · ')]];$('audioEvidenceReport').innerHTML='<div class="report-table">'+rows.map(([a,b])=>`<div>${safeText(a)}</div><div>${safeText(b)}</div>`).join('')+'</div><p class="muted">'+safeText(r.scope)+'</p>';}
function exportEvidenceReport(){const report={version:'3.8.10',created:new Date().toISOString(),audioEvidence:audioEvidenceData,project:mixProjectPayload(),limits:['Bu rapor otomatik kalite kontrol desteğidir; kritik dosyalar dinlenmelidir.','Sample peak/RMS, LUFS, dBTP ve kalibreli dB SPL yerine geçmez.']};downloadBlob(new Blob([JSON.stringify(report,null,2)],{type:'application/json'}),'Stagepulse_QC_Kanit_Raporu.json');$('projectStatus').textContent='QC kanıt raporu JSON olarak dışa aktarıldı.';}
async function indexSoundLibrary(){const files=Array.from($('soundLibraryFiles').files||[]);if(!files.length){$('soundLibraryResults').textContent='Önce yerel ses dosyaları seç.';return;}if(files.length>150){$('soundLibraryResults').textContent='Bir indeks için en fazla 150 dosya seç.';return;}const ctx=mixerAudioContext||(mixerAudioContext=new (window.AudioContext||window.webkitAudioContext)());soundLibraryIndex=[];$('indexSoundLibrary').disabled=true;$('soundLibraryResults').textContent='Yerel dosyalar inceleniyor…';try{for(let i=0;i<files.length;i++){const f=files[i];try{const b=await ctx.decodeAudioData((await f.arrayBuffer()).slice(0));let peak=0,ss=0,n=0;for(let ch=0;ch<b.numberOfChannels;ch++){const a=b.getChannelData(ch);for(let j=0;j<a.length;j++){const v=a[j];peak=Math.max(peak,Math.abs(v));ss+=v*v;n++;}}soundLibraryIndex.push({name:f.name,size:f.size,duration:b.duration,sampleRate:b.sampleRate,channels:b.numberOfChannels,peakDbfs:peak?20*Math.log10(peak):null,rmsDbfs:ss&&n?20*Math.log10(Math.sqrt(ss/n)):null,category:guessAudioCategory(f.name)});}catch(err){soundLibraryIndex.push({name:f.name,size:f.size,duration:null,sampleRate:null,channels:null,peakDbfs:null,rmsDbfs:null,category:guessAudioCategory(f.name),error:'Tarayıcı çözemedi'});}if(i%5===0)await new Promise(resolve=>requestAnimationFrame(resolve));}renderSoundLibrary();setStatus(`Ses kütüphanesi yerel indekslendi: ${soundLibraryIndex.length} dosya.`);}catch(err){$('soundLibraryResults').textContent='İndeks başarısız: '+err.message;}finally{$('indexSoundLibrary').disabled=false;}}
function renderSoundLibrary(){const q=$('soundLibrarySearch').value.trim().toLocaleLowerCase('tr');const xs=soundLibraryIndex.filter(x=>(x.name+' '+x.category).toLocaleLowerCase('tr').includes(q));if(!xs.length){$('soundLibraryResults').textContent=soundLibraryIndex.length?'Arama sonucu yok.':'Henüz indeks oluşturulmadı. Dosyalar yüklenmez.';return;}$('soundLibraryResults').innerHTML='<div class="report-table">'+xs.map(x=>`<div>${safeText(x.name)}</div><div>${safeText(x.category)} · ${x.duration===null?'süre yok':fmt(x.duration,2)+' s'} · peak ${x.peakDbfs===null?'—':fmt(x.peakDbfs,1)+' dBFS'}</div>`).join('')+'</div><p class="muted">${xs.length} / ${soundLibraryIndex.length} dosya · sadece bu oturumdaki dosya adları ve ölçümleri gösterilir.</p>';}
function matchSoundCues(){if(!cueRows.length||!soundLibraryIndex.length){$('soundPlanOutput').value='Cue eşleştirmesi için hem cue notları hem de yerel ses indeksi gerekli.';return;}const stop=new Set(['için','olan','bunu','şunu','ses','not','the','and','with','from','clip','audio']);const lines=[];for(const cue of cueRows){const words=(String(cue.text)+' '+String(cue.type)).toLocaleLowerCase('tr').split(/[^\p{L}\p{N}]+/u).filter(w=>w.length>3&&!stop.has(w));const ranked=soundLibraryIndex.map(x=>({x,score:words.reduce((n,w)=>n+(x.name.toLocaleLowerCase('tr').includes(w)?1:0),0)})).filter(x=>x.score>0).sort((a,b)=>b.score-a.score).slice(0,3);lines.push({time:cue.time,cue:cue.text,category:cue.type,matches:ranked.map(r=>({name:r.x.name,score:r.score,category:r.x.category}))});}editDraft=lines;$('soundPlanOutput').value=JSON.stringify(lines,null,2);setStatus('Cue ve yerel ses dosyası adları arasında eşleşme önerileri üretildi.');}
function renderSceneMarkers(){if(!videoSceneMarkers.length){$('sceneMarkerList').innerHTML='';return;}$('sceneMarkerList').innerHTML='<div class="scene-markers">'+videoSceneMarkers.map((t,i)=>`<button class="tiny-btn" data-seek-scene="${i}">${fmt(t,2)} s · ${i===0?'Başlangıç':i===videoSceneMarkers.length-1?'Bitiş':'Sahne '+i}</button>`).join('')+'</div>';}
async function seekLocalVideo(time){const video=$('localVideo');if(Math.abs(video.currentTime-time)<.03)return;await new Promise((resolve,reject)=>{const timer=setTimeout(()=>{cleanup();reject(new Error('Video arama zaman aşımı.'));},4000);const done=()=>{cleanup();resolve();};function cleanup(){clearTimeout(timer);video.removeEventListener('seeked',done);}video.addEventListener('seeked',done,{once:true});video.currentTime=Math.min(Math.max(0,time),Math.max(0,(video.duration||time)-.02));});}
async function analyzeVideoLocal(){const video=$('localVideo');if(!video.src||!Number.isFinite(video.duration)||video.duration<=0){$('videoAnalysisReport').textContent='Önce süre bilgisi yüklenmiş bir yerel video seç.';return;}const wasPlaying=!video.paused,oldTime=video.currentTime;video.pause();$('analyzeVideoLocal').disabled=true;$('videoAnalysisReport').textContent='Video kareleri yerel olarak örnekleniyor…';try{const c=document.createElement('canvas'),w=80,h=45;c.width=w;c.height=h;const ctx=c.getContext('2d',{willReadFrequently:true});const interval=Math.max(.5,video.duration/160);let prev=null,changes=[],samples=0;for(let t=0;t<video.duration-.02;t+=interval){await seekLocalVideo(t);await new Promise(resolve=>requestAnimationFrame(resolve));ctx.drawImage(video,0,0,w,h);const px=ctx.getImageData(0,0,w,h).data;let lum=0;const vector=new Uint8Array(w*h);for(let j=0,k=0;j<px.length;j+=4,k++){const v=Math.round(.2126*px[j]+.7152*px[j+1]+.0722*px[j+2]);vector[k]=v;lum+=v;}if(prev){let diff=0;for(let j=0;j<vector.length;j++)diff+=Math.abs(vector[j]-prev[j]);diff/=vector.length;samples++;if(diff>26&&(!changes.length||t-changes[changes.length-1]>=1.5))changes.push({time:t,difference:diff,brightness:lum/vector.length});}prev=vector;if(samples%12===0)await new Promise(resolve=>requestAnimationFrame(resolve));}videoSceneMarkers=[0,...changes.map(x=>x.time),Math.max(0,video.duration)];renderSceneMarkers();$('videoAnalysisReport').innerHTML=`<strong>${samples+1} örnek kare</strong><br>${changes.length} olası sahne geçişi bulundu.<br><small class="muted">Eşik tabanlı görüntü farkı; kamera hareketi/ışık değişimi yanlış pozitif üretebilir, sakin sahne kesmelerini kaçırabilir.</small>`;setStatus('Yerel video taraması tamamlandı; geçişleri gözden geçir.');}catch(err){$('videoAnalysisReport').textContent='Video taraması başarısız: '+err.message;}finally{try{await seekLocalVideo(oldTime);if(wasPlaying)await video.play();}catch(_){}$('analyzeVideoLocal').disabled=false;}}
function stageSceneCues(){if(videoSceneMarkers.length<=2){$('videoAnalysisReport').textContent='Önce video sahne taraması yap; en az bir geçiş bulunmalı.';return;}for(const t of videoSceneMarkers.slice(1,-1)){if(!cueRows.some(c=>c.type==='Sahne sınırı'&&Math.abs(c.time-t)<.1))addCue({time:t,type:'Sahne sınırı',text:'Olası görüntü kesmesi. Diyalog, ambiyans, müzik ve efekt sürekliliğini kontrol et.'});}renderSceneMarkers();$('videoAnalysisReport').textContent='Sahne işaretleri cue listesine eklendi. Her işareti görüntü ve sesle doğrula.';}
function buildLocalSoundPlan(){const rows=[];for(const t of videoSceneMarkers.slice(1,-1))rows.push({time:Number(t.toFixed(3)),type:'Sahne sınırı',note:'Görüntü geçişinde ses sürekliliğini kontrol et.'});for(const c of cueRows)rows.push({time:c.time,type:c.type,note:c.text});for(const t of mixerTracks)rows.push({time:t.start,type:t.category||guessAudioCategory(t.name),note:`Kaynak: ${t.name}; trim ${fmt(t.trimIn,2)}–${fmt(t.trimOut,2)} s; gain ${fmt(20*Math.log10(Math.max(t.gain,.00001)),1)} dB.`});editDraft=rows.filter(x=>Number.isFinite(x.time)).sort((a,b)=>a.time-b.time);$('soundPlanOutput').value=JSON.stringify({method:'Yerel kural tabanlı taslak; otomatik yapay zekâ kararı değil.',created:new Date().toISOString(),duration:Math.max($('localVideo').duration||0,...mixerTracks.map(t=>t.start+t.trimOut)),items:editDraft},null,2);setStatus('Yerel ses planı taslağı oluşturuldu.');}
function applyPlanCues(){if(!editDraft.length){buildLocalSoundPlan();if(!editDraft.length)return;}let added=0;for(const item of editDraft){const time=Number(item.time)||0,type=String(item.type||item.category||'Teknik not'),text=String(item.note||item.cue||item.name||'Yerel plan işareti');if(!cueRows.some(c=>Math.abs(c.time-time)<.05&&c.type===type&&c.text===text)){cueRows.push({id:Date.now()+Math.random(),time,type,text});added++;}}cueRows.sort((a,b)=>a.time-b.time);renderCueRows();renderMixerCues();persistStudentLocal();setStatus(`${added} taslak işareti cue listesine eklendi.`);}
function exportPlanJSON(){downloadBlob(new Blob([JSON.stringify({version:'3.8.10',created:new Date().toISOString(),markers:videoSceneMarkers,plan:editDraft},null,2)],{type:'application/json'}),'Stagepulse_Ses_Plani.json');}
function exportPlanCSV(){const quote=s=>'"'+String(s??'').replace(/"/g,'""')+'"';const rows=[['time_seconds','type','note'],...editDraft.map(x=>[Number(x.time)||0,quote(x.type||x.category||''),quote(x.note||x.cue||x.name||'')])];downloadBlob(new Blob(['\ufeff'+rows.map(r=>r.join(',')).join('\r\n')],{type:'text/csv;charset=utf-8'}),'Stagepulse_Ses_Plani.csv');}
function loadLocalVideo(e){const file=e.target.files&&e.target.files[0];if(!file)return;if(videoObjectUrl)URL.revokeObjectURL(videoObjectUrl);videoObjectUrl=URL.createObjectURL(file);$('localVideo').src=videoObjectUrl;$('localVideo').load();$('framePreview').textContent='';videoSceneMarkers=[];$('videoAnalysisReport').textContent='Yeni video yüklendi; sahne taramasını tekrar çalıştır.';$('sceneMarkerList').innerHTML='';}
function captureFrame(){const video=$('localVideo');if(!video.videoWidth||!video.videoHeight){alert('Önce yerel bir video seç ve oynatıcıda bir kareye git.');return;}const canvas=document.createElement('canvas');const scale=Math.min(1,960/video.videoWidth);canvas.width=Math.round(video.videoWidth*scale);canvas.height=Math.round(video.videoHeight*scale);canvas.getContext('2d').drawImage(video,0,0,canvas.width,canvas.height);canvas.toBlob(blob=>{if(!blob)return;const url=URL.createObjectURL(blob);$('framePreview').innerHTML=`<img src="${url}" alt="Yakalanan video karesi"><small class="muted">${fmt(video.currentTime,3)} s noktasından yerel kare.</small>`;addCue({time:video.currentTime,type:'Video karesi',text:'Yakalanan kareyi incele; ilgili ses/ambiyans işaretini ekle.'});},'image/jpeg',.85);}
function addCue(cue){const time=Math.max(0,Number(cue.time)||0);cueRows.push({id:Date.now()+Math.random(),time,type:cue.type||'Teknik not',text:cue.text||''});cueRows.sort((a,b)=>a.time-b.time);renderCueRows();renderMixerCues();persistStudentLocal();}
function deleteCue(id){cueRows=cueRows.filter(c=>String(c.id)!==String(id));renderCueRows();renderMixerCues();persistStudentLocal();}
function renderCueRows(){const html=cueRows.length?cueRows.map(c=>`<div class="cue-row"><span class="cue-time">${fmt(c.time,3)} s</span><span class="cue-kind">${safeText(c.type)}</span><span class="cue-text">${safeText(c.text)}</span><button class="cue-remove" data-delete-cue="${c.id}" title="Cue sil">×</button></div>`).join(''):'<p class="muted">Henüz cue yok.</p>';$('cueListFull').innerHTML=html;document.querySelectorAll('[data-delete-cue]').forEach(b=>b.addEventListener('click',()=>deleteCue(b.dataset.deleteCue)));}
function renderMixerCues(){if(!$('mixerCueList'))return;$('mixerCueList').innerHTML=cueRows.length?cueRows.slice(-8).map(c=>`<div class="cue-row"><span class="cue-time">${fmt(c.time,2)} s</span><span class="cue-kind">${safeText(c.type)}</span><span class="cue-text">${safeText(c.text)}</span><button class="cue-remove" data-delete-cue="${c.id}">×</button></div>`).join(''):'<p class="muted">Cue listesi boş.</p>';document.querySelectorAll('#mixerCueList [data-delete-cue]').forEach(b=>b.addEventListener('click',()=>deleteCue(b.dataset.deleteCue)));}
function initCues(){$('saveCue').addEventListener('click',()=>{const text=$('cueText').value.trim();if(!text){$('cueText').focus();return;}let time=$('cueTime').value.trim();let seconds=Number(time);if(time.includes(':')){const parts=time.split(':').map(Number);if(parts.some(n=>!Number.isFinite(n))){alert('Zaman saniye veya ss:dd:ss biçiminde olmalı.');return;}seconds=parts.length===3?parts[0]*3600+parts[1]*60+parts[2]:parts.length===2?parts[0]*60+parts[1]:NaN;}if(!Number.isFinite(seconds)||seconds<0){alert('Geçerli zaman gir.');return;}addCue({time:seconds,type:$('cueType').value,text});$('cueText').value='';});$('exportCueJson').addEventListener('click',()=>downloadBlob(new Blob([JSON.stringify(cueRows,null,2)],{type:'application/json'}),'Stagepulse_Cue_Listesi.json'));$('exportCueCsv').addEventListener('click',()=>{const quote=s=>'"'+String(s).replace(/"/g,'""')+'"';const csv=['time_seconds,type,note',...cueRows.map(c=>[c.time,quote(c.type),quote(c.text)].join(','))].join('\r\n');downloadBlob(new Blob(['\ufeff'+csv],{type:'text/csv;charset=utf-8'}),'Stagepulse_Cue_Listesi.csv');});$('clearCues').addEventListener('click',()=>{if(confirm('Cue listesi temizlensin mi?')){cueRows=[];renderCueRows();renderMixerCues();persistStudentLocal();}});renderCueRows();}

// --- Checklists and student records ---
function initChecklists(){$('checklistType').addEventListener('change',renderChecklist);$('saveChecklist').addEventListener('click',async()=>{persistChecklistState();await saveStudentProfile(false);setStatus('Kontrol listesi profille kaydedildi.');});$('resetChecklist').addEventListener('click',()=>{if(confirm('Bu kontrol listesi sıfırlansın mı?')){studentData.checklists[$('checklistType').value]=[];renderChecklist();persistStudentLocal();}});}
function renderChecklist(){const key=$('checklistType').value,items=checklistData[key]||[],checked=new Set(studentData.checklists[key]||[]);$('checklistItems').innerHTML=items.map((label,i)=>`<label class="check-item"><input type="checkbox" data-check-index="${i}" ${checked.has(i)?'checked':''}><span>${safeText(label)}</span></label>`).join('');$('checklistItems').querySelectorAll('input').forEach(inp=>inp.addEventListener('change',()=>{persistChecklistState();updateHomeMetrics();persistStudentLocal();}));}
function persistChecklistState(){const key=$('checklistType').value;studentData.checklists[key]=Array.from($('checklistItems').querySelectorAll('input:checked')).map(i=>Number(i.dataset.checkIndex));}
function initStudent(){
 $('studentLoad').addEventListener('click',()=>{const name=$('studentSelect').value||$('studentName').value.trim();if(!name){alert('Kişisel çalışma profili seç veya ad gir.');return;}if(profiles[name]){activeStudent=name;loadStudentData(name);$('studentName').value=name;setStatus('Kişisel çalışma profili yüklendi: '+name);}else{activeStudent=name;studentData={completedModules:[],checklists:{},cues:[]};cueRows=[];refreshProfiles();renderStudentModules();renderChecklist();renderCueRows();renderMixerCues();updateHomeMetrics();setStatus('Yeni kişisel çalışma profili hazır.');}});
 $('studentSave').addEventListener('click',()=>saveStudentProfile(true));
 $('studentDelete').addEventListener('click',async()=>{const name=$('studentSelect').value||activeStudent;if(!name||!confirm(`${name} kişisel profili silinsin mi?`))return;if(api()){await api().delete_profile(name);profiles=(await api().load_profiles()).profiles||{};profilesLoaded=true;}else delete profiles[name];if(activeStudent===name){activeStudent='';studentData={completedModules:[],checklists:{},cues:[]};cueRows=[];}refreshProfiles();renderStudentModules();updateHomeMetrics();});
 $('studentExport').addEventListener('click',()=>downloadBlob(new Blob([JSON.stringify({name:activeStudent,profile:{...studentData,completedModules:[]}},null,2)],{type:'application/json'}),'Stagepulse_Yerel_Calisma_Notlari.json'));
 $('studentImport').addEventListener('click',()=>$('studentImportFile').click());
 $('studentImportFile').addEventListener('change',async e=>{const f=e.target.files&&e.target.files[0];if(!f)return;try{const parsed=JSON.parse(await f.text());if(!parsed.profile||typeof parsed.profile!=='object')throw new Error('Profil şeması tanınmadı.');studentData={...parsed.profile,completedModules:[]};activeStudent=String(parsed.name||$('studentName').value||'İçe aktarılan çalışma').slice(0,80);cueRows=Array.isArray(studentData.cues)?studentData.cues:[];renderCueRows();renderMixerCues();renderChecklist();await saveStudentProfile(false);refreshProfiles();}catch(err){alert('İçe aktarma başarısız: '+err.message);}e.target.value='';});
 $('teacherRefreshStudents')?.addEventListener('click',refreshTeacherStudents);
 $('teacherStudentSelect')?.addEventListener('change',async()=>{selectedTeacherStudentId=$('teacherStudentSelect').value;await refreshStudentProgress(selectedTeacherStudentId);});
 renderStudentModules();
}
async function ensureProfilesLoaded(){
 if(profilesLoaded)return profiles;
 if(profilesLoadPromise)return profilesLoadPromise;
 if(!api()){profilesLoaded=true;return profiles;}
 profilesLoadPromise=(async()=>{
  const result=await api().load_profiles();
  profiles=(result&&result.profiles&&typeof result.profiles==='object')?result.profiles:{};
  profilesLoaded=true;
  refreshProfiles();
  if(!activeStudent&&Object.keys(profiles).length)loadStudentData(Object.keys(profiles).sort()[0]);
  return profiles;
 })().catch(err=>{profilesLoaded=false;throw err;}).finally(()=>{profilesLoadPromise=null;});
 return profilesLoadPromise;
}
function refreshProfiles(){
 const select=$('studentSelect');if(!select)return;
 const previous=select.value;
 select.innerHTML='<option value="">Profil seç</option>'+Object.keys(profiles).sort().map(n=>`<option value="${safeText(n)}">${safeText(n)}</option>`).join('');
 if(activeStudent&&profiles[activeStudent])select.value=activeStudent;else if(previous&&profiles[previous])select.value=previous;
 $('activeStudentName').textContent=activeStudent||currentAccountContext?.user?.name||'Öğrenci profili seçilmedi';
 if($('studentName'))$('studentName').value=activeStudent||$('studentName').value;
}
function loadStudentData(name){activeStudent=name;studentData=JSON.parse(JSON.stringify(profiles[name]||{completedModules:[],checklists:{},cues:[]}));studentData.completedModules=[];studentData.checklists=studentData.checklists||{};cueRows=Array.isArray(studentData.cues)?studentData.cues:[];refreshProfiles();renderStudentModules();renderChecklist();renderCueRows();renderMixerCues();updateHomeMetrics();}
function persistStudentLocal(){studentData.cues=cueRows;studentData.completedModules=[];updateHomeMetrics();}
async function saveStudentProfile(showMessage=true){const name=String($('studentName').value||activeStudent).trim();if(!name){if(showMessage)alert('Çalışma profili adı gir.');return;}activeStudent=name;studentData.cues=cueRows;studentData.completedModules=[];try{if(api()){await api().save_profile(name,JSON.stringify(studentData));const r=await api().load_profiles();profiles=r.profiles||{};profilesLoaded=true;}else profiles[name]=JSON.parse(JSON.stringify(studentData));refreshProfiles();renderStudentModules();updateHomeMetrics();if(showMessage)setStatus('Kişisel çalışma notları şifreli olarak kaydedildi: '+name);}catch(err){if(showMessage)alert('Profil kaydedilemedi: '+err.message);}}
async function refreshStudentProgress(studentUserId=''){
 if(!api()||!currentAccountContext||!appAuthorized){renderStudentModules();return;}
 try{const result=await api().student_progress(studentUserId||'');remoteProgress={};for(const row of (result.progress||[]))remoteProgress[row.module_id]=row;renderStudentModules();$('teacherProgressStatus').textContent=`${progressModules.filter(([id])=>remoteProgress[id]?.completed).length} / ${progressModules.length} aşama öğretmen tarafından onaylanmış.`;updateHomeMetrics();}
 catch(err){if($('teacherProgressStatus'))$('teacherProgressStatus').textContent='İlerleme okunamadı: '+err.message;renderStudentModules();}
}
function renderStudentModules(){
 if(!$('studentModules'))return;
 const isTeacher=currentRole==='owner'&&Boolean(selectedTeacherStudentId);
 $('studentModules').innerHTML=progressModules.map(([id,label])=>{
  const row=remoteProgress[id]||{};const done=row.completed===true;const stamp=row.marked_at?new Date(row.marked_at).toLocaleDateString('tr-TR'):'';
  if(isTeacher)return `<label class="student-module"><input type="checkbox" data-server-module="${id}" ${done?'checked':''}><span>${safeText(label)}</span><small>${done?'Onaylandı':'Bekliyor'}</small></label>`;
  const status=done?'Öğretmen onayladı':currentRole==='student'?'Onay bekliyor':'Hesaba giriş gerekli';
  return `<div class="student-module readonly-module"><span>${safeText(label)}</span><small>${status}${stamp?' · '+stamp:''}</small></div>`;
 }).join('');
 if(isTeacher){$('studentModules').querySelectorAll('[data-server-module]').forEach(inp=>inp.addEventListener('change',async()=>{const moduleId=inp.dataset.serverModule;inp.disabled=true;try{const result=await api().teacher_mark_progress(selectedTeacherStudentId,moduleId,inp.checked,$('teacherNote').value.trim());remoteProgress[moduleId]=result.progress;setStatus('Öğretmen onayı sunucuya kaydedildi.');await refreshTeacherStudents();}catch(err){alert('Aşama kaydedilemedi: '+err.message);await refreshStudentProgress(selectedTeacherStudentId);}finally{inp.disabled=false;}}));}
 $('progressRoleBadge').textContent=currentRole==='owner'?'Öğretmen / yönetici':currentRole==='student'?'Öğrenci · salt okunur':'Hesap gerekli';
 $('courseProgressSubtitle').textContent=currentRole==='owner'?'Seçili öğrenci için öğretmen onayı':currentRole==='student'?'Resmî sunucu kayıtları · öğrenci değiştiremez':'Lisanslı hesaba giriş yapınca görünür';
 updateHomeMetrics();
}
function updateHomeMetrics(){const n=progressModules.filter(([id])=>remoteProgress[id]?.completed===true).length,p=Math.round(100*n/progressModules.length);$('studentProgressText').textContent=p+'%';$('studentProgressBar').style.width=p+'%';$('homeProgressValue').textContent=p+'%';$('activeStudentName').textContent=activeStudent||currentAccountContext?.user?.name||'Öğrenci profili seçilmedi';}


// --- Local course documents / student PDF library ---
const fallbackStudentPdfs=[
 {file:'00_Uygulama_Kullanimi_Ogrenci.pdf',title:'Uygulamayı Kullanma Rehberi',description:'Araçlar, çevrimdışı kullanım, mikrofon/RTA sorun giderme ve güvenli öğrenci akışı.'},
 {file:'01_Ses_Muhendisligi_Ogrenci_Ders_Kitabi.pdf',title:'Ses Mühendisliği Öğrenci Ders Kitabı',description:'35 ders; temel kavramlar, formüller, teknik uygulamalar ve vaka analizleri.'},
 {file:'02_Canli_Ses_Live_Sound_Ogrenci_Dersleri.pdf',title:'Canlı Ses / Live Sound Öğrenci Dersleri',description:'FOH, sinyal akışı, sahne patch, monitör/IEM, PA ve DSP.'},
 {file:'03_Studio_Ses_Muhendisligi_Ogrenci_Dersleri.pdf',title:'Stüdyo Ses Mühendisliği Öğrenci Dersleri',description:'Kayıt, düzenleme, miks ve kalite kontrol.'},
 {file:'04_Dijital_Ses_Mikseri_Ogrenci_Calisma_Kitabi.pdf',title:'Dijital Ses Mikseri Öğrenci Çalışma Kitabı',description:'12 günlük uygulama planı ve gözlenebilir kanıtlar.'},
 {file:'05_Canli_Ses_Mikseri_Hizli_Basvuru.pdf',title:'Canlı Ses Mikseri Hızlı Başvuru',description:'Mikser başında hızlı kontrol listeleri.'},
 {file:'06_Ogrenci_Uygulama_Formlari.pdf',title:'Öğrenci Uygulama Formları',description:'Sinyal akışı, ölçüm notları ve öz değerlendirme.'},
 {file:'07_Saha_Olcumu_SPL_Raporlama_Egitimi.pdf',title:'Saha Ölçümü, SPL ve Raporlama Eğitimi',description:'Saha ölçümü, SPL kayıtları ve raporlama sınırları.'},
 {file:'08_SPL_Alan_RTA_Teknik_Uygulama_Eki.pdf',title:'SPL, Alan Boyutlandırma ve RTA Teknik Uygulama Eki',description:'Çözümlü dB/SPL, mesafe, alan kapsaması, oda modları, güvenli maruziyet ve RTA karar desteği.'},
 {file:'09_SPL_dB_3D_Gorsel_Atlasi.pdf',title:'SPL, dB ve 3D Görsel Atlası',description:'SPL model haritaları, mesafe profili, dB basınç/güç karşılaştırmaları ve görsel okuma rehberi.'},
 {file:'10_Midas_M32_Live_Uygulamali_Egitim.pdf',title:'Midas M32 Live Uygulamalı Eğitim',description:'Sinyal akışı, gain staging, bus/monitor, AES50, efektler, scene ve canlı uygulama.'},
 {file:'11_Yamaha_CL5_Uygulamali_Egitim.pdf',title:'Yamaha CL5 Uygulamalı Eğitim',description:'Centralogic, Selected Channel, Dante, HA, mix bus ve scene recall güvenliği.'},
 {file:'12_Allen_Heath_Avantis_Uygulamali_Egitim.pdf',title:'Allen & Heath Avantis Uygulamalı Eğitim',description:'Continuity UI, bank view, I/O patch, bus, scenes, FX ve canlı sorun giderme.'}
];
let studentPdfs=fallbackStudentPdfs,selectedStudentPdf=fallbackStudentPdfs[1].file;
function initDocs(){
 $('pdfDownload').addEventListener('click',async()=>{const item=studentPdfs.find(x=>x.file===selectedStudentPdf)||studentPdfs[0];try{if(api()){const r=await api().save_student_pdf_dialog(item.file);if(r&&r.ok)setStatus('PDF kaydedildi: '+r.path);else if(!(r&&r.cancelled))setStatus((r&&r.error)||'PDF kaydedilemedi.');}else{const a=document.createElement('a');a.href='/egitim_paketleri/'+encodeURIComponent(item.file);a.download=item.file;document.body.appendChild(a);a.click();a.remove();}}catch(err){setStatus('PDF kaydedilemedi: '+err.message);}});
}
async function loadStudentPdfs(){
 if(api()){try{const list=await api().list_student_pdfs();if(Array.isArray(list)&&list.length)studentPdfs=list;}catch(_){} }
 const list=$('studentPdfButtons');if(!list)return;
 list.innerHTML=studentPdfs.map(item=>`<button class="student-pdf-btn ${item.file===selectedStudentPdf?'active':''}" data-student-pdf="${safeText(item.file)}"><strong>${safeText(item.title)}</strong><span>${safeText(item.description||'Öğrenci eğitim materyali')}</span></button>`).join('');
 list.querySelectorAll('[data-student-pdf]').forEach(btn=>btn.addEventListener('click',()=>openStudentPdf(btn.dataset.studentPdf)));
 if(!studentPdfs.some(x=>x.file===selectedStudentPdf))selectedStudentPdf=studentPdfs[0].file;
 openStudentPdf(selectedStudentPdf,false);
}
function openStudentPdf(filename,updateButtons=true){const item=studentPdfs.find(x=>x.file===filename);if(!item)return;selectedStudentPdf=item.file;$('studentPdfTitle').textContent=item.title;$('studentPdfDescription').textContent=item.description||'Öğrenci eğitim PDF dosyası.';$('pdfFrame').src='/egitim_paketleri/'+encodeURIComponent(item.file);if(updateButtons)document.querySelectorAll('[data-student-pdf]').forEach(b=>b.classList.toggle('active',b.dataset.studentPdf===item.file));setStatus('Açık eğitim PDF’si: '+item.title);}
async function loadDocs(){if(!$('docSelect').options.length){let list=[];try{list=api()?await api().list_docs():await fetch('/ui/docs-list.json').then(r=>r.json());}catch(_){list=[];}if(!list.length)list=[{file:'00_BASLANGIC_TR.md',title:'Başlangıç ve güvenli kullanım'}];$('docSelect').innerHTML=list.map(d=>`<option value="${safeText(d.file)}">${safeText(d.title)}</option>`).join('');$('docListButtons').innerHTML=list.map(d=>`<button class="doc-select-btn" data-doc="${safeText(d.file)}">${safeText(d.title)}</button>`).join('');$('docSelect').addEventListener('change',()=>openDoc($('docSelect').value));$('docListButtons').querySelectorAll('[data-doc]').forEach(b=>b.addEventListener('click',()=>openDoc(b.dataset.doc)));}if($('docSelect').value)openDoc($('docSelect').value);}
async function openDoc(filename){try{let d;if(api())d=await api().read_doc(filename);else{const response=await fetch('/assets/docs/'+encodeURIComponent(filename));d={title:filename,content:await response.text()};} const friendlyTitle=$('docSelect').selectedOptions?.[0]?.textContent;$('docTitle').textContent=friendlyTitle||d.title||'Ders kılavuzu';$('docBody').innerHTML=renderMarkdown(d.content||'');$('docSelect').value=filename;document.querySelectorAll('[data-doc]').forEach(b=>b.classList.toggle('active',b.dataset.doc===filename));}catch(err){$('docTitle').textContent='Belge açılamadı';$('docBody').textContent=err.message;}}
function renderMarkdown(md){
 const esc=String(md).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
 const lines=esc.split(/\r?\n/);let html='',inList=false,inCode=false,code=[];
 const closeList=()=>{if(inList){html+='</ul>';inList=false;}};
 for(const raw of lines){
  const line=raw.trimEnd();
  if(/^\s*```/.test(line)){
   closeList();
   if(inCode){html+='<pre><code>'+code.join('\n')+'</code></pre>';code=[];inCode=false;}
   else inCode=true;
   continue;
  }
  if(inCode){code.push(line);continue;}
  if(!line.trim()){closeList();continue;}
  if(/^---+$/.test(line)){closeList();html+='<hr>';continue;}
  const heading=line.match(/^(#{1,3})\s+(.+)$/);
  if(heading){closeList();const level=heading[1].length;html+=`<h${level}>${inlineMd(heading[2])}</h${level}>`;continue;}
  if(/^\s*[-*]\s+/.test(line)){if(!inList){html+='<ul>';inList=true;}html+=`<li>${inlineMd(line.replace(/^\s*[-*]\s+/,''))}</li>`;continue;}
  closeList();html+=`<p>${inlineMd(line)}</p>`;
 }
 if(inCode)html+='<pre><code>'+code.join('\n')+'</code></pre>';
 closeList();return html;
}
function inlineMd(s){return s.replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>').replace(/\*([^*]+)\*/g,'<em>$1</em>').replace(/\[([^\]]+)\]\((https?:[^ )]+)\)/g,'<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');}

// --- AI providers: local Ollama auto-routing and optional Groq fallback ---
const aiDefaults={
 auto:{endpoint:'http://127.0.0.1:11434/api/chat',model:'auto'},
 ollama:{endpoint:'http://127.0.0.1:11434/api/chat',model:'auto'},
 groq:{endpoint:'https://api.groq.com/openai/v1/chat/completions',model:'openai/gpt-oss-120b'}
};
function applyAiProviderDefaults(force=true){
 const id=$('aiProvider').value,config=aiDefaults[id]||aiDefaults.ollama;
 if(force||!$('aiEndpoint').value)$('aiEndpoint').value=config.endpoint;
 $('aiModel').value=config.model;
 $('aiModel').readOnly=true;
 $('aiKey').placeholder=id==='ollama'?'Ollama için API anahtarı gerekmez':id==='auto'?'İsteğe bağlı Groq yedek anahtarı':'Groq API anahtarı';
 $('aiStatus').textContent=id==='auto'?'Otomatik mod: önce yerel Ollama; yalnızca yerel hata ve etkin lisans varsa Groq yedeği.':id==='ollama'?'Yalnızca yerel Ollama seçildi. Yüklü modeller görev türüne göre otomatik yönlendirilir.':'Yalnızca GroqCloud seçildi. Etkin lisans ve Groq API anahtarı gerekir.';
}
async function refreshOllamaModels(){
 const status=$('ollamaModelStatus');
 if(!api()){status.textContent='Yerel model listesi masaüstü uygulama köprüsünü gerektirir.';return;}
 const button=$('refreshOllamaModels');
 button.disabled=true;status.textContent='127.0.0.1:11434 üzerindeki Ollama modelleri okunuyor…';
 try{
  const result=await api().ai_list_models();
  const models=result.models||[];
  const routes=result.routes||{};
  status.textContent='Ollama bağlantısı başarılı · '+models.length+' model bulundu\n'
   +'Genel sohbet: '+(routes.general||'—')+'\n'
   +'Kodlama: '+(routes.coding||'—')+'\n'
   +'Kapsamlı analiz: '+(routes.analysis||'—')+'\n\n'
   +models.map(x=>x.name).join('\n');
 }catch(err){
  status.textContent='Ollama model listesi okunamadı: '+err.message+'\nOllama uygulamasının açık olduğunu ve ollama list komutunda modellerin göründüğünü doğrula.';
 }finally{button.disabled=false;}
}
function initAssistant(){
 $('buildPrompt').addEventListener('click',()=>{
  const task=prompts[$('promptType').value]||'';
  const context=$('promptContext').value.trim();
  $('promptOutput').value=task+(context?'\n\nBağlam:\n'+context:'');
 });
 $('copyPrompt').addEventListener('click',async()=>{
  try{await navigator.clipboard.writeText($('promptOutput').value);$('aiStatus').textContent='İstem panoya kopyalandı.';}
  catch(_){$('promptOutput').select();document.execCommand('copy');}
 });
 $('aiProvider').addEventListener('change',()=>applyAiProviderDefaults(true));
 $('refreshOllamaModels').addEventListener('click',refreshOllamaModels);
 applyAiProviderDefaults(false);
 $('sendAI').addEventListener('click',sendAiText);
 $('testAIConnection').addEventListener('click',testAiConnection);
 refreshOllamaModels();
}
function isLocalAiEndpoint(provider, endpoint){
 try{const u=new URL(endpoint);return ['auto','ollama'].includes(provider)&&['localhost','127.0.0.1','[::1]','::1'].includes(u.hostname.toLowerCase())&&u.port==='11434';}
 catch(_){return false;}
}
async function testAiConnection(){
 const button=$('testAIConnection');
 if(!api()){$('aiStatus').textContent='Bağlantı testi masaüstü uygulamasını gerektirir.';return;}
 const provider=$('aiProvider').value,endpoint=$('aiEndpoint').value.trim(),model=$('aiModel').value.trim(),key=$('aiKey').value;
 if(!appAuthorized){$('aiStatus').textContent='AI araçları için ödeme onaylı etkin Stagepulse lisansı gerekir.';return;}
 if(!$('aiConsent').checked){$('aiStatus').textContent='Önce seçili sağlayıcıya metin gönderme iznini işaretle.';return;}
 if(!endpoint||!model){$('aiStatus').textContent='Bağlantı adresi ve otomatik model yönlendirmesi gerekli.';return;}
 try{
  button.disabled=true;$('aiStatus').textContent='Seçili sağlayıcı test ediliyor…';
  const result=await api().ai_chat(provider,model,key,'Bu bir bağlantı testidir. Yalnızca STAGEPULSE_BAGLANTI_OK yaz.',endpoint);
  $('aiStatus').textContent='Bağlantı başarılı · '+(result.provider_name||provider)+' · '+(result.model||model)+'\nYanıt: '+(result.content||'').slice(0,500);
 }catch(err){
  $('aiStatus').textContent='Bağlantı testi başarısız: '+err.message+'\nOllama servisinin çalıştığını ve modelin yerel listede bulunduğunu kontrol et.';
 }finally{
  $('aiKey').value='';
  button.disabled=false;
 }
}
async function sendAiText(){
 const button=$('sendAI');
 if(!api()){$('aiStatus').textContent='Yerel AI çağrısı masaüstü uygulama köprüsünü gerektirir.';return;}
 const provider=$('aiProvider').value,endpoint=$('aiEndpoint').value.trim(),model=$('aiModel').value.trim(),key=$('aiKey').value,prompt=$('promptOutput').value.trim()||$('promptContext').value.trim();
 if(!appAuthorized){$('aiStatus').textContent='AI araçları için ödeme onaylı etkin Stagepulse lisansı gerekir.';return;}
 if(!$('aiConsent').checked){$('aiStatus').textContent='Önce veri gönderim iznini işaretle.';return;}
 if(!endpoint||!model||!prompt){$('aiStatus').textContent='Bağlantı, otomatik model yönlendirmesi ve istem gerekli.';return;}
 try{
  button.disabled=true;$('aiStatus').textContent='İstem seçili AI sağlayıcısına gönderiliyor…';
  const result=await api().ai_chat(provider,model,key,prompt,endpoint);
  $('aiStatus').textContent=(result.model||model)+' yanıtı:\n\n'+(result.content||JSON.stringify(result,null,2));
 }catch(err){
  $('aiStatus').textContent='AI isteği başarısız: '+err.message+'\nOllama yüklü modellerinden otomatik seçim yapılır; Groq anahtarı kaydedilmez.';
 }finally{
  $('aiKey').value='';
  button.disabled=false;
 }
}

// --- Commercial account, license and teacher progress ---
function commerceApi(){return api();}
function applyAccountContext(context){
 currentAccountContext=context||null;currentRole=context?.role||'guest';
 const license=context?.licensed||{},trial=context?.trial||{};appAuthorized=currentRole==='owner'||license.active===true||trial.active===true;
 if(licenseGatePending){licenseGatePending=false;setPage(appAuthorized?'home':'account');}
 else if(!appAuthorized&&activeRoute!=='account')setPage('account');
 if($('accountRoleBadge'))$('accountRoleBadge').textContent=currentRole==='owner'?'Sahip / öğretmen':currentRole==='student'?'Lisanslı öğrenci':'Misafir / lisans gerekli';
 if($('progressRoleBadge'))$('progressRoleBadge').textContent=currentRole==='owner'?'Öğretmen / yönetici':currentRole==='student'?'Öğrenci · salt okunur':'Hesap gerekli';
 const admin=currentRole==='owner';$('teacherLicensePanel').classList.toggle('hidden',!admin);$('teacherProgressPanel').classList.toggle('hidden',!admin);$('fullPackageAdminPanel')?.classList.toggle('hidden',!admin);$('fullPackagePurchasePanel')?.classList.toggle('hidden',!context?.user?.id);
 $('licenseActivate').disabled=currentRole==='owner';$('licenseActivate').textContent=currentRole==='owner'?'Sahip hesabı lisans gerektirmez':'Bu cihazı etkinleştir';
 if(trial.active){const seconds=Math.max(0,Number(trial.remaining_seconds||0)),days=Math.floor(seconds/86400),hours=Math.ceil((seconds%86400)/3600);$('licenseStatusText').textContent=`7 günlük demo açık · ${days>0?days+' gün ':''}${Math.max(1,hours)} saat kaldı`;appAuthorized=true;}
 else if(license.active){$('licenseStatusText').textContent=`Lisans etkin · FULL PAKET${license.expires_at?' · son tarih '+new Date(license.expires_at).toLocaleDateString('tr-TR'):''}`;appAuthorized=true;}
 else $('licenseStatusText').textContent=currentRole==='owner'?'Stagepulse sahibi hesabı doğrulandı.':'Ödeme onaylı etkin lisans veya süresi dolmamış demo gerekli.';
 $('accountStatus').textContent=`Hesap: ${context?.user?.email||'—'}\nYetki: ${currentRole}\nLisans: ${license.active?'etkin':'etkin değil'}\nWeb: https://stagepulse.com.tr`;
 if(context?.user?.email&&!$('accountEmail').value)$('accountEmail').value=context.user.email;if(context?.user?.name&&!$('purchaseCustomerName').value)$('purchaseCustomerName').value=context.user.name;
 refreshProfiles();renderStudentModules();
 if(currentRole==='student')refreshStudentProgress().catch(err=>{$('accountStatus').textContent+='\nİlerleme: '+err.message;});
 if(admin){refreshTeacherStudents().catch(err=>{$('teacherProgressStatus').textContent='Öğrenci listesi alınamadı: '+err.message;});refreshLicenseList();}if(context?.user?.id)refreshFullPackageStore();
 if(appAuthorized&&activeRoute==='account')setStatus('Stagepulse hesabı doğrulandı.');
}
function refreshAccountUi(){
 if(!api()){$('accountStatus').textContent='Masaüstü çalışma köprüsü bulunamadı. Kaynak önizlemesinde hesap/lisans işlemleri devre dışıdır.';return;}
 if(currentAccountContext){applyAccountContext(currentAccountContext);return;}
 api().app_info().then(info=>{
  const cached=info?.cached_license;
  if(cached?.active){
   appAuthorized=true;
   $('licenseStatusText').textContent=cached.trial?'7 günlük demo önbelleği geçerli; demo bitişine kadar çevrimdışı kullanım açık.':'FULL PAKET lisans önbelleği geçerli; çevrimdışı kullanım açık.';
   $('accountStatus').textContent='Çevrimdışı lisans etkin. Öğretmen/yönetici işlemleri için yeniden internet bağlantısı gerekir.';
   if(!currentAccountContext)currentRole='guest';
  }else{
   $('licenseStatusText').textContent='Ödeme onaylı lisans gerekli.';
   $('accountStatus').textContent='Bu uygulamayı kullanmak için Stagepulse hesabına giriş yapıp ödeme onaylı lisansı etkinleştir.';
  }
  if(licenseGatePending){licenseGatePending=false;setPage(appAuthorized?'home':'account');}
 }).catch(()=>{});
}
async function initAccount(){
 initFullPackageCommerce();
 $('accountLogin').addEventListener('click',async()=>{try{$('accountLogin').disabled=true;$('accountStatus').textContent='Hesap doğrulanıyor…';const result=await api().auth_login($('accountEmail').value,$('accountPassword').value);applyAccountContext(result.context);$('accountPassword').value='';setStatus('Stagepulse hesabına giriş yapıldı.');}catch(err){$('accountStatus').textContent='Giriş başarısız: '+err.message;}finally{$('accountLogin').disabled=false;}});
 $('accountSignup').addEventListener('click',async()=>{try{if(!$('accountEmail').value.trim().includes('@'))throw new Error('Öğrenci hesabı oluşturmak için e-posta adresi gerekir. Yönetici kullanıcı adıyla yalnızca giriş yapabilirsin.');$('accountSignup').disabled=true;$('accountStatus').textContent='Öğrenci hesabı oluşturuluyor…';const result=await api().auth_signup($('accountEmail').value,$('accountPassword').value,$('accountDisplayName').value);$('accountStatus').textContent=result.message;if(result.session_created){const context=await api().auth_context();applyAccountContext(context);}else $('accountPassword').value='';}catch(err){$('accountStatus').textContent='Hesap oluşturulamadı: '+err.message;}finally{$('accountSignup').disabled=false;}});
 $('licenseActivate').addEventListener('click',async()=>{try{if(!api())throw new Error('Masaüstü köprüsü yok.');$('licenseActivate').disabled=true;$('accountStatus').textContent='Lisans anahtarı sunucuda doğrulanıyor…';const r=await api().license_activate($('licenseKeyInput').value);$('licenseKeyInput').value='';applyAccountContext(r.context);$('accountStatus').textContent='Lisans etkinleştirildi.\n'+JSON.stringify(r.activation.result||{},null,2);}catch(err){$('accountStatus').textContent='Lisans etkinleştirilemedi: '+err.message;}finally{$('licenseActivate').disabled=false;}});
 $('accountLogout').addEventListener('click',async()=>{try{if(api())await api().auth_logout();}catch(_){}currentAccountContext=null;currentRole='guest';appAuthorized=false;remoteProgress={};selectedTeacherStudentId='';latestUpdateManifest=null;$('teacherLicensePanel').classList.add('hidden');$('teacherProgressPanel').classList.add('hidden');$('fullPackageAdminPanel')?.classList.add('hidden');$('fullPackagePurchasePanel')?.classList.add('hidden');$('accountPassword').value='';$('accountStatus').textContent='Oturum kapatıldı. Yerel lisans önbelleği de temizlendi.';setPage('account');renderStudentModules();});

 $('refreshLicenseList')?.addEventListener('click',refreshLicenseList);
 $('checkUpdates').addEventListener('click',async()=>{try{$('checkUpdates').disabled=true;$('updateStatus').textContent='Stagepulse güncelleme bildirimi denetleniyor…';const r=await api().check_updates();latestUpdateManifest=r;$('updateStatus').textContent=`Mevcut sürüm: ${r.current_version||'—'}\nSunucu sürümü: ${r.version||'—'}\n${r.message||''}${r.notes?'\n\nNotlar: '+r.notes:''}`;$('installUpdate').classList.toggle('hidden',!r.available);if(!r.published)$('updateStatus').textContent+='\n\nNot: Web sitesinde latest.json ve kurulum EXE’si yayımlanmadığı için otomatik güncelleme henüz etkin değil.';}catch(err){$('updateStatus').textContent='Güncelleme denetlenemedi: '+err.message;}finally{$('checkUpdates').disabled=false;}});
 $('installUpdate').addEventListener('click',async()=>{if(!latestUpdateManifest)return;try{$('installUpdate').disabled=true;$('updateStatus').textContent='Kurulum paketi indiriliyor ve SHA-256 doğrulanıyor…';const r=await api().install_update(JSON.stringify(latestUpdateManifest));$('updateStatus').textContent=r.message||'Güncelleme başlatıldı.';}catch(err){$('updateStatus').textContent='Güncelleme kurulamadı: '+err.message;}finally{$('installUpdate').disabled=false;}});
 $('openStagepulseSite').addEventListener('click',()=>api()?.open_website('home'));$('openSupportSite').addEventListener('click',()=>api()?.open_website('support'));
 // Updates are checked only when the user opens this panel and clicks the button.
}
async function refreshLicenseList(){
 const host=$('licenseList'),status=$('licenseListStatus');if(!host||!status)return;if(currentRole!=='owner'||!api()){host.innerHTML='';status.textContent='Bu liste yalnızca Stagepulse sahibine açıktır.';return;}
 const refresh=$('refreshLicenseList');if(refresh)refresh.disabled=true;status.textContent='Lisans kayıtları sunucudan alınıyor…';
 try{const result=await api().license_list();const items=result.licenses||[];if(!items.length){host.innerHTML='';status.textContent='Henüz lisans oluşturulmadı.';return;}
 host.innerHTML=items.map(x=>{const active=x.is_active===true,paid=x.payment_status==='paid',expiry=x.expires_at?new Date(x.expires_at).toLocaleDateString('tr-TR'):'Süresiz';const count=Number(x.active_activations||0),max=Number(x.max_activations||1),paymentLabel={paid:'Ödendi',unpaid:'Ödeme bekliyor',refunded:'İade edildi'}[x.payment_status||'paid']||'Durum bilinmiyor',methodLabel={cash:'Elden / nakit',bank_transfer:'Havale / EFT',card:'Kart',other:'Diğer',legacy:'Eski kayıt'}[x.payment_method||'legacy']||x.payment_method||'—',customer=x.customer_name||'FULL PAKET',amount=`${Number(x.amount||0).toLocaleString('tr-TR',{minimumFractionDigits:2,maximumFractionDigits:2})} ${safeText(x.currency||'TRY')}`;return `<article class="license-row"><div class="license-row-main"><strong>${safeText(customer)}</strong><span class="license-status ${active&&paid?'is-active':'is-revoked'}">${!active?'Lisans kapalı':paid?'Lisans etkin':'Aktivasyon bekliyor'} · ${paymentLabel}</span><small>FULL PAKET · ${count}/${max} cihaz · ${safeText(expiry)} · ${amount} · ${safeText(methodLabel)}</small><small>${safeText(x.customer_email||'')} ${x.payment_reference?'· Referans: '+safeText(x.payment_reference):''} · ${safeText(new Date(x.created_at).toLocaleDateString('tr-TR'))}</small></div>${active?`<button class="btn btn-danger btn-small" data-revoke-license="${safeText(x.id)}">Lisansı iptal et</button>`:''}</article>`;}).join('');
 
 host.querySelectorAll('[data-revoke-license]').forEach(btn=>btn.addEventListener('click',async()=>{const id=btn.dataset.revokeLicense;if(!id||!confirm('Bu lisansın tüm etkin cihazlarını ve öğrencinin resmî erişimini iptal etmek istiyor musun?'))return;btn.disabled=true;try{await api().license_revoke(id);status.textContent='Lisans iptal edildi ve bağlı öğrenci erişimleri kapatıldı.';await refreshLicenseList();}catch(err){status.textContent='Lisans iptal edilemedi: '+err.message;btn.disabled=false;}}));
 status.textContent=`${items.length} lisans kaydı. Ödeme durumu bu listede izlenir; anahtarlar güvenlik nedeniyle yeniden gösterilmez.`;
 }catch(err){host.innerHTML='';status.textContent='Lisans listesi alınamadı: '+err.message;}finally{if(refresh)refresh.disabled=false;}
}

function commerceApi(){return accountApi();}
async function refreshFullPackageStore(){
 const apiClient=commerceApi();if(!apiClient)return;
 try{const result=await apiClient.store_get(),s=result.settings||{};
  $("fullPackagePrice").textContent=Number(s.price||0).toLocaleString("tr-TR",{minimumFractionDigits:2,maximumFractionDigits:2})+" TL";
  $("fullPackageBankInfo").innerHTML=s.iban?`<strong>${safeText(s.bank_name||"Banka")}</strong><br>Hesap sahibi: ${safeText(s.account_holder||"")}<br>IBAN: <strong>${safeText(s.iban)}</strong>${s.payment_instructions?`<br>${safeText(s.payment_instructions)}`:""}${s.contact_phone?`<br>İletişim: ${safeText(s.contact_phone)}`:""}`:"<strong>Havale/EFT hesabı henüz tanımlanmadı.</strong><br>Satın alma bildirimleri hesap bilgileri girilene kadar kapalıdır.";
  $("submitFullPackagePurchase").disabled=!s.iban||!s.account_holder;
  if(currentRole==="owner"){ $("fullPackageAdminPrice").value=s.price??2500;$("fullPackageBankName").value=s.bank_name||"";$("fullPackageAccountHolder").value=s.account_holder||"";$("fullPackageIban").value=s.iban||"";$("fullPackagePaymentInstructions").value=s.payment_instructions||"";$("fullPackageContactPhone").value=s.contact_phone||""; }
  if(currentRole==="owner")await refreshFullPackagePurchases();
 }catch(err){$("fullPackageBankInfo").textContent="Mağaza bilgileri alınamadı: "+err.message;if(currentRole==="owner")$("fullPackageAdminStatus").textContent=err.message;}
}
async function refreshFullPackagePurchases(){
 const host=$("fullPackagePurchaseList");if(!host||currentRole!=="owner"||!commerceApi())return;
 try{const result=await commerceApi().purchase_list(),items=result.purchases||[];
  host.innerHTML=items.length?items.map(x=>`<article class="license-row"><div class="license-row-main"><strong>${safeText(x.customer_name)} · ${safeText(x.product_name)}</strong><span class="license-status ${x.status==="approved"?"is-active":x.status==="pending"?"":"is-revoked"}">${({pending:"Ödeme kontrolü bekliyor",approved:"Onaylandı",rejected:"Reddedildi"})[x.status]||x.status}</span><small>${Number(x.amount||0).toLocaleString("tr-TR",{minimumFractionDigits:2,maximumFractionDigits:2})} TL · ${safeText(x.customer_email)} · ${safeText(x.customer_phone||"")}</small><small>Referans: ${safeText(x.transfer_reference)} · ${safeText(new Date(x.created_at).toLocaleString("tr-TR"))}</small>${x.customer_note?`<small>Not: ${safeText(x.customer_note)}</small>`:""}${x.admin_note?`<small>Yönetici notu: ${safeText(x.admin_note)}</small>`:""}</div>${x.status==="pending"?`<button class="btn btn-gold btn-small" data-full-approve="${safeText(x.id)}">Banka hareketi doğrulandı</button><button class="btn btn-danger btn-small" data-full-reject="${safeText(x.id)}">Reddet</button>`:""}</article>`).join(""):"<div class=\"report-box\">Henüz satın alma bildirimi yok.</div>";
  host.querySelectorAll("[data-full-approve]").forEach(btn=>btn.addEventListener("click",async()=>{if(!confirm("Banka hesabına tutarın geçtiğini doğruladın mı? Onay lisansı oluşturur."))return;btn.disabled=true;try{const out=await commerceApi().purchase_review(btn.dataset.fullApprove,"approved","Banka hareketi yönetici tarafından doğrulandı.");$("fullPackageIssuedKey").value=out.key||"";$("fullPackageAdminStatus").textContent="Satın alma onaylandı. Lisans anahtarı aşağıda yalnızca bir kez gösteriliyor; müşteriye güvenli kanaldan ilet.";$("accountStatus").textContent="FULL PAKET lisansı oluşturuldu. Anahtar yönetici panelinde gösteriliyor.";$("copyFullPackageIssuedKey").disabled=!out.key;await refreshFullPackagePurchases();await refreshLicenseList();}catch(err){$("fullPackageAdminStatus").textContent="Onay başarısız: "+err.message;btn.disabled=false;}}));
  host.querySelectorAll("[data-full-reject]").forEach(btn=>btn.addEventListener("click",async()=>{const note=prompt("Red nedeni (isteğe bağlı):")||"";btn.disabled=true;try{await commerceApi().purchase_review(btn.dataset.fullReject,"rejected",note);$("fullPackageAdminStatus").textContent="Satın alma bildirimi reddedildi.";await refreshFullPackagePurchases();}catch(err){$("fullPackageAdminStatus").textContent="İşlem başarısız: "+err.message;btn.disabled=false;}}));
 }catch(err){host.innerHTML="";$("fullPackageAdminStatus").textContent="Bildirimler alınamadı: "+err.message;}
}
function initFullPackageCommerce(){
 $("submitFullPackagePurchase")?.addEventListener("click",async()=>{try{if(!currentAccountContext?.user?.id)throw new Error("Satın alma bildirimi için önce hesabına giriş yap.");$("submitFullPackagePurchase").disabled=true;$("fullPackagePurchaseStatus").textContent="Ödeme bildirimi gönderiliyor…";const r=await commerceApi().purchase_submit({customer_name:$("purchaseCustomerName").value,customer_phone:$("purchaseCustomerPhone").value,transfer_reference:$("purchaseTransferReference").value,customer_note:$("purchaseCustomerNote").value});$("fullPackagePurchaseStatus").textContent=`${r.purchase.product_name} ödeme bildirimi alındı. Tutar: ${Number(r.purchase.amount).toLocaleString("tr-TR",{minimumFractionDigits:2,maximumFractionDigits:2})} TL. Banka hareketi yönetici tarafından doğrulanınca lisans oluşturulacak.`;}catch(err){$("fullPackagePurchaseStatus").textContent="Bildirim gönderilemedi: "+err.message;}finally{$("submitFullPackagePurchase").disabled=false;}});
 $("saveFullPackageSettings")?.addEventListener("click",async()=>{try{if(currentRole!=="owner")throw new Error("Yalnızca yönetici değiştirebilir.");$("saveFullPackageSettings").disabled=true;const s=await commerceApi().store_update({price:Number($("fullPackageAdminPrice").value),bank_name:$("fullPackageBankName").value,account_holder:$("fullPackageAccountHolder").value,iban:$("fullPackageIban").value,payment_instructions:$("fullPackagePaymentInstructions").value,contact_phone:$("fullPackageContactPhone").value});$("fullPackageAdminStatus").textContent="FULL PAKET mağaza ayarları kaydedildi. Yeni fiyat: "+Number(s.settings.price).toLocaleString("tr-TR")+" TL." ;await refreshFullPackageStore();}catch(err){$("fullPackageAdminStatus").textContent="Ayarlar kaydedilemedi: "+err.message;}finally{$("saveFullPackageSettings").disabled=false;}});
 $("refreshFullPackagePurchases")?.addEventListener("click",refreshFullPackagePurchases);
 $("copyFullPackageIssuedKey")?.addEventListener("click",async()=>{const key=$("fullPackageIssuedKey").value;if(!key)return;try{await navigator.clipboard.writeText(key);$("fullPackageAdminStatus").textContent="Lisans anahtarı panoya kopyalandı.";}catch(_){$("fullPackageIssuedKey").select();document.execCommand("copy");}});
}

async function refreshTeacherStudents(){if(currentRole!=='owner'||!api())return;try{const result=await api().teacher_students();teacherStudents=result.students||[];const sel=$('teacherStudentSelect'),old=sel.value;sel.innerHTML='<option value="">Öğrenci seç</option>'+teacherStudents.map(st=>`<option value="${safeText(st.user_id)}">${safeText(st.display_name||st.email||st.user_id)} · ${safeText(st.email||'')}</option>`).join('');if(old&&teacherStudents.some(st=>st.user_id===old))sel.value=old;else selectedTeacherStudentId='';if(sel.value){selectedTeacherStudentId=sel.value;await refreshStudentProgress(selectedTeacherStudentId);}else{remoteProgress={};renderStudentModules();$('teacherProgressStatus').textContent=`Kayıtlı öğrenci: ${teacherStudents.length}. Öğrenciyi seçerek aşama durumunu aç.`;}}catch(err){$('teacherProgressStatus').textContent='Öğrenci listesi okunamadı: '+err.message;}}

// --- Settings ---
function initSettings(){$('checkOffline').addEventListener('click',()=>{$('settingsInfo').textContent=`Tarayıcı bağlantı işareti: ${navigator.onLine?'ağ bağlantısı var':'çevrimdışı'}\nYerel araçlar: hazır\nMikrofon: yalnızca RTA başlatılınca istenir\nÖğrenci deposu: ${apiReady?'bağlı':'önizleme modu'}`;});$('exportAllData').addEventListener('click',()=>downloadBlob(new Blob([JSON.stringify({profiles},null,2)],{type:'application/json'}),'Stagepulse_Tum_Ogrenci_Verileri.json'));}
async function loadAppInfo(){if(!api())return;try{const info=await api().app_info();$('settingsInfo').textContent=Object.entries(info).map(([k,v])=>`${k}: ${typeof v==='object'?JSON.stringify(v):v}`).join('\n');if(!currentAccountContext&&info.cached_license?.active){appAuthorized=true;if(activeRoute==='account')refreshAccountUi();}}catch(err){$('settingsInfo').textContent='Uygulama bilgisi okunamadı: '+err.message;}}

// Keyboard shortcut: Ctrl+K focuses current module (future-proof, no network calls).
document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();const route=prompt('Araç adı gir: '+Object.values(routes).join(', '));if(!route)return;const entry=Object.entries(routes).find(([,label])=>label.toLocaleLowerCase('tr').includes(route.toLocaleLowerCase('tr')));if(entry)setPage(entry[0]);}});
