@echo off
rem Runs 6502DOS in x16emu, the Commander X16 emulator, with the SD card SD.IMG.
rem Files saved on the X16 stay in SD.IMG.
rem Arguments pass on to x16emu, such as -scale 2 or -fullscreen; x16emu\x16emu.exe -help lists them.
cd /d "%~dp0"
x16emu\x16emu.exe -rom 6502DOS.ROM -sdcard SD.IMG -rtc -nohostfs %*
