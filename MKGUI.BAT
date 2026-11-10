@echo off
rem Builds BUILDGUI.EXE in the repo root from tools\gui\buildgui.py with PyInstaller.
if "%PYTHON%"=="" set PYTHON=C:\Users\Admin\AppData\Local\Programs\Python\Python313\python.exe
"%PYTHON%" -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo PyInstaller is missing. Install it with: "%PYTHON%" -m pip install pyinstaller
    exit /b 1
)
"%PYTHON%" -m PyInstaller --noconfirm --distpath "%~dp0." --workpath "%~dp0build\pyinstaller" "%~dp0tools\gui\buildgui.spec"
