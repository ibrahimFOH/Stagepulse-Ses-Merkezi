from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_customer_delivers_one_setup_exe_and_shortcuts():
    script = (ROOT / "EXE_OLUSTUR.ps1").read_text("utf-8")
    nsi = (ROOT / "setup" / "StagepulseSesMerkezi.nsi").read_text("utf-8")
    bat = (ROOT / "EXE_OLUSTUR.bat").read_text("utf-8")
    assert "StagepulseSesMerkezi-Kurulum-$version.exe" in script
    assert "dist klasöründe tam olarak bir EXE" in script
    assert "CreateShortcut \"$DESKTOP\\Stagepulse Ses Merkezi.lnk\"" in nsi
    assert "CreateShortcut \"$SMPROGRAMS\\Stagepulse\\Stagepulse Ses Merkezi.lnk\"" in nsi
    assert "RequestExecutionLevel user" in nsi
    assert "InstallDir \"$LOCALAPPDATA\\Programs\\Stagepulse\\SesMerkezi\"" in nsi
    assert "EXE_OLUSTUR.ps1" in bat


def test_release_manifest_is_generated_not_faked():
    script = (ROOT / "EXE_OLUSTUR.ps1").read_text("utf-8")
    assert "Get-FileHash -Algorithm SHA256 -LiteralPath $setupPath" in script
    assert "latest.json" in script
    assert "https://stagepulse.com.tr/downloads/ses-merkezi/" in script


def test_successful_build_removes_intermediate_exes_and_build_tools():
    from pathlib import Path
    script = (Path(__file__).resolve().parents[1] / "EXE_OLUSTUR.ps1").read_text("utf-8")
    assert "Remove-Item -Recurse -Force -ErrorAction SilentlyContinue 'build'" in script
    assert "build_support\\MicrosoftEdgeWebView2RuntimeInstallerX64.exe" in script
    assert "Son temizlikten sonra dist klasorunde tam olarak bir kurulum EXE" in script


def test_nsis_download_uses_pinned_hash_and_fallback_instead_of_disabling_validation():
    script = (ROOT / "EXE_OLUSTUR.ps1").read_text("utf-8")
    assert "ba63dffc4410ee89193e1cb5a41989991bd77c61068da17e3156d136b7b0b3d8" in script
    assert "db9a1038bbc0e53fef24f423fd609979bd578e942f1be1198db186d1c42652a3" in script
    assert "https://sourceforge.net/projects/nsis/files/NSIS%203/3.13/nsis-3.13.zip/download" in script
    assert "https://sourceforge.net/projects/nsis/files/NSIS%203/3.13/nsis-3.13-setup.exe/download" in script
    assert "PK başlığı bulunamadı" in script
    assert "SHA-256 kontrolü devre dışı bırakılmadı" in script
    assert "Join-Path $buildSupport 'nsis-3.13-setup.exe'" in script


def test_powershell_build_script_has_utf8_bom_for_windows_powershell_51():
    script = (ROOT / "EXE_OLUSTUR.ps1").read_bytes()
    assert script.startswith(b"\xef\xbb\xbf")


def test_powershell_script_avoids_smart_quotes_that_break_single_quoted_strings():
    script = (ROOT / "EXE_OLUSTUR.ps1").read_text("utf-8-sig")
    assert not any(ch in script for ch in "’‘“”")
    assert "Testler gecmedi; kurulum EXE dosyasi uretilmedi." in script
    assert "NSIS tek kurulum EXE dosyasini olusturamadi." in script

def test_nsis_fallback_quotes_install_path_with_spaces():
    script = (ROOT / "EXE_OLUSTUR.ps1").read_text("utf-8-sig")
    assert r'''('/D="' + $nsisRoot + '"')''' in script


def test_setup_installs_webview_only_if_missing_and_copies_complete_onedir_payload():
    nsi = (ROOT / "setup" / "StagepulseSesMerkezi.nsi").read_text("utf-8")
    ps = (ROOT / "EXE_OLUSTUR.ps1").read_text("utf-8-sig")
    assert "Function CheckWebView2Runtime" in nsi
    assert 'File /oname=${WEBVIEW2_FILE} "${WEBVIEW2_INSTALLER}"' in nsi
    assert 'ExecWait' in nsi and '/silent /install' in nsi
    assert 'File /r "${APP_PAYLOAD}\\*"' in nsi
    assert 'Delete "$INSTDIR\\Uninstall.exe"' in nsi
    assert 'RMDir /r "$INSTDIR"' in nsi
    assert 'File /oname=${PRODUCT_EXE} "${APP_PAYLOAD}"' not in nsi
    assert "WEBVIEW2_INSTALLER=$webview" in ps
    assert "--onedir" in ps and "--onefile" not in ps
    assert "Resolve-Path 'build\\payload\\StagepulseSesMerkezi'" in ps
    assert "Join-Path $payload 'StagepulseSesMerkezi.exe'" in ps
    assert not any("--add-data" in line and "MicrosoftEdgeWebView2RuntimeInstallerX64.exe" in line for line in ps.splitlines())


def test_build_creates_student_zip_with_only_setup_exe_after_tests():
    ps = (ROOT / "EXE_OLUSTUR.ps1").read_text("utf-8-sig")
    assert "ogrenciye_gonder" in ps
    assert "Stagepulse_Kurulum.exe" in ps
    assert "Compress-Archive -LiteralPath $studentSetupPath" in ps
    assert "$zipCheck.Entries.Count -ne 1" in ps
    assert "Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $PSScriptRoot 'ogrenciye_gonder')" in ps
