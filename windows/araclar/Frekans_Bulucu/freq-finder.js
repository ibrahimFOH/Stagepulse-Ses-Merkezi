// Frekans Bulucu — notalar eşit aralıklı temperamanda hesaplanır.
const AudioContextClass = window.AudioContext || window.webkitAudioContext;
const audio = new AudioContextClass();

function playNote(frequency, volume = 0.15, duration = 1) {
    const output = document.getElementById("freq");
    output.className = "freq";
    output.innerText = `${Number(frequency).toFixed(2)} Hz`;
    // Tarayıcılar ilk kullanıcı etkileşimine kadar ses bağlamını askıya alabilir.
    if (audio.state === "suspended") audio.resume();
    const oscillator = audio.createOscillator();
    const gain = audio.createGain();
    oscillator.type = "sine";
    oscillator.frequency.value = Number(frequency);
    gain.gain.value = Math.min(Math.max(Number(volume) || 0.15, 0), 0.3);
    oscillator.connect(gain);
    gain.connect(audio.destination);
    oscillator.start();
    oscillator.stop(audio.currentTime + Math.max(0.05, Number(duration) || 1));
}
