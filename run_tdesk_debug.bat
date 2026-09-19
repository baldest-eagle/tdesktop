@echo off
setlocal
cd /d "C:\Users\kyleh\tdesktop"
set LOGFILE=%TEMP%\tdesktop_debug_%RANDOM%.log
echo %DATE% %TIME% - Starting Telegram.exe > "%LOGFILE%"
out\Debug\Telegram.exe >> "%LOGFILE%" 2>&1
echo %DATE% %TIME% - Telegram.exe exited with code %ERRORLEVEL% >> "%LOGFILE%"
echo LOGFILE=%LOGFILE% > "%TEMP%\tdesktop_logpath.txt"
