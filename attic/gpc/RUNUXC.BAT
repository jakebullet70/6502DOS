@echo off
rem Run UXC in a normal x16emu window, from disk\, the user's drive.
rem BUILD.BAT builds it and copies it to disk\.
setlocal
set PY=C:\Users\Admin\AppData\Local\Programs\Python\Python313\python.exe
cd /d "%~dp0"
if not exist "disk\UXC.PRG" goto missing
"%PY%" run.py UXC --disk --window
goto :eof
:missing
echo RUNUXC: no disk\UXC.PRG. Run BUILD first.
pause
