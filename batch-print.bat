@echo off
cd /d "%~dp0"
if "%~1"=="" (
    echo Usage: batch-print.bat orders.xlsx [photos_folder]
    echo Example: batch-print.bat templates\lgbtiqasb-orders-template.xlsx
    pause
    exit /b 1
)

set SHEET=%~1
set PHOTOS=%~2
set OUTPUT=output\lgbtiqasb-batch-%date:~-4,4%%date:~-10,2%%date:~-7,2%.pdf

if "%PHOTOS%"=="" (
    python scripts\batch_print.py "%SHEET%" --output "%OUTPUT%"
) else (
    python scripts\batch_print.py "%SHEET%" --photos-dir "%PHOTOS%" --output "%OUTPUT%"
)

if %ERRORLEVEL%==0 (
    echo.
    echo Done: %OUTPUT%
    start "" "%OUTPUT%"
)
pause