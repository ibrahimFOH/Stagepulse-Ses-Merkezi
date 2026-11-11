param(
    [string]$PayloadPath = '',
    [string]$OutputDirectory = '',
    [string]$CertificatePath = '',
    [string]$CertificatePassword = '',
    [switch]$StoreSubmission
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

$identityName = if ($StoreSubmission) { 'stagepulse.stagepulsesesmerkezi' } else { 'Stagepulse.SesMerkezi' }
$identityPublisher = if ($StoreSubmission) { 'CN=8CD6B337-E6A4-4EAB-B0B3-AA17F70913DD' } else { 'CN=Stagepulse' }
$publisherDisplayName = 'stagepulse'
$signingCert = $null
$securePassword = $null
if (-not $StoreSubmission) {
    if ($CertificatePassword) {
        $securePassword = ConvertTo-SecureString -String $CertificatePassword -AsPlainText -Force
    } else {
        $securePassword = Read-Host 'MSIX PFX parolasını girin veya yeni sertifika için belirleyin' -AsSecureString
    }
    if (-not $securePassword -or $securePassword.Length -lt 12) { throw 'PFX parolası en az 12 karakter olmalıdır.' }
    if (-not (Test-Path -LiteralPath $CertificatePath)) {
        & (Join-Path $root 'MSIX_SERTIFIKA_OLUSTUR.ps1') -Password $securePassword
    }
    if (-not (Test-Path -LiteralPath $CertificatePath)) { throw "MSIX imza sertifikası bulunamadı: $CertificatePath" }
    $pfxData = Get-PfxData -FilePath $CertificatePath -Password $securePassword
    $signingCert = @($pfxData.EndEntityCertificates)[0]
    if ($signingCert.Subject -ne $identityPublisher) { throw "Sertifika Publisher eşleşmiyor. Beklenen $identityPublisher, bulunan: $($signingCert.Subject)" }
}

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
  <Identity Name="$identityName" Publisher="$identityPublisher" Version="$version" ProcessorArchitecture="x64" />
  <Properties>
    <DisplayName>Stagepulse Ses Mühendisliği Merkezi</DisplayName>
    <PublisherDisplayName>$publisherDisplayName</PublisherDisplayName>
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
  <Capabilities><Capability Name="internetClient" /><rescap:Capability Name="runFullTrust" /><DeviceCapability Name="microphone" /></Capabilities>
</Package>
"@
$manifestPath = Join-Path $stage 'AppxManifest.xml'
[System.IO.File]::WriteAllText($manifestPath, $manifest + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))

New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$packageName = if ($StoreSubmission) {
    "Stagepulse-Ses-Merkezi-Store-$($version -replace '\.0$','').msix"
} else {
    "Stagepulse-Ses-Merkezi-MSIX-$($version -replace '\.0$','').msix"
}
$packagePath = Join-Path $OutputDirectory $packageName
& $makeAppx.FullName pack /o /h SHA256 /d $stage /p $packagePath
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $packagePath)) { throw "MakeAppx MSIX paketi oluşturamadı. Çıkış kodu: $LASTEXITCODE" }

if ($StoreSubmission) {
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $packagePath).Hash.ToLowerInvariant()
    Set-Content -LiteralPath "$($packagePath).sha256" -Value "$hash  $packageName" -Encoding ascii -NoNewline
    Write-Host "STORE MSIX HAZIR (imzasız; Microsoft Store imzalayacak): $packagePath" -ForegroundColor Green
    Write-Host "Identity: $identityName"
    Write-Host "Publisher: $identityPublisher"
    Write-Host "PublisherDisplayName: $publisherDisplayName"
    Write-Host "SHA-256: $hash"
    return
}

$cerPath = Join-Path $OutputDirectory 'Stagepulse-MSIX-Signing.cer'
[System.IO.File]::WriteAllBytes($cerPath, $signingCert.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert))
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
try { $plainPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
$signArgs = @('sign','/fd','SHA256','/a','/f',$CertificatePath,'/p',$plainPassword,'/tr','http://timestamp.digicert.com','/td','SHA256',$packagePath)
& $signTool.FullName @signArgs
if ($LASTEXITCODE -ne 0) { throw "SignTool MSIX imzalayamadı. Çıkış kodu: $LASTEXITCODE" }
if ($signingCert.Subject -eq $signingCert.Issuer) {
    $principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Kendinden imzalı MSIX sertifikasını güvenilir kılmak için PowerShell Yönetici olarak çalıştırılmalıdır.'
    }
    Import-Certificate -FilePath $cerPath -CertStoreLocation 'Cert:\LocalMachine\TrustedPeople' | Out-Null
}
$verifyOutput = (& $signTool.FullName verify /pa /v $packagePath 2>&1 | Out-String)
$verifyExit = $LASTEXITCODE
if ($verifyExit -ne 0) {
    $selfSignedTrustOnly = ($signingCert.Subject -eq $signingCert.Issuer) -and
        ($verifyOutput -match '0x800B0109|A certificate chain processed, but terminated in a root certificate which is not trusted') -and
        $verifyOutput.Contains($signingCert.Subject)
    if (-not $selfSignedTrustOnly) {
        throw "MSIX imza doğrulaması başarısız oldu: $verifyOutput"
    }
    Write-Warning 'Self-signed sertifikanın zincir güveni SignTool tarafından varsayılan olarak kabul edilmedi. Paket güvenini, sertifika TrustedPeople deposundayken Add-AppxPackage kurulumu doğrular.'
} else {
    Write-Host 'MSIX imza doğrulaması başarılı.' -ForegroundColor Green
}
$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $packagePath).Hash.ToLowerInvariant()
Set-Content -LiteralPath "${packagePath}.sha256" -Value "$hash  $packageName" -Encoding ascii -NoNewline
Write-Host ''
Write-Host "MSIX BAŞARILI: $packagePath" -ForegroundColor Green
Write-Host "SHA-256: $hash"
Write-Host "Sertifika: $cerPath"
Write-Host 'WebView2 Runtime yükleyicisi paket içine alındı.' -ForegroundColor Green
