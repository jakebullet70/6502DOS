@echo off
rem Runs the UXCBASIC tests in UXCBASIC\tests, headless, on build\6502DOS.ROM. BUILD first.
rem   RUNUXCTESTS           run them all
rem   RUNUXCTESTS SKEL ...  run only the tests named
if "%PYTHON%"=="" set PYTHON=C:\Users\Admin\AppData\Local\Programs\Python\Python313\python.exe
"%PYTHON%" "%~dp0UXCBASIC\tests.py" %*
pause
