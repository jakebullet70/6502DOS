@echo off
rem Builds build\6502DOS.ROM, the UXCBASIC programs and the folder card. Arguments pass to build.py.
if "%PYTHON%"=="" set PYTHON=C:\Users\Admin\AppData\Local\Programs\Python\Python313\python.exe
"%PYTHON%" "%~dp0tools\build.py" %*
