'use strict';
/* UI-side band selection/smoothing. Capture and FFT power math lives in core/rta_capture.py. */
(function (root) {
  const THIRD_CENTERS = Object.freeze([20,25,31.5,40,50,63,80,100,125,160,200,250,315,400,500,630,800,1000,1250,1600,2000,2500,3150,4000,5000,6300,8000,10000,12500,16000,20000]);
  const OCTAVE_CENTERS = Object.freeze([31.5,63,125,250,500,1000,2000,4000,8000,16000]);
  function normalizeBands(mode) {
    if (mode === 'third') return 3;
    if (mode === 'octave') return 1;
    const bands = Number(mode);
    if (![1,3,6,12,24,48].includes(bands)) throw new Error('Bant çözünürlüğü 1, 3, 6, 12, 24 veya 48 olmalı.');
    return bands;
  }
  function ratio(mode) {
    const bands = normalizeBands(mode);
    if (bands === 3) return Math.pow(10, 1/20);
    if (bands === 1) return Math.pow(10, 3/20);
    return Math.pow(2, 1/(2*bands));
  }
  function centers(mode) {
    const bands = normalizeBands(mode);
    if (bands === 3) return THIRD_CENTERS.slice();
    if (bands === 1) return OCTAVE_CENTERS.slice();
    const first = Math.ceil(bands*Math.log2(20/1000)-1e-12);
    const last = Math.floor(bands*Math.log2(20000/1000)+1e-12);
    const result = [];
    for(let k=first;k<=last;k++) result.push(1000*Math.pow(2,k/bands));
    return result;
  }
  function supportedCenters(sampleRate, mode, minHz=20, maxHz=20000) {
    if (!(Number.isFinite(sampleRate) && sampleRate > 0)) return [];
    const br = ratio(mode), nyquist = sampleRate/2;
    return centers(mode).filter(f => f >= minHz && f <= maxHz && f*br <= nyquist*.999);
  }
  function clampRangeToSupported(sampleRate, mode, low, high) {
    const bands = supportedCenters(sampleRate, mode, 20, 20000);
    const maxSupported = bands.length ? bands[bands.length - 1] : 20;
    let lo = Number(low), hi = Math.min(Number(high), maxSupported);
    if (!Number.isFinite(lo) || !Number.isFinite(hi)) return [20, maxSupported];
    if (lo >= maxSupported) lo = Math.max(20, maxSupported / 2);
    if (hi <= lo) lo = Math.min(lo, Math.max(20, maxSupported / 2));
    return [lo, Math.max(lo + 0.1, hi)];
  }
  function smooth(previous, current, dtSeconds, tauSeconds) {
    const dt=Math.max(.001,Number(dtSeconds)||.001), tau=Math.max(.001,Number(tauSeconds)||.5);
    const alpha=1-Math.exp(-dt/tau);
    if(!Array.isArray(previous)||previous.length!==current.length)return current.slice();
    return current.map((value,index)=>previous[index]+alpha*(value-previous[index]));
  }
  function applyMicCorrection(centers, values, profile) {
    if(!Array.isArray(values))return [];
    if(!Array.isArray(centers)||!Array.isArray(profile)||profile.length<2)return values.slice();
    const points=profile.filter(p=>Number.isFinite(Number(p.frequency_hz))&&Number.isFinite(Number(p.correction_db)))
      .map(p=>({frequency_hz:Number(p.frequency_hz),correction_db:Number(p.correction_db)}))
      .sort((a,b)=>a.frequency_hz-b.frequency_hz);
    if(points.length<2)return values.slice();
    return values.map((value,index)=>{
      const frequency=Number(centers[index]);
      if(!Number.isFinite(frequency)||frequency<points[0].frequency_hz||frequency>points[points.length-1].frequency_hz)return value;
      let hi=points.findIndex(p=>p.frequency_hz>=frequency);
      if(hi<=0)return value+points[0].correction_db;
      const a=points[hi-1],b=points[hi];
      if(b.frequency_hz===a.frequency_hz)return value+a.correction_db;
      const t=(Math.log(frequency)-Math.log(a.frequency_hz))/(Math.log(b.frequency_hz)-Math.log(a.frequency_hz));
      return value+a.correction_db+(b.correction_db-a.correction_db)*t;
    });
  }
  function fractionalCenters(sampleRate,bandsPerOctave,minHz=20,maxHz=20000) {
    const bands=Number(bandsPerOctave), low=Number(minHz), high=Number(maxHz);
    if(!Number.isFinite(sampleRate)||sampleRate<=0)return [];
    if(![1,3,6,12,24,48].includes(bands))throw new Error('Bant çözünürlüğü 1, 3, 6, 12, 24 veya 48 olmalı.');
    if(!Number.isFinite(low)||!Number.isFinite(high)||low<=0||high<=low)throw new Error('Frekans aralığı pozitif ve artan olmalı.');
    const halfBandRatio=Math.pow(2,1/(2*bands)), nyquist=sampleRate/2;
    const first=Math.ceil(bands*Math.log2(low/1000)-1e-12);
    const last=Math.floor(bands*Math.log2(high/1000)+1e-12);
    const result=[];
    for(let k=first;k<=last;k++){
      const center=1000*Math.pow(2,k/bands);
      if(center>=low&&center<=high&&center*halfBandRatio<=nyquist*.999)result.push(center);
    }
    return result;
  }
  const api={ratio,centers,supportedCenters,clampRangeToSupported,smooth,fractionalCenters,normalizeBands,applyMicCorrection};
  root.StagepulseRtaMath=api;
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
