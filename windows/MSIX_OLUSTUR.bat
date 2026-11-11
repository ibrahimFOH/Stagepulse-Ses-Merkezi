@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

net session >nul 2>&1
if errorlevel 1 (
  echo MSIX derlemesi sertifika guvenini yuklemek icin Yonetici yetkisi ister.
  echo Bu dosyaya sag tiklayip "Yonetici olarak calistir" sec.
  pause
  exit /b 1
)

echo Stagepulse Ses Merkezi - MSIX derleme
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0MSIX_OLUSTUR.ps1"
if errorlevel 1 (
  echo.
  echo MSIX DERLEMESI BASARISIZ. Yukaridaki hatayi kontrol et.
  pause
  exit /b 1
)

echo.
echo MSIX ve SHA-256 dosyasi windows\dist klasorunde hazir.
pause
