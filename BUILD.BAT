@echo off
rem Builds build\6502DOS.ROM, the UXCBASIC programs and build\SD.IMG. Arguments pass to build.py.
"C:\Users\Admin\AppData\Local\Programs\Python\Python313\python.exe" "%~dp0tools\build.py" %*
