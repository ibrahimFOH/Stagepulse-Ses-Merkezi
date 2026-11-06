'use strict';
/* Transparent acoustic calculations for education/planning. No device control. */
(function(root){
  const REF_PRESSURE_PA = 20e-6;
  const SOUND_SPEED_DEFAULT = 343;
  function finite(name, value){const v=Number(value);if(!Number.isFinite(v))throw new Error(name+' sayısal ve sonlu olmalı.');return v;}
  function positive(name,value){const v=finite(name,value);if(v<=0)throw new Error(name+' sıfırdan büyük olmalı.');return v;}
  function dbSum(levels){
    if(!Array.isArray(levels)||levels.length<1)throw new Error('En az bir seviye gerekli.');
    const xs=levels.map((v)=>finite('dB seviyesi',v));
    const max=Math.max(...xs);
    return max+10*Math.log10(xs.reduce((s,v)=>s+Math.pow(10,(v-max)/10),0));
  }
  function pressureToSpl(pressurePa){const p=positive('Ses basıncı (Pa)',pressurePa);if(p<2e-6||p>2000)throw new Error('Ses basıncı 0,000002-2000 Pa RMS aralığında olmalı (uygulama çalışma aralığı).');return 20*Math.log10(p/REF_PRESSURE_PA);}
  function splToPressure(levelDbSpl){const l=finite('dB SPL',levelDbSpl);if(l < -20 || l > 160)throw new Error('dB SPL -20 ile 160 arasında olmalı (uygulama çalışma aralığı).');return REF_PRESSURE_PA*Math.pow(10,l/20);}
  function distanceSpl(referenceLevelDbSpl, referenceDistanceM, targetDistanceM, sourceCount=1){
    const level=finite('Referans seviye',referenceLevelDbSpl);
    if(level < -20 || level > 160)throw new Error('Referans dB SPL -20 ile 160 arasında olmalı.');
    const r1=positive('Referans mesafe',referenceDistanceM), r2=positive('Hedef mesafe',targetDistanceM);
    if(r1>10000||r2>10000)throw new Error('Mesafeler 10000 m sınırını aşmamalı.');
    const n=finite('Kaynak sayısı',sourceCount);
    if(n<1||n>128||Math.floor(n)!==n)throw new Error('Kaynak sayısı 1-128 arasında tam sayı olmalı.');
    return {singleSourceDbSpl:level-20*Math.log10(r2/r1),
      combinedEnergyEstimateDbSpl:level-20*Math.log10(r2/r1)+10*Math.log10(n),
      distanceCorrectionDb:-20*Math.log10(r2/r1),
      sourceCountEnergyCorrectionDb:10*Math.log10(n),
      assumptions:['Serbest alan noktasal kaynak yaklaşımı; uzak alan ve yansımasız koşul varsayılır.',
        'Birden fazla kaynak için yalnızca eşit seviyeli, enerji toplamı kestirimi kullanılır; faz girişimi/array davranışı modellenmez.',
        'Hoparlör yönlülüğü, oda, hava, engeller, güç sıkıştırması ve limiter hesaba katılmaz.']};
  }
  function areaPlan(widthM, depthM, heightM, horizontalCoverageDeg){
    const w=positive('Alan genişliği',widthM), d=positive('Alan derinliği',depthM), h=positive('Alan yüksekliği',heightM);
    if(w>1000||d>1000||h>1000)throw new Error('Genişlik, derinlik ve yükseklik 1000 m sınırını aşmamalı.');
    const a=finite('Yatay kapsama açısı',horizontalCoverageDeg);
    if(a<1||a>179)throw new Error('Kapsama açısı 1-179 derece arasında olmalı.');
    const coveredWidth=2*d*Math.tan(a*Math.PI/360);
    return {widthM:w,depthM:d,heightM:h,areaM2:w*d,volumeM3:w*d*h,
      farthestCornerDistanceM:Math.hypot(d,w/2),
      idealWidthAtRearM:coveredWidth,
      idealWidthCoveragePercent:Math.min(100,100*coveredWidth/w),
      assumptions:['Dikdörtgen alan; PA alanın ön kenarının ortasında kabul edilir.',
        'Yatay kapsama geometrik açı projeksiyonudur; gerçek kutup grafiği/coverage, yükseklik, dikey açı, engeller ve koltuk düzenini modellemez.']};
  }
  function wavelength(frequencyHz, soundSpeed= SOUND_SPEED_DEFAULT){
    const f=positive('Frekans',frequencyHz), c=positive('Ses hızı',soundSpeed);
    if(f>100000||c<250||c>380)throw new Error('Frekans 100 kHz altında, ses hızı 250-380 m/s aralığında olmalı.');
    const lambda=c/f;return {frequencyHz:f,soundSpeedMps:c,wavelengthM:lambda,quarterWaveM:lambda/4,halfWaveM:lambda/2,periodMs:1000/f,
      note:'Dalga boyu ölçüsü tek başına end-fire/gradient DSP delay veya polarite ayarı değildir. Dizi geometrisi, üretici kılavuzu ve ölçüm gerekir.'};
  }
  function axialModes(lengthM,widthM,heightM,soundSpeed=SOUND_SPEED_DEFAULT,maxOrder=4){
    const dims=[['Uzunluk',positive('Uzunluk',lengthM)],['Genişlik',positive('Genişlik',widthM)],['Yükseklik',positive('Yükseklik',heightM)]];
    if(dims.some(([,d])=>d>1000))throw new Error('Oda boyutları 1000 m sınırını aşmamalı.');
    const c=positive('Ses hızı',soundSpeed), order=finite('Harmonik sayısı',maxOrder);
    if(c<250||c>380||order<1||order>10||Math.floor(order)!==order)throw new Error('Ses hızı 250-380 m/s, harmonik sayısı 1-10 tam sayı olmalı.');
    return dims.flatMap(([axis,d])=>Array.from({length:order},(_,i)=>({axis,order:i+1,dimensionM:d,frequencyHz:(i+1)*c/(2*d)})))
      .sort((a,b)=>a.frequencyHz-b.frequencyHz);
  }
  function sabineRt60(volumeM3, equivalentAbsorptionM2){
    const v=positive('Oda hacmi',volumeM3), a=positive('Eşdeğer soğurma alanı',equivalentAbsorptionM2);
    if(v>1e9||a>1e8)throw new Error('Oda hacmi/soğurma girdisi uygulama sınırını aşıyor.');
    return {volumeM3:v,equivalentAbsorptionM2:a,rt60Seconds:0.161*v/a,
      note:'Sabine kestirimi; difüz alan ve bilinen eşdeğer soğurma varsayımı. Düşük frekans, geometri, dağılım, bağlantılı hacimler ve ölçüm farklılıkları ayrıca değerlendirilmelidir.'};
  }
  function equivalentAbsorption(widthM,depthM,heightM,alphaFloor,alphaCeiling,alphaLongWalls,alphaShortWalls,frequencyHz=500){
    const w=positive('Oda genişliği',widthM), d=positive('Oda uzunluğu',depthM), h=positive('Oda yüksekliği',heightM);
    if(w>100||d>100||h>30)throw new Error('Eşdeğer soğurma hesabında oda sınırları: genişlik/uzunluk ≤100 m, yükseklik ≤30 m.');
    const frequency=finite('Soğurma katsayısı frekansı',frequencyHz);if(![125,250,500,1000,2000,4000,8000].includes(frequency))throw new Error('Soğurma katsayısı frekansı 125, 250, 500, 1000, 2000, 4000 veya 8000 Hz olmalı.');
    const coeffs=[['Zemin',alphaFloor],['Tavan',alphaCeiling],['Uzun duvar',alphaLongWalls],['Kısa duvar',alphaShortWalls]].map(([name,value])=>{const a=finite(name+' soğurma katsayısı',value);if(a<0||a>1)throw new Error(name+' soğurma katsayısı 0 ile 1 arasında olmalı.');return a;});
    const [floor,ceiling,longWall,shortWall]=coeffs;
    const areasM2={floor:w*d,ceiling:w*d,longWalls:2*d*h,shortWalls:2*w*h};
    const contributionsM2Sabin={floor:areasM2.floor*floor,ceiling:areasM2.ceiling*ceiling,longWalls:areasM2.longWalls*longWall,shortWalls:areasM2.shortWalls*shortWall};
    const equivalentAbsorptionM2=Object.values(contributionsM2Sabin).reduce((a,b)=>a+b,0);
    if(equivalentAbsorptionM2<=0)throw new Error('Eşdeğer soğurma A sıfır olamaz; en az bir yüzey için gerçek ve pozitif soğurma gir.');
    return {widthM:w,depthM:d,heightM:h,volumeM3:w*d*h,selectedFrequencyHz:frequency,areasM2,coefficients:{floor,ceiling,longWalls:longWall,shortWalls:shortWall},contributionsM2Sabin,equivalentAbsorptionM2,note:`Katsayılar ${frequency} Hz merkez frekansı için girilmiş kabul edilir ve malzemeye bağlıdır. Örnek varsayılan katsayılar gerçek oda ölçümü/RT60 verisi değildir; uygulamadaki Sabine sonucu yalnızca ilk kestirimdir.`};
  }
  function nioshExposure(levelDba,durationMinutes){
    const l=finite('LAeq seviyesi',levelDba), t=positive('Maruziyet süresi',durationMinutes);
    if(l<70||l>140||t>10080)throw new Error('Seviye 70-140 dBA, süre 0-10080 dakika aralığında olmalı.');
    const allowedMinutes=480/Math.pow(2,(l-85)/3);
    return {levelDba:l,durationMinutes:t,nioshReferenceMinutes:allowedMinutes,dosePercent:100*t/allowedMinutes,
      referenceDoseReached:(100*t/allowedMinutes)>=100,
      note:'NIOSH mesleki işitme koruma kestirimidir: 85 dBA, 8 saat, 3 dB değişim oranı. Genel halk için yasal sınır, konser sınırı veya kalibrasyonsuz mikrofon ölçümü değildir.'};
  }
  function nioshDose(segments){
    if(!Array.isArray(segments)||segments.length<1||segments.length>12)throw new Error('1-12 maruziyet bloğu girilmeli.');
    const analyzed=segments.map((segment,index)=>{
      if(!segment||typeof segment!=='object')throw new Error(`Maruziyet bloğu ${index+1} geçersiz.`);
      const r=nioshExposure(segment.levelDba,segment.durationMinutes);
      return {levelDba:r.levelDba,durationMinutes:r.durationMinutes,referenceMinutes:r.nioshReferenceMinutes,dosePercent:r.dosePercent};
    });
    const totalDurationMinutes=analyzed.reduce((sum,x)=>sum+x.durationMinutes,0);
    const dosePercent=analyzed.reduce((sum,x)=>sum+x.dosePercent,0);
    return {segments:analyzed,totalDurationMinutes,dosePercent,referenceDoseReached:dosePercent>=100,
      note:'Doz, her düzey için süre/izin verilen süre oranlarının toplamıdır. NIOSH mesleki referansıdır; genel halk, konser veya yerel mevzuat sınırı değildir. Girdi LAeq değerleri uygun kalibreli ölçümle belirlenmelidir.'};
  }
  function recommendCuts(centers,values,thresholdDb=6){
    if(!Array.isArray(centers)||!Array.isArray(values)||centers.length!==values.length)throw new Error('RTA bant dizileri eşleşmiyor.');
    const threshold=finite('Tepe eşiği',thresholdDb);if(threshold<3||threshold>12)throw new Error('Tepe eşiği 3-12 dB arasında olmalı.');
    const result=[];
    for(let i=3;i<centers.length-3;i++){
      const v=Number(values[i]); if(!Number.isFinite(v)||v<=-110)continue;
      if(v<Number(values[i-1])||v<Number(values[i+1]))continue;
      const neigh=[values[i-3],values[i-2],values[i+2],values[i+3]].map(Number).filter(x=>Number.isFinite(x)&&x>-110).sort((a,b)=>a-b);
      if(neigh.length<3)continue;
      const baseline=(neigh[1]+neigh[2])/2;
      const excess=v-baseline;
      if(excess>=threshold){
        result.push({frequencyHz:Number(centers[i]),excessDb:excess,baselineDbfs:baseline,
          suggestedCutDb:-Math.min(3,Math.max(1,Math.round(excess/2))),qApprox:4.3,
          action:'Yalnızca aday kesim; donanıma otomatik uygulanmaz.'});
      }
    }
    // Keep separated peaks. If two candidates are close, keep the stronger one.
    const filtered=[];
    for(const item of result){const last=filtered[filtered.length-1];if(last && item.frequencyHz/last.frequencyHz<Math.pow(2,2/3)){if(item.excessDb>last.excessDb)filtered[filtered.length-1]=item;}else filtered.push(item);}
    return filtered.slice(0,5);
  }
  const api={REF_PRESSURE_PA,SOUND_SPEED_DEFAULT,dbSum,pressureToSpl,splToPressure,distanceSpl,areaPlan,wavelength,axialModes,sabineRt60,equivalentAbsorption,nioshExposure,nioshDose,recommendCuts};
  root.StagepulseAcousticMath=api;
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
