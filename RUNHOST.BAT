@echo off
rem Starts x16emu in a window on build\6502DOS.ROM with the folder card as C:, at scale 2,
rem with the emulator command keys off so Ctrl and Alt keys reach the X16. Files saved on the X16
rem are files in card. Arguments pass to x16emu.
start "" "C:\8bitProgramming\x16emu\x16emu.exe" -rom "%~dp0build\6502DOS.ROM" -fsroot "%~dp0card" -scale 2 -noemucmdkeys -rtc %*
