/* Stagepulse ortak Türkçe–İngilizce teknik terminoloji katmanı. */
(() => {
  'use strict';
  const TERMS = [
    ["Kompresör", "Compressor"],
    ["Gürültü kapısı", "Noise Gate"],
    ["Eşik", "Threshold"],
    ["Oran", "Ratio"],
    ["Diz", "Knee"],
    ["Atak", "Attack"],
    ["Atak süresi", "Attack Time"],
    ["Bırakma", "Release"],
    ["Bırakma süresi", "Release Time"],
    ["Çıkış kazancı", "Makeup Gain"],
    ["Kısma aralığı", "Range"],
    ["Bekletme", "Hold"],
    ["Ham sinyal", "Dry Signal"],
    ["İşlenmiş sinyal", "Processed Signal"],
    ["Test sinyali", "Test Signal"],
    ["Konuşma benzeri sinyal", "Speech-like Signal"],
    ["Vurmalı sinyal", "Drum Signal"],
    ["Bas sinyali", "Bass Signal"],
    ["Sinyal akışı", "Signal Flow"],
    ["Kazanç yapısı", "Gain Staging"],
    ["Giriş / Çıkış", "Input / Output"],
    ["Ön yükselteç", "Preamplifier"],
    ["Kazanç", "Gain"],
    ["Kazanç azaltımı", "Gain Reduction"],
    ["Baş boşluğu", "Headroom"],
    ["Kırpılma", "Clipping"],
    ["Veriyolu", "Bus"],
    ["Ana çıkış", "Main Output"],
    ["Gönderim", "Send"],
    ["Dönüş", "Return"],
    ["Ekleme", "Insert"],
    ["Yan zincir", "Sidechain"],
    ["Kaydırma", "Pan"],
    ["Susturma", "Mute"],
    ["Tek başına dinleme", "Solo"],
    ["Sürgü", "Fader"],
    ["Ses basınç seviyesi", "Sound Pressure Level"],
    ["Gerçek zamanlı analiz", "Real-Time Analysis"],
    ["Frekans yanıtı", "Frequency Response"],
    ["Gürültü tabanı", "Noise Floor"],
    ["Örnekleme hızı", "Sample Rate"],
    ["Örnekleme frekansı", "Sampling Frequency"],
    ["Bit derinliği", "Bit Depth"],
    ["Nyquist frekansı", "Nyquist Frequency"],
    ["Süzgeç", "Filter"],
    ["Yüksek geçiren filtre", "High-Pass Filter"],
    ["Alçak geçiren filtre", "Low-Pass Filter"],
    ["Bant geçiren filtre", "Band-Pass Filter"],
    ["Bant durduran filtre", "Band-Stop Filter"],
    ["Kesim frekansı", "Crossover Frequency"],
    ["Merkez frekans", "Center Frequency"],
    ["Faz", "Phase"],
    ["Polarite", "Polarity"],
    ["Gecikme", "Delay"],
    ["Gecikme telafisi", "Latency Compensation"],
    ["Dinamik aralık", "Dynamic Range"],
    ["Sıkıştırma", "Compression"],
    ["Genişletici", "Expander"],
    ["Sınırlayıcı", "Limiter"],
    ["Ses yüksekliği", "Loudness"],
    ["Tepe seviyesi", "Peak Level"],
    ["Örnek tepe", "Sample Peak"],
    ["Gerçek tepe", "True Peak"],
    ["A/B karşılaştırma", "A/B Comparison"],
    ["Referans sinyal", "Reference Signal"],
    ["Kalibrasyon", "Calibration"],
    ["Ağırlıklandırma", "Weighting"],
    ["Zaman ağırlıklandırma", "Time Weighting"],
    ["Mikrofon", "Microphone"],
    ["Anten", "Antenna"],
    ["Kablosuz sistem", "Wireless System"],
    ["Frekans koordinasyonu", "Frequency Coordination"],
    ["RF taraması", "RF Scan"],
    ["Girişim ürünleri", "Intermodulation Products"],
    ["Dijital sinyal işleme", "Digital Signal Processing"],
    ["Hoparlör", "Loudspeaker"],
    ["Monitör", "Monitor"],
    ["Hat dizisi", "Line Array"],
    ["Alt frekans hoparlörü", "Subwoofer"],
    ["Çapraz geçiş", "Crossover"],
    ["Darbe yanıtı", "Impulse Response"],
    ["Aktarım işlevi", "Transfer Function"],
    ["Tutarlılık", "Coherence"],
    ["Genlik", "Magnitude"],
    ["Spektrum", "Spectrum"],
    ["Oktav bandı", "Octave Band"],
    ["Üçte bir oktav", "One-Third Octave"],
    ["Hızlı Fourier dönüşümü", "Fast Fourier Transform"],
    ["Pencere işlevi", "Window Function"],
    ["Yankı", "Reverb"],
    ["Ses kontrolü", "Soundcheck"],
    ["Sahne planı", "Stage Plot"],
    ["Giriş listesi", "Input List"],
    ["Teknik şartname", "Technical Rider"],
    ["Ön alan", "Front of House"],
    ["Kulak içi monitör", "In-Ear Monitor"],
    ["Ölçüm mikrofonu", "Measurement Microphone"],
    ["Yankılanma süresi", "Reverberation Time"]
  ];
  const SKIP = new Set(['SCRIPT','STYLE','NOSCRIPT','CODE','PRE','TEXTAREA','INPUT','SVG','PATH']);
  const escapeRegex = value => value.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\$&');
  const pattern = new RegExp('(?<![\\wğüşöçıİĞÜŞÖÇ])(' + TERMS.map(([tr]) => escapeRegex(tr)).sort((a,b)=>b.length-a.length).join('|') + ')(?![\\wğüşöçıİĞÜŞÖÇ])(?!\\s*\\()', 'giu');
  const lookup = new Map(TERMS.map(([tr,en]) => [tr.toLocaleLowerCase('tr-TR'), {tr,en}]));
  function translate(value) {
    if (!value || !/[ğüşöçıİĞÜŞÖÇ]/i.test(value)) return value;
    return value.replace(pattern, match => {
      const item = lookup.get(match.toLocaleLowerCase('tr-TR'));
      if (!item) return match;
      const label = match[0] === match[0].toLocaleLowerCase('tr-TR') ? item.tr.toLocaleLowerCase('tr-TR') : item.tr;
      return label + ' (' + item.en + ')';
    });
  }
  function translateElement(el) {
    if (!el || el.nodeType !== 1 || el.closest('[data-no-bilingual]')) return;
    if (!SKIP.has(el.tagName)) for (const attr of ['title','aria-label','placeholder','alt']) {
      const value = el.getAttribute(attr);
      if (value) { const next = translate(value); if (next !== value) el.setAttribute(attr, next); }
    }
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        const parent = node.parentElement;
        if (!parent || SKIP.has(parent.tagName) || parent.closest('[data-no-bilingual]')) return NodeFilter.FILTER_REJECT;
        return /[ğüşöçıİĞÜŞÖÇ]/i.test(node.nodeValue || '') ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
      }
    });
    const nodes=[]; while(walker.nextNode()) nodes.push(walker.currentNode);
    for(const node of nodes){const next=translate(node.nodeValue);if(next!==node.nodeValue)node.nodeValue=next;}
  }
  function start() {
    translateElement(document.body);
    const observer = new MutationObserver(records => {
      for(const record of records){
        if(record.type==='characterData'){
          const p=record.target.parentElement;
          if(p&&!SKIP.has(p.tagName)&&!p.closest('[data-no-bilingual]')){
            const next=translate(record.target.nodeValue);if(next!==record.target.nodeValue)record.target.nodeValue=next;
          }
        } else for(const node of record.addedNodes){
          if(node.nodeType===1) translateElement(node);
          else if(node.nodeType===3&&node.parentElement&&!SKIP.has(node.parentElement.tagName)){
            const next=translate(node.nodeValue);if(next!==node.nodeValue)node.nodeValue=next;
          }
        }
      }
    });
    observer.observe(document.body,{subtree:true,childList:true,characterData:true});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
  window.StagepulseBilingualTerms=Object.freeze({translate,terms:TERMS.length});
})();
