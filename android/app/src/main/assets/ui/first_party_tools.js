/* Stagepulse - özgün yerel mühendislik araçları, sürüm 4.0.6
   Dış kütüphane, CDN veya çevrimiçi hesaplama servisi kullanmaz. */
(function () {
  'use strict';

  const byId = (id) => document.getElementById(id);
  const text = (id, value) => { const node = byId(id); if (node) node.textContent = value; };
  const number = (id) => Number(byId(id)?.value);
  const showError = (id, error) => text(id, 'İşlem tamamlanamadı: ' + (error && error.message ? error.message : String(error)));
  const fmt = (n, digits = 2) => Number(n).toLocaleString('tr-TR', { maximumFractionDigits: digits, minimumFractionDigits: 0 });
  const safeFileName = (name) => String(name || 'stagepulse').replace(/[^a-zA-Z0-9_-]+/g, '_').slice(0, 48);
  const downloadText = (name, content, type) => {
    const blob = new Blob([content], { type: type || 'text/plain;charset=utf-8' });
    if (window.StagepulseAndroid && typeof window.StagepulseAndroid.saveBase64File === 'function') {
      if (blob.size > 18 * 1024 * 1024) {
        text('footerStatus', 'Dosya 18 MiB sınırını aşıyor; daha küçük bir dışa aktarım oluştur.');
        return;
      }
      const reader = new FileReader();
      reader.onload = () => {
        try {
          const encoded = String(reader.result || '').split(',')[1] || '';
          const saved = window.StagepulseAndroid.saveBase64File(name, blob.type || 'application/octet-stream', encoded);
          text('footerStatus', saved ? 'Dosya İndirilenler/Stagepulse klasörüne kaydedildi.' : 'Dosya Android depolamasına kaydedilemedi.');
        } catch (error) {
          text('footerStatus', 'Dosya kaydedilemedi: ' + (error && error.message ? error.message : String(error)));
        }
      };
      reader.onerror = () => text('footerStatus', 'Dışa aktarım dosyası okunamadı.');
      reader.readAsDataURL(blob);
      return;
    }
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1500);
  };
  const bind = (id, event, fn) => { const node = byId(id); if (node && !node.dataset.spBound) { node.addEventListener(event, fn); if (event === 'click') node.dataset.spBound = '1'; } };
  const clamp = (v, min, max) => Math.min(max, Math.max(min, v));

  // ---------------------------------------------------------------------------
  // 1. KOMPRESÖR VE NOISE GATE KULAK EĞİTİMİ
  // ---------------------------------------------------------------------------
  let dynamicsContext = null;
  let dynamicsBuffers = {};
  let dynamicsSources = { comp: null, gate: null };

  function getDynamicsContext() {
    if (!dynamicsContext) {
      const Ctor = window.AudioContext || window.webkitAudioContext;
      if (!Ctor) throw new Error('Bu Windows WebView ortamında Web Audio desteklenmiyor. WebView2 Runtime güncellenmeli.');
      dynamicsContext = new Ctor();
    }
    return dynamicsContext;
  }

  function makeTrainingSignal(kind, sampleRate) {
    const seconds = 2.4;
    const data = new Float32Array(Math.floor(seconds * sampleRate));
    let seed = kind === 'drums' ? 94117 : kind === 'bass' ? 38129 : 72531;
    const noise = () => { seed = (seed * 16807) % 2147483647; return (seed / 1073741823.5) - 1; };
    for (let i = 0; i < data.length; i++) {
      const t = i / sampleRate;
      let value = 0;
      if (kind === 'drums') {
        const hitTimes = [0.08, 0.42, 0.78, 1.12, 1.48, 1.86, 2.18];
        for (let h = 0; h < hitTimes.length; h++) {
          const dt = t - hitTimes[h];
          if (dt >= 0 && dt < 0.22) {
            const kick = Math.sin(2 * Math.PI * (78 - 35 * dt) * dt) * Math.exp(-dt * 24);
            const snare = noise() * Math.exp(-dt * 34) * 0.34;
            value += (h % 2 === 0 ? kick * 0.9 : snare);
          }
        }
        value += noise() * 0.012;
      } else if (kind === 'bass') {
        const pulse = Math.max(0, Math.sin(2 * Math.PI * 1.45 * t));
        const env = Math.exp(-((t % 0.43) * 5.5));
        const f = 58 + 12 * Math.sin(2 * Math.PI * 0.3 * t);
        value = (Math.sin(2 * Math.PI * f * t) + .24 * Math.sin(4 * Math.PI * f * t) + .08 * Math.sin(6 * Math.PI * f * t)) * env * (0.18 + pulse * 0.48);
        value += noise() * 0.008;
      } else {
        const phrase = (t % 0.56);
        const env = phrase < 0.37 ? (0.22 + 0.6 * Math.sin(Math.PI * phrase / 0.37)) : 0.035;
        const f = 125 + 18 * Math.sin(2 * Math.PI * 2.2 * t);
        const vowel = Math.sin(2 * Math.PI * f * t) + .42 * Math.sin(4 * Math.PI * f * t) + .19 * Math.sin(6 * Math.PI * f * t) + .08 * Math.sin(10 * Math.PI * f * t);
        const sibilance = noise() * (phrase > 0.29 && phrase < 0.39 ? .22 : .018);
        value = env * (vowel * .20 + sibilance);
        if (t > 0.84 && t < 0.96) value += noise() * .30;
        if (t > 1.62 && t < 1.78) value += noise() * .18;
      }
      data[i] = clamp(value, -0.92, 0.92);
    }
    return data;
  }

  function rmsOf(data) {
    let sum = 0;
    for (let i = 0; i < data.length; i++) sum += data[i] * data[i];
    return Math.sqrt(sum / Math.max(1, data.length));
  }

  function processCompressor(input, sampleRate, settings) {
    const output = new Float32Array(input.length);
    const attack = Math.max(0.0001, settings.attack / 1000);
    const release = Math.max(0.001, settings.release / 1000);
    const attackCoef = Math.exp(-1 / (attack * sampleRate));
    const releaseCoef = Math.exp(-1 / (release * sampleRate));
    let envelope = 0, maxReduction = 0;
    for (let i = 0; i < input.length; i++) {
      const level = Math.abs(input[i]);
      const coef = level > envelope ? attackCoef : releaseCoef;
      envelope = coef * envelope + (1 - coef) * level;
      const inputDb = 20 * Math.log10(Math.max(envelope, 1e-7));
      const threshold = settings.threshold;
      const knee = settings.knee;
      let outputDb = inputDb;
      if (knee <= 0) {
        if (inputDb > threshold) outputDb = threshold + (inputDb - threshold) / settings.ratio;
      } else if (inputDb > threshold - knee / 2) {
        if (inputDb >= threshold + knee / 2) outputDb = threshold + (inputDb - threshold) / settings.ratio;
        else {
          const x = inputDb - threshold + knee / 2;
          outputDb = inputDb + (1 / settings.ratio - 1) * x * x / (2 * knee);
        }
      }
      const reduction = Math.max(0, inputDb - outputDb);
      if (reduction > maxReduction) maxReduction = reduction;
      output[i] = input[i] * Math.pow(10, (outputDb - inputDb + settings.makeup) / 20);
    }
    let matchDb = 0;
    if (settings.match) {
      const inRms = rmsOf(input), outRms = rmsOf(output);
      if (inRms > 0 && outRms > 0) {
        matchDb = clamp(20 * Math.log10(inRms / outRms), -12, 12);
        const gain = Math.pow(10, matchDb / 20);
        for (let i = 0; i < output.length; i++) output[i] *= gain;
      }
    }
    return { data: output, maxReduction, matchDb };
  }

  function processGate(input, sampleRate, settings) {
    const output = new Float32Array(input.length);
    const attackCoef = Math.exp(-1 / (Math.max(.001, settings.attack / 1000) * sampleRate));
    const releaseCoef = Math.exp(-1 / (Math.max(.001, settings.release / 1000) * sampleRate));
    const holdSamples = Math.round(settings.hold / 1000 * sampleRate);
    const floorGain = Math.pow(10, settings.range / 20);
    const threshold = Math.pow(10, settings.threshold / 20);
    let envelope = 0, gain = floorGain, holdLeft = 0, maxAttenuation = 0, openSamples = 0;
    for (let i = 0; i < input.length; i++) {
      const level = Math.abs(input[i]);
      const envCoef = level > envelope ? attackCoef : releaseCoef;
      envelope = envCoef * envelope + (1 - envCoef) * level;
      if (envelope >= threshold) holdLeft = holdSamples;
      else if (holdLeft > 0) holdLeft--;
      const shouldOpen = envelope >= threshold || holdLeft > 0;
      const target = shouldOpen ? 1 : floorGain;
      const coef = target > gain ? attackCoef : releaseCoef;
      gain = target + coef * (gain - target);
      if (shouldOpen) openSamples++;
      const attenuation = -20 * Math.log10(Math.max(gain, 1e-7));
      if (attenuation > maxAttenuation) maxAttenuation = attenuation;
      output[i] = input[i] * gain;
    }
    return { data: output, maxAttenuation, openPercent: openSamples / Math.max(1, input.length) * 100 };
  }

  function stopDynamicsSource(type) {
    const source = dynamicsSources[type];
    if (source) { try { source.stop(); } catch (_) {} try { source.disconnect(); } catch (_) {} }
    dynamicsSources[type] = null;
  }

  async function playProcessed(type, data) {
    const ctx = getDynamicsContext();
    if (ctx.state !== 'running') await ctx.resume();
    stopDynamicsSource(type);
    const isFloat32View = data && ArrayBuffer.isView(data) && data.BYTES_PER_ELEMENT === 4;
    if (!isFloat32View && !Array.isArray(data)) {
      throw new TypeError('Ses örneği Float32Array veya sayı dizisi olmalı.');
    }
    const samples = data instanceof Float32Array ? data : Float32Array.from(data);
    if (!samples.length || !Array.from(samples).every(Number.isFinite)) {
      throw new TypeError('Ses örneği boş veya geçersiz değer içeriyor.');
    }
    const buffer = ctx.createBuffer(1, samples.length, 44100);
    // copyToChannel bazı Android WebView sürümlerinde farklı realm'den gelen Float32Array'i reddedebiliyor.
    // Web Audio'nun kendi kanal görünümüne kopyalamak aynı Float32 örneklerini güvenli biçimde aktarır.
    buffer.getChannelData(0).set(samples);
    const source = ctx.createBufferSource();
    const gain = ctx.createGain();
    gain.gain.value = 0.34;
    source.buffer = buffer;
    source.connect(gain).connect(ctx.destination);
    dynamicsSources[type] = source;
    source.onended = () => { if (dynamicsSources[type] === source) dynamicsSources[type] = null; };
    source.start();
  }

  function initDynamicsEarTraining() {
    const compButtons = ['compPlayA', 'compPlayB', 'compNew'];
    const gateButtons = ['gatePlayA', 'gatePlayB', 'gateNew'];
    if (!compButtons.every((id) => byId(id)) || !gateButtons.every((id) => byId(id))) return;
    const compRender = () => {
      const kind = byId('compSignalType').value;
      const sr = 44100;
      const input = makeTrainingSignal(kind, sr);
      const settings = {
        threshold: number('compThreshold'), ratio: number('compRatio'), knee: number('compKnee'),
        attack: number('compAttack'), release: number('compRelease'), makeup: number('compMakeup'),
        match: byId('compLevelMatch').checked
      };
      const processed = processCompressor(input, sr, settings);
      dynamicsBuffers.comp = { dry: input, wet: processed.data, result: processed };
      text('compQuizFeedback', 'Rastgele dinleme turu için “Yeni rastgele tur” düğmesine bas.');
      text('compReduction', 'En yüksek kazanç azaltımı: ' + fmt(processed.maxReduction, 1) + ' dB');
      text('compMatchInfo', settings.match ? 'A/B düzey eşitleme: ' + (processed.matchDb >= 0 ? '+' : '') + fmt(processed.matchDb, 1) + ' dB telafi.' : 'A/B düzey eşitleme kapalı.');
      byId('compMeter').style.width = clamp(processed.maxReduction / 24 * 100, 0, 100) + '%';
      text('compFeedback', 'A: işlenmemiş sinyal. B: kompresör uygulanmış sinyal. Önce A ve B’yi aynı ses düzeyinde karşılaştır.');
    };
    const gateRender = () => {
      const kind = byId('gateSignalType').value;
      const sr = 44100;
      const input = makeTrainingSignal(kind, sr);
      const settings = {
        threshold: number('gateThreshold'), range: number('gateRange'), attack: number('gateAttack'),
        hold: number('gateHold'), release: number('gateRelease')
      };
      const processed = processGate(input, sr, settings);
      dynamicsBuffers.gate = { dry: input, wet: processed.data, result: processed };
      text('gateQuizFeedback', 'Rastgele dinleme turu için “Yeni rastgele tur” düğmesine bas.');
      text('gateReduction', 'En yüksek kısma: ' + fmt(processed.maxAttenuation, 1) + ' dB');
      text('gateOpenInfo', 'Kapı açık süre: %' + fmt(processed.openPercent, 1) + ' · Kapalı durumdaki seviye: ' + fmt(settings.range, 0) + ' dB');
      byId('gateMeter').style.width = clamp(processed.maxAttenuation / 60 * 100, 0, 100) + '%';
      text('gateFeedback', 'A: ham sinyal. B: gate uygulanmış sinyal. Eşik altındaki gürültünün nasıl bastırıldığını dinle.');
    };
    const safePlay = async (type, variant) => {
      const item = dynamicsBuffers[type];
      if (!item) throw new Error('Önce yeni alıştırma oluştur.');
      await playProcessed(type, item[variant]);
    };
    const generateQuiz = (type) => {
      const item = dynamicsBuffers[type];
      if (!item) throw new Error('Önce ayarları uygula.');
      item.quizOrder = Math.random() < 0.5 ? ['dry', 'wet'] : ['wet', 'dry'];
      item.quizAnswered = false;
      text(type + 'QuizFeedback', 'Yeni tur hazır. A ve B örneklerini dinle; hangisinde işlem bulunduğunu seç.');
    };
    const playQuizSample = async (type, slot) => {
      const item = dynamicsBuffers[type];
      if (!item || !item.quizOrder) throw new Error('Önce yeni rastgele tur oluştur.');
      const variant = item.quizOrder[slot];
      await playProcessed(type, item[variant]);
    };
    const answerQuiz = (type, answer) => {
      const item = dynamicsBuffers[type];
      if (!item || !item.quizOrder) throw new Error('Önce yeni rastgele tur oluştur.');
      if (item.quizAnswered) { text(type + 'QuizFeedback', 'Bu turun yanıtı zaten verildi. Yeni bir tur oluştur.'); return; }
      const correct = item.quizOrder[0] === 'wet' ? 'A' : 'B';
      item.quizAnswered = true;
      const effectName = type === 'comp' ? 'Kompresör' : 'Gürültü kapısı';
      text(type + 'QuizFeedback', answer === correct
        ? 'Doğru. ' + effectName + ' uygulanmış örnek ' + correct + ' idi.'
        : 'Bu tur doğru değil. ' + effectName + ' uygulanmış örnek ' + correct + ' idi. Yeniden dinleyip yeni tur deneyebilirsin.');
    };
    bind('compNew', 'click', () => { try { compRender(); } catch (e) { showError('compFeedback', e); } });
    bind('compPlayA', 'click', async () => { try { await safePlay('comp', 'dry'); } catch (e) { showError('compFeedback', e); } });
    bind('compPlayB', 'click', async () => { try { await safePlay('comp', 'wet'); } catch (e) { showError('compFeedback', e); } });
    bind('gateNew', 'click', () => { try { gateRender(); } catch (e) { showError('gateFeedback', e); } });
    bind('compQuizNew', 'click', () => { try { compRender(); generateQuiz('comp'); } catch (e) { showError('compQuizFeedback', e); } });
    bind('gateQuizNew', 'click', () => { try { gateRender(); generateQuiz('gate'); } catch (e) { showError('gateQuizFeedback', e); } });
    bind('compQuizPlayA', 'click', async () => { try { await playQuizSample('comp', 0); } catch (e) { showError('compQuizFeedback', e); } });
    bind('compQuizPlayB', 'click', async () => { try { await playQuizSample('comp', 1); } catch (e) { showError('compQuizFeedback', e); } });
    bind('gateQuizPlayA', 'click', async () => { try { await playQuizSample('gate', 0); } catch (e) { showError('gateQuizFeedback', e); } });
    bind('gateQuizPlayB', 'click', async () => { try { await playQuizSample('gate', 1); } catch (e) { showError('gateQuizFeedback', e); } });
    bind('compQuizAnswerA', 'click', () => { try { answerQuiz('comp', 'A'); } catch (e) { showError('compQuizFeedback', e); } });
    bind('compQuizAnswerB', 'click', () => { try { answerQuiz('comp', 'B'); } catch (e) { showError('compQuizFeedback', e); } });
    bind('gateQuizAnswerA', 'click', () => { try { answerQuiz('gate', 'A'); } catch (e) { showError('gateQuizFeedback', e); } });
    bind('gateQuizAnswerB', 'click', () => { try { answerQuiz('gate', 'B'); } catch (e) { showError('gateQuizFeedback', e); } });
    bind('gatePlayA', 'click', async () => { try { await safePlay('gate', 'dry'); } catch (e) { showError('gateFeedback', e); } });
    bind('gatePlayB', 'click', async () => { try { await safePlay('gate', 'wet'); } catch (e) { showError('gateFeedback', e); } });
    ['compThreshold','compRatio','compKnee','compAttack','compRelease','compMakeup','compSignalType','compLevelMatch'].forEach((id) => bind(id, 'change', () => { try { compRender(); } catch (e) { showError('compFeedback', e); } }));
    ['gateThreshold','gateRange','gateAttack','gateHold','gateRelease','gateSignalType'].forEach((id) => bind(id, 'change', () => { try { gateRender(); } catch (e) { showError('gateFeedback', e); } }));
    ['compThreshold','compRatio','compKnee','compAttack','compRelease','compMakeup','gateThreshold','gateRange','gateAttack','gateHold','gateRelease'].forEach((id) => {
      bind(id, 'input', () => {
        const suffix = id.includes('Threshold') || id === 'compKnee' || id === 'gateRange' ? ' dB' :
          id.includes('Attack') || id.includes('Release') || id === 'gateHold' ? ' ms' :
          id === 'compRatio' ? ':1' : ' dB';
        text(id + 'Value', byId(id).value + suffix);
      });
    });
    text('compFeedback', 'Alıştırmayı başlatmak için “Ayarları uygula” düğmesine bas.');
    text('gateFeedback', 'Alıştırmayı başlatmak için “Ayarları uygula” düğmesine bas.');
  }

  // ---------------------------------------------------------------------------
  // 2. 70 / 100 V HAT HESABI VE KABLO KAYBI
  // ---------------------------------------------------------------------------
  const copperOhmsKm = {
    '0.5': 36.0, '0.75': 24.5, '1': 18.1, '1.5': 12.1, '2.5': 7.41,
    '4': 4.61, '6': 3.08, '10': 1.83, '16': 1.15, '25': .727, '35': .524, '50': .387
  };

  function calculatePowerLine() {
    const voltage = number('lineVoltage');
    const headroom = number('lineHeadroom');
    const utilization = number('lineUtilization');
    const length = number('lineLength');
    const section = byId('lineSection').value;
    const resistance = copperOhmsKm[section];
    const rawLines = byId('lineLoads').value.split(/\r?\n/).map((s) => s.trim()).filter((s) => s && !s.startsWith('#'));
    if (![70.7, 100].includes(voltage)) throw new Error('Hat gerilimi 70,7 V veya 100 V olmalı.');
    if (!Number.isFinite(headroom) || headroom < 0 || headroom > 100) throw new Error('Güç payı %0 ile %100 arasında olmalı.');
    if (!Number.isFinite(utilization) || utilization < 10 || utilization > 100) throw new Error('Yükselteç kullanım oranı %10 ile %100 arasında olmalı.');
    if (!Number.isFinite(length) || length < 0 || length > 5000 || !resistance) throw new Error('Kablo uzunluğu veya kesiti geçersiz.');
    if (!rawLines.length) throw new Error('En az bir hoparlör/tap satırı gir.');
    let total = 0, units = 0;
    const rows = [];
    rawLines.forEach((line, index) => {
      const match = line.match(/^(\d+)\s*[xX×,;]\s*(\d+(?:[.,]\d+)?)$/) || line.match(/^(\d+)\s+(\d+(?:[.,]\d+)?)$/);
      if (!match) throw new Error((index + 1) + '. satır hatalı. Örnek biçim: 10x15 (10 hoparlör, her biri 15 W).');
      const count = Number(match[1]), watts = Number(match[2].replace(',', '.'));
      if (!Number.isInteger(count) || count < 1 || count > 10000 || !(watts > 0) || watts > 1000) throw new Error((index + 1) + '. satırdaki hoparlör sayısı veya tap gücü geçersiz.');
      total += count * watts; units += count; rows.push({ count, watts, power: count * watts });
    });
    const loadWithHeadroom = total * (1 + headroom / 100);
    const ampMinimum = loadWithHeadroom / (utilization / 100);
    const current = total / voltage;
    const loopResistance = 2 * length * resistance / 1000;
    const dropV = current * loopResistance;
    const dropPercent = voltage > 0 ? dropV / voltage * 100 : 0;
    const lossW = current * current * loopResistance;
    return { voltage, total, units, loadWithHeadroom, ampMinimum, current, loopResistance, dropV, dropPercent, lossW, rows };
  }

  function initPowerLine() {
    if (!byId('lineCalculate')) return;
    bind('lineCalculate', 'click', () => {
      try {
        const r = calculatePowerLine();
        text('lineResult', 'Toplam hoparlör: ' + r.units + ' · Tap yükü: ' + fmt(r.total, 1) + ' W · Güç payı sonrası: ' + fmt(r.loadWithHeadroom, 1) + ' W · Önerilen yükselteç anma gücü: en az ' + fmt(r.ampMinimum, 0) + ' W');
        text('lineCableResult', 'Hat akımı yaklaşık ' + fmt(r.current, 3) + ' A · Döngü direnci ' + fmt(r.loopResistance, 3) + ' Ω · Kablo gerilim düşümü ' + fmt(r.dropV, 2) + ' V (%' + fmt(r.dropPercent, 2) + ') · Kablo kaybı yaklaşık ' + fmt(r.lossW, 1) + ' W.');
        text('lineCaution', 'Ön hesap: bakır iletkenin 20 °C direnç tablosu ve toplam yükün kablonun en uzak ucunda toplandığı muhafazakâr varsayımı kullanılır. Gerçek dağıtılmış yük, trafo kayıpları, frekans cevabı, kablo sıcaklığı ve üretici sınırları ayrıca doğrulanmalıdır.');
      } catch (e) { showError('lineResult', e); text('lineCableResult', ''); }
    });
    bind('lineReset', 'click', () => {
      byId('lineLoads').value = '12x15\n8x7.5'; byId('lineLength').value = '100'; byId('lineSection').value = '2.5';
      byId('lineVoltage').value = '100'; byId('lineHeadroom').value = '25'; byId('lineUtilization').value = '80';
      byId('lineCalculate').click();
    });
    byId('lineCalculate').click();
  }

  // ---------------------------------------------------------------------------
  // 3. RF KANAL PLANI: yalnızca kullanıcının doğruladığı bant ve tarama verisi
  // ---------------------------------------------------------------------------
  let rfBlocked = [];
  let rfAssignments = [];

  function rfIntermodCollision(candidate, assigned, guard) {
    const carriers = assigned.concat([candidate]);
    for (let i = 0; i < carriers.length; i++) {
      for (let j = i + 1; j < carriers.length; j++) {
        const a = carriers[i], b = carriers[j];
        const products = [2 * a - b, 2 * b - a];
        for (let k = 0; k < carriers.length; k++) {
          if (k !== i && k !== j && products.some((product) => Math.abs(carriers[k] - product) < guard)) return true;
        }
      }
    }
    for (let i = 0; i < carriers.length; i++) {
      for (let j = i + 1; j < carriers.length; j++) {
        for (let k = j + 1; k < carriers.length; k++) {
          const a = carriers[i], b = carriers[j], c = carriers[k];
          const products = [a + b - c, a + c - b, b + c - a];
          for (let m = 0; m < carriers.length; m++) {
            if (m !== i && m !== j && m !== k &&
                products.some((product) => Math.abs(carriers[m] - product) < guard)) return true;
          }
        }
      }
    }
    return false;
  }

  function buildRfPlan() {
    const low = number('rfBandMin'), high = number('rfBandMax');
    const count = Math.floor(number('rfCount'));
    const spacing = number('rfSpacing');
    const guard = number('rfGuard');
    if (!Number.isFinite(low) || !Number.isFinite(high) || low <= 0 || high <= low || high > 10000) throw new Error('İzinli bant alt/üst sınırını MHz cinsinden doğru gir.');
    if (!Number.isInteger(count) || count < 1 || count > 64) throw new Error('Kanal sayısı 1 ile 64 arasında olmalı.');
    if (!Number.isFinite(spacing) || spacing < .01 || spacing > 20 || !Number.isFinite(guard) || guard < .01 || guard > 10) throw new Error('Kanal aralığı veya koruma aralığı geçersiz.');
    const rawStep = Math.max(.01, Math.min(spacing, (high - low) / 1600));
    const step = Math.max(rawStep, (high - low) / 20000);
    const candidates = [];
    for (let f = low + spacing / 2; f <= high - spacing / 2 + 1e-9; f += step) {
      if (rfBlocked.some((b) => Math.abs(b.frequency - f) <= b.guard)) continue;
      candidates.push(Number(f.toFixed(5)));
    }
    const selected = [];
    for (let slot = 0; slot < count; slot++) {
      const target = low + (slot + 1) * (high - low) / (count + 1);
      const choices = candidates.filter((f) => !selected.includes(f) && selected.every((s) => Math.abs(s - f) >= spacing) && !rfIntermodCollision(f, selected, guard));
      choices.sort((a, b) => Math.abs(a - target) - Math.abs(b - target));
      if (!choices.length) break;
      selected.push(choices[0]);
    }
    selected.sort((a, b) => a - b);
    rfAssignments = selected.map((frequency, i) => ({ channel: i + 1, frequency, name: 'Kablosuz kanal ' + (i + 1) }));
    return { low, high, requested: count, selected: rfAssignments, blocked: rfBlocked.length, spacing, guard };
  }

  function renderRfPlan() {
    const r = buildRfPlan();
    const body = byId('rfTableBody');
    body.textContent = '';
    r.selected.forEach((item) => {
      const tr = document.createElement('tr');
      [String(item.channel), item.name, fmt(item.frequency, 3) + ' MHz', 'Kullanıcı bandı içinde'].forEach((value) => {
        const td = document.createElement('td'); td.textContent = value; tr.appendChild(td);
      });
      body.appendChild(tr);
    });
    text('rfResult', r.selected.length + ' / ' + r.requested + ' kanal üretildi. Tarama verisinden engellenen frekans aralığı: ' + r.blocked + '.');
    text('rfWarning', 'Yasal kullanım onayı değildir. Bant sınırını bulunduğun yer, cihaz modeli ve güncel BTK/izin koşullarına göre sen belirlemelisin. Program kendiliğinden ülke frekans tablosu veya cihaz uygunluğu varsaymaz.');
  }

  function initRfPlanner() {
    if (!byId('rfGenerate')) return;
    bind('rfGenerate', 'click', () => { try { renderRfPlan(); } catch (e) { showError('rfResult', e); } });
    bind('rfScanFile', 'change', async (event) => {
      try {
        const file = event.target.files && event.target.files[0];
        if (!file) return;
        if (file.size > 5 * 1024 * 1024) throw new Error('Tarama CSV dosyası 5 MB sınırını aşamaz.');
        const raw = await file.text();
        const rows = raw.split(/\r?\n/).slice(0, 20001);
        const blocked = [];
        rows.forEach((line, index) => {
          const cells = line.split(/[;,\t]/).map((s) => s.trim().replace(/^"|"$/g, '').replace(',', '.'));
          if (!cells.length || !cells[0]) return;
          const f = Number(cells[0]);
          const level = Number(cells[1]);
          if (!Number.isFinite(f)) { if (index === 0) return; return; }
          if (f <= 0 || f > 10000) return;
          const limit = number('rfNoiseLimit');
          if (Number.isFinite(level) && level >= limit) blocked.push({ frequency: f, guard: number('rfGuard') });
        });
        rfBlocked = blocked;
        text('rfScanInfo', blocked.length + ' yoğun frekans noktası okundu. CSV biçimi: frekans_MHz,seviye_dBm. Cihaz ölçüm birimini doğrula.');
        renderRfPlan();
      } catch (e) { showError('rfScanInfo', e); }
      finally { event.target.value = ''; }
    });
    bind('rfExport', 'click', () => {
      if (!rfAssignments.length) { try { renderRfPlan(); } catch (e) { showError('rfResult', e); return; } }
      const lines = ['Kanal;Etiket;Frekans_MHz'].concat(rfAssignments.map((x) => [x.channel, x.name, x.frequency].join(';')));
      downloadText('stagepulse_kablosuz_frekans_plani.csv', '\uFEFF' + lines.join('\r\n'), 'text/csv;charset=utf-8');
    });
    text('rfResult', 'Önce bulunduğun yer için doğrulanmış frekans aralığını gir.');
  }

  // ---------------------------------------------------------------------------
  // 4. M32 / X32 SAHNE DOSYASI OKUYUCU
  // ---------------------------------------------------------------------------
  function tokenizeSceneLine(line) {
    const tokens = [];
    let current = '', quoted = false, active = false;
    for (let i = 0; i < line.length; i++) {
      const c = line[i];
      if (c === '"' && (i === 0 || line[i - 1] !== '\\')) { quoted = !quoted; active = true; }
      else if (/\s/.test(c) && !quoted) {
        if (active) { tokens.push(current); current = ''; active = false; }
      } else { current += c; active = true; }
    }
    if (active) tokens.push(current);
    return tokens;
  }

  function sceneConnector(block, offset) {
    const m = String(block || '').match(/^([A-Z]+)(\d+)-(\d+)$/i);
    if (!m) return null;
    const prefix = m[1].toUpperCase(), first = Number(m[2]), last = Number(m[3]);
    if (!Number.isInteger(first) || !Number.isInteger(last) || last < first || last - first > 47) return null;
    const names = { IN: 'Yerel XLR', A: 'AES50-A', B: 'AES50-B', CARD: 'Kart girişi', AUX: 'Yardımcı giriş' };
    if (!names[prefix]) return null;
    return { device: names[prefix], first, last, offset };
  }

  function parseM32Scene(content, fileName) {
    if (typeof content !== 'string' || content.length > 8 * 1024 * 1024) throw new Error('Sahne dosyası boş veya 8 MB sınırından büyük.');
    const lines = content.replace(/^\uFEFF/, '').split(/\r?\n/).slice(0, 100000);
    if (!lines[0] || !lines[0].trim().startsWith('#')) throw new Error('Beklenen X32/M32 .scn dosya başlığı bulunamadı.');
    const parsed = new Map();
    lines.forEach((line) => {
      if (!line || line[0] !== '/') return;
      const tokens = tokenizeSceneLine(line);
      if (tokens.length) parsed.set(tokens[0], tokens.slice(1));
    });
    const routingTokens = parsed.get('/config/routing/IN') || [];
    const slotMap = new Map();
    routingTokens.slice(0, 4).forEach((block, index) => {
      const b = sceneConnector(block, index * 8);
      if (!b) return;
      for (let n = 0; n < 8 && b.first + n <= b.last; n++) {
        slotMap.set(index * 8 + n + 1, b.device + ' ' + (b.first + n));
      }
    });
    const channels = [];
    for (let ch = 1; ch <= 32; ch++) {
      const n = String(ch).padStart(2, '0');
      const conf = parsed.get('/ch/' + n + '/config');
      if (!conf) continue;
      const sourceSlot = Number(conf[conf.length - 1]);
      const source = Number.isInteger(sourceSlot) && sourceSlot >= 1 && sourceSlot <= 32
        ? (slotMap.get(sourceSlot) || 'Giriş yuvası ' + sourceSlot + ' (eşleme çözülemedi)')
        : sourceSlot >= 33 && sourceSlot <= 40 ? 'Yardımcı giriş ' + (sourceSlot - 32)
        : sourceSlot >= 41 && sourceSlot <= 48 ? 'FX dönüşü ' + (sourceSlot - 40)
        : sourceSlot === 0 ? 'Kapalı' : 'Bilinmeyen kaynak (' + conf[conf.length - 1] + ')';
      const preamp = parsed.get('/ch/' + n + '/preamp') || [];
      const gate = parsed.get('/ch/' + n + '/gate') || [];
      const dyn = parsed.get('/ch/' + n + '/dyn') || [];
      const eq = parsed.get('/ch/' + n + '/eq') || [];
      const gateEnabled = gate[0] === 'ON' ? 'Açık' : gate[0] === 'OFF' ? 'Kapalı' : gate[0] || 'Bilinmiyor';
      const gateLabel = gate.length > 1 && gateEnabled !== 'Bilinmiyor' ? gateEnabled + ' · ' + gate[1] + (gate[2] ? ' · Eşik ' + gate[2] + ' dB' : '') : gateEnabled;
      const dynTypes = { COMP: 'Kompresör', EXP: 'Genişletici', GATE: 'Gürültü kapısı', LIMIT: 'Sınırlayıcı' };
      const dynEnabled = dyn[0] === 'ON' ? 'Açık' : dyn[0] === 'OFF' ? 'Kapalı' : dyn[0] || 'Bilinmiyor';
      const dynLabel = dynEnabled === 'Açık'
        ? [dynTypes[dyn[1]] || dyn[1] || 'Dinamik işlemci', dyn[4] ? 'Eşik ' + dyn[4] + ' dB' : '', dyn[5] ? 'Oran ' + dyn[5] + ':1' : ''].filter(Boolean).join(' · ')
        : dynEnabled;
      const eqLabel = eq[0] === 'ON' ? 'Açık' : eq[0] === 'OFF' ? 'Kapalı' : eq[0] || 'Bilinmiyor';
      const sends = [];
      for (let bus = 1; bus <= 16; bus++) {
        const busTokens = parsed.get('/ch/' + n + '/mix/' + String(bus).padStart(2, '0'));
        if (busTokens && busTokens[0] === 'ON') {
          const level = busTokens[1] || '';
          sends.push(level === '-oo' || level.toLowerCase() === '-inf' ? 'Yardımcı yol (Bus) ' + bus + ' (seviye −∞ dB)' :
            level ? 'Yardımcı yol (Bus) ' + bus + ' (' + level + ' dB)' : 'Yardımcı yol (Bus) ' + bus + ' (seviye bilinmiyor)');
        }
      }
      channels.push({
        channel: ch, name: conf[0] || 'Kanal ' + ch, inputSlot: sourceSlot, source,
        preampGain: preamp[0] || 'Bilinmiyor',
        gate: gateLabel, compressor: dynLabel,
        eq: eqLabel, sends
      });
    }
    const warnings = [];
    if (routingTokens.length < 4) warnings.push('Giriş yönlendirme satırı eksik veya kısmi; bazı fiziksel girişler kesin eşlenemedi.');
    if (!channels.length) warnings.push('Kanal yapılandırması bulunamadı.');
    if (lines.length > 100000) warnings.push('Dosya çok uzun; yalnızca ilk 100.000 satır işlendi.');
    return {
      fileName: fileName || 'Sahne dosyası',
      header: lines[0].trim(),
      channels,
      routing: routingTokens,
      outputRouting: parsed.get('/config/routing/OUT') || [],
      warnings,
      lineCount: lines.length
    };
  }

  let parsedScene = null;
  function renderSceneReport(report) {
    const body = byId('patchTableBody');
    body.textContent = '';
    report.channels.forEach((ch) => {
      const tr = document.createElement('tr');
      [String(ch.channel), ch.name, String(ch.inputSlot), ch.source, ch.preampGain + ' dB', ch.gate, ch.compressor, ch.eq, ch.sends.join(', ') || 'Yok'].forEach((value) => {
        const td = document.createElement('td'); td.textContent = value; tr.appendChild(td);
      });
      body.appendChild(tr);
    });
    text('patchSummary', report.fileName + ' · ' + report.channels.length + ' kanal bulundu · ' + report.lineCount + ' satır okundu. Dosya bu bilgisayarda çözümlendi.');
    text('patchWarnings', report.warnings.length ? report.warnings.join(' ') : 'Başlık, kanal adları ve temel giriş eşlemesi okundu. Bilinmeyen alanlar tahmin edilmedi.');
    text('patchRouteInfo', 'Giriş blokları: ' + (report.routing.join(' · ') || 'Bulunamadı') + ' | Çıkış blokları: ' + (report.outputRouting.join(' · ') || 'Bulunamadı'));
    byId('patchExport').disabled = report.channels.length === 0;
    byId('patchPrint').disabled = report.channels.length === 0;
  }

  function initPatchAnalyzer() {
    if (!byId('patchFile')) return;
    bind('patchFile', 'change', async (event) => {
      try {
        const file = event.target.files && event.target.files[0];
        if (!file) return;
        if (file.size > 8 * 1024 * 1024) throw new Error('Sahne dosyası 8 MB sınırını aşamaz.');
        const content = await file.text();
        parsedScene = parseM32Scene(content, file.name);
        renderSceneReport(parsedScene);
      } catch (e) { showError('patchSummary', e); }
      finally { event.target.value = ''; }
    });
    bind('patchExport', 'click', () => {
      if (!parsedScene) return;
      const headers = ['Kanal', 'Ad', 'Giriş_yuvası', 'Fiziksel_kaynak', 'Ön_yükselteç_dB', 'Gürültü_kapısı', 'Dinamik_işlemci', 'Ekolayzer', 'Gönderimler'];
      const rows = parsedScene.channels.map((c) => [c.channel, c.name, c.inputSlot, c.source, c.preampGain, c.gate, c.compressor, c.eq, c.sends.join(' | ')]);
      const csv = [headers].concat(rows).map((row) => row.map((x) => '"' + String(x ?? '').replace(/"/g, '""') + '"').join(';')).join('\r\n');
      downloadText(safeFileName(parsedScene.fileName) + '_kanal_baglanti_raporu.csv', '\uFEFF' + csv, 'text/csv;charset=utf-8');
    });
    bind('patchPrint', 'click', () => { if (parsedScene) window.print(); });
  }

  // ---------------------------------------------------------------------------
  // 5. ÖLÇÜM NOKTALARINDAN ODA SPL HARİTASI (CSV)
  // ---------------------------------------------------------------------------
  let roomMeasurements = [];
  function roomHeatColor(value, min, max) {
    const t = clamp((value - min) / Math.max(.001, max - min), 0, 1);
    const hue = 220 - 220 * t;
    return 'hsl(' + hue + ',78%,48%)';
  }
  function isRoomMeasurementInsideRoom(point, roomW, roomD) {
    return Number.isFinite(point.x) && Number.isFinite(point.y) &&
      Number.isFinite(roomW) && Number.isFinite(roomD) && roomW > 0 && roomD > 0 &&
      point.x >= 0 && point.y >= 0 && point.x <= roomW && point.y <= roomD;
  }

  function drawRoomMap() {
    const canvas = byId('roomMapCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width, height = canvas.height;
    const roomW = number('roomMapWidth'), roomD = number('roomMapDepth');
    if (!(roomW > 0 && roomD > 0)) throw new Error('Oda genişliği ve derinliği pozitif olmalı.');
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#10151d'; ctx.fillRect(0, 0, width, height);
    if (!roomMeasurements.length) {
      const margin = 44, plotW = width - margin * 2, plotH = height - margin * 2;
      ctx.strokeStyle = 'rgba(255,255,255,.10)'; ctx.lineWidth = 1;
      for (let x = 0; x <= 10; x++) { const px = margin + x * plotW / 10; ctx.beginPath(); ctx.moveTo(px, margin); ctx.lineTo(px, margin + plotH); ctx.stroke(); }
      for (let y = 0; y <= 8; y++) { const py = margin + y * plotH / 8; ctx.beginPath(); ctx.moveTo(margin, py); ctx.lineTo(margin + plotW, py); ctx.stroke(); }
      ctx.strokeStyle = '#657181'; ctx.lineWidth = 2; ctx.strokeRect(margin, margin, plotW, plotH);
      ctx.fillStyle = '#aab5c2'; ctx.textAlign = 'center'; ctx.font = '600 18px Segoe UI, Arial';
      ctx.fillText('Ölçüm CSV dosyası bekleniyor', width / 2, height / 2 - 8);
      ctx.font = '13px Segoe UI, Arial'; ctx.fillText(roomW + ' m × ' + roomD + ' m · en az 3 nokta', width / 2, height / 2 + 20);
      text('roomMapSummary', 'Ölçüm verisi yok. CSV dosyası seçildiğinde göreli dağılım çizilir.');
      text('roomMapWarning', 'Henüz ölçüm verisi yüklenmedi. Boş görünüm ölçüm sonucu değildir.');
      return;
    }
    const vals = roomMeasurements.map((p) => p.spl);
    const min = Math.min.apply(null, vals), max = Math.max.apply(null, vals);
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#10151d'; ctx.fillRect(0, 0, width, height);
    const margin = 44, plotW = width - margin * 2, plotH = height - margin * 2;
    const nx = 28, ny = 18;
    for (let gy = 0; gy < ny; gy++) {
      for (let gx = 0; gx < nx; gx++) {
        const x = (gx + .5) / nx * roomW, y = (gy + .5) / ny * roomD;
        let weighted = 0, weights = 0, exact = null;
        roomMeasurements.forEach((p) => {
          const dx = x - p.x, dy = y - p.y, d2 = dx * dx + dy * dy;
          if (d2 < .0001) exact = p.spl;
          const w = 1 / Math.max(.01, d2);
          weighted += p.spl * w; weights += w;
        });
        const value = exact === null ? weighted / weights : exact;
        ctx.fillStyle = roomHeatColor(value, min, max);
        const px = margin + gx * plotW / nx, py = margin + gy * plotH / ny;
        ctx.fillRect(px, py, plotW / nx + 1, plotH / ny + 1);
      }
    }
    ctx.strokeStyle = '#d9e0e8'; ctx.lineWidth = 2; ctx.strokeRect(margin, margin, plotW, plotH);
    ctx.fillStyle = '#f4f5f6'; ctx.font = '12px Segoe UI, Arial'; ctx.textAlign = 'center';
    ctx.fillText(roomW + ' m', margin + plotW / 2, height - 10);
    ctx.save(); ctx.translate(14, margin + plotH / 2); ctx.rotate(-Math.PI / 2); ctx.fillText(roomD + ' m', 0, 0); ctx.restore();
    roomMeasurements.forEach((p, index) => {
      const x = margin + p.x / roomW * plotW, y = margin + p.y / roomD * plotH;
      ctx.beginPath(); ctx.arc(x, y, 5, 0, Math.PI * 2); ctx.fillStyle = '#fff'; ctx.fill();
      ctx.strokeStyle = '#10151d'; ctx.lineWidth = 2; ctx.stroke();
      ctx.fillStyle = '#fff'; ctx.font = 'bold 11px Segoe UI, Arial'; ctx.fillText(fmt(p.spl, 1), x, y - 9);
    });
    text('roomMapSummary', roomMeasurements.length + ' ölçüm noktası · En düşük ' + fmt(min, 1) + ' dB · En yüksek ' + fmt(max, 1) + ' dB · Aralık ' + fmt(max - min, 1) + ' dB.');
    text('roomMapWarning', 'Renkli yüzey, ölçüm noktaları arasında ters uzaklık ağırlıklı enterpolasyondur. Kalibrasyon, mikrofon yüksekliği, zaman ağırlığı ve ölçüm standardı doğrulanmadan raporlanabilir mutlak SPL sonucu sayılmaz.');
  }

  function initRoomMap() {
    if (!byId('roomMapFile')) return;
    bind('roomMapFile', 'change', async (event) => {
      try {
        const file = event.target.files && event.target.files[0];
        if (!file) return;
        if (file.size > 2 * 1024 * 1024) throw new Error('Ölçüm CSV dosyası 2 MB sınırını aşamaz.');
        const roomW = number('roomMapWidth'), roomD = number('roomMapDepth');
        if (!(roomW > 0 && roomD > 0)) throw new Error('Önce geçerli oda genişliği ve derinliği gir.');
        const rows = (await file.text()).split(/\r?\n/).slice(0, 501);
        const points = [];
        let outsideCount = 0;
        rows.forEach((line, index) => {
          const cells = line.split(/[;,\t]/).map((s) => s.trim().replace(/^"|"$/g, ''));
          if (cells.length < 3) return;
          const x = Number(cells[0].replace(',', '.')), y = Number(cells[1].replace(',', '.')), spl = Number(cells[2].replace(',', '.'));
          if (![x, y, spl].every(Number.isFinite)) { if (index === 0) return; return; }
          if (spl < 0 || spl > 180) return;
          const point = { x, y, spl };
          if (!isRoomMeasurementInsideRoom(point, roomW, roomD)) { outsideCount++; return; }
          points.push(point);
        });
        if (points.length < 3) throw new Error('Oda sınırları içinde en az üç geçerli ölçüm noktası gerekli. Oda dışındaki ' + outsideCount + ' nokta reddedildi.');
        if (points.length > 500) throw new Error('Bu sürümde en fazla 500 ölçüm noktası işlenebilir.');
        roomMeasurements = points;
        drawRoomMap();
        if (outsideCount) text('roomMapSummary', points.length + ' ölçüm noktası kullanıldı; oda dışındaki ' + outsideCount + ' nokta reddedildi. ' + byId('roomMapSummary').textContent);
      } catch (e) { showError('roomMapSummary', e); }
      finally { event.target.value = ''; }
    });
    ['roomMapWidth','roomMapDepth'].forEach((id) => bind(id, 'change', () => { try { drawRoomMap(); } catch (e) { showError('roomMapSummary', e); } }));
    bind('roomMapClear', 'click', () => { roomMeasurements = []; drawRoomMap(); });
    drawRoomMap();
  }

  // ---------------------------------------------------------------------------
  // 6. HOPARLÖR KABİNİ VE GEÇİŞ FİLTRESİ EĞİTİM HESABI
  // ---------------------------------------------------------------------------
  function initSpeakerTools() {
    if (!byId('speakerCalculate')) return;
    bind('speakerCalculate', 'click', () => {
      try {
        const fs = number('speakerFs'), vas = number('speakerVas'), qts = number('speakerQts'), qtc = number('speakerQtc');
        if (!(fs > 0 && fs <= 500) || !(vas > 0 && vas <= 10000) || !(qts > 0.05 && qts < 1.5) || !(qtc > qts && qtc <= 1.5)) throw new Error('Fs, Vas, Qts ve Qtc değerlerini geçerli aralıklarda gir. Kapalı kutuda Qtc, Qts değerinden büyük olmalı.');
        const ratio = qtc / qts;
        const box = vas / (ratio * ratio - 1);
        const fc = fs * ratio;
        const result = 'Kapalı kutu eşdeğer hacmi: ' + fmt(box, 2) + ' L · Sistem rezonansı: ' + fmt(fc, 1) + ' Hz · Hedef toplam Q: ' + fmt(qtc, 3) + '. Bu hesap küçük işaretli ideal Thiele–Small modelidir; sürücü doğrusal olmayan davranışı ve gerçek kabin kayıpları ölçülmelidir.';
        text('speakerBoxResult', result);
      } catch (e) { showError('speakerBoxResult', e); }
    });
    bind('speakerFilterCalculate', 'click', () => {
      try {
        const fc = number('speakerCrossover'), order = Number(byId('speakerOrder').value), mode = byId('speakerFilterMode').value;
        if (!(fc >= 20 && fc <= 20000) || ![1,2,4].includes(order)) throw new Error('Kesim frekansı 20-20.000 Hz ve filtre derecesi 1, 2 veya 4 olmalı.');
        const ratios = [0.5, 0.7071, 1, 1.4142, 2];
        const rows = ratios.map((r) => {
          const f = fc * r;
          const gain = mode === 'high' ? 1 / Math.sqrt(1 + Math.pow(fc / f, 2 * order)) : 1 / Math.sqrt(1 + Math.pow(f / fc, 2 * order));
          return fmt(f, 0) + ' Hz: ' + fmt(20 * Math.log10(Math.max(gain, 1e-8)), 2) + ' dB';
        });
        text('speakerFilterResult', rows.join(' · ') + '. Teorik Butterworth genlik eğrisidir; gerçek FIR/IIR tasarımı, faz, gecikme ve DSP uygulaması değildir.');
      } catch (e) { showError('speakerFilterResult', e); }
    });
    byId('speakerCalculate').click();
    byId('speakerFilterCalculate').click();
  }

  // ---------------------------------------------------------------------------
  // 7. ÖLÇEKLİ 2B SAHNE / AV PLANI
  // ---------------------------------------------------------------------------
  let stageItems = [];
  let stageSelected = -1;
  let stageDrag = null;
  let stageObjectId = 1;
  const stageTypes = {
    speaker: { label: 'Ana hoparlör', code: 'PA', color: '#e5bc63' },
    sub: { label: 'Alt frekans hoparlörü', code: 'SUB', color: '#d89562' },
    monitor: { label: 'Sahne monitörü', code: 'MON', color: '#83b9ef' },
    foh: { label: 'Ön alan kontrol konsolu', code: 'FOH', color: '#8dc9a8' },
    stagebox: { label: 'Sahne kutusu', code: 'I/O', color: '#b89bea' },
    mic: { label: 'Mikrofon', code: 'MIC', color: '#dca0b8' },
    rack: { label: 'Cihaz kabini', code: 'RACK', color: '#a7b2bf' },
    delay: { label: 'Gecikme hoparlörü', code: 'DLY', color: '#f08b83' },
    display: { label: 'LED ekran', code: 'LED', color: '#78c8cf' }
  };

  function stageDefaults() {
    stageItems = [
      { id: stageObjectId++, type: 'speaker', name: 'Sol ana PA', x: 4, y: 2 },
      { id: stageObjectId++, type: 'speaker', name: 'Sağ ana PA', x: 16, y: 2 },
      { id: stageObjectId++, type: 'sub', name: 'Sol sub', x: 5, y: 3.5 },
      { id: stageObjectId++, type: 'sub', name: 'Sağ sub', x: 15, y: 3.5 },
      { id: stageObjectId++, type: 'monitor', name: 'Monitör 1', x: 8, y: 9 },
      { id: stageObjectId++, type: 'monitor', name: 'Monitör 2', x: 12, y: 9 },
      { id: stageObjectId++, type: 'stagebox', name: 'Sahne kutusu', x: 10, y: 7 },
      { id: stageObjectId++, type: 'foh', name: 'FOH', x: 10, y: 24 }
    ];
    stageSelected = -1;
  }

  function stageMetrics() {
    const roomW = number('stageRoomWidth'), roomD = number('stageRoomDepth'), stageW = number('stageDeckWidth'), stageD = number('stageDeckDepth');
    if (![roomW, roomD, stageW, stageD].every(Number.isFinite) || roomW < 4 || roomD < 4 || stageW < 2 || stageD < 1 || stageW > roomW || stageD > roomD) throw new Error('Oda ve sahne ölçüleri geçersiz. Sahne oda sınırlarının içinde kalmalı.');
    return { roomW, roomD, stageW, stageD };
  }

  function drawStagePlan() {
    const canvas = byId('stageCanvas');
    if (!canvas) return;
    const c = canvas.getContext('2d');
    const p = stageMetrics(), w = canvas.width, h = canvas.height, margin = 42;
    const scale = Math.min((w - margin * 2) / p.roomW, (h - margin * 2) / p.roomD);
    const rw = p.roomW * scale, rd = p.roomD * scale, ox = (w - rw) / 2, oy = (h - rd) / 2;
    const px = (x) => ox + x * scale, py = (y) => oy + y * scale;
    c.clearRect(0, 0, w, h); c.fillStyle = '#0d121a'; c.fillRect(0, 0, w, h);
    c.fillStyle = '#17202b'; c.fillRect(ox, oy, rw, rd);
    c.strokeStyle = 'rgba(255,255,255,.10)'; c.lineWidth = 1;
    for (let x = 0; x <= p.roomW; x++) { c.beginPath(); c.moveTo(px(x), oy); c.lineTo(px(x), oy + rd); c.stroke(); }
    for (let y = 0; y <= p.roomD; y++) { c.beginPath(); c.moveTo(ox, py(y)); c.lineTo(ox + rw, py(y)); c.stroke(); }
    const sx = px((p.roomW - p.stageW) / 2), sy = py(1), sw = p.stageW * scale, sh = p.stageD * scale;
    c.fillStyle = '#393126'; c.fillRect(sx, sy, sw, sh); c.strokeStyle = '#d8b45d'; c.lineWidth = 2; c.strokeRect(sx, sy, sw, sh);
    c.fillStyle = '#f3e3bb'; c.font = 'bold 15px Segoe UI, Arial'; c.textAlign = 'center'; c.fillText('SAHNE · ' + p.stageW + ' × ' + p.stageD + ' m', sx + sw / 2, sy + sh / 2 + 5);
    c.fillStyle = 'rgba(130,185,239,.09)'; c.fillRect(ox, py(1 + p.stageD + .5), rw, Math.max(0, rd - (1 + p.stageD + .5) * scale));
    c.fillStyle = '#9ca7b5'; c.font = '12px Segoe UI, Arial'; c.fillText('İZLEYİCİ ALANI', ox + rw / 2, py(Math.min(p.roomD - .5, 1 + p.stageD + 2)));
    stageItems.forEach((item, index) => {
      const type = stageTypes[item.type] || stageTypes.mic;
      const x = px(item.x), y = py(item.y), radius = Math.max(10, Math.min(16, scale * .28));
      c.beginPath(); c.arc(x, y, radius, 0, Math.PI * 2); c.fillStyle = type.color; c.fill();
      c.lineWidth = index === stageSelected ? 4 : 1.5; c.strokeStyle = index === stageSelected ? '#fff' : '#10151d'; c.stroke();
      c.fillStyle = '#10151d'; c.font = 'bold 9px Segoe UI, Arial'; c.textAlign = 'center'; c.fillText(type.code, x, y + 3);
      c.fillStyle = '#f3f5f7'; c.font = '11px Segoe UI, Arial'; c.fillText(item.name, x, y - radius - 5);
    });
    c.fillStyle = '#9ca7b5'; c.font = '11px Segoe UI, Arial'; c.textAlign = 'left'; c.fillText('ÖLÇEKLİ ÜSTTEN GÖRÜNÜŞ · 1 kare = 1 m', 12, 20);
    const cableTotal = stageItems.reduce((sum, item) => {
      if (item.type === 'foh') return sum;
      const foh = stageItems.find((x) => x.type === 'foh');
      if (!foh) return sum;
      return sum + Math.hypot(item.x - foh.x, item.y - foh.y) * 1.15;
    }, 0);
    text('stageSummary', stageItems.length + ' ekipman yerleşimi · Yaklaşık kablo toplamı ' + fmt(cableTotal, 1) + ' m (doğrusal mesafe + %15 servis payı).');
    const selected = stageItems[stageSelected];
    text('stageSelectedInfo', selected ? selected.name + ' · ' + fmt(selected.x, 1) + ' m / ' + fmt(selected.y, 1) + ' m' : 'Taşımak için nesneyi sürükle. Silmek için nesneyi seçip kaldır düğmesine bas.');
  }

  function stagePointFromEvent(event) {
    const canvas = byId('stageCanvas'), r = canvas.getBoundingClientRect(), p = stageMetrics();
    const margin = 42, scale = Math.min((canvas.width - margin * 2) / p.roomW, (canvas.height - margin * 2) / p.roomD);
    const rw = p.roomW * scale, rd = p.roomD * scale, ox = (canvas.width - rw) / 2, oy = (canvas.height - rd) / 2;
    const x = (event.clientX - r.left) / r.width * canvas.width, y = (event.clientY - r.top) / r.height * canvas.height;
    return { x: clamp((x - ox) / scale, 0, p.roomW), y: clamp((y - oy) / scale, 0, p.roomD), px: x, py: y, scale, ox, oy };
  }

  function renderStageInventory() {
    const body = byId('stageInventory');
    if (!body) return;
    body.textContent = '';
    stageItems.forEach((item) => {
      const tr = document.createElement('tr');
      [item.name, (stageTypes[item.type] || stageTypes.mic).label, fmt(item.x, 1) + ' m', fmt(item.y, 1) + ' m'].forEach((v) => {
        const td = document.createElement('td'); td.textContent = v; tr.appendChild(td);
      });
      body.appendChild(tr);
    });
    drawStagePlan();
  }

  function initStagePlanner() {
    if (!byId('stageCanvas')) return;
    stageDefaults();
    const canvas = byId('stageCanvas');
    bind('stageAdd', 'click', () => {
      if (stageItems.length >= 250) { showError('stageSelectedInfo', 'Bir planda en fazla 250 ekipman kullanılabilir.'); return; }
      const type = byId('stageItemType').value, label = (stageTypes[type] || stageTypes.mic).label;
      stageItems.push({ id: stageObjectId++, type, name: label + ' ' + (stageItems.filter((x) => x.type === type).length + 1), x: number('stageRoomWidth') / 2, y: Math.min(number('stageRoomDepth') - 1, number('stageDeckDepth') + 2) });
      stageSelected = stageItems.length - 1; renderStageInventory();
    });
    bind('stageRemove', 'click', () => {
      if (stageSelected < 0) return;
      stageItems.splice(stageSelected, 1); stageSelected = -1; renderStageInventory();
    });
    bind('stageReset', 'click', () => { stageDefaults(); renderStageInventory(); });
    ['stageRoomWidth','stageRoomDepth','stageDeckWidth','stageDeckDepth'].forEach((id) => bind(id, 'change', () => { try { drawStagePlan(); } catch (e) { showError('stageSelectedInfo', e); } }));
    canvas.addEventListener('pointerdown', (event) => {
      const p = stagePointFromEvent(event);
      let best = -1, distance = Infinity;
      stageItems.forEach((item, i) => { const d = Math.hypot(item.x - p.x, item.y - p.y); if (d < distance) { distance = d; best = i; } });
      if (distance <= .8) { stageSelected = best; stageDrag = { id: stageItems[best].id }; canvas.setPointerCapture(event.pointerId); renderStageInventory(); }
      else { stageSelected = -1; drawStagePlan(); }
    });
    canvas.addEventListener('pointermove', (event) => {
      if (!stageDrag) return;
      const p = stagePointFromEvent(event), item = stageItems.find((x) => x.id === stageDrag.id);
      if (!item) return;
      item.x = Number(p.x.toFixed(2)); item.y = Number(p.y.toFixed(2)); drawStagePlan();
    });
    const stopDrag = () => { if (stageDrag) { stageDrag = null; renderStageInventory(); } };
    canvas.addEventListener('pointerup', stopDrag); canvas.addEventListener('pointercancel', stopDrag);
    bind('stageExportJson', 'click', () => {
      const p = stageMetrics();
      downloadText('stagepulse_sahne_plani.json', JSON.stringify({ version: 1, room: { width: p.roomW, depth: p.roomD }, stage: { width: p.stageW, depth: p.stageD }, items: stageItems }, null, 2), 'application/json;charset=utf-8');
    });
    bind('stageExportCsv', 'click', () => {
      const lines = ['Ad;Ekipman;X_m;Y_m'].concat(stageItems.map((x) => [x.name, (stageTypes[x.type] || stageTypes.mic).label, x.x, x.y].join(';')));
      downloadText('stagepulse_sahne_envanteri.csv', '\uFEFF' + lines.join('\r\n'), 'text/csv;charset=utf-8');
    });
    bind('stageLoadJson', 'change', async (event) => {
      try {
        const file = event.target.files && event.target.files[0]; if (!file) return;
        if (file.size > 1024 * 1024) throw new Error('Plan dosyası 1 MB sınırını aşamaz.');
        const data = JSON.parse(await file.text());
        if (data.version !== 1 || !Array.isArray(data.items) || data.items.length > 250) throw new Error('Desteklenmeyen veya bozuk plan dosyası.');
        const roomW = Number(data.room?.width), roomD = Number(data.room?.depth), deckW = Number(data.stage?.width), deckD = Number(data.stage?.depth);
        if (![roomW, roomD, deckW, deckD].every(Number.isFinite) || roomW < 4 || roomD < 4 || deckW < 2 || deckD < 1 || deckW > roomW || deckD > roomD) throw new Error('Plan ölçüleri geçersiz.');
        const allowed = Object.keys(stageTypes);
        const items = data.items.map((x) => {
          if (!allowed.includes(x.type) || !Number.isFinite(Number(x.x)) || !Number.isFinite(Number(x.y))) throw new Error('Plan içinde geçersiz ekipman bulundu.');
          return { id: stageObjectId++, type: x.type, name: String(x.name || stageTypes[x.type].label).slice(0, 80), x: clamp(Number(x.x), 0, roomW), y: clamp(Number(x.y), 0, roomD) };
        });
        byId('stageRoomWidth').value = roomW; byId('stageRoomDepth').value = roomD; byId('stageDeckWidth').value = deckW; byId('stageDeckDepth').value = deckD;
        stageItems = items; stageSelected = -1; renderStageInventory();
      } catch (e) { showError('stageSelectedInfo', e); }
      finally { event.target.value = ''; }
    });
    renderStageInventory();
  }

  // ---------------------------------------------------------------------------
  // 8. DALGA, FAZ, İKİ KAYNAK VE SES GECİKMESİ LABORATUVARI
  // ---------------------------------------------------------------------------
  const waveMath = Object.freeze({
    soundSpeed(medium, temperatureC = 20) {
      if (medium === 'air') {
        if (!Number.isFinite(temperatureC) || temperatureC < -30 || temperatureC > 50) {
          throw new Error('Hava sıcaklığı -30 ile 50 °C arasında olmalı.');
        }
        return 331.3 * Math.sqrt(1 + temperatureC / 273.15);
      }
      if (medium === 'water') return 1480;
      if (medium === 'steel') return 5960;
      throw new Error('Bilinmeyen ses yayılma ortamı.');
    },
    calculate(medium, temperatureC, frequencyHz, distanceM) {
      const speed = waveMath.soundSpeed(medium, temperatureC);
      if (!Number.isFinite(frequencyHz) || frequencyHz < 20 || frequencyHz > 20000) {
        throw new Error('Frekans 20 ile 20.000 Hz arasında olmalı.');
      }
      if (!Number.isFinite(distanceM) || distanceM < 0 || distanceM > 100000) {
        throw new Error('Mesafe 0 ile 100.000 m arasında olmalı.');
      }
      const wavelengthM = speed / frequencyHz;
      const periodS = 1 / frequencyHz;
      const delayS = distanceM / speed;
      const phaseDeg = ((360 * frequencyHz * delayS) % 360 + 360) % 360;
      return { speedMps: speed, wavelengthM, periodS, delayS, phaseDeg, cycles: distanceM / wavelengthM };
    },
    combinedAmplitudeRatio(phaseDeg) {
      if (!Number.isFinite(phaseDeg)) throw new Error('Faz açısı sayısal olmalı.');
      return 2 * Math.abs(Math.cos(phaseDeg * Math.PI / 360));
    },
    relativeLevelDb(amplitudeRatio) {
      if (!Number.isFinite(amplitudeRatio) || amplitudeRatio < 0) throw new Error('Genlik oranı geçersiz.');
      return amplitudeRatio === 0 ? -Infinity : 20 * Math.log10(amplitudeRatio);
    },
    pascalsToDbSpl(rmsPa) {
      if (!Number.isFinite(rmsPa) || rmsPa <= 0) throw new Error('RMS basınç sıfırdan büyük olmalı.');
      return 20 * Math.log10(rmsPa / 0.00002);
    },
    dbSplToPascals(dbSpl) {
      if (!Number.isFinite(dbSpl) || dbSpl < -100 || dbSpl > 200) throw new Error('dB SPL değeri -100 ile 200 arasında olmalı.');
      return 0.00002 * Math.pow(10, dbSpl / 20);
    },
    twoSource(frequencyHz, speedMps, ax, ay, bx, by, mx, my) {
      const rA = Math.max(0.001, Math.hypot(mx - ax, my - ay));
      const rB = Math.max(0.001, Math.hypot(mx - bx, my - by));
      const aA = 1 / Math.sqrt(Math.max(rA, 0.5));
      const aB = 1 / Math.sqrt(Math.max(rB, 0.5));
      const thetaA = 2 * Math.PI * frequencyHz * rA / speedMps;
      const thetaB = 2 * Math.PI * frequencyHz * rB / speedMps;
      const real = aA * Math.cos(thetaA) + aB * Math.cos(thetaB);
      const imaginary = aA * Math.sin(thetaA) + aB * Math.sin(thetaB);
      const amplitude = Math.hypot(real, imaginary);
      const ratio = amplitude / Math.max(aA + aB, 1e-12);
      const delayS = (rB - rA) / speedMps;
      const phaseDeg = ((360 * frequencyHz * delayS) % 360 + 360) % 360;
      return {
        distanceAM: rA, distanceBM: rB, pathDifferenceM: rB - rA,
        delayS, phaseDeg, amplitudeRatio: ratio,
        relativeLevelDb: ratio === 0 ? -Infinity : 20 * Math.log10(ratio)
      };
    }
  });

  function initWaveLab() {
    const canvas = byId('waveLabCanvas');
    if (!canvas || canvas.dataset.spBound) return;
    canvas.dataset.spBound = '1';
    const id = (name) => byId(name);
    const put = (name, value) => { const node = id(name); if (node) node.textContent = value; };
    const read = (name, fallback = 0) => {
      const node = id(name), value = node ? Number(String(node.value).replace(',', '.')) : fallback;
      return Number.isFinite(value) ? value : fallback;
    };
    const state = { medium: 'air', temperatureC: 20, frequencyHz: 440, distanceM: 1, phaseDeg: 90 };
    let audio = null, dragging = null;

    let micDelayStream = null, micDelayAudio = null;
    let micDelayStartToken = 0, micDelayPendingContext = null;
    function updateMicDelay() {
      const delayMs = clamp(read('waveMicDelay', 20), 0, 5000);
      if (id('waveMicDelay') && document.activeElement !== id('waveMicDelay')) id('waveMicDelay').value = fmt(delayMs, 1);
      if (id('waveMicDelaySlider')) id('waveMicDelaySlider').value = delayMs;
      if (micDelayAudio) micDelayAudio.delay.delayTime.setTargetAtTime(delayMs / 1000, micDelayAudio.context.currentTime, 0.015);
      const airSpeed = waveMath.soundSpeed('air', state.temperatureC);
      const phase = ((360 * state.frequencyHz * delayMs / 1000) % 360 + 360) % 360;
      const sampleRate = micDelayAudio ? micDelayAudio.context.sampleRate : 48000;
      put('waveMicDistance', fmt(airSpeed * delayMs / 1000, 3) + ' m');
      put('waveMicPhase', fmt(phase, 2) + '°');
      put('waveMicSamples', Math.round(delayMs / 1000 * sampleRate).toLocaleString('tr-TR') + ' örnek');
      put('waveMicRate', Math.round(sampleRate).toLocaleString('tr-TR') + ' Hz');
    }
    async function refreshMicDevices() {
      if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) return;
      const devices = await navigator.mediaDevices.enumerateDevices();
      const input = id('waveMicInput'), output = id('waveMicOutput');
      const selectedInput = input.value, selectedOutput = output.value;
      input.innerHTML = '<option value="">Sistem varsayılanı</option>';
      output.innerHTML = '<option value="">Sistem varsayılanı</option>';
      devices.filter(device => device.kind === 'audioinput').forEach((device, index) => {
        const option = document.createElement('option');
        option.value = device.deviceId; option.textContent = device.label || ('Mikrofon ' + (index + 1));
        input.appendChild(option);
      });
      devices.filter(device => device.kind === 'audiooutput').forEach((device, index) => {
        const option = document.createElement('option');
        option.value = device.deviceId; option.textContent = device.label || ('Ses çıkışı ' + (index + 1));
        output.appendChild(option);
      });
      if ([...input.options].some(option => option.value === selectedInput)) input.value = selectedInput;
      if ([...output.options].some(option => option.value === selectedOutput)) output.value = selectedOutput;
      const canSelectOutput = !!(micDelayAudio && typeof micDelayAudio.context.setSinkId === 'function');
      output.disabled = !!micDelayAudio && !canSelectOutput;
      if (!canSelectOutput) output.title = 'Bu WebView ses çıkış cihazı seçimini desteklemiyor; sistem varsayılanı kullanılır.';
    }
    async function startMicDelay() {
      if (micDelayAudio || micDelayPendingContext) return;
      const startToken = ++micDelayStartToken;
      const media = navigator.mediaDevices;
      if (!media || !media.getUserMedia) {
        put('waveMicStatus', 'Mikrofon erişimi desteklenmiyor. Güvenli bağlam (HTTPS veya localhost) ve mikrofon izni gerekir.');
        return;
      }
      const AudioCtor = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtor) { put('waveMicStatus', 'Bu cihazda Web Audio desteklenmiyor.'); return; }
      id('waveMicStart').disabled = true;
      put('waveMicStatus', 'Mikrofon izni bekleniyor…');
      let startStream = null, startContext = null;
      try {
        const selectedInput = id('waveMicInput').value;
        const audioConstraints = {
          echoCancellation: false, noiseSuppression: false, autoGainControl: false,
          channelCount: 1
        };
        if (selectedInput) audioConstraints.deviceId = { exact: selectedInput };
        startStream = await media.getUserMedia({ audio: audioConstraints, video: false });
        if (startToken !== micDelayStartToken || document.hidden) {
          startStream.getTracks().forEach(track => track.stop());
          return;
        }
        micDelayStream = startStream;
        try { await refreshMicDevices(); } catch (_) {}
        startContext = new AudioCtor({ latencyHint: 'interactive' });
        micDelayPendingContext = startContext;
        await startContext.resume();
        if (startToken !== micDelayStartToken || document.hidden) {
          if (micDelayStream === startStream) micDelayStream = null;
          startStream.getTracks().forEach(track => track.stop());
          if (micDelayPendingContext === startContext) micDelayPendingContext = null;
          try { startContext.close().catch(() => {}); } catch (_) {}
          return;
        }
        const source = startContext.createMediaStreamSource(startStream);
        const delay = startContext.createDelay(5.0);
        const monitorGain = startContext.createGain();
        const limiter = startContext.createDynamicsCompressor();
        delay.delayTime.value = clamp(read('waveMicDelay', 20), 0, 5000) / 1000;
        monitorGain.gain.value = id('waveMicMonitor').checked ? 0.06 : 0;
        limiter.threshold.value = -8; limiter.knee.value = 0; limiter.ratio.value = 20;
        limiter.attack.value = 0.003; limiter.release.value = 0.15;
        source.connect(delay).connect(monitorGain).connect(limiter).connect(startContext.destination);
        micDelayAudio = { context: startContext, source, delay, monitorGain, limiter };
        micDelayPendingContext = null;
        const selectedOutput = id('waveMicOutput').value;
        let outputNote = 'Sistem varsayılan ses çıkışı kullanılıyor.';
        if (selectedOutput && typeof startContext.setSinkId === 'function') {
          await startContext.setSinkId(selectedOutput);
          if (startToken !== micDelayStartToken || document.hidden) return;
          outputNote = 'Seçilen ses çıkışı kullanılıyor.';
        } else if (selectedOutput) {
          outputNote = 'Bu cihaz özel ses çıkışı seçimini desteklemiyor; sistem varsayılanı kullanılıyor.';
        }
        await refreshMicDevices();
        if (startToken !== micDelayStartToken || document.hidden) return;
        id('waveMicInput').disabled = true;
        id('waveMicStart').disabled = true;
        id('waveMicStop').disabled = false;
        updateMicDelay();
        put('waveMicStatus', 'Mikrofon açık. Gecikmiş izleme ' + (id('waveMicMonitor').checked ? 'etkin' : 'sessiz') + '. ' + outputNote + ' Geri besleme riskine karşı kulaklık kullan.');
      } catch (error) {
        const stillCurrent = startToken === micDelayStartToken;
        if (startContext) {
          if (micDelayAudio && micDelayAudio.context === startContext) {
            const failedAudio = micDelayAudio;
            micDelayAudio = null;
            try { failedAudio.source.disconnect(); failedAudio.delay.disconnect(); failedAudio.monitorGain.disconnect(); failedAudio.limiter.disconnect(); } catch (_) {}
          }
          if (micDelayPendingContext === startContext) micDelayPendingContext = null;
          try { startContext.close().catch(() => {}); } catch (_) {}
        }
        if (startStream) startStream.getTracks().forEach(track => track.stop());
        if (micDelayStream === startStream) micDelayStream = null;
        if (!stillCurrent) return;
        id('waveMicInput').disabled = false;
        id('waveMicStart').disabled = false;
        id('waveMicStop').disabled = true;
        put('waveMicStatus', 'Mikrofon başlatılamadı: ' + (error && error.message ? error.message : String(error)) + '. Cihaz iznini, bağlantıyı ve uygulama mikrofon iznini kontrol et.');
      }
    }
    function stopMicDelay() {
      micDelayStartToken += 1;
      const current = micDelayAudio; micDelayAudio = null;
      const pendingContext = micDelayPendingContext; micDelayPendingContext = null;
      if (current) {
        try { current.monitorGain.gain.setTargetAtTime(0, current.context.currentTime, 0.01); } catch (_) {}
        try { current.source.disconnect(); current.delay.disconnect(); current.monitorGain.disconnect(); current.limiter.disconnect(); } catch (_) {}
        try { current.context.close().catch(() => {}); } catch (_) {}
      }
      if (pendingContext && (!current || pendingContext !== current.context)) {
        try { pendingContext.close().catch(() => {}); } catch (_) {}
      }
      if (micDelayStream) micDelayStream.getTracks().forEach(track => track.stop());
      micDelayStream = null;
      if (id('waveMicInput')) id('waveMicInput').disabled = false;
      if (id('waveMicStart')) id('waveMicStart').disabled = false;
      if (id('waveMicStop')) id('waveMicStop').disabled = true;
      if (id('waveMicMonitor')) id('waveMicMonitor').checked = false;
      if (id('waveMicStatus')) put('waveMicStatus', 'Mikrofon ve gecikmiş ses izleme durduruldu.');
    }

    const fmt = (value, digits = 2) => Number(value).toLocaleString('tr-TR', { maximumFractionDigits: digits, minimumFractionDigits: 0 });
    const fmtTime = (seconds) => {
      const ms = seconds * 1000;
      return ms >= 1000 ? fmt(seconds, 3) + ' s' : ms >= 1 ? fmt(ms, 3) + ' ms' : fmt(ms * 1000, 2) + ' µs';
    };
    const fmtDb = (value) => Number.isFinite(value) ? (value > 0 ? '+' : '') + fmt(value, 2) + ' dB' : '−∞ dB (ideal iptal)';
    const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
    const speed = () => waveMath.soundSpeed(state.medium, state.temperatureC);
    const canvasContext = (node) => {
      if (!node) return null;
      const rect = node.getBoundingClientRect();
      const dpr = Math.min(1.5, window.devicePixelRatio || 1);
      const width = Math.max(1, Math.round(rect.width));
      const height = Math.max(1, Math.round(rect.height || Number(node.getAttribute('height')) || 240));
      if (node.width !== Math.round(width * dpr) || node.height !== Math.round(height * dpr)) {
        node.width = Math.round(width * dpr); node.height = Math.round(height * dpr);
      }
      const ctx = node.getContext('2d');
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      return { ctx, width, height };
    };
    const currentWaveResult = () => waveMath.calculate(state.medium, state.temperatureC, state.frequencyHz, state.distanceM);

    function drawWave() {
      const out = canvasContext(id('waveLabCanvas')); if (!out) return;
      const { ctx, width: w, height: h } = out;
      ctx.clearRect(0, 0, w, h); ctx.fillStyle = '#0d131a'; ctx.fillRect(0, 0, w, h);
      const left = 28, right = w - 22, center = h * 0.51, span = Math.max(1, right - left);
      ctx.strokeStyle = '#34404b'; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(left, center); ctx.lineTo(right, center); ctx.stroke();
      const result = currentWaveResult();
      const cycles = clamp(5 / result.wavelengthM, 0.25, 12), amplitude = Math.min(52, h * 0.24);
      ctx.strokeStyle = '#d8b45d'; ctx.lineWidth = 2.5; ctx.beginPath();
      for (let x = 0; x <= span; x += 1) {
        const y = center - Math.sin((x / span) * Math.PI * 2 * cycles) * amplitude;
        if (x === 0) ctx.moveTo(left + x, y); else ctx.lineTo(left + x, y);
      }
      ctx.stroke();
      ctx.fillStyle = '#f4e7c8';
      for (let i = 0; i < 45; i++) {
        const x = left + span * i / 44;
        const displacement = Math.sin((i / 44) * Math.PI * 2 * cycles) * 5;
        ctx.beginPath(); ctx.arc(x + displacement, h - 24, 2.1, 0, Math.PI * 2); ctx.fill();
      }
      ctx.strokeStyle = '#d8b45d'; ctx.lineWidth = 1.5;
      const x1 = left + span * 0.12, x2 = Math.min(right, x1 + span / cycles), y = 24;
      ctx.beginPath(); ctx.moveTo(x1, y); ctx.lineTo(x2, y); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(x1, y); ctx.lineTo(x1 + 7, y - 4); ctx.lineTo(x1 + 7, y + 4); ctx.closePath(); ctx.fill();
      ctx.beginPath(); ctx.moveTo(x2, y); ctx.lineTo(x2 - 7, y - 4); ctx.lineTo(x2 - 7, y + 4); ctx.closePath(); ctx.fill();
      ctx.fillStyle = '#f1d38a'; ctx.font = '600 12px Segoe UI, Arial'; ctx.textAlign = 'center';
      ctx.fillText('λ = ' + fmt(currentWaveResult().wavelengthM, 3) + ' m', (x1 + x2) / 2, 18);
      ctx.fillStyle = '#9ca7b5'; ctx.textAlign = 'left'; ctx.font = '11px Segoe UI, Arial';
      ctx.fillText(cycles >= 12 ? 'Görsel sıkıştırılmıştır; sayısal hesaplar seçili frekansı kullanır.' : 'Temsili görsel: basınç değişimi ve parçacık titreşimi', left, h - 7);
    }

    function drawPhase() {
      const out = canvasContext(id('wavePhaseCanvas')); if (!out) return;
      const { ctx, width: w, height: h } = out;
      ctx.clearRect(0, 0, w, h); ctx.fillStyle = '#0d131a'; ctx.fillRect(0, 0, w, h);
      const left = 38, right = w - 18, plot = Math.max(1, right - left), mid = h * 0.48, amp = Math.min(40, h * 0.19);
      const phase = state.phaseDeg * Math.PI / 180, halfCos = Math.cos(phase / 2);
      const totalAmp = 2 * Math.abs(halfCos), totalPhase = phase / 2 + (halfCos < 0 ? Math.PI : 0);
      ctx.strokeStyle = '#34404b'; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(left, mid); ctx.lineTo(right, mid); ctx.stroke();
      const traces = [
        { color: '#d8b45d', factor: 1, shift: 0, label: 'A kaynağı' },
        { color: '#f4e7c8', factor: 1, shift: phase, label: 'B kaynağı' },
        { color: '#65b7a4', factor: totalAmp, shift: totalPhase, label: 'Toplam' }
      ];
      traces.forEach(trace => {
        ctx.strokeStyle = trace.color; ctx.lineWidth = 2; ctx.beginPath();
        for (let x = 0; x <= plot; x += 1) {
          const angle = (x / plot) * Math.PI * 4;
          const y = mid - Math.sin(angle + trace.shift) * amp * trace.factor;
          if (x === 0) ctx.moveTo(left + x, y); else ctx.lineTo(left + x, y);
        }
        ctx.stroke();
      });
      ctx.font = '11px Segoe UI, Arial'; ctx.textAlign = 'left';
      traces.forEach((trace, index) => { ctx.fillStyle = trace.color; ctx.fillText(trace.label, left + index * 112, h - 10); });
    }

    function updateWave() {
      try {
        state.medium = id('waveMedium').value;
        state.temperatureC = clamp(read('waveAirTemp', 20), -30, 50);
        state.frequencyHz = clamp(read('waveFrequency', 440), 20, 20000);
        const unit = id('waveDistanceUnit').value;
        const inputDistance = clamp(read('waveDistance', 1), 0, 100000);
        state.distanceM = Math.min(100000, inputDistance * (unit === 'km' ? 1000 : 1));
        id('waveAirTemp').disabled = state.medium !== 'air';
        id('waveAirTempWrap').classList.toggle('is-disabled', state.medium !== 'air');
        id('waveDistanceSlider').max = unit === 'km' ? '100' : '1000';
        id('waveDistanceSlider').step = unit === 'km' ? '0.1' : '1';
        const sliderValue = unit === 'km' ? state.distanceM / 1000 : state.distanceM;
        id('waveDistanceSlider').value = clamp(sliderValue, 0, Number(id('waveDistanceSlider').max));
        id('waveDistance').max = unit === 'km' ? '100' : '100000';
        if (document.activeElement !== id('waveDistance')) id('waveDistance').value = fmt(sliderValue, 3);
        const result = currentWaveResult();
        if (document.activeElement !== id('waveFrequency')) id('waveFrequency').value = state.frequencyHz;
      id('waveFrequencySlider').value = state.frequencyHz;
        put('waveSpeedValue', fmt(result.speedMps, 2) + ' m/s');
        put('waveLengthValue', fmt(result.wavelengthM, 4) + ' m');
        put('wavePeriodValue', fmtTime(result.periodS));
        put('waveDelayValue', fmtTime(result.delayS));
        put('waveDistancePhaseValue', fmt(result.phaseDeg, 2) + '°');
        put('waveCycleValue', fmt(result.cycles, 3) + ' λ');
        put('waveCanvasLabel', 'λ = ' + fmt(result.wavelengthM, 3) + ' m');
        put('waveDistanceMax', unit === 'km' ? '100 km' : '1.000 m');
        put('waveMediumNote', state.medium === 'air'
          ? 'Hava hızı 331,3 × √(1 + T/273,15) yaklaşımıyla hesaplanır.'
          : state.medium === 'water'
            ? 'Su için 1.480 m/s yaklaşık referans kullanılır; sıcaklık, tuzluluk ve basınca göre değişir.'
            : 'Çelik için 5.960 m/s yaklaşık boyuna dalga hızı kullanılır; alaşım ve sıcaklığa göre değişir.');
        drawWave(); updatePhase(false);
        return result;
      } catch (error) { put('waveToneStatus', error.message); return null; }
    }

    function updatePhase(fromDistance) {
      try {
        if (fromDistance) {
          const delay = read('wavePhaseDistance', 0) / speed();
          state.phaseDeg = ((360 * state.frequencyHz * delay) % 360 + 360) % 360;
          id('wavePhaseSlider').value = state.phaseDeg;
          id('wavePhaseAngle').value = fmt(state.phaseDeg, 2);
        } else {
          state.phaseDeg = clamp(read('wavePhaseAngle', state.phaseDeg), 0, 360);
          id('wavePhaseSlider').value = state.phaseDeg;
          id('wavePhaseDistance').value = fmt(speed() * (state.phaseDeg / 360) / state.frequencyHz, 4);
        }
        const delayS = (state.phaseDeg / 360) / state.frequencyHz;
        const distanceM = speed() * delayS;
        const ratio = waveMath.combinedAmplitudeRatio(state.phaseDeg);
        const db = waveMath.relativeLevelDb(ratio);
        put('wavePhaseDelayValue', fmtTime(delayS));
        put('wavePhasePathValue', fmt(distanceM, 4) + ' m');
        put('wavePhaseAmplitudeValue', fmt(ratio, 4) + '×');
        put('wavePhaseDbValue', fmtDb(db));
        put('wavePhaseInterpretation', ratio < 1e-8
          ? '180° faz farkında, eşit genlikli iki ideal sinüs birbirini tamamen söndürür.'
          : 'Eşit genlikli iki sinüsün toplam basınç genliği tek kaynağa göre ' + fmt(ratio, 3) + ' kattır. Seviye farkı ' + fmtDb(db) + '.');
        drawPhase();
      } catch (error) { put('wavePhaseInterpretation', error.message); }
    }

    function mapGeometry(width, height) {
      const scale = Math.min(width / 10, height / 8);
      const mapWidth = scale * 10, mapHeight = scale * 8;
      return { scale, ox: (width - mapWidth) / 2, oy: (height - mapHeight) / 2, width: mapWidth, height: mapHeight };
    }

    const offscreen = document.createElement('canvas');
    const offContext = offscreen.getContext('2d');
    function sourceValues() {
      const names = ['waveSourceAX','waveSourceAY','waveSourceBX','waveSourceBY','waveListenerX','waveListenerY'];
      const values = names.map(name => read(name));
      return values.map((value, index) => clamp(value, 0, index % 2 === 0 ? 10 : 8));
    }

    function drawSources(ax, ay, bx, by, mx, my) {
      const out = canvasContext(id('waveSourcesCanvas')); if (!out) return;
      const { ctx, width: w, height: h } = out, gridW = 180, gridH = 144;
      const geometry = mapGeometry(w, h), c = waveMath.soundSpeed('air', 20), f = state.frequencyHz;
      const image = offContext.createImageData(gridW, gridH), data = image.data;
      const bg = [12, 18, 25], gold = [216, 180, 93];
      for (let y = 0; y < gridH; y++) {
        for (let x = 0; x < gridW; x++) {
          const px = x / (gridW - 1) * 10, py = y / (gridH - 1) * 8;
          const rA = Math.max(0.001, Math.hypot(px - ax, py - ay));
          const rB = Math.max(0.001, Math.hypot(px - bx, py - by));
          const aA = 1 / Math.sqrt(Math.max(rA, 0.5)), aB = 1 / Math.sqrt(Math.max(rB, 0.5));
          const thetaA = 2 * Math.PI * f * rA / c, thetaB = 2 * Math.PI * f * rB / c;
          const re = aA * Math.cos(thetaA) + aB * Math.cos(thetaB);
          const im = aA * Math.sin(thetaA) + aB * Math.sin(thetaB);
          const ratio = clamp(Math.hypot(re, im) / Math.max(aA + aB, 1e-12), 0, 1);
          const intensity = Math.pow(ratio, 0.75), index = (y * gridW + x) * 4;
          data[index] = bg[0] + (gold[0] - bg[0]) * intensity;
          data[index + 1] = bg[1] + (gold[1] - bg[1]) * intensity;
          data[index + 2] = bg[2] + (gold[2] - bg[2]) * intensity; data[index + 3] = 255;
        }
      }
      offscreen.width = gridW; offscreen.height = gridH;
      offContext.putImageData(image, 0, 0);
      ctx.clearRect(0, 0, w, h); ctx.fillStyle = '#0d131a'; ctx.fillRect(0, 0, w, h);
      ctx.imageSmoothingEnabled = false;
      ctx.drawImage(offscreen, geometry.ox, geometry.oy, geometry.width, geometry.height);
      const point = (x, y) => ({ x: geometry.ox + x * geometry.scale, y: geometry.oy + y * geometry.scale });
      ctx.strokeStyle = 'rgba(255,255,255,.17)'; ctx.lineWidth = 1;
      for (let x = 0; x <= 10; x++) { const p = point(x, 0).x; ctx.beginPath(); ctx.moveTo(p, geometry.oy); ctx.lineTo(p, geometry.oy + geometry.height); ctx.stroke(); }
      for (let y = 0; y <= 8; y++) { const p = point(0, y).y; ctx.beginPath(); ctx.moveTo(geometry.ox, p); ctx.lineTo(geometry.ox + geometry.width, p); ctx.stroke(); }
      const marks = [{ key:'A', x:ax, y:ay, color:'#f1d38a' },{ key:'B', x:bx, y:by, color:'#ffffff' },{ key:'M', x:mx, y:my, color:'#65b7a4' }];
      marks.forEach(mark => {
        const p = point(mark.x, mark.y);
        ctx.fillStyle = mark.color; ctx.beginPath(); ctx.arc(p.x, p.y, 7, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = '#0b1117'; ctx.lineWidth = 2; ctx.stroke();
        ctx.font = '700 12px Segoe UI, Arial'; ctx.fillStyle = mark.color; ctx.textAlign = 'left';
        ctx.fillText(mark.key, p.x + 10, p.y - 9);
      });
      ctx.strokeStyle = '#d8b45d'; ctx.strokeRect(geometry.ox, geometry.oy, geometry.width, geometry.height);
    }

    function updateSources() {
      const [ax, ay, bx, by, mx, my] = sourceValues();
      const names = ['waveSourceAX','waveSourceAY','waveSourceBX','waveSourceBY','waveListenerX','waveListenerY'];
      [ax, ay, bx, by, mx, my].forEach((value, index) => { const node = id(names[index]); if (document.activeElement !== node) node.value = fmt(value, 1); });
      const result = waveMath.twoSource(state.frequencyHz, waveMath.soundSpeed('air', 20), ax, ay, bx, by, mx, my);
      put('waveSourceR1', fmt(result.distanceAM, 3) + ' m');
      put('waveSourceR2', fmt(result.distanceBM, 3) + ' m');
      put('waveSourcePathDiff', fmt(result.pathDifferenceM, 3) + ' m');
      put('waveSourcePhase', fmt(result.phaseDeg, 2) + '°');
      put('waveSourceAmplitude', fmt(result.amplitudeRatio, 4) + '×');
      put('waveSourceLevel', fmtDb(result.relativeLevelDb));
      drawSources(ax, ay, bx, by, mx, my);
    }

    function sourcePointFromEvent(event) {
      const rect = id('waveSourcesCanvas').getBoundingClientRect(), geometry = mapGeometry(rect.width, rect.height);
      const x = (event.clientX - rect.left - geometry.ox) / geometry.scale;
      const y = (event.clientY - rect.top - geometry.oy) / geometry.scale;
      return { x, y };
    }
    id('waveSourcesCanvas').addEventListener('pointerdown', event => {
      const p = sourcePointFromEvent(event), values = sourceValues();
      const marks = [{ key:'A', x:values[0], y:values[1] },{ key:'B', x:values[2], y:values[3] },{ key:'M', x:values[4], y:values[5] }];
      const nearest = marks.map(mark => ({ ...mark, distance: Math.hypot(mark.x - p.x, mark.y - p.y) })).sort((a, b) => a.distance - b.distance)[0];
      if (nearest && nearest.distance < 0.65) {
        dragging = nearest.key; id('waveSourcesCanvas').setPointerCapture(event.pointerId);
      }
    });
    id('waveSourcesCanvas').addEventListener('pointermove', event => {
      if (!dragging) return;
      const p = sourcePointFromEvent(event), x = clamp(p.x, 0, 10), y = clamp(p.y, 0, 8);
      const fields = dragging === 'A' ? ['waveSourceAX','waveSourceAY'] : dragging === 'B' ? ['waveSourceBX','waveSourceBY'] : ['waveListenerX','waveListenerY'];
      id(fields[0]).value = fmt(x, 1); id(fields[1]).value = fmt(y, 1); updateSources();
    });
    const stopDrag = () => { dragging = null; };
    ['pointerup','pointercancel','lostpointercapture'].forEach(name => id('waveSourcesCanvas').addEventListener(name, stopDrag));

    function updateSpl(fromPressure) {
      if (fromPressure) {
        try {
          const db = waveMath.pascalsToDbSpl(read('waveSplPa', 1));
          id('waveSplDb').value = fmt(db, 3);
          put('waveSplFromPa', fmt(db, 3) + ' dB SPL');
          put('waveSplNote', 'p₀ = 20 µPa. Girdi RMS ses basıncıdır; bu işlem yalnızca matematiksel dönüşümdür.');
        } catch (error) { put('waveSplFromPa', error.message); }
      } else {
        try {
          const pressure = waveMath.dbSplToPascals(read('waveSplDb', 94));
          id('waveSplPa').value = Number(pressure.toPrecision(6));
          put('waveSplFromDb', fmt(pressure, pressure < 0.01 ? 6 : 4) + ' Pa RMS');
          put('waveSplNote', 'dB SPL, 20 µPa referans basıncına göre hesaplanır. A/C ağırlıklandırması veya maruziyet süresi bu dönüşümün parçası değildir.');
        } catch (error) { put('waveSplFromDb', error.message); }
      }
    }


    function stopTone() {
      if (!audio) return;
      const current = audio; audio = null;
      try {
        current.master.gain.cancelScheduledValues(current.context.currentTime);
        current.master.gain.setTargetAtTime(0, current.context.currentTime, 0.025);
        window.setTimeout(() => {
          try { current.oscillator.stop(); } catch (_) {}
          current.context.close().catch(() => {});
        }, 180);
      } catch (_) { current.context.close().catch(() => {}); }
      id('waveTonePlay').disabled = false; id('waveToneStop').disabled = true;
      put('waveToneStatus', 'Test tonu durduruldu.');
    }

    async function playTone() {
      stopTone();
      const AudioCtor = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtor) { put('waveToneStatus', 'Bu cihazda Web Audio desteklenmiyor.'); return; }
      try {
        const context = new AudioCtor(); await context.resume();
        const oscillator = context.createOscillator(), delay = context.createDelay(5);
        const dry = context.createGain(), wet = context.createGain(), master = context.createGain();
        const limiter = context.createDynamicsCompressor();
        oscillator.type = 'sine'; oscillator.frequency.value = state.frequencyHz;
        const actualDelay = currentWaveResult().delayS;
        delay.delayTime.value = Math.min(5, actualDelay);
        dry.gain.value = 0.035; wet.gain.value = 0.035; master.gain.value = 0.5;
        limiter.threshold.value = -12; limiter.knee.value = 0; limiter.ratio.value = 12;
        limiter.attack.value = 0.003; limiter.release.value = 0.12;
        oscillator.connect(dry).connect(master);
        oscillator.connect(delay).connect(wet).connect(master);
        master.connect(limiter).connect(context.destination); oscillator.start();
        audio = { context, oscillator, master };
        id('waveTonePlay').disabled = true; id('waveToneStop').disabled = false;
        put('waveToneStatus', actualDelay > 5
          ? 'Test tonu çalıyor. Hesaplanan gecikme 5 saniyeyi aştığı için dinleme örneği 5 saniyede sınırlandı.'
          : 'Test tonu çalıyor: doğrudan sinyal ile gecikmiş kopyası düşük seviyede toplanıyor. Sistem sesini düşük tut.');
      } catch (error) {
        put('waveToneStatus', 'Test tonu başlatılamadı: ' + (error.message || String(error)));
        stopTone();
      }
    }

    function setTab(name) {
      document.querySelectorAll('[data-wave-tab]').forEach(button => {
        const active = button.dataset.waveTab === name;
        button.classList.toggle('active', active); button.setAttribute('aria-selected', String(active));
      });
      document.querySelectorAll('[data-wave-panel]').forEach(panel => { panel.hidden = panel.dataset.wavePanel !== name; });
      if (name === 'wave') updateWave();
      if (name === 'phase') updatePhase(false);
      if (name === 'sources') updateSources();
      if (name === 'spl') updateSpl(true);
      if (name === 'live') { updateMicDelay(); refreshMicDevices().catch(error => put('waveMicStatus', 'Ses cihazları listelenemedi: ' + error.message)); }
    }

    document.querySelectorAll('[data-wave-tab]').forEach(button => button.addEventListener('click', () => setTab(button.dataset.waveTab)));
    ['waveMedium','waveAirTemp','waveFrequency','waveDistance'].forEach(name => id(name).addEventListener('input', () => {
      updateWave(); updateSources(); updateMicDelay();
    }));
    id('waveMedium').addEventListener('change', () => { updateWave(); updateSources(); updateMicDelay(); });
    id('waveFrequency').addEventListener('change', () => { updateWave(); updateSources(); updateMicDelay(); });
    id('waveFrequencySlider').addEventListener('input', () => {
      id('waveFrequency').value = id('waveFrequencySlider').value; updateWave(); updateSources(); updateMicDelay();
    });
    id('waveDistanceSlider').addEventListener('input', () => {
      id('waveDistance').value = id('waveDistanceSlider').value; updateWave();
    });
    id('waveDistanceUnit').addEventListener('change', () => {
      const meters = state.distanceM;
      id('waveDistance').value = id('waveDistanceUnit').value === 'km' ? meters / 1000 : meters;
      updateWave();
    });
    document.querySelectorAll('[data-wave-frequency]').forEach(button => button.addEventListener('click', () => {
      id('waveFrequency').value = button.dataset.waveFrequency; updateWave(); updateSources(); updateMicDelay();
    }));
    id('wavePhaseAngle').addEventListener('input', () => updatePhase(false));
    id('wavePhaseSlider').addEventListener('input', () => {
      id('wavePhaseAngle').value = id('wavePhaseSlider').value; updatePhase(false);
    });
    id('wavePhaseDistance').addEventListener('input', () => updatePhase(true));
    document.querySelectorAll('[data-wave-phase]').forEach(button => button.addEventListener('click', () => {
      id('wavePhaseAngle').value = button.dataset.wavePhase; updatePhase(false);
    }));
    ['waveSourceAX','waveSourceAY','waveSourceBX','waveSourceBY','waveListenerX','waveListenerY'].forEach(name => id(name).addEventListener('input', updateSources));
    id('waveSplPa').addEventListener('input', () => updateSpl(true));
    id('waveSplDb').addEventListener('input', () => updateSpl(false));
    document.querySelectorAll('[data-wave-spl]').forEach(button => button.addEventListener('click', () => {
      id('waveSplPa').value = button.dataset.waveSpl; updateSpl(true);
    }));
    id('waveTonePlay').addEventListener('click', playTone); id('waveToneStop').addEventListener('click', stopTone);
    window.addEventListener('resize', () => {
      if (activeRoute === 'wavelab') { drawWave(); drawPhase(); updateSources(); }
    });
    document.addEventListener('visibilitychange', () => { if (document.hidden) stopAllWaveAudio(); });
    function stopAllWaveAudio() { stopTone(); stopMicDelay(); }
    id('waveMicStart').addEventListener('click', startMicDelay);
    id('waveMicStop').addEventListener('click', stopMicDelay);
    id('waveMicDelay').addEventListener('input', updateMicDelay);
    id('waveMicDelaySlider').addEventListener('input', () => {
      id('waveMicDelay').value = id('waveMicDelaySlider').value; updateMicDelay();
    });
    document.querySelectorAll('[data-wave-mic-delay]').forEach(button => button.addEventListener('click', () => {
      id('waveMicDelay').value = button.dataset.waveMicDelay; updateMicDelay();
    }));
    id('waveMicMonitor').addEventListener('change', () => {
      if (micDelayAudio) micDelayAudio.monitorGain.gain.setTargetAtTime(id('waveMicMonitor').checked ? 0.06 : 0, micDelayAudio.context.currentTime, 0.02);
      put('waveMicStatus', id('waveMicMonitor').checked
        ? 'Gecikmiş ses çıkışı etkin. Kulaklık kullan; hoparlöre yönlendirme yapma.'
        : 'Gecikmiş ses çıkışı sessize alındı. Mikrofon girişi çalışmaya devam ediyor.');
    });
    id('waveMicOutput').addEventListener('change', async () => {
      if (!micDelayAudio || typeof micDelayAudio.context.setSinkId !== 'function') return;
      try { await micDelayAudio.context.setSinkId(id('waveMicOutput').value || ''); put('waveMicStatus', 'Ses çıkışı güncellendi. Kulaklık kullan.'); }
      catch (error) { put('waveMicStatus', 'Ses çıkışı değiştirilemedi: ' + error.message); }
    });
    window.addEventListener('pagehide', stopAllWaveAudio);
    window.StagepulseWaveLabStop = stopAllWaveAudio;
    window.StagepulseWaveLabRefresh = () => { updateWave(); updateSources(); updateSpl(true); updateMicDelay(); };
    updateWave(); updatePhase(false); updateSources(); updateSpl(true); updateMicDelay();
  }


  // ---------------------------------------------------------------------------
  // 9. OSC / UDP VE STANDART MIDI DOSYASI ARAÇLARI
  // ---------------------------------------------------------------------------
  function oscPaddedString(value) {
    const bytes = new TextEncoder().encode(String(value));
    const length = Math.ceil((bytes.length + 1) / 4) * 4;
    const padded = new Uint8Array(length);
    padded.set(bytes);
    return padded;
  }

  function buildOscPacket(options = {}) {
    const address = String(options.address || '').trim();
    const type = String(options.valueType || 'float').toLowerCase();
    if (!/^\/[A-Za-z0-9_./-]{1,127}$/.test(address)) throw new Error('OSC adresi / ile başlamalı ve yalnızca harf, rakam, nokta, alt çizgi, tire veya / içermeli.');
    const tags = { float: 'f', int: 'i', string: 's' };
    if (!Object.prototype.hasOwnProperty.call(tags, type)) throw new Error('OSC veri türü float, int veya string olmalı.');
    const parts = [oscPaddedString(address), oscPaddedString(',' + tags[type])];
    if (type === 'float') {
      const value = Number(String(options.value ?? '').replace(',', '.'));
      if (!Number.isFinite(value) || Math.abs(value) > 3.4028235e38) throw new Error('OSC float değeri sonlu ve geçerli olmalı.');
      const bytes = new Uint8Array(4);
      new DataView(bytes.buffer).setFloat32(0, value, false);
      parts.push(bytes);
    } else if (type === 'int') {
      const raw = String(options.value ?? '').trim();
      if (!/^-?\d+$/.test(raw)) throw new Error('OSC integer değeri tam sayı olmalı.');
      const value = Number(raw);
      if (!Number.isSafeInteger(value) || value < -2147483648 || value > 2147483647) throw new Error('OSC integer değeri 32 bit sınırını aşamaz.');
      const bytes = new Uint8Array(4);
      new DataView(bytes.buffer).setInt32(0, value, false);
      parts.push(bytes);
    } else {
      const value = String(options.value ?? '');
      if (value.includes('\0') || new TextEncoder().encode(value).length > 256) throw new Error('OSC metin değeri boş karakter içeremez ve 256 UTF-8 baytını aşamaz.');
      parts.push(oscPaddedString(value));
    }
    const size = parts.reduce((sum, part) => sum + part.length, 0);
    if (size > 1024) throw new Error('OSC paketi 1024 bayt sınırını aşıyor.');
    const packet = new Uint8Array(size);
    let offset = 0;
    parts.forEach(part => { packet.set(part, offset); offset += part.length; });
    return packet;
  }

  function midiVariableLength(value) {
    let remaining = Math.max(0, Math.floor(value));
    const bytes = [remaining & 0x7f];
    while ((remaining >>= 7) > 0) bytes.unshift((remaining & 0x7f) | 0x80);
    return bytes;
  }

  function buildMidiFile(options = {}) {
    const tempo = Number(options.tempo ?? 120);
    const channel = Number(options.channel ?? 1);
    const program = Number(options.program ?? 0);
    const note = Number(options.note ?? 69);
    const velocity = Number(options.velocity ?? 100);
    const duration = Number(options.duration ?? 1);
    if (!Number.isInteger(tempo) || tempo < 20 || tempo > 300) throw new Error('Tempo 20–300 BPM arasında tam sayı olmalı.');
    if (!Number.isInteger(channel) || channel < 1 || channel > 16) throw new Error('MIDI kanalı 1–16 arasında olmalı.');
    if (!Number.isInteger(program) || program < 0 || program > 127) throw new Error('Program numarası 0–127 arasında olmalı.');
    if (!Number.isInteger(note) || note < 0 || note > 127) throw new Error('Nota numarası 0–127 arasında olmalı.');
    if (!Number.isInteger(velocity) || velocity < 1 || velocity > 127) throw new Error('Velocity 1–127 arasında olmalı.');
    if (!Number.isFinite(duration) || duration < 0.05 || duration > 120) throw new Error('Nota süresi 0,05–120 saniye arasında olmalı.');
    const micros = Math.round(60000000 / tempo);
    const offTick = Math.max(1, Math.round(duration * tempo / 60 * 480));
    const events = [
      { tick: 0, order: 0, data: [0xff, 0x51, 0x03, (micros >> 16) & 255, (micros >> 8) & 255, micros & 255] },
      { tick: 0, order: 1, data: [0xc0 + channel - 1, program] },
      { tick: 0, order: 2, data: [0x90 + channel - 1, note, velocity] },
      { tick: offTick, order: 0, data: [0x80 + channel - 1, note, 0] },
      { tick: offTick, order: 1, data: [0xff, 0x2f, 0x00] }
    ].sort((a, b) => a.tick - b.tick || a.order - b.order);
    const track = [];
    let previousTick = 0;
    for (const event of events) {
      track.push(...midiVariableLength(event.tick - previousTick), ...event.data);
      previousTick = event.tick;
    }
    const u32 = value => [(value >>> 24) & 255, (value >>> 16) & 255, (value >>> 8) & 255, value & 255];
    return new Uint8Array([
      0x4d, 0x54, 0x68, 0x64, 0, 0, 0, 6, 0, 0, 0, 1, 1, 0xe0,
      0x4d, 0x54, 0x72, 0x6b, ...u32(track.length), ...track
    ]);
  }

  async function downloadBinaryFile(filename, bytes, mimeType) {
    const blob = new Blob([bytes], { type: mimeType });
    const android = window.StagepulseAndroid;
    if (android && typeof android.saveBase64File === 'function') {
      if (blob.size > 18 * 1024 * 1024) throw new Error('Dosya 18 MiB sınırını aşıyor.');
      const encoded = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result || '').split(',')[1] || '');
        reader.onerror = () => reject(new Error('MIDI dosyası okunamadı.'));
        reader.readAsDataURL(blob);
      });
      if (!android.saveBase64File(filename, mimeType, encoded)) throw new Error('Android dosya deposuna kayıt yapılamadı.');
      return;
    }
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url; link.download = filename;
    document.body.appendChild(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1500);
  }

  function initOscMidiTools() {
    if (!byId('oscSend') || !byId('midiCreate')) return;
    const sendButton = byId('oscSend');
    const midiButton = byId('midiCreate');
    bind('oscSend', 'click', async () => {
      sendButton.disabled = true;
      try {
        const host = byId('oscHost').value.trim();
        const port = Number(byId('oscPort').value);
        const address = byId('oscAddress').value.trim();
        const value = byId('oscValue').value;
        const valueType = byId('oscValueType').value;
        buildOscPacket({ address, value, valueType });
        let result;
        if (window.StagepulseAndroid && typeof window.StagepulseAndroid.sendOscMessage === 'function') {
          const raw = window.StagepulseAndroid.sendOscMessage(host, port, address, value, valueType);
          result = typeof raw === 'string' ? JSON.parse(raw) : raw;
        } else if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.send_osc_message === 'function') {
          result = await window.pywebview.api.send_osc_message(host, port, address, value, valueType);
        } else {
          throw new Error('OSC UDP gönderimi yalnızca Stagepulse Windows EXE veya Android uygulamasında kullanılabilir.');
        }
        if (!result || !result.ok) throw new Error(result && result.error ? result.error : 'UDP paketi gönderilemedi.');
        text('oscStatus', 'OSC UDP paketi ' + host + ':' + port + ' adresine gönderildi. Cihaz yanıtı alınmaz; mikser bağlantısını ve OSC ayarını ayrıca doğrula.');
      } catch (error) {
        showError('oscStatus', error);
      } finally {
        sendButton.disabled = false;
      }
    });
    bind('midiCreate', 'click', async () => {
      midiButton.disabled = true;
      try {
        const bytes = buildMidiFile({
          tempo: number('midiTempo'), channel: number('midiChannel'), program: number('midiProgram'),
          note: number('midiNote'), velocity: number('midiVelocity'), duration: number('midiDuration')
        });
        let filename = safeFileName(byId('midiFilename').value || 'Stagepulse_MIDI');
        if (!filename.toLowerCase().endsWith('.mid')) filename += '.mid';
        await downloadBinaryFile(filename, bytes, 'audio/midi');
        text('midiStatus', filename + ' oluşturuldu. Format 0, tek kanal/tek nota olayı; dosya MIDI uyumlu DAW veya oynatıcıda açılabilir.');
      } catch (error) {
        showError('midiStatus', error);
      } finally {
        midiButton.disabled = false;
      }
    });
  }


  // Hafif 2B sistem tasarımcısı. Akustik polar/GLL tahmini değildir.
  function calculateArrayGeometry(input) {
    const count=Number(input.cabinetCount),splay=Number(input.splayDeg),aim=Number(input.aimDeg),hang=Number(input.hangHeightM);
    if(!Number.isInteger(count)||count<2||count>24)throw new Error('Kabin sayısı 2–24 arasında tam sayı olmalı.');
    if(!Number.isFinite(splay)||splay<0||splay>15)throw new Error('Splay 0–15° arasında olmalı.');
    if(!Number.isFinite(aim)||aim< -45||aim>45)throw new Error('Aiming -45° ile +45° arasında olmalı.');
    if(!Number.isFinite(hang)||hang<2||hang>30)throw new Error('Askı yüksekliği 2–30 m arasında olmalı.');
    const anglesDeg=Array.from({length:count},(_,i)=>aim+(i-(count-1)/2)*splay);
    return {cabinetCount:count,splayDeg:splay,aimDeg:aim,hangHeightM:hang,anglesDeg,totalCurvatureDeg:(count-1)*splay,
      note:'Geometrik yan görünüş; akustik array/polar tahmini değildir.'};
  }
  function estimateSystemCoverage(input) {
    const x=Number(input.xM),y=Number(input.yM),width=Number(input.widthM),depth=Number(input.depthM),reference=Number(input.referenceDbSpl);
    if(![x,y,width,depth,reference].every(Number.isFinite)||width<4||width>200||depth<4||depth>300||x<0||x>width||y<0||y>depth||reference<60||reference>140)
      throw new Error('Kapsama hesabı girdileri geçersiz.');
    const levels=[width*.28,width*.72].map(sx=>{const distance=Math.max(1,Math.hypot(x-sx,y-1.5));return {distanceM:distance,levelDbSpl:reference-20*Math.log10(distance)};});
    const peak=Math.max(...levels.map(v=>v.levelDbSpl));
    return {levelDbSpl:peak+10*Math.log10(levels.reduce((sum,v)=>sum+Math.pow(10,(v.levelDbSpl-peak)/10),0)),
      sourceLevels:levels,method:'Serbest alan noktasal kaynak ve enerji toplamı',
      assumptions:['İki eşit kaynak, her biri için girilen 1 m referans seviyesi.','Faz, polar/yönlülük, oda yansımaları, hava soğurması ve limiter hesaba katılmaz.']};
  }
  function calculateSubTopAlignment(input) {
    const sub=Number(input.subDistanceM),top=Number(input.topDistanceM),frequency=Number(input.crossoverHz),temperature=Number(input.temperatureC);
    if(![sub,top,frequency,temperature].every(Number.isFinite)||sub<.1||sub>10000||top<.1||top>10000||frequency<20||frequency>20000||temperature< -30||temperature>50)
      throw new Error('Mesafeler, crossover frekansı veya sıcaklık geçersiz.');
    const speedMps=331.3+.606*temperature,distanceDifferenceM=Math.abs(sub-top),delayMs=distanceDifferenceM/speedMps*1000;
    return {subDistanceM:sub,topDistanceM:top,speedMps,distanceDifferenceM,delayMs,delayTarget:sub<top?'Sub':top<sub?'Top':'Yok',
      crossoverHz:frequency,phaseDifferenceDeg:(delayMs*frequency*.36)%360,
      note:'Geometrik yol farkı kestirimidir. Nihai hizalama için aynı referans noktada Transfer Function/Impulse Response ölçümü gerekir.'};
  }
  function systemDesignerMarkup() {
    return [
      '<div class="sp-sd-head"><div><span class="eyebrow">PA / ARRAY / SPL / HİZALAMA</span><h3>System Designer</h3><p>Hafif 2B tasarım ve ön hesap. Üretici verisi veya saha ölçümünün yerine geçmez.</p></div><button class="btn btn-secondary btn-small" id="spSystemExport" type="button">Sistem taslağını JSON kaydet</button></div>',
      '<div class="sp-sd-tabs" role="tablist" aria-label="Sistem tasarım araçları"><button class="sp-sd-tab active" type="button" data-sd-tab="array" role="tab" aria-selected="true">Line Array</button><button class="sp-sd-tab" type="button" data-sd-tab="coverage" role="tab" aria-selected="false">SPL Coverage</button><button class="sp-sd-tab" type="button" data-sd-tab="alignment" role="tab" aria-selected="false">Sub-Top Alignment</button></div>',
      '<section class="sp-sd-panel active" data-sd-panel="array" role="tabpanel"><div class="sp-sd-layout"><div class="sp-sd-controls">',
      '<div class="field-row"><label for="spArrayCount">Kabin sayısı</label><input id="spArrayCount" type="number" min="2" max="24" step="1" value="8"></div><div class="field-row"><label for="spArrayHang">Askı yüksekliği (m)</label><input id="spArrayHang" type="number" min="2" max="30" step="0.5" value="7"></div>',
      '<div class="field-row"><label for="spArraySplay">Kabinler arası splay (°)</label><input id="spArraySplay" type="number" min="0" max="15" step="0.1" value="2"></div><div class="field-row"><label for="spArrayAim">Dikey aiming (°)</label><input id="spArrayAim" type="number" min="-45" max="45" step="0.5" value="5"></div><div class="result-line" id="spArraySummary">Array geometrisi hazırlanıyor.</div></div>',
      '<div class="sp-sd-visual"><canvas id="spArrayCanvas" class="sp-sd-canvas" width="900" height="430" aria-label="Line array geometrik yan görünüşü"></canvas><p class="sp-sd-caption">Kabin çizimi ve ışınlar geometrik gösterimdir; gerçek dikey polar kapsama veya SPL tahmini değildir.</p></div></div></section>',
      '<section class="sp-sd-panel" data-sd-panel="coverage" role="tabpanel" hidden><div class="sp-sd-layout"><div class="sp-sd-controls">',
      '<div class="field-row"><label for="spCoverageWidth">Dinleyici alanı genişliği (m)</label><input id="spCoverageWidth" type="number" min="4" max="200" step="0.5" value="24"></div><div class="field-row"><label for="spCoverageDepth">Dinleyici alanı derinliği (m)</label><input id="spCoverageDepth" type="number" min="4" max="300" step="0.5" value="35"></div>',
      '<div class="field-row"><label for="spCoverageLevel">Referans seviye (dB SPL @ 1 m)</label><input id="spCoverageLevel" type="number" min="60" max="140" step="0.5" value="100"></div><div class="field-row"><label for="spCoverageAngle">Nominal yatay açı (°)</label><input id="spCoverageAngle" type="number" min="30" max="150" step="1" value="90"></div><div class="result-line" id="spCoverageSummary">Kapsama haritası hazırlanıyor.</div></div>',
      '<div class="sp-sd-visual"><canvas id="spCoverageCanvas" class="sp-sd-canvas" width="900" height="480" aria-label="Tahmini SPL ısı haritası ve nominal açı sınırları"></canvas><p class="sp-sd-caption">Renkler serbest alan noktasal kaynak enerji toplamı kestirimidir. Kesikli çizgiler yalnızca nominal açı geometrisidir; polar veri uygulanmaz.</p></div></div></section>',
      '<section class="sp-sd-panel" data-sd-panel="alignment" role="tabpanel" hidden><div class="sp-sd-layout"><div class="sp-sd-controls">',
      '<div class="field-row"><label for="spSubDistance">Sub → referans nokta mesafesi (m)</label><input id="spSubDistance" type="number" min="0.1" max="10000" step="0.1" value="22"></div><div class="field-row"><label for="spTopDistance">Top → referans nokta mesafesi (m)</label><input id="spTopDistance" type="number" min="0.1" max="10000" step="0.1" value="18"></div>',
      '<div class="field-row"><label for="spCrossover">Crossover frekansı (Hz)</label><input id="spCrossover" type="number" min="20" max="20000" step="1" value="100"></div><div class="field-row"><label for="spTemperature">Hava sıcaklığı (°C)</label><input id="spTemperature" type="number" min="-30" max="50" step="0.5" value="20"></div><div class="result-line" id="spAlignmentSummary">Hizalama hesabı hazırlanıyor.</div></div>',
      '<div class="sp-sd-visual"><canvas id="spAlignmentCanvas" class="sp-sd-canvas" width="900" height="300" aria-label="Sub ve top ses yolları karşılaştırması"></canvas><p class="sp-sd-caption">Gecikme yakın olan kaynağın geometrik yolunu uzatmak içindir. Polarite/faz tepkisi ölçümle doğrulanmalıdır.</p></div></div></section>',
      '<div class="sp-sd-disclaimer"><strong>Model sınırları</strong><span>Rigging yükü, üretici GLL/polar verisi, gerçek line-array toplamı, oda yansımaları veya sertifikalı SPL kapsaması hesaplanmaz. Değerleri üretici dokümanı ve saha ölçümüyle doğrula.</span></div>'
    ].join('');
  }
  function systemDesignerCanvas(id) {
    const canvas=byId(id),ctx=canvas&&canvas.getContext('2d');
    return canvas&&ctx?{ctx,width:canvas.width,height:canvas.height}:null;
  }
  function drawSystemArray() {
    const c=systemDesignerCanvas('spArrayCanvas');if(!c)return;
    const p=calculateArrayGeometry({cabinetCount:number('spArrayCount'),splayDeg:number('spArraySplay'),aimDeg:number('spArrayAim'),hangHeightM:number('spArrayHang')});
    const ctx=c.ctx,w=c.width,h=c.height;ctx.clearRect(0,0,w,h);ctx.fillStyle='#0b1016';ctx.fillRect(0,0,w,h);
    ctx.strokeStyle='rgba(255,255,255,.08)';ctx.lineWidth=1;
    for(let x=30;x<w;x+=45){ctx.beginPath();ctx.moveTo(x,25);ctx.lineTo(x,h-45);ctx.stroke();}
    for(let y=35;y<h-35;y+=35){ctx.beginPath();ctx.moveTo(25,y);ctx.lineTo(w-25,y);ctx.stroke();}
    const floorY=h-55;ctx.strokeStyle='#d8b45d';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(30,floorY);ctx.lineTo(w-30,floorY);ctx.stroke();
    ctx.fillStyle='#b9c3cf';ctx.font='13px Segoe UI, Arial';ctx.textAlign='left';ctx.fillText('SAHNE / ZEMİN',34,floorY-10);
    let cx=235,cy=82;ctx.strokeStyle='#8995a4';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(cx,24);ctx.lineTo(cx,60);ctx.stroke();ctx.fillStyle='#d8b45d';ctx.fillRect(cx-17,18,34,7);
    p.anglesDeg.forEach((angle,index)=>{const rad=angle*Math.PI/180;ctx.save();ctx.translate(cx,cy);ctx.rotate(rad);ctx.fillStyle='#343b46';ctx.fillRect(-25,-9,50,18);ctx.strokeStyle=index===0||index===p.anglesDeg.length-1?'#f1d38a':'#aab4c0';ctx.lineWidth=2;ctx.strokeRect(-25,-9,50,18);ctx.restore();
      const ax=cx+Math.cos(rad)*28,ay=cy+Math.sin(rad)*28;ctx.strokeStyle='rgba(216,180,93,.58)';ctx.lineWidth=1.5;ctx.setLineDash([6,5]);ctx.beginPath();ctx.moveTo(ax,ay);ctx.lineTo(ax+Math.cos(rad)*210,ay+Math.sin(rad)*210);ctx.stroke();ctx.setLineDash([]);
      ctx.fillStyle='#e8edf3';ctx.font='11px Segoe UI, Arial';ctx.textAlign='left';ctx.fillText(fmt(angle,1)+'°',ax+6,ay-6);cx+=Math.sin(rad)*13;cy+=23;});
    ctx.fillStyle='#d8b45d';ctx.font='bold 14px Segoe UI, Arial';ctx.fillText('DİKEY YAN GÖRÜNÜŞ',30,28);ctx.fillStyle='#9ca7b5';ctx.font='12px Segoe UI, Arial';ctx.fillText('Askı yüksekliği: '+fmt(p.hangHeightM,1)+' m',30,50);
    text('spArraySummary',p.cabinetCount+' kabin · toplam geometrik eğrilik '+fmt(p.totalCurvatureDeg,1)+'° · splay '+fmt(p.splayDeg,1)+'°/kabin. '+p.note);
  }
  function systemCoverageColor(level,min,max) {
    const stops=[[30,55,140],[0,126,190],[0,177,168],[83,183,104],[224,205,58],[235,125,45],[190,48,42]];
    const t=clamp((level-min)/Math.max(1,max-min),0,1)*(stops.length-1),index=Math.min(stops.length-2,Math.floor(t)),part=t-index;
    return 'rgb('+stops[index].map((v,i)=>Math.round(v+(stops[index+1][i]-v)*part)).join(',')+')';
  }
  function drawSystemCoverage() {
    const c=systemDesignerCanvas('spCoverageCanvas');if(!c)return;
    const width=number('spCoverageWidth'),depth=number('spCoverageDepth'),reference=number('spCoverageLevel'),angle=number('spCoverageAngle');
    if(![width,depth,reference,angle].every(Number.isFinite)||width<4||width>200||depth<4||depth>300||reference<60||reference>140||angle<30||angle>150)
      throw new Error('Alan 4–200 × 4–300 m, referans 60–140 dB SPL ve açı 30–150° aralığında olmalı.');
    const ctx=c.ctx,w=c.width,h=c.height,pad={l:62,r:30,t:38,b:48},plotW=w-pad.l-pad.r,plotH=h-pad.t-pad.b,cols=72,rows=38,values=[];
    for(let j=0;j<rows;j++)for(let i=0;i<cols;i++)values.push(estimateSystemCoverage({xM:(i+.5)/cols*width,yM:(j+.5)/rows*depth,widthM:width,depthM:depth,referenceDbSpl:reference}).levelDbSpl);
    const min=Math.floor(Math.min(...values)/5)*5,max=Math.ceil(Math.max(...values)/5)*5;
    ctx.clearRect(0,0,w,h);ctx.fillStyle='#0b1016';ctx.fillRect(0,0,w,h);ctx.fillStyle='#d8b45d';ctx.font='bold 13px Segoe UI, Arial';ctx.textAlign='left';ctx.fillText('TAHMİNİ SPL · SERBEST ALAN MODELİ',pad.l,22);
    const cellW=plotW/cols,cellH=plotH/rows;
    for(let j=0;j<rows;j++)for(let i=0;i<cols;i++){ctx.fillStyle=systemCoverageColor(values[j*cols+i],min,max);ctx.fillRect(pad.l+i*cellW,pad.t+j*cellH,Math.ceil(cellW+.4),Math.ceil(cellH+.4));}
    ctx.strokeStyle='rgba(255,255,255,.25)';ctx.lineWidth=1;
    for(let i=0;i<=4;i++){const x=pad.l+plotW*i/4;ctx.beginPath();ctx.moveTo(x,pad.t);ctx.lineTo(x,pad.t+plotH);ctx.stroke();ctx.fillStyle='#c5cfda';ctx.font='10px Segoe UI, Arial';ctx.textAlign='center';ctx.fillText(fmt(width*i/4,1)+' m',x,h-22);}
    for(let i=0;i<=5;i++){const y=pad.t+plotH*i/5;ctx.beginPath();ctx.moveTo(pad.l,y);ctx.lineTo(pad.l+plotW,y);ctx.stroke();ctx.fillStyle='#c5cfda';ctx.textAlign='right';ctx.fillText(fmt(depth*i/5,0)+' m',pad.l-8,y+3);}
    const px=x=>pad.l+x/width*plotW,py=y=>pad.t+y/depth*plotH,half=angle*Math.PI/360,sourceY=1.5;
    [width*.28,width*.72].forEach((sx,i)=>{ctx.strokeStyle='#fff2c9';ctx.lineWidth=2;ctx.setLineDash([7,5]);ctx.beginPath();ctx.moveTo(px(sx),py(sourceY));ctx.lineTo(px(sx-Math.tan(half)*depth),py(depth));ctx.moveTo(px(sx),py(sourceY));ctx.lineTo(px(sx+Math.tan(half)*depth),py(depth));ctx.stroke();ctx.setLineDash([]);
      ctx.fillStyle='#10151d';ctx.beginPath();ctx.arc(px(sx),py(sourceY),8,0,Math.PI*2);ctx.fill();ctx.strokeStyle='#f1d38a';ctx.lineWidth=2;ctx.stroke();ctx.fillStyle='#fff';ctx.font='bold 10px Segoe UI, Arial';ctx.textAlign='center';ctx.fillText(i===0?'L PA':'R PA',px(sx),py(sourceY)-13);});
    ctx.fillStyle='#30291d';ctx.fillRect(pad.l,pad.t-13,plotW,10);ctx.fillStyle='#f1d38a';ctx.textAlign='center';ctx.font='bold 10px Segoe UI, Arial';ctx.fillText('SAHNE',pad.l+plotW/2,pad.t-4);
    const rear=estimateSystemCoverage({xM:width/2,yM:depth,widthM:width,depthM:depth,referenceDbSpl:reference}).levelDbSpl;
    text('spCoverageSummary',fmt(width*depth,1)+' m² alan · uzak merkezde yaklaşık '+fmt(rear,1)+' dB SPL. İki eşit noktasal kaynağın enerji toplamı; '+fmt(angle,0)+'° açı yalnızca kesikli çizgilerde gösterilir.');
  }
  function drawSystemAlignment() {
    const c=systemDesignerCanvas('spAlignmentCanvas');if(!c)return;
    const p=calculateSubTopAlignment({subDistanceM:number('spSubDistance'),topDistanceM:number('spTopDistance'),crossoverHz:number('spCrossover'),temperatureC:number('spTemperature')});
    const ctx=c.ctx,w=c.width,h=c.height;ctx.clearRect(0,0,w,h);ctx.fillStyle='#0b1016';ctx.fillRect(0,0,w,h);
    const maxDistance=Math.max(p.subDistanceM,p.topDistanceM,1),x0=75,x1=w-105;
    ctx.fillStyle='#d8b45d';ctx.font='bold 13px Segoe UI, Arial';ctx.fillText('ORTAK DİNLEME REFERANS NOKTASI',w-315,28);
    [[p.subDistanceM,105,'#55c4d0','SUB'],[p.topDistanceM,190,'#f1d38a','TOP']].forEach(([distance,y,color,label])=>{const endX=x0+(x1-x0)*Number(distance)/maxDistance;ctx.strokeStyle=color;ctx.lineWidth=5;ctx.beginPath();ctx.moveTo(x0,y);ctx.lineTo(endX,y);ctx.stroke();ctx.fillStyle=color;ctx.font='bold 13px Segoe UI, Arial';ctx.fillText(label+' · '+fmt(distance,1)+' m',x0,y-14);ctx.beginPath();ctx.arc(endX,y,5,0,Math.PI*2);ctx.fill();});
    ctx.strokeStyle='#fff';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(x1,65);ctx.lineTo(x1,235);ctx.stroke();ctx.fillStyle='#e7edf5';ctx.font='12px Segoe UI, Arial';ctx.fillText('Yol farkı: '+fmt(p.distanceDifferenceM,2)+' m',x0,255);
    text('spAlignmentSummary',(p.delayTarget==='Yok'?'Mesafe farkı yok.':p.delayTarget+' kanalına '+fmt(p.delayMs,3)+' ms geometrik gecikme')+' · crossover '+fmt(p.crossoverHz,0)+' Hz · faz farkı yaklaşık '+fmt(p.phaseDifferenceDeg,1)+'° · ses hızı '+fmt(p.speedMps,1)+' m/s. '+p.note);
  }
  function renderSystemDesigner(active) {
    try { if(active==='array')drawSystemArray();else if(active==='coverage')drawSystemCoverage();else if(active==='alignment')drawSystemAlignment(); }
    catch(error){showError(active==='array'?'spArraySummary':active==='coverage'?'spCoverageSummary':'spAlignmentSummary',error);}
  }
  function initSystemDesigner() {
    const page=document.querySelector('[data-page="systemplan"]'),anchor=page&&page.querySelector('.table-panel');
    if(!anchor||byId('spSystemDesigner'))return;
    const section=document.createElement('section');section.className='panel sp-system-designer';section.id='spSystemDesigner';section.innerHTML=systemDesignerMarkup();anchor.insertAdjacentElement('afterend',section);
    section.querySelectorAll('[data-sd-tab]').forEach(button=>button.addEventListener('click',()=>{const tab=button.dataset.sdTab;
      section.querySelectorAll('[data-sd-tab]').forEach(item=>{const active=item===button;item.classList.toggle('active',active);item.setAttribute('aria-selected',String(active));});
      section.querySelectorAll('[data-sd-panel]').forEach(panel=>{const active=panel.dataset.sdPanel===tab;panel.classList.toggle('active',active);panel.hidden=!active;});renderSystemDesigner(tab);}));
    ['spArrayCount','spArrayHang','spArraySplay','spArrayAim','spCoverageWidth','spCoverageDepth','spCoverageLevel','spCoverageAngle','spSubDistance','spTopDistance','spCrossover','spTemperature'].forEach(id=>byId(id).addEventListener('input',()=>renderSystemDesigner(section.querySelector('[data-sd-panel].active')?.dataset.sdPanel||'array')));
    byId('spSystemExport').addEventListener('click',()=>{try{
      const array=calculateArrayGeometry({cabinetCount:number('spArrayCount'),splayDeg:number('spArraySplay'),aimDeg:number('spArrayAim'),hangHeightM:number('spArrayHang')});
      const coverage={widthM:number('spCoverageWidth'),depthM:number('spCoverageDepth'),referenceDbSpl:number('spCoverageLevel'),nominalHorizontalAngleDeg:number('spCoverageAngle')};
      const alignment=calculateSubTopAlignment({subDistanceM:number('spSubDistance'),topDistanceM:number('spTopDistance'),crossoverHz:number('spCrossover'),temperatureC:number('spTemperature')});
      downloadText('stagepulse_system_taslagi.json',JSON.stringify({version:1,array,coverage,alignment,stageItems},null,2),'application/json;charset=utf-8');
      text('spArraySummary','Sistem taslağı JSON olarak dışa aktarıldı.');
    }catch(error){showError('spArraySummary',error);}});
    renderSystemDesigner('array');renderSystemDesigner('coverage');renderSystemDesigner('alignment');
    section.querySelectorAll('[data-sd-panel]').forEach((panel,index)=>{if(index)panel.hidden=true;});
  }

  function initAll() {
    const steps = [
      ['Kompresör ve gate kulak eğitimi', initDynamicsEarTraining],
      ['70/100 V hat hesabı', initPowerLine],
      ['RF kanal planı', initRfPlanner],
      ['Mikser sahne dosyası çözümleyici', initPatchAnalyzer],
      ['Oda SPL haritası', initRoomMap],
      ['Hoparlör kabini ve filtre hesabı', initSpeakerTools],
      ['Sahne ve AV planı', initStagePlanner],
      ['Hafif 2B sistem tasarımcısı', initSystemDesigner],
      ['Dalga, faz ve ses gecikmesi laboratuvarı', initWaveLab],
      ['OSC / MIDI kontrol araçları', initOscMidiTools]
    ];

    // Android ve Windows aynı sıralı başlatma akışını kullanır.
    // Her ağır ekranı ayrı tarayıcı görevinde başlat. Böylece WebView2
    // ilk açılışta tek uzun JavaScript döngüsü yüzünden yanıt vermez olmaz.
    const runStep = (index) => {
      if (index >= steps.length) return;
      const [name, fn] = steps[index];
      try { fn(); }
      catch (error) { console.error('Stagepulse araç başlatma hatası [' + name + ']:', error); }
      if (index + 1 < steps.length) {
        window.requestAnimationFrame(() => window.setTimeout(() => runStep(index + 1), 0));
      }
    };

    window.requestAnimationFrame(() => window.setTimeout(() => runStep(0), 0));
  }

  window.StagepulseFirstPartyTools = {
    initAll,
    calculateArrayGeometry,
    estimateSystemCoverage,
    calculateSubTopAlignment,
    parseM32Scene,
    calculatePowerLine,
    processCompressor,
    processGate,
    waveMath,
    isRoomMeasurementInsideRoom,
    buildOscPacket,
    buildMidiFile
  };
})();