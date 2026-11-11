param(
    [string]$PayloadPath = '',
    [string]$OutputDirectory = '',
    [string]$CertificatePath = '',
    [string]$CertificatePassword = ''
)
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
Set-Location $root
if (-not $OutputDirectory) { $OutputDirectory = Join-Path $root 'dist' }
if (-not $PayloadPath) { $PayloadPath = Join-Path $root 'build\payload\StagepulseSesMerkezi' }
if (-not $CertificatePath) { $CertificatePath = Join-Path $root 'msix\cert\Stagepulse-MSIX.pfx' }
if (-not $CertificatePassword) { $CertificatePassword = $env:MSIX_SIGNING_PFX_PASSWORD }

if (-not (Test-Path -LiteralPath (Join-Path $PayloadPath 'StagepulseSesMerkezi.exe'))) {
    Write-Host 'Uygulama payload bulunamadı; mevcut EXE derleyicisi çalıştırılıyor...' -ForegroundColor Cyan
    $previousKeep = $env:STAGEPULSE_KEEP_PAYLOAD
    $env:STAGEPULSE_KEEP_PAYLOAD = '1'
    try {
        & (Join-Path $root 'EXE_OLUSTUR.ps1')
        if ($LASTEXITCODE -ne 0) { throw "EXE_OLUSTUR.ps1 başarısız oldu: $LASTEXITCODE" }
    } finally {
        if ($null -eq $previousKeep) { Remove-Item Env:STAGEPULSE_KEEP_PAYLOAD -ErrorAction SilentlyContinue }
        else { $env:STAGEPULSE_KEEP_PAYLOAD = $previousKeep }
    }
}
if (-not (Test-Path -LiteralPath (Join-Path $PayloadPath 'StagepulseSesMerkezi.exe'))) { throw "PyInstaller payload bulunamadı: $PayloadPath" }

$versionMatch = [regex]::Match((Get-Content -LiteralPath (Join-Path $root 'Merkez.py') -Raw), 'APP_VERSION\s*=\s*"([^"]+)"')
if (-not $versionMatch.Success -or $versionMatch.Groups[1].Value -notmatch '^\d+\.\d+\.\d+$') { throw 'Merkez.py içindeki APP_VERSION X.Y.Z biçiminde bulunamadı.' }
$version = $versionMatch.Groups[1].Value + '.0'

if (-not (Test-Path -LiteralPath $CertificatePath)) { & (Join-Path $root 'MSIX_SERTIFIKA_OLUSTUR.ps1') }
if (-not (Test-Path -LiteralPath $CertificatePath)) { throw "MSIX imza sertifikası bulunamadı: $CertificatePath" }
if (-not $CertificatePassword) { $securePassword = Read-Host 'MSIX PFX parolasını girin' -AsSecureString }
else { $securePassword = ConvertTo-SecureString -String $CertificatePassword -AsPlainText -Force }
$pfxData = Get-PfxData -FilePath $CertificatePath -Password $securePassword
$signingCert = @($pfxData.EndEntityCertificates)[0]
if ($signingCert.Subject -ne 'CN=Stagepulse') { throw "Sertifika Publisher eşleşmiyor. Beklenen CN=Stagepulse, bulunan: $($signingCert.Subject)" }

$sdkBin = Join-Path ([Environment]::GetEnvironmentVariable('ProgramFiles(x86)')) 'Windows Kits\10\bin'
$makeAppx = Get-ChildItem -Path $sdkBin -Filter MakeAppx.exe -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match '\\x64\\MakeAppx\.exe$' } | Sort-Object FullName -Descending | Select-Object -First 1
$signTool = Get-ChildItem -Path $sdkBin -Filter SignTool.exe -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match '\\x64\\SignTool\.exe$' } | Sort-Object FullName -Descending | Select-Object -First 1
if (-not $makeAppx -or -not $signTool) { throw 'Windows SDK MakeAppx.exe veya SignTool.exe bulunamadı. Windows 10/11 SDK kurulu olmalıdır.' }

$buildRoot = Join-Path $root 'build'
$stage = Join-Path $buildRoot 'msix-package'
$runtimeSource = Join-Path $buildRoot 'msix-support\MicrosoftEdgeWebView2RuntimeInstallerX64.exe'
$runtimeTarget = Join-Path $stage 'Runtime\MicrosoftEdgeWebView2RuntimeInstallerX64.exe'
$assets = Join-Path $stage 'Assets'
if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
New-Item -ItemType Directory -Force -Path $stage, $assets | Out-Null
Copy-Item -Path (Join-Path $PayloadPath '*') -Destination $stage -Recurse -Force
if (-not (Test-Path -LiteralPath $runtimeSource)) { throw "WebView2 yükleyicisi bulunamadı: $runtimeSource. EXE_OLUSTUR.ps1 STAGEPULSE_KEEP_PAYLOAD=1 ile çalıştırılmalı." }
New-Item -ItemType Directory -Force -Path (Split-Path $runtimeTarget) | Out-Null
Copy-Item -LiteralPath $runtimeSource -Destination $runtimeTarget -Force
$sig = Get-AuthenticodeSignature -LiteralPath $runtimeTarget
if ($sig.Status -ne 'Valid' -or $sig.SignerCertificate.Subject -notmatch 'Microsoft') { throw 'WebView2 yükleyicisinin Microsoft imzası doğrulanamadı.' }

Add-Type -AssemblyName System.Drawing
$sourceIcon = Join-Path $root 'ui\assets\stagepulse-icon-256.png'
if (-not (Test-Path -LiteralPath $sourceIcon)) { throw "MSIX kaynak simgesi bulunamadı: $sourceIcon" }
$image = [System.Drawing.Image]::FromFile($sourceIcon)
try {
    foreach ($size in @(44, 50, 150)) {
        $bitmap = New-Object System.Drawing.Bitmap($size, $size)
        try {
            $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
            try {
                $graphics.Clear([System.Drawing.Color]::FromArgb(13, 16, 21))
                $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
                $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
                $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
                $graphics.DrawImage($image, 0, 0, $size, $size)
            } finally { $graphics.Dispose() }
            $name = if ($size -eq 44) { 'Square44x44Logo.png' } elseif ($size -eq 150) { 'Square150x150Logo.png' } else { 'StoreLogo.png' }
            $bitmap.Save((Join-Path $assets $name), [System.Drawing.Imaging.ImageFormat]::Png)
        } finally { $bitmap.Dispose() }
    }
} finally { $image.Dispose() }

$manifest = @"
<?xml version="1.0" encoding="utf-8"?>
<Package xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
         xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
         xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities"
         IgnorableNamespaces="uap rescap">
  <Identity Name="Stagepulse.SesMerkezi" Publisher="CN=Stagepulse" Version="$version" ProcessorArchitecture="x64" />
  <Properties>
    <DisplayName>Stagepulse Ses Mühendisliği Merkezi</DisplayName>
    <PublisherDisplayName>Stagepulse</PublisherDisplayName>
    <Description>Stagepulse ses mühendisliği, ölçüm ve eğitim araçları.</Description>
    <Logo>Assets\StoreLogo.png</Logo>
  </Properties>
  <Dependencies>
    <TargetDeviceFamily Name="Windows.Desktop" MinVersion="10.0.17763.0" MaxVersionTested="10.0.26100.0" />
  </Dependencies>
  <Resources><Resource Language="tr-TR" /></Resources>
  <Applications>
    <Application Id="StagepulseSesMerkezi" Executable="StagepulseSesMerkezi.exe" EntryPoint="Windows.FullTrustApplication">
      <uap:VisualElements DisplayName="Stagepulse Ses Merkezi" Description="Stagepulse Ses Mühendisliği Merkezi" BackgroundColor="#0D1015" Square150x150Logo="Assets\Square150x150Logo.png" Square44x44Logo="Assets\Square44x44Logo.png" />
    </Application>
  </Applications>
  <Capabilities><rescap:Capability Name="runFullTrust" /></Capabilities>
</Package>
"@
$manifestPath = Join-Path $stage 'AppxManifest.xml'
[System.IO.File]::WriteAllText($manifestPath, $manifest + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))

New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$packageName = "Stagepulse-Ses-Merkezi-MSIX-$($version -replace '\.0$','').msix"
$packagePath = Join-Path $OutputDirectory $packageName
& $makeAppx.FullName pack /o /h SHA256 /d $stage /p $packagePath
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $packagePath)) { throw "MakeAppx MSIX paketi oluşturamadı. Çıkış kodu: $LASTEXITCODE" }

$cerPath = Join-Path $OutputDirectory 'Stagepulse-MSIX-Signing.cer'
[System.IO.File]::WriteAllBytes($cerPath, $signingCert.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert))
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
try { $plainPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
$signArgs = @('sign','/fd','SHA256','/a','/f',$CertificatePath,'/p',$plainPassword,'/tr','http://timestamp.digicert.com','/td','SHA256',$packagePath)
& $signTool.FullName @signArgs
if ($LASTEXITCODE -ne 0) { throw "SignTool MSIX imzalayamadı. Çıkış kodu: $LASTEXITCODE" }
Import-Certificate -FilePath $cerPath -CertStoreLocation 'Cert:\CurrentUser\TrustedPeople' | Out-Null
& $signTool.FullName verify /pa /v $packagePath
if ($LASTEXITCODE -ne 0) { throw "MSIX imza doğrulaması başarısız. Çıkış kodu: $LASTEXITCODE" }
$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $packagePath).Hash.ToLowerInvariant()
Set-Content -LiteralPath "${packagePath}.sha256" -Value "$hash  $packageName" -Encoding ascii -NoNewline
Write-Host ''
Write-Host "MSIX BAŞARILI: $packagePath" -ForegroundColor Green
Write-Host "SHA-256: $hash"
Write-Host "Sertifika: $cerPath"
Write-Host 'WebView2 Runtime yükleyicisi paket içine alındı.' -ForegroundColor Green
