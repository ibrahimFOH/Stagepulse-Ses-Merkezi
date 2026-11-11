$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Sertifika güvenini LocalMachine deposuna kurmak için PowerShell Yönetici olarak çalıştırılmalıdır.'
}
$certDir = Join-Path $root 'msix\cert'
$pfxPath = Join-Path $certDir 'Stagepulse-MSIX.pfx'
$cerPath = Join-Path $certDir 'Stagepulse-MSIX.cer'
if (Test-Path -LiteralPath $pfxPath) { throw "Sertifika zaten var: $pfxPath. Üzerine yazılmadı." }
New-Item -ItemType Directory -Force -Path $certDir | Out-Null
Write-Host 'Stagepulse MSIX geliştirme sertifikası oluşturuluyor.' -ForegroundColor Cyan
Write-Host 'Bu sertifika yerel test içindir. Genel dağıtımda güvenilir kod imzalama sertifikası gerekir.' -ForegroundColor Yellow
$password = Read-Host 'PFX için güçlü bir parola belirleyin (GitHub secret olarak da kaydedilecek)' -AsSecureString
if (-not $password -or $password.Length -lt 12) { throw 'PFX parolası en az 12 karakter olmalıdır.' }
$cert = New-SelfSignedCertificate -Type Custom -Subject 'CN=Stagepulse' -FriendlyName 'Stagepulse MSIX Package Signing' -CertStoreLocation 'Cert:\CurrentUser\My' -KeyAlgorithm RSA -KeyLength 3072 -HashAlgorithm SHA256 -KeyExportPolicy Exportable -KeyUsage DigitalSignature -TextExtension @('2.5.29.37={text}1.3.6.1.5.5.7.3.3','2.5.29.19={text}') -NotAfter (Get-Date).AddYears(5)
Export-PfxCertificate -Cert $cert -FilePath $pfxPath -Password $password | Out-Null
Export-Certificate -Cert $cert -FilePath $cerPath -Type CERT | Out-Null
Import-Certificate -FilePath $cerPath -CertStoreLocation 'Cert:\LocalMachine\TrustedPeople' | Out-Null
Write-Host ''
Write-Host 'SERTİFİKA HAZIR' -ForegroundColor Green
Write-Host "PFX: $pfxPath"
Write-Host "CER: $cerPath"
Write-Host "Publisher: $($cert.Subject)"
Write-Host "SHA-256: $((Get-FileHash -Algorithm SHA256 -LiteralPath $cerPath).Hash)"
Write-Host ''
Write-Host 'Stagepulse-Releases deposunda şu GitHub Actions secrets değerlerini tanımlayın:' -ForegroundColor Cyan
Write-Host 'MSIX_SIGNING_PFX_BASE64 = PFX dosyasının Base64 içeriği'
Write-Host 'MSIX_SIGNING_PFX_PASSWORD = belirlediğiniz PFX parolası'
Write-Host "[Convert]::ToBase64String([IO.File]::ReadAllBytes('$pfxPath')) | Set-Clipboard"
