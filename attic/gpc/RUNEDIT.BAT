@echo off
rem Run UXCEDIT, the editor, in a normal x16emu window, from disk\, the user's drive.
rem BUILD.BAT builds it and copies it to disk\.
setlocal
set PY=C:\Users\Admin\AppData\Local\Programs\Python\Python313\python.exe
cd /d "%~dp0"
if not exist "disk\UXCEDIT.PRG" goto missing
"%PY%" run.py UXCEDIT --disk --window
goto :eof
:missing
echo RUNEDIT: no disk\UXCEDIT.PRG. Run BUILD first.
pause
