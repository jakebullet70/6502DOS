@echo off
rem Starts x16emu in a window on build\6502DOS.ROM with the card build\SD.IMG as C:, at scale 2, with the
rem emulator command keys off so Ctrl and Alt keys reach the X16. Arguments pass to x16emu.
start "" "C:\8bitProgramming\x16emu\x16emu.exe" -rom "%~dp0build\6502DOS.ROM" -sdcard "%~dp0build\SD.IMG" -scale 2 -noemucmdkeys %*
