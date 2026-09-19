# Package Telegram Desktop into a standalone installer for end users
$ErrorActionPreference = "Stop"

$repoRoot = $PSScriptRoot
$releaseDir = Join-Path $repoRoot "out\Debug"
$exePath = Join-Path $releaseDir "Telegram.exe"
$d3dPath = Join-Path $releaseDir "modules\x64\d3d\d3dcompiler_47.dll"
$issPath = Join-Path $repoRoot "package_installer.iss"

# Locate Inno Setup Compiler (ISCC.exe)
$isccCandidates = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 7\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 5\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)

$iscc = $null
foreach ($candidate in $isccCandidates) {
    if (Test-Path $candidate) {
        $iscc = $candidate
        break
    }
}

if (-not $iscc) {
    $cmd = Get-Command iscc.exe -ErrorAction SilentlyContinue
    if ($cmd) { $iscc = $cmd.Source }
}

if (-not $iscc) {
    Write-Error "Inno Setup compiler (ISCC.exe) not found. Please ensure Inno Setup is installed."
    exit 1
}

# Verify built binaries exist
if (-not (Test-Path $exePath)) {
    Write-Error "Telegram.exe not found at $exePath. Please build Telegram first!"
    exit 1
}

if (-not (Test-Path $d3dPath)) {
    Write-Warning "d3dcompiler_47.dll not found at $d3dPath."
}

Write-Host "Compiling standalone installer for end users..." -ForegroundColor Cyan
Write-Host "Using compiler: $iscc" -ForegroundColor Gray
Write-Host "Source binary: $exePath" -ForegroundColor Gray

& $iscc -ns "$issPath"

$outputInstaller = Join-Path $releaseDir "TelegramSetup.exe"
if (Test-Path $outputInstaller) {
    $sizeMB = [math]::Round(((Get-Item $outputInstaller).Length / 1MB), 2)
    Write-Host "`nSuccessfully created installer!" -ForegroundColor Green
    Write-Host "Installer file: $outputInstaller" -ForegroundColor Yellow
    Write-Host "Installer size: $sizeMB MB" -ForegroundColor Yellow
    Write-Host "Ready to share with end users! Double-clicking it installs and launches Telegram with no prompts.`n" -ForegroundColor Green
} else {
    Write-Error "Installer compilation completed but TelegramSetup.exe was not found."
    exit 1
}
