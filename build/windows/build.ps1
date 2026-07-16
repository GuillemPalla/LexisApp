<#
.SYNOPSIS
    Builds the LexisApp Windows installer end-to-end, from a clean checkout
    to a finished LexisApp-Setup.exe.

.DESCRIPTION
    This is a reconstruction of the manual steps that originally produced
    the installer, turned into one repeatable script so the "python" folder
    and "launcher.exe" never have to be hand-built or hand-copied again.

    Steps:
      1. Download the embeddable Python runtime and unzip it into ./python
      2. Enable site-packages in that runtime (required for pip to work)
      3. Bootstrap pip into it, then install requirements.txt
      4. Run PyInstaller to build launcher.exe (icon baked in)
      5. Run the Inno Setup Compiler (ISCC.exe) against setup.iss

    ASSUMPTIONS (please confirm/adjust for your machine):
      - PyInstaller and Inno Setup 6 are already installed on THIS machine
        (the one running this script), separately from the embedded runtime
        that ships inside the installer. PyInstaller can live in your normal
        dev Python environment: `pip install pyinstaller`.
      - requirements.txt at the repo root lists every runtime dependency
        (textual, textual-serve, pystray, pillow, plus whatever the
        screens/ and tokenizers/ code needs - onnxruntime, numpy, etc.).
        Double-check it's complete before relying on this script.

.NOTES
    Run this from build/windows/, or anywhere - it resolves paths from its
    own location.
#>

$ErrorActionPreference = "Stop"

$WinDir  = $PSScriptRoot
$RepoRoot = Resolve-Path (Join-Path $WinDir "..\..")
$SrcDir  = Join-Path $RepoRoot "src"
$Requirements = Join-Path $RepoRoot "requirements.txt"

$PythonVersion = "3.12.2"
$PythonZipUrl  = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip"
$GetPipUrl     = "https://bootstrap.pypa.io/get-pip.py"

$PythonDir = Join-Path $WinDir "python"
$TmpDir    = Join-Path $WinDir "build_tmp"

Write-Host "== 1/5: Embedded Python runtime ==" -ForegroundColor Cyan
if (Test-Path $PythonDir) { Remove-Item $PythonDir -Recurse -Force }
New-Item -ItemType Directory -Path $PythonDir | Out-Null
New-Item -ItemType Directory -Path $TmpDir -Force | Out-Null

$zipPath = Join-Path $TmpDir "python-embed.zip"
Invoke-WebRequest -Uri $PythonZipUrl -OutFile $zipPath
Expand-Archive -Path $zipPath -DestinationPath $PythonDir -Force

Write-Host "== 2/5: Enabling site-packages in the embedded runtime ==" -ForegroundColor Cyan
# The embeddable distro ships with a ._pth file that disables 'site' by
# default, which also disables pip. Uncomment the "import site" line.
$pthFile = Get-ChildItem $PythonDir -Filter "python*._pth" | Select-Object -First 1
(Get-Content $pthFile.FullName) -replace '^#\s*import site', 'import site' |
    Set-Content $pthFile.FullName

Write-Host "== 3/5: Installing pip + dependencies into the embedded runtime ==" -ForegroundColor Cyan
$getPipPath = Join-Path $TmpDir "get-pip.py"
Invoke-WebRequest -Uri $GetPipUrl -OutFile $getPipPath
& "$PythonDir\python.exe" $getPipPath --no-warn-script-location

if (Test-Path $Requirements) {
    & "$PythonDir\python.exe" -m pip install --no-warn-script-location -r $Requirements
} else {
    Write-Warning "No requirements.txt found at $Requirements - skipping dependency install."
}

Write-Host "== 4/5: Building launcher.exe with PyInstaller ==" -ForegroundColor Cyan
# Uses whatever PyInstaller is on THIS machine's PATH, not the embedded runtime.
pyinstaller --onefile --noconsole `
    --icon "$SrcDir\icon.ico" `
    --name launcher `
    --distpath "$WinDir" `
    --workpath "$TmpDir\pyinstaller" `
    --specpath "$TmpDir" `
    "$WinDir\launcher.py"

Write-Host "== 5/5: Compiling the installer with Inno Setup ==" -ForegroundColor Cyan
$iscc = $null

$cmd = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue
if ($cmd) { $iscc = $cmd.Source }

if (-not $iscc) {
    # Try the common install locations across 32-bit/64-bit and version 6/7 builds.
    $candidates = @(
        "C:\Program Files\Inno Setup 7\ISCC.exe",
        "C:\Program Files (x86)\Inno Setup 7\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe",
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    )
    foreach ($path in $candidates) {
        if (Test-Path $path) { $iscc = $path; break }
    }
}

if (-not $iscc) {
    # Fall back to the registry keys Inno Setup's installer writes (checks both versions).
    $regPaths = @(
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 7_is1",
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 7_is1",
        "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 7_is1",
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1",
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1",
        "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1"
    )
    foreach ($regPath in $regPaths) {
        if (Test-Path $regPath) {
            $installLoc = (Get-ItemProperty -Path $regPath -ErrorAction SilentlyContinue).InstallLocation
            if ($installLoc) {
                $candidate = Join-Path $installLoc "ISCC.exe"
                if (Test-Path $candidate) { $iscc = $candidate; break }
            }
        }
    }
}

if (-not $iscc) {
    throw "ISCC.exe not found on PATH, in the standard Program Files locations, or in the registry. " + `
          "Find it manually with: Get-ChildItem 'C:\' -Filter ISCC.exe -Recurse -ErrorAction SilentlyContinue " + `
          "then either add its folder to PATH or hardcode the path in this script."
}

Write-Host "Using Inno Setup at: $iscc"
& $iscc "$WinDir\setup.iss"

Write-Host ""
Write-Host "Done. Installer at: $WinDir\Output\LexisApp-Setup.exe" -ForegroundColor Green