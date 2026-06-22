$ErrorActionPreference = "Stop"

$python = Get-Command py -ErrorAction SilentlyContinue
if ($python) {
    $pythonExe = "py"
    $pythonArgs = @("-3")
} else {
    $pythonExe = "python"
    $pythonArgs = @()
}

& $pythonExe @pythonArgs -m PyInstaller --version *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller is not installed."
    Write-Host "Install it with: python -m pip install pyinstaller"
    exit 1
}

& $pythonExe @pythonArgs -m PyInstaller `
    --onefile `
    --windowed `
    --name BatchArchiveExtractor `
    batch_extract_gui.py

Write-Host ""
Write-Host "Built: dist\BatchArchiveExtractor.exe"
Write-Host "Install 7-Zip if the target machine does not already have it:"
Write-Host "https://www.7-zip.org/"
