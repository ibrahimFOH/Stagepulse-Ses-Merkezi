'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const sourcePath = path.join(__dirname, '..', 'ui', 'first_party_tools.js');
const source = fs.readFileSync(sourcePath, 'utf8');
const context = { window: {}, console, Blob, URL, setTimeout };
vm.runInNewContext(source, context, { filename: 'first_party_tools.js' });
const tools = context.window.StagepulseFirstPartyTools;
assert.ok(tools, 'Yerel araç modülü dışa açılmalı.');

const scene = [
  '#2.7# "Stagepulse Test" "" %000000000 1',
  '/config/routing/IN A1-8 A9-16 A17-24 B1-8 AUX1-4',
  '/config/routing/OUT OUT1-4 OUT5-8 OUT9-12 OUT13-16',
  '/ch/01/config "Vokal Ana" 1 CY 1',
  '/ch/01/preamp +3.0 OFF OFF 24 144',
  '/ch/01/gate ON EXP4 -46.5 27.0 20 100 576 0',
  '/ch/01/dyn ON COMP PEAK LIN -26.0 3.0 2 8.00 71 0.03 538 POST 0 100 OFF',
  '/ch/01/eq ON',
  '/ch/01/mix/01 ON -7.5 +0 PRE',
  '/ch/02/config "Bas DI" 1 CY 26',
  '/ch/02/preamp +0.0 OFF OFF 24 79',
  '/ch/02/mix/01 ON -oo +0 PRE'
].join('\n');

const report = tools.parseM32Scene('\uFEFF' + scene, 'Stagepulse-Test.scn');
assert.equal(report.channels.length, 2);
assert.equal(report.channels[0].name, 'Vokal Ana');
assert.equal(report.channels[0].source, 'AES50-A 1');
assert.equal(report.channels[1].source, 'AES50-B 2');
assert.equal(report.channels[0].preampGain, '+3.0');
assert.ok(report.channels[0].gate.startsWith('Açık'));
assert.ok(report.channels[0].compressor.startsWith('Kompresör'));
assert.ok(report.channels[0].sends.includes('Yardımcı yol (Bus) 1 (-7.5 dB)'));
assert.ok(report.channels[1].sends.some(x => x.includes('−∞ dB')));

assert.throws(() => tools.parseM32Scene('bozuk sahne', 'bozuk.scn'), /başlığı/);
assert.throws(() => tools.parseM32Scene('x'.repeat(8 * 1024 * 1024 + 1), 'büyük.scn'), /8 MB/);

const input = new Float32Array(4410);
for (let i = 0; i < input.length; i++) input[i] = 0.7 * Math.sin(2 * Math.PI * 440 * i / 44100);
const compressed = tools.processCompressor(input, 44100, {
  threshold: -18, ratio: 4, knee: 6, attack: 2, release: 90, makeup: 0, match: false
});
assert.equal(compressed.data.length, input.length);
assert.ok(compressed.maxReduction > 0, 'Kompresör kazanç azaltımı üretmeli.');
assert.ok(Array.from(compressed.data).every(Number.isFinite));

const gated = tools.processGate(input, 44100, {
  threshold: -30, range: -60, attack: 5, hold: 60, release: 120
});
assert.equal(gated.data.length, input.length);
assert.ok(gated.maxAttenuation >= 0);
assert.ok(gated.openPercent >= 0 && gated.openPercent <= 100);
assert.ok(Array.from(gated.data).every(Number.isFinite));


assert.match(source, /function startMicDelay\(\)/, 'Canlı mikrofon gecikme motoru bulunmalı.');
assert.match(source, /let micDelayStartToken = 0, micDelayPendingContext = null;/, 'Bekleyen mikrofon başlatma işlemi izlenmeli.');
assert.match(source, /const startToken = \+\+micDelayStartToken;/, 'Her mikrofon başlatma işlemi benzersiz iptal belirteci almalı.');
assert.match(source, /startToken !== micDelayStartToken/, 'İzin beklerken iptal edilen mikrofon akışı kullanılmamalı.');
assert.match(source, /micDelayStartToken \+= 1;/, 'Laboratuvardan çıkış bekleyen mikrofon başlatmasını iptal etmeli.');
assert.match(source, /function stopMicDelay\(\)/, 'Mikrofon akışı güvenli biçimde durdurulmalı.');
assert.match(source, /createDelay\(5\.0\)/, 'Canlı gecikme en fazla 5 saniye ile sınırlandırılmalı.');
assert.match(source, /echoCancellation: false/, 'Faz/gecikme deneyinde yankı iptali kapalı olmalı.');
assert.match(source, /monitorGain\.gain\.value = id\('waveMicMonitor'\)\.checked \? 0\.06 : 0/, 'Mikrofon izlemesi varsayılan olarak sessiz ve düşük kazançlı olmalı.');

assert.equal(tools.isRoomMeasurementInsideRoom({ x: 0, y: 0 }, 10, 8), true, 'Oda köşesindeki ölçüm kabul edilmeli.');
assert.equal(tools.isRoomMeasurementInsideRoom({ x: 10, y: 8 }, 10, 8), true, 'Oda sınırındaki ölçüm kabul edilmeli.');
assert.equal(tools.isRoomMeasurementInsideRoom({ x: 10.01, y: 4 }, 10, 8), false, 'Oda dışındaki X koordinatı reddedilmeli.');
assert.equal(tools.isRoomMeasurementInsideRoom({ x: 4, y: 8.01 }, 10, 8), false, 'Oda dışındaki Y koordinatı reddedilmeli.');
assert.equal(tools.isRoomMeasurementInsideRoom({ x: -0.01, y: 4 }, 10, 8), false, 'Negatif koordinat reddedilmeli.');
assert.equal(tools.isRoomMeasurementInsideRoom({ x: 4, y: 4 }, 0, 8), false, 'Geçersiz oda ölçüsü reddedilmeli.');

const math = tools.waveMath;
assert.ok(math, 'Dalga laboratuvarı matematik işlevleri dışa açılmalı.');
assert.ok(Math.abs(math.soundSpeed('air', 20) - 343.2) < 0.5);
const wave = math.calculate('air', 20, 440, 1);
assert.ok(Math.abs(wave.wavelengthM - 0.780) < 0.003);
assert.ok(Math.abs(wave.periodS - 1 / 440) < 1e-12);
assert.ok(Math.abs(wave.delayS - 1 / wave.speedMps) < 1e-12);
assert.ok(Math.abs(math.combinedAmplitudeRatio(0) - 2) < 1e-12);
assert.ok(Math.abs(math.combinedAmplitudeRatio(90) - Math.SQRT2) < 1e-12);
assert.ok(math.combinedAmplitudeRatio(180) < 1e-12);
assert.ok(Math.abs(math.pascalsToDbSpl(1) - 93.9794) < 0.001);
assert.ok(Math.abs(math.dbSplToPascals(93.9794) - 1) < 0.001);
const twoSource = math.twoSource(440, 343.2, 2, 2, 8, 2, 5, 7);
assert.ok(Number.isFinite(twoSource.phaseDeg));
assert.ok(twoSource.amplitudeRatio >= 0 && twoSource.amplitudeRatio <= 1);
assert.throws(() => math.calculate('air', 20, 0, 1), /Frekans/);
assert.throws(() => math.pascalsToDbSpl(0), /RMS/);

const htmlPath = path.join(__dirname, '..', 'ui', 'index.html');
const htmlSource = fs.readFileSync(htmlPath, 'utf8');
assert.match(htmlSource, /N = round\(Δt × fₛ\)/, 'Gecikme örneği formülü en yakın tam örneğe yuvarlamayı göstermeli.');
assert.match(htmlSource, /varsayılan olarak kamera veya mikrofon açmaz/, 'Mikrofon izni açıklaması isteğe bağlı başlatmayı doğru anlatmalı.');
const versionSource = fs.readFileSync(path.join(__dirname, '..', 'Merkez.py'), 'utf8');
const appVersion = versionSource.match(/APP_VERSION\s*=\s*"([^"]+)"/)?.[1];
assert.ok(appVersion, 'Merkez.py uygulama sürümü tanımlı olmalı.');
assert.ok(htmlSource.includes(`v${appVersion} · Stagepulse`), 'Windows arayüzü uygulama sürümünü göstermeli.');


const androidUiPath = path.join(__dirname, '..', '..', 'android', 'app', 'src', 'main', 'assets', 'ui');
const androidHtml = fs.readFileSync(path.join(androidUiPath, 'index.html'), 'utf8');
const androidApp = fs.readFileSync(path.join(androidUiPath, 'app.js'), 'utf8');
assert.ok(!/ÖNERİLEN BAŞLANGIÇ FİYATLARI|2\.490 TL|7\.490 TL|49\.900 TL|downloadCurriculumDoc/.test(htmlSource), 'Windows eğitim ekranında fiyat listesi veya fiyat belgesi bağlantısı kalmamalı.');
assert.ok(!/ÖNERİLEN BAŞLANGIÇ FİYATLARI|2\.490 TL|7\.490 TL|49\.900 TL|downloadCurriculumDoc/.test(androidHtml), 'Android eğitim ekranında fiyat listesi veya fiyat belgesi bağlantısı kalmamalı.');
assert.match(htmlSource, /UYGULAMALI ATÖLYE/, 'Fiyatlar kaldırılırken eğitim içeriği korunmalı.');
assert.match(androidHtml, /UYGULAMALI ATÖLYE/, 'Android eğitim içeriği korunmalı.');
assert.match(androidHtml, /id="patchExport" disabled/, 'SCN dosyası seçilmeden CSV dışa aktarma kapalı olmalı.');
assert.match(androidHtml, /id="patchPrint" disabled/, 'SCN dosyası seçilmeden rapor yazdırma kapalı olmalı.');
assert.match(androidApp, /Durdur düğmesi bekleyen izni iptal eder/, 'Android mikrofon başlatılırken durdurma kullanılabilir olmalı.');
assert.ok(androidApp.includes("if(token!==rtaGeneration){$('rtaStart').disabled=false;$('rtaStop').disabled=true;return;}"), 'İptal edilen mikrofon başlatması getUserMedia öncesinde durmalı.');

console.log('İLK TARAF ARAÇ TESTLERİ BAŞARILI');

const advancedPath = path.join(__dirname, '..', 'ui', 'advanced_modules.js');
const advancedSource = fs.readFileSync(advancedPath, 'utf8');
const advancedContext = { window: {}, console, Math, Number, Array, Object, Error, String, JSON };
vm.runInNewContext(advancedSource, advancedContext, { filename: 'advanced_modules.js' });
const advanced = advancedContext.window.StagepulseAdvanced;
assert.ok(advanced, 'Gelişmiş mühendislik modülleri dışa açılmalı.');
const singlePhase = advanced.calculatePower({phase:'single',powerW:3000,voltage:230,powerFactor:0.9,efficiency:0.9,reserve:0,lengthM:20,sectionMm2:2.5,material:'copper'});
assert.ok(Math.abs(singlePhase.currentA - 16.103) < 0.02, 'Tek faz akımı doğru hesaplanmalı.');
const threePhase = advanced.calculatePower({phase:'three',powerW:12000,voltage:400,powerFactor:0.9,efficiency:0.95,reserve:0,lengthM:30,sectionMm2:6,material:'copper'});
assert.ok(Math.abs(threePhase.currentA - 20.267) < 0.03, 'Üç faz akımı doğru hesaplanmalı.');
assert.ok(threePhase.voltageDropV > 0 && threePhase.voltageDropPercent > 0, 'Kablo gerilim düşümü hesaplanmalı.');
assert.throws(() => advanced.calculatePower({phase:'single',powerW:0,voltage:230,powerFactor:0.9,efficiency:0.9,lengthM:10,sectionMm2:2.5}), /Güç/);
const rfPlan = advanced.coordinateRf({minMHz:470,maxMHz:694,handhelds:4,iems:2,stepMHz:0.025,spacingMHz:0.3,guardMHz:0.15,noiseThresholdDbm:-70,scan:[]});
assert.equal(rfPlan.assigned,6, 'Dört el mikrofonu ve iki IEM için altı aday kanal bulunmalı.');
assert.equal(rfPlan.channels.filter(x=>x.type==='El mikrofonu').length,4);
assert.equal(rfPlan.channels.filter(x=>x.type==='IEM').length,2);
for(let i=0;i<rfPlan.channels.length;i++)for(let j=i+1;j<rfPlan.channels.length;j++)assert.ok(Math.abs(rfPlan.channels[i].frequencyMHz-rfPlan.channels[j].frequencyMHz)>=0.3,'RF kanalları minimum aralığı korumalı.');
const parsed=advanced.parseRtaCandidates('125 Hz\nKomşu bant medyanından +6,0 dB · aday kesim 3 dB\n1,25 kHz\nKomşu bant medyanından +4,5 dB · aday kesim 2 dB');
assert.equal(parsed.length,2);assert.equal(parsed[0].frequencyHz,125);assert.equal(parsed[0].excessDb,6);
assert.equal(advanced.videoLessons.length,8,'Video akademi için sekiz ders senaryosu bulunmalı.');
assert.ok(advanced.videoLessons.every(x=>x.script.length>100&&x.shots.length>=3),'Her video dersi anlatım ve storyboard içermeli.');
