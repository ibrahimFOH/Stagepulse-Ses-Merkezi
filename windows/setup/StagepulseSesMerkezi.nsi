Unicode true
!pragma codepage 65001
!include "MUI2.nsh"
!include "LogicLib.nsh"

!ifndef VERSION
  !define VERSION "4.0.6"
!endif
!ifndef APP_PAYLOAD
  !error "APP_PAYLOAD tanımlanmamış. EXE_OLUSTUR.ps1 üzerinden çalıştırın."
!endif
!ifndef WEBVIEW2_INSTALLER
  !error "WEBVIEW2_INSTALLER tanımlanmamış. Kurulum çevrimdışı WebView2 bileşenini içermelidir."
!endif
!ifndef OUTPUT_PATH
  !define OUTPUT_PATH "dist\StagepulseSesMerkezi-Kurulum-${VERSION}.exe"
!endif

!define PRODUCT_NAME "Stagepulse Ses Mühendisliği Merkezi"
!define PRODUCT_EXE "StagepulseSesMerkezi.exe"
!define WEBVIEW2_FILE "MicrosoftEdgeWebView2RuntimeInstallerX64.exe"
!define UNINSTALL_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\StagepulseSesMerkezi"

Name "${PRODUCT_NAME} ${VERSION}"
Caption "${PRODUCT_NAME} Kurulumu"
OutFile "${OUTPUT_PATH}"
InstallDir "$LOCALAPPDATA\Programs\Stagepulse\SesMerkezi"
InstallDirRegKey HKCU "${UNINSTALL_KEY}" "InstallLocation"
RequestExecutionLevel user
SetCompressor /SOLID lzma
SetCompressorDictSize 32
ShowInstDetails nevershow
ShowUninstDetails nevershow
XPStyle on

VIProductVersion "${VERSION}.0"
VIAddVersionKey /LANG=1055 "ProductName" "${PRODUCT_NAME}"
VIAddVersionKey /LANG=1055 "FileDescription" "Stagepulse Ses Mühendisliği Merkezi kurulumu"
VIAddVersionKey /LANG=1055 "CompanyName" "Stagepulse"
VIAddVersionKey /LANG=1055 "LegalCopyright" "Copyright Stagepulse"
VIAddVersionKey /LANG=1055 "ProductVersion" "${VERSION}"

Var WebView2Installed
Var WebView2Version
Var WebView2ExitCode

; Match the WebView2 detection used by Merkez.py. Check 64-bit and 32-bit registry views.
Function CheckWebView2Runtime
  StrCpy $WebView2Installed "0"
  StrCpy $WebView2Version ""
  SetRegView 64
  ClearErrors
  ReadRegStr $WebView2Version HKLM "SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}" "pv"
  ${IfNot} ${Errors}
    ${If} $WebView2Version != ""
      ${If} $WebView2Version != "0.0.0.0"
        StrCpy $WebView2Installed "1"
      ${EndIf}
    ${EndIf}
  ${EndIf}
  ${If} $WebView2Installed != "1"
    ClearErrors
    ReadRegStr $WebView2Version HKCU "Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}" "pv"
    ${IfNot} ${Errors}
      ${If} $WebView2Version != ""
        ${If} $WebView2Version != "0.0.0.0"
          StrCpy $WebView2Installed "1"
        ${EndIf}
      ${EndIf}
    ${EndIf}
  ${EndIf}
  ${If} $WebView2Installed != "1"
    SetRegView 32
    ClearErrors
    ReadRegStr $WebView2Version HKLM "SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}" "pv"
    ${IfNot} ${Errors}
      ${If} $WebView2Version != ""
        ${If} $WebView2Version != "0.0.0.0"
          StrCpy $WebView2Installed "1"
        ${EndIf}
      ${EndIf}
    ${EndIf}
    SetRegView 64
  ${EndIf}
FunctionEnd

!define MUI_ABORTWARNING
!define MUI_WELCOMEPAGE_TITLE "Stagepulse Ses Mühendisliği Merkezi"
!define MUI_WELCOMEPAGE_TEXT "Uygulama, öğrenci ders kitapları ve ses araçları tek kurulumda yüklenecek. Kurulum Python veya komut satırı gerektirmez.$\r$\n$\r$\nKurulum kullanıcı hesabınıza yapılır; yönetici izni istenmez."
!define MUI_FINISHPAGE_RUN "$INSTDIR\${PRODUCT_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "Stagepulse Ses Merkezi'ni şimdi aç"
!define MUI_FINISHPAGE_LINK "Stagepulse.com.tr destek sayfası"
!define MUI_FINISHPAGE_LINK_LOCATION "https://stagepulse.com.tr/iletisim.html"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "Turkish"

Function .onInit
  SetShellVarContext current
FunctionEnd

Section "Stagepulse Ses Merkezi" SEC_APP
  SectionIn RO
  SetShellVarContext current

  ; Install the runtime silently only when missing. The installer is extracted to a temp directory,
  ; never left beside the app. Microsoft documents /silent /install for per-user installs.
  Call CheckWebView2Runtime
  ${If} $WebView2Installed != "1"
    SetOutPath "$PLUGINSDIR"
    File /oname=${WEBVIEW2_FILE} "${WEBVIEW2_INSTALLER}"
    DetailPrint "Microsoft WebView2 Runtime denetleniyor ve gerekirse kuruluyor..."
    ExecWait '"$PLUGINSDIR\${WEBVIEW2_FILE}" /silent /install' $WebView2ExitCode
    ${If} $WebView2ExitCode != 0
      ${If} $WebView2ExitCode != 3010
        MessageBox MB_ICONSTOP|MB_OK "Microsoft WebView2 Runtime kurulamadı (kod: $WebView2ExitCode). Kurulum durduruldu."
        Abort
      ${EndIf}
    ${EndIf}
    Call CheckWebView2Runtime
    ${If} $WebView2Installed != "1"
      MessageBox MB_ICONSTOP|MB_OK "Microsoft WebView2 Runtime doğrulanamadı. Bilgisayarı yeniden başlatıp kurulumu tekrar deneyin."
      Abort
    ${EndIf}
  ${EndIf}

  SetOutPath "$INSTDIR"
  ; PyInstaller onedir output: EXE stays at $INSTDIR root, dependencies live in _internal.
  File /r "${APP_PAYLOAD}\*"

  CreateDirectory "$SMPROGRAMS\Stagepulse"
  CreateShortcut "$SMPROGRAMS\Stagepulse\Stagepulse Ses Merkezi.lnk" "$INSTDIR\${PRODUCT_EXE}" "" "$INSTDIR\${PRODUCT_EXE}" 0 SW_SHOWNORMAL
  CreateShortcut "$DESKTOP\Stagepulse Ses Merkezi.lnk" "$INSTDIR\${PRODUCT_EXE}" "" "$INSTDIR\${PRODUCT_EXE}" 0 SW_SHOWNORMAL

  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "Publisher" "Stagepulse"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayIcon" "$INSTDIR\${PRODUCT_EXE}"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "UninstallString" "$\"$INSTDIR\Uninstall.exe$\""
  WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoModify" 1
  WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoRepair" 1
  WriteRegDWORD HKCU "${UNINSTALL_KEY}" "EstimatedSize" 350000
SectionEnd

Section "Uninstall"
  SetShellVarContext current
  Delete "$DESKTOP\Stagepulse Ses Merkezi.lnk"
  Delete "$SMPROGRAMS\Stagepulse\Stagepulse Ses Merkezi.lnk"
  RMDir "$SMPROGRAMS\Stagepulse"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir /r "$INSTDIR"
  DeleteRegKey HKCU "${UNINSTALL_KEY}"
  ; Öğrenci profilleri ve lisans önbelleği kullanıcı verisi olarak korunur.
SectionEnd
