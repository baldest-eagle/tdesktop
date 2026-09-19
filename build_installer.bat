@echo off
:: =============================================================================
:: tdesktop — One-Click Installer Builder
:: =============================================================================
:: Just double-click this file to build the installer.
:: Supports optional argument: build_installer.bat [Debug|Release]
:: Default targets Debug if present, or Release if only Release exists.
:: =============================================================================

title Building tdesktop Installer...

echo.
echo ===============================================================================
echo   Building tdesktop Installer
echo ===============================================================================
echo.

:: Check for Inno Setup
set "ISCC_PATH="

for %%p in (
    "%LOCALAPPDATA%\Programs\Inno Setup 7\ISCC.exe"
    "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
    "%ProgramFiles(x86)%\Inno Setup 7\ISCC.exe"
    "%ProgramFiles%\Inno Setup 7\ISCC.exe"
    "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
    "%ProgramFiles%\Inno Setup 6\ISCC.exe"
) do (
    if exist "%%~p" (
        set "ISCC_PATH=%%~p"
        goto :found
    )
)

:: Try PATH fallback
where iscc.exe >nul 2>nul
if %errorlevel% equ 0 (
    for /f "delims=" %%i in ('where iscc.exe') do (
        set "ISCC_PATH=%%i"
        goto :found
    )
)

echo ERROR: Inno Setup not found.
echo.
echo To fix this, download and install Inno Setup from:
echo   https://jrsoftware.org/isdl.php
echo.
echo Choose "Inno Setup 7" (or 6) and run the installer with default settings.
echo.
pause
exit /b 1

:found
echo Found Inno Setup at: %ISCC_PATH%
echo.

set "SCRIPT_DIR=%~dp0"
set "BUILD_TYPE=%~1"

if "%BUILD_TYPE%"=="" (
    if exist "%SCRIPT_DIR%out\Debug\Telegram.exe" (
        set "BUILD_TYPE=Debug"
    ) else if exist "%SCRIPT_DIR%out\Release\Telegram.exe" (
        set "BUILD_TYPE=Release"
    ) else (
        set "BUILD_TYPE=Debug"
    )
)

set "TARGET_DIR=%SCRIPT_DIR%out\%BUILD_TYPE%"
set "TELEGRAM_EXE=%TARGET_DIR%\Telegram.exe"
set "D3D_DLL=%TARGET_DIR%\modules\x64\d3d\d3dcompiler_47.dll"

:: Verify Telegram.exe exists
if not exist "%TELEGRAM_EXE%" (
    echo ERROR: Telegram.exe not found at:
    echo   %TELEGRAM_EXE%
    echo.
    echo Please build Telegram Desktop first:
    echo   1. Open Telegram.sln in Visual Studio 2022
    echo   2. Set configuration to %BUILD_TYPE%, platform to x64
    echo   3. Build the "Telegram" target
    echo.
    pause
    exit /b 1
)

:: Verify d3dcompiler_47.dll exists
if not exist "%D3D_DLL%" (
    echo ERROR: Direct3D shader compiler not found at:
    echo   %D3D_DLL%
    echo.
    echo Please ensure the modules\x64\d3d directory was built or copied properly.
    echo.
    pause
    exit /b 1
)

echo Configuration: %BUILD_TYPE%
echo Source binary:  %TELEGRAM_EXE%
echo Direct3D DLL:   %D3D_DLL%
echo Output folder:  %TARGET_DIR%
echo.
echo Compiling installer with LZMA2 compression (this typically takes ~1 minute)...
echo.

:: Run ISCC with BuildType parameter
"%ISCC_PATH%" "%SCRIPT_DIR%installer.iss" /dBuildType=%BUILD_TYPE%

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Installer compilation failed.
    echo.
    pause
    exit /b 1
)

:: Verify output
set "OUTPUT_INSTALLER=%TARGET_DIR%\tdesktop-Setup.exe"

if exist "%OUTPUT_INSTALLER%" (
    echo.
    echo ===============================================================================
    echo   SUCCESS!
    echo ===============================================================================
    echo.
    echo Installer created: %OUTPUT_INSTALLER%
    echo.
    echo To install tdesktop, simply double-click the file above.
    echo Share this installer with anyone — they don't need any technical knowledge!
    echo.
) else (
    echo.
    echo ERROR: Installer file was not created. Check the build output for errors.
    echo.
)

pause
