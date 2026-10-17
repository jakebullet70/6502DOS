@echo off
rem Build the UXCBASIC programs into build\.
rem   BUILD              build all three: UXC, UXC.HELP and UXCEDIT
rem   BUILD UXC ...      build only the programs named
rem A build empties build\. It keeps the PRGs of the programs it does not build, and
rem SETTINGS.KVB. Any other file in build\ is lost.
setlocal
set PY=C:\Users\Admin\AppData\Local\Programs\Python\Python313\python.exe
cd /d "%~dp0"
if "%~1"=="" (
    "%PY%" build.py ALL
) else (
    "%PY%" build.py %*
)
if errorlevel 1 echo BUILD: the build failed.
pause
