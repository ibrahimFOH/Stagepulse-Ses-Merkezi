@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
echo Stagepulse Ses Muhendisligi Merkezi - tek kurulum EXE derleme
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0EXE_OLUSTUR.ps1"
if errorlevel 1 (
  echo.
  echo DERLEME BASARISIZ. Yukaridaki hatayi kontrol edin.
  pause
  exit /b 1
)
echo.
echo Derleme tamamlandi. Dagitim klasorunde tek kurulum EXE dosyasi var: dist
pause
