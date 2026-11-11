/* Stagepulse Stereo Scope - bağımsız yerel stereo analiz modülü. */
(function (root) {
  'use strict';
  function finite(value) { return Number.isFinite(value) ? value : 0; }
  function db(value) { return value > 1e-12 ? 20 * Math.log10(value) : -120; }

  function analyzeStereo(left, right) {
    if (!left || !right || left.length !== right.length || left.length < 2) throw new Error('Eşit uzunlukta iki stereo kanal gerekli.');
    var n = left.length, sumL = 0, sumR = 0, sumL2 = 0, sumR2 = 0, sumMid2 = 0, sumSide2 = 0;
    for (var i = 0; i < n; i++) {
      var l = finite(left[i]), r = finite(right[i]);
      sumL += l; sumR += r; sumL2 += l * l; sumR2 += r * r;
      var mid = (l + r) * 0.5, side = (l - r) * 0.5;
      sumMid2 += mid * mid; sumSide2 += side * side;
    }
    var meanL = sumL / n, meanR = sumR / n, covariance = 0, varianceL = 0, varianceR = 0;
    for (var j = 0; j < n; j++) {
      var dl = finite(left[j]) - meanL, dr = finite(right[j]) - meanR;
      covariance += dl * dr; varianceL += dl * dl; varianceR += dr * dr;
    }
    var denominator = Math.sqrt(varianceL * varianceR);
    var correlation = denominator > 1e-18 ? Math.max(-1, Math.min(1, covariance / denominator)) : 0;
    var rmsL = Math.sqrt(sumL2 / n), rmsR = Math.sqrt(sumR2 / n);
    var rmsMid = Math.sqrt(sumMid2 / n), rmsSide = Math.sqrt(sumSide2 / n);
    var stereoRms = Math.sqrt((sumL2 + sumR2) / (2 * n));
    return { samples:n, correlation:correlation, rmsLeftDbfs:db(rmsL), rmsRightDbfs:db(rmsR),
      midDbfs:db(rmsMid), sideDbfs:db(rmsSide), widthDb:db(rmsSide / Math.max(rmsMid, 1e-12)),
      monoDeltaDb:db(rmsMid / Math.max(stereoRms, 1e-12)), rmsLeft:rmsL, rmsRight:rmsR };
  }

  var api = { analyzeStereo: analyzeStereo };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (!root || !root.document) return;

  var $ = function (id) { return root.document.getElementById(id); };
  var currentAudioContext = null, currentBuffer = null;
  function format(value, digits) {
    return Number.isFinite(value) ? value.toLocaleString('tr-TR', { minimumFractionDigits:digits, maximumFractionDigits:digits }) : '—';
  }
  function status(message, warning) {
    var node = $('stereoScopeStatus'); if (!node) return;
    node.textContent = message; node.classList.toggle('notice-warn', !!warning);
  }
  function paintMetrics(result, buffer) {
    $('stereoCorrelation').textContent = format(result.correlation, 3);
    $('stereoWidth').textContent = format(result.widthDb, 1) + ' dB';
    $('stereoLeftRms').textContent = format(result.rmsLeftDbfs, 1) + ' dBFS';
    $('stereoRightRms').textContent = format(result.rmsRightDbfs, 1) + ' dBFS';
    $('stereoMonoDelta').textContent = format(result.monoDeltaDb, 1) + ' dB';
    $('stereoSampleInfo').textContent = format(buffer.sampleRate, 0) + ' Hz · ' + format(buffer.duration, 2) + ' sn · ' + format(result.samples, 0) + ' örnek/kanal';
    var note = result.correlation < -0.15
      ? 'Negatif korelasyon: mono toplamada belirgin seviye kaybı veya faz iptali riski var.'
      : result.correlation < 0.2
        ? 'Korelasyon düşük: stereo içerik geniş veya kanallar arası ilişki zayıf. Mono uyumluluğunu dinleyerek kontrol et.'
        : result.correlation > 0.85
          ? 'Yüksek pozitif korelasyon: kanallar birbirine benzer; görüntü merkeze yakın kalabilir.'
          : 'Korelasyon pozitif. Stereo genişliği ve mono uyumluluğunu birlikte değerlendir.';
    status(note + ' Dosya yalnızca cihaz belleğinde çözümlendi; sunucuya gönderilmedi.', result.correlation < -0.15);
  }
  function drawScope(buffer) {
    var canvas = $('stereoScopeCanvas'); if (!canvas || !buffer) return;
    var rect = canvas.getBoundingClientRect(); if (rect.width < 30) return;
    var dpr = Math.min(2, Math.max(1, root.devicePixelRatio || 1));
    var width = Math.max(280, Math.floor(rect.width * dpr)), height = Math.max(220, Math.floor(rect.height * dpr));
    canvas.width = width; canvas.height = height;
    var ctx = canvas.getContext('2d'); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    var w = width / dpr, h = height / dpr, cx = w / 2, cy = h / 2, radius = Math.min(w, h) * 0.43;
    ctx.clearRect(0, 0, w, h); ctx.fillStyle = '#090d12'; ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = 'rgba(160,174,192,.22)'; ctx.lineWidth = 1;
    [0.25, 0.5, 0.75, 1].forEach(function (scale) { ctx.beginPath(); ctx.arc(cx, cy, radius * scale, 0, Math.PI * 2); ctx.stroke(); });
    ctx.beginPath(); ctx.moveTo(cx - radius, cy); ctx.lineTo(cx + radius, cy); ctx.moveTo(cx, cy - radius); ctx.lineTo(cx, cy + radius);
    ctx.moveTo(cx - radius * 0.707, cy - radius * 0.707); ctx.lineTo(cx + radius * 0.707, cy + radius * 0.707);
    ctx.moveTo(cx - radius * 0.707, cy + radius * 0.707); ctx.lineTo(cx + radius * 0.707, cy - radius * 0.707); ctx.stroke();
    ctx.fillStyle = 'rgba(216,180,93,.75)'; ctx.font = '10px Segoe UI, Arial';
    ctx.fillText('MID', cx + radius + 7, cy - 5); ctx.fillText('SIDE', cx + 6, cy - radius - 7);
    var left = buffer.getChannelData(0), right = buffer.getChannelData(1), count = Math.min(left.length, right.length);
    var stride = Math.max(1, Math.floor(count / 14000)), peak = 0;
    for (var p = 0; p < count; p += stride) {
      var a = finite(left[p]), b = finite(right[p]);
      peak = Math.max(peak, Math.abs((a + b) * 0.5), Math.abs((a - b) * 0.5));
    }
    var gain = peak > 1e-8 ? 0.95 / peak : 1; ctx.fillStyle = 'rgba(232,194,105,.62)';
    for (var k = 0; k < count; k += stride) {
      var l = finite(left[k]), r = finite(right[k]), x = (l + r) * 0.5 * gain, y = (l - r) * 0.5 * gain;
      ctx.fillRect(cx + x * radius, cy - y * radius, 1.5, 1.5);
    }
  }
  async function loadFile(file) {
    if (!file) return;
    if (file.size > 150 * 1024 * 1024) { status('Dosya 150 MB sınırını aşıyor. Daha kısa veya daha küçük bir WAV dosyası kullan.', true); return; }
    var AudioCtor = root.AudioContext || root.webkitAudioContext;
    if (!AudioCtor) { status('Bu cihaz Web Audio API desteklemiyor.', true); return; }
    status('Stereo ses dosyası çözümleniyor…');
    try {
      if (currentAudioContext) await currentAudioContext.close().catch(function () {});
      currentAudioContext = new AudioCtor();
      var buffer = await currentAudioContext.decodeAudioData(await file.arrayBuffer());
      if (buffer.numberOfChannels < 2) throw new Error('Dosya mono. Vectorscope için iki kanallı stereo WAV yükle.');
      if (buffer.duration > 600) throw new Error('Dosya süresi 10 dakikayı aşıyor. Bellek güvenliği için daha kısa bölüm kullan.');
      currentBuffer = buffer;
      paintMetrics(analyzeStereo(buffer.getChannelData(0), buffer.getChannelData(1)), buffer);
      drawScope(buffer);
    } catch (error) {
      currentBuffer = null; status('Analiz yapılamadı: ' + (error && error.message ? error.message : String(error)), true);
    }
  }
  function init() {
    var input = $('stereoScopeFile'), canvas = $('stereoScopeCanvas');
    if (!input || !canvas || input.dataset.bound) return;
    input.dataset.bound = '1'; input.addEventListener('change', function () { loadFile(input.files && input.files[0]); });
    var clear = $('stereoScopeClear');
    if (clear) clear.addEventListener('click', function () {
      input.value = ''; currentBuffer = null;
      ['stereoCorrelation','stereoWidth','stereoLeftRms','stereoRightRms','stereoMonoDelta'].forEach(function (id) { $(id).textContent = '—'; });
      $('stereoSampleInfo').textContent = 'Dosya seçilmedi'; status('Analiz temizlendi. Stereo WAV dosyası seçerek başlayabilirsin.');
      canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
    });
    if (typeof ResizeObserver !== 'undefined') {
      var observer = new ResizeObserver(function () { if (currentBuffer) drawScope(currentBuffer); }); observer.observe(canvas);
    } else root.addEventListener('resize', function () { if (currentBuffer) drawScope(currentBuffer); });
    root.addEventListener('pagehide', function () { if (currentAudioContext) currentAudioContext.close().catch(function () {}); });
    status('Analiz için iki kanallı stereo WAV dosyası seç.');
  }
  root.StagepulseStereoScope = api;
  if (root.document.readyState === 'loading') root.document.addEventListener('DOMContentLoaded', init, { once:true });
  else init();
})(typeof window !== 'undefined' ? window : null);
