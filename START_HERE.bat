@echo off
title NXN Quality System

echo ============================================
echo   NXN Quality System - Setup and Start
echo ============================================
echo.

where py >nul 2>&1
if %errorlevel%==0 (
    set PYCMD=py
    goto found
)

where python >nul 2>&1
if %errorlevel%==0 (
    set PYCMD=python
    goto found
)

echo ERROR: Python was not found.
echo.
echo Please install Python from:
echo https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH" during installation.
echo.
pause
exit /b 1

:found
echo Using Python command: %PYCMD%
echo.
echo [1/2] Installing requirements (first time only, may take a minute)...
%PYCMD% -m pip install --quiet --disable-pip-version-check -r requirements.txt

echo.
echo [2/2] Starting the app...
echo Your browser will open automatically in a few seconds.
echo To stop the system later, just close this black window.
echo.

%PYCMD% -m streamlit run app.py

pause
