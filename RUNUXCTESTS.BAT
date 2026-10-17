@echo off
rem Runs the UXCBASIC tests in UXCBASIC\tests, headless, on build\UXDOS16.ROM. BUILD first.
rem   RUNUXCTESTS           run them all
rem   RUNUXCTESTS SKEL ...  run only the tests named
"C:\Users\Admin\AppData\Local\Programs\Python\Python313\python.exe" "%~dp0UXCBASIC\tests.py" %*
pause
