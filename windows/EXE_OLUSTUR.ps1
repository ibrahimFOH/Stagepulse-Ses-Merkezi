$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
try { [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false) } catch { }
Set-Location $PSScriptRoot

# Remove an older student-delivery ZIP before tests; build products must never be mistaken for source assets.
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $PSScriptRoot 'ogrenciye_gonder')

$version = '4.0.2'
$appIcon = Join-Path $PSScriptRoot 'ui\assets\stagepulse.ico'
if (-not (Test-Path -LiteralPath $appIcon)) { throw 'Stagepulse uygulama simgesi eksik: ui\assets\stagepulse.ico' }
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) { throw 'Derleme bilgisayarında Python 3.11, 3.12, 3.13 veya 3.14 x64 gerekli. Son kullanıcının Python kurmasına gerek yoktur.' }
$pyInfo = (& python -c "import struct,sys; print(str(sys.version_info.major)+'.'+str(sys.version_info.minor)+'|'+str(struct.calcsize('P')*8))").Trim()
$parts = $pyInfo.Split('|')
if ($parts[0] -notin @('3.11','3.12','3.13','3.14') -or $parts[1] -ne '64') { throw "Desteklenmeyen Python: $pyInfo. Derleme için 3.11/3.12/3.13/3.14 x64 gerekir." }
Write-Host "Derleme Python'u: $($parts[0]) x64" -ForegroundColor Green

# Build tooling is used only on the developer/build machine; customers receive one Setup.exe.
$webview = Join-Path $PSScriptRoot 'build_support\MicrosoftEdgeWebView2RuntimeInstallerX64.exe'
New-Item -ItemType Directory -Force -Path (Split-Path $webview) | Out-Null
if (-not (Test-Path $webview)) {
  Write-Host 'WebView2 çevrimdışı yükleyicisi indiriliyor...' -ForegroundColor Cyan
  Invoke-WebRequest -Uri 'https://go.microsoft.com/fwlink/p/?LinkId=2124703' -OutFile $webview -UseBasicParsing
}
$sig = Get-AuthenticodeSignature -LiteralPath $webview
if ($sig.Status -ne 'Valid' -or $sig.SignerCertificate.Subject -notmatch 'Microsoft') {
  Remove-Item -LiteralPath $webview -Force -ErrorAction SilentlyContinue
  throw 'WebView2 yükleyicisinin Microsoft dijital imzası doğrulanamadı.'
}

$nsisRoot = Join-Path $PSScriptRoot 'build_support\nsis-3.13'
$makensis = Join-Path $nsisRoot 'makensis.exe'
if (-not (Test-Path $makensis)) {
  $buildSupport = Join-Path $PSScriptRoot 'build_support'
  New-Item -ItemType Directory -Force -Path $buildSupport | Out-Null
  $zip = Join-Path $buildSupport 'nsis-3.13.zip'
  # Official SourceForge SHA-256 for nsis-3.13.zip. Never skip this check.
  $expectedZipHash = 'ba63dffc4410ee89193e1cb5a41989991bd77c61068da17e3156d136b7b0b3d8'
  $zipUrls = @(
    'https://downloads.sourceforge.net/project/nsis/NSIS%203/3.13/nsis-3.13.zip',
    'https://sourceforge.net/projects/nsis/files/NSIS%203/3.13/nsis-3.13.zip/download',
    'https://netix.dl.sourceforge.net/project/nsis/NSIS%203/3.13/nsis-3.13.zip',
    'https://master.dl.sourceforge.net/project/nsis/NSIS%203/3.13/nsis-3.13.zip'
  )
  $zipVerified = $false
  $sourceIndex = 0
  foreach ($url in $zipUrls) {
    $sourceIndex++
    if ($zipVerified) { break }
    for ($attempt = 1; $attempt -le 2; $attempt++) {
      Remove-Item -LiteralPath $zip -Force -ErrorAction SilentlyContinue
      try {
        Write-Host "NSIS arşivi indiriliyor (kaynak $sourceIndex/$($zipUrls.Count), deneme $attempt)..." -ForegroundColor Cyan
        Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing -MaximumRedirection 10 -TimeoutSec 120 -Headers @{ 'User-Agent' = 'StagepulseSesMerkezi-Build/4.0.2' }
        if (-not (Test-Path -LiteralPath $zip)) { throw 'İndirme dosyası oluşmadı.' }
        $fileInfo = Get-Item -LiteralPath $zip
        if ($fileInfo.Length -lt 1000000) { throw "İndirilen dosya beklenenden küçük ($($fileInfo.Length) bayt); sunucu indirme sayfası döndürmüş olabilir." }
        $stream = [System.IO.File]::OpenRead($zip)
        try { $b1 = $stream.ReadByte(); $b2 = $stream.ReadByte() } finally { $stream.Dispose() }
        if ($b1 -ne 0x50 -or $b2 -ne 0x4B) { throw 'İndirilen içerik ZIP dosyası değil (PK başlığı bulunamadı).' }
        $actualZipHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $zip).Hash.ToLowerInvariant()
        if ($actualZipHash -eq $expectedZipHash) {
          $zipVerified = $true
          Write-Host 'NSIS arşivi SHA-256 ile doğrulandı.' -ForegroundColor Green
          break
        }
        Write-Warning "NSIS ZIP özeti uyuşmadı; kaynak atlanacak. Boyut: $($fileInfo.Length) bayt; alınan SHA-256: $actualZipHash"
      } catch {
        Write-Warning "NSIS ZIP indirme/doğrulama başarısız: $($_.Exception.Message)"
      }
      Remove-Item -LiteralPath $zip -Force -ErrorAction SilentlyContinue
      Start-Sleep -Seconds 2
    }
  }

  if ($zipVerified) {
    $expand = Join-Path $buildSupport 'nsis_extract'
    Remove-Item $expand -Recurse -Force -ErrorAction SilentlyContinue
    Expand-Archive -LiteralPath $zip -DestinationPath $expand -Force
    $found = Get-ChildItem -LiteralPath $expand -Filter makensis.exe -Recurse | Select-Object -First 1
    if (-not $found) { throw 'SHA-256 ile doğrulanmış NSIS arşivinde makensis.exe bulunamadı.' }
    New-Item -ItemType Directory -Force -Path $nsisRoot | Out-Null
    Copy-Item -Path (Join-Path $found.Directory.FullName '*') -Destination $nsisRoot -Recurse -Force
    # The verified NSIS archive is temporary build tooling, not a distributable asset.
    # Remove it before pytest starts, otherwise archive-integrity tests correctly fail.
    Remove-Item -LiteralPath $zip -Force -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $expand
  } else {
    # Fallback: the official NSIS installer, pinned by its published SHA-256.
    # This tool is installed silently only on the developer/build computer.
    $nsisSetup = Join-Path $buildSupport 'nsis-3.13-setup.exe'
    $expectedSetupHash = 'db9a1038bbc0e53fef24f423fd609979bd578e942f1be1198db186d1c42652a3'
    $setupUrls = @(
      'https://sourceforge.net/projects/nsis/files/NSIS%203/3.13/nsis-3.13-setup.exe/download',
      'https://downloads.sourceforge.net/project/nsis/NSIS%203/3.13/nsis-3.13-setup.exe'
    )
    $setupVerified = $false
    foreach ($url in $setupUrls) {
      if ($setupVerified) { break }
      Remove-Item -LiteralPath $nsisSetup -Force -ErrorAction SilentlyContinue
      try {
        Write-Host 'Arşiv aynası çalışmadı. Resmî NSIS 3.13 kurulum dosyası indiriliyor...' -ForegroundColor Yellow
        Invoke-WebRequest -Uri $url -OutFile $nsisSetup -UseBasicParsing -MaximumRedirection 10 -TimeoutSec 120 -Headers @{ 'User-Agent' = 'StagepulseSesMerkezi-Build/4.0.2' }
        if (-not (Test-Path -LiteralPath $nsisSetup) -or (Get-Item -LiteralPath $nsisSetup).Length -lt 1000000) { throw 'NSIS kurulum dosyası eksik veya beklenenden küçük.' }
        $actualSetupHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $nsisSetup).Hash.ToLowerInvariant()
        if ($actualSetupHash -ne $expectedSetupHash) { throw "Kurulum dosyasının SHA-256 değeri uyuşmadı: $actualSetupHash" }
        $setupVerified = $true
        Write-Host 'NSIS kurulum dosyası SHA-256 ile doğrulandı.' -ForegroundColor Green
      } catch {
        Write-Warning "NSIS kurulum dosyası doğrulanamadı: $($_.Exception.Message)"
        Remove-Item -LiteralPath $nsisSetup -Force -ErrorAction SilentlyContinue
      }
    }
    if (-not $setupVerified) {
      throw 'NSIS 3.13 indirilemedi veya doğrulanamadı. Ağ/proxy engelini kontrol edin; güvenlik için SHA-256 kontrolü devre dışı bırakılmadı.'
    }
    Remove-Item -LiteralPath $nsisRoot -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $nsisRoot | Out-Null
    Write-Host 'NSIS yalnızca derleme bilgisayarına sessizce kuruluyor...' -ForegroundColor Cyan
    $installerProcess = Start-Process -FilePath $nsisSetup -ArgumentList @('/S', ('/D="' + $nsisRoot + '"')) -Wait -PassThru
    if ($installerProcess.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $makensis)) {
      throw "NSIS sessiz kurulum başarısız oldu (çıkış kodu: $($installerProcess.ExitCode))."
    }
    Remove-Item -LiteralPath $nsisSetup -Force -ErrorAction SilentlyContinue
  }
}
if (-not (Test-Path $makensis)) { throw 'NSIS komut satırı derleyicisi bulunamadı.' }

Write-Host 'Bağımlılıklar yükleniyor...' -ForegroundColor Cyan
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Write-Host 'Otomatik testler çalıştırılıyor...' -ForegroundColor Cyan
python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw 'Testler gecmedi; kurulum EXE dosyasi uretilmedi.' }
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if ($nodeCmd) {
  node --check ui\app.js
  if ($LASTEXITCODE -ne 0) { throw 'Ana arayüz JavaScript sözdizim kontrolü başarısız.' }
  node --check ui\first_party_tools.js
  if ($LASTEXITCODE -ne 0) { throw 'Özgün yerel araçlar JavaScript sözdizim kontrolü başarısız.' }
  node --check ui\stereo_scope.js
  if ($LASTEXITCODE -ne 0) { throw 'Stereo Vectorscope JavaScript sözdizim kontrolü başarısız.' }
  node --check tests\test_first_party_tools.js
  if ($LASTEXITCODE -ne 0) { throw 'Yerel araç test dosyası sözdizim kontrolü başarısız.' }
  node tests\test_first_party_tools.js
  if ($LASTEXITCODE -ne 0) { throw 'Yerel araç çalışma zamanı testleri başarısız.' }
} else {
  Write-Host 'Node.js bulunamadı; ayrı Node kurulumu istemeyen Python test paketiyle devam ediliyor.' -ForegroundColor Yellow
}

Remove-Item -Recurse -Force -ErrorAction SilentlyContinue build, dist
New-Item -ItemType Directory -Force -Path 'build\payload','dist','website_release' | Out-Null
$sep = [IO.Path]::PathSeparator
$arguments = @(
  '-m','PyInstaller','--noconfirm','--clean','--onedir','--windowed','--contents-directory','_internal',
  '--workpath','build\pyinstaller','--distpath','build\payload',
  '--name','StagepulseSesMerkezi','--icon','ui\assets\stagepulse.ico',
  '--collect-all','webview','--collect-all','pythonnet','--collect-all','clr_loader',
  '--collect-all','numpy','--collect-all','sounddevice','--collect-all','_sounddevice_data',
  '--hidden-import','webview.platforms.edgechromium','--hidden-import','cryptography.hazmat.primitives.ciphers.aead',
  '--add-data',"ui${sep}ui",'--add-data',"araclar${sep}araclar",'--add-data',"egitim_paketleri${sep}egitim_paketleri",'--add-data',"references${sep}references"
)
$studentDocs = @(
 '00_BASLANGIC_TR.md','01_CANLI_SES_IS_AKISI_TR.md','02_PA_ARRAY_SUB_HIZALAMA_TR.md',
 '03_RF_KABLOSUZ_SISTEM_TR.md','04_SES_KALITE_KONTROL_TR.md','05_KONUSMA_KAYDI_HAZIRLIK_TR.md',
 '06_YAPAY_ZEKA_ISTEMLERI_TR.md','07_GURULTU_YALITIM_RAPORU_TR.md','08_SES_AI_ARASTIRMA_REHBERI_TR.md',
 '09_API_GIZLILIK_TR.md','10_MUZIK_PRODUKSIYONU_VE_OGRENME_TR.md'
)
foreach ($doc in $studentDocs) {
  $docPath = Join-Path $PSScriptRoot (Join-Path 'docs' $doc)
  if (-not (Test-Path $docPath)) { throw "Öğrenci eğitim belgesi eksik: $doc" }
  $arguments += @('--add-data',"docs\$doc${sep}docs")
}
$arguments += 'Merkez.py'
Write-Host 'Uygulama klasör paketi ara dizinde derleniyor...' -ForegroundColor Cyan
python @arguments
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller uygulama paketi oluşturamadı.' }
$payload = (Resolve-Path 'build\payload\StagepulseSesMerkezi').Path
$payloadExe = Join-Path $payload 'StagepulseSesMerkezi.exe'
if (-not (Test-Path -LiteralPath $payloadExe)) { throw 'PyInstaller klasör paketinde uygulama EXE dosyası bulunamadı.' }
$setupName = "StagepulseSesMerkezi-Kurulum-$version.exe"
$setupPath = (Join-Path (Resolve-Path 'dist').Path $setupName)
Write-Host 'Tek kurulum dosyası oluşturuluyor...' -ForegroundColor Cyan
& $makensis "/DVERSION=$version" "/DAPP_PAYLOAD=$payload" "/DWEBVIEW2_INSTALLER=$webview" "/DOUTPUT_PATH=$setupPath" (Join-Path $PSScriptRoot 'setup\StagepulseSesMerkezi.nsi')
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $setupPath)) { throw 'NSIS tek kurulum EXE dosyasini olusturamadi.' }

# Only the installer is placed in dist; intermediate application EXE is kept out of delivery.
if ((Get-ChildItem -LiteralPath 'dist' -Filter '*.exe' -File).Count -ne 1) { throw 'dist klasöründe tam olarak bir EXE bulunmalıdır.' }
$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $setupPath).Hash.ToLowerInvariant()
$manifest = [ordered]@{
  version = $version
  url = "https://stagepulse.com.tr/downloads/ses-merkezi/$setupName"
  sha256 = $hash
  notes = 'Stagepulse logolu tek kurulum; lisanssız yerel demo, üç konsol eğitim paketi, şifreli profiller ve manuel satış/ödeme kayıtları.'
  published_at = (Get-Date).ToUniversalTime().ToString('o')
}
$manifestPath = Join-Path $PSScriptRoot 'website_release\latest.json'
$manifestJson = $manifest | ConvertTo-Json -Depth 4
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($manifestPath, $manifestJson + [Environment]::NewLine, $utf8NoBom)
@"
Kurulum EXE: $setupPath
SHA-256: $hash
Güncelleme bildirimi: $manifestPath

Yayın için EXE'yi ve latest.json dosyasını şu konumlara yükleyin:
https://stagepulse.com.tr/downloads/ses-merkezi/$setupName
https://stagepulse.com.tr/downloads/ses-merkezi/latest.json
"@ | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'website_release\YAYIN_KONTROL_TR.txt') -Encoding UTF8
Get-FileHash -Algorithm SHA256 -LiteralPath $setupPath | Format-List
# MSIX needs the same tested PyInstaller payload. Preserve only that payload and the
# Microsoft-signed WebView2 bootstrapper when the caller explicitly requests it.
if ($env:STAGEPULSE_KEEP_PAYLOAD -eq '1') {
  $msixSupport = Join-Path 'build' 'msix-support'
  New-Item -ItemType Directory -Force -Path $msixSupport | Out-Null
  Copy-Item -LiteralPath $webview -Destination (Join-Path $msixSupport 'MicrosoftEdgeWebView2RuntimeInstallerX64.exe') -Force
  Remove-Item -Recurse -Force -ErrorAction SilentlyContinue 'build\pyinstaller'
  Write-Host 'MSIX payload ve WebView2 yükleyicisi korundu.' -ForegroundColor Green
} else {
  Remove-Item -Recurse -Force -ErrorAction SilentlyContinue 'build'
}
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue 'build_support'
if ((Get-ChildItem -LiteralPath 'dist' -Filter '*.exe' -File).Count -ne 1) { throw 'Son temizlikten sonra dist klasorunde tam olarak bir kurulum EXE dosyasi bulunmalidir.' }
Write-Host "BAŞARILI: tek dağıtım dosyası $setupPath" -ForegroundColor Green
Write-Host 'Son kullanici yalnizca kurulum EXE dosyasini calistirir; Python/CMD/ayri arac EXE dosyasi gerekmez.' -ForegroundColor Green
Write-Host 'Ara uygulama paketi ve derleme araclari temizlendi; dist icinde yalnizca Setup.exe kaldi.' -ForegroundColor Green
Write-Host 'İmzalama sertifikası yapılandırılmadığı için SmartScreen uyarısı görülebilir.' -ForegroundColor Yellow

# Create a student-ready ZIP containing exactly one file: the friendly setup EXE.
$deliveryDir = Join-Path $PSScriptRoot 'ogrenciye_gonder'
New-Item -ItemType Directory -Force -Path $deliveryDir | Out-Null
$studentSetupName = 'Stagepulse_Kurulum.exe'
$studentSetupPath = Join-Path $deliveryDir $studentSetupName
Copy-Item -LiteralPath $setupPath -Destination $studentSetupPath -Force
$studentZip = Join-Path $deliveryDir ("Stagepulse_Ogrenci_Kurulum_$version.zip")
Compress-Archive -LiteralPath $studentSetupPath -DestinationPath $studentZip -CompressionLevel Optimal -Force
Remove-Item -LiteralPath $studentSetupPath -Force
$zipCheck = [System.IO.Compression.ZipFile]::OpenRead($studentZip)
try {
  if ($zipCheck.Entries.Count -ne 1 -or $zipCheck.Entries[0].Name -ne $studentSetupName) { throw 'Öğrenci ZIP dosyası yalnızca Stagepulse_Kurulum.exe içermelidir.' }
} finally { $zipCheck.Dispose() }
Write-Host "OGRENCIYE GONDERILECEK ZIP: $studentZip" -ForegroundColor Green
