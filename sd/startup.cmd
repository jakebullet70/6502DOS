cls
print "-------------------------------------------------------------------------"
PRINT "-"
PRINT "- Starting 6502DOS, Yes, 95% of this OS is written in UXCBASIC" 
print "- And it's in ";
gosub PrintColor 
print "-"
print "-------------------------------------------------------------------------"
print "Target --> Commander X16" 
print "512k System - Emulator running - Fat32 SD" 
print "BASICShell v0.1.0, setting path and binds"
print


PATH$ = "C:\DOS;C:\"
print "Checking disk..."
REM BIND LS FILES
diskinfo c:
BIND SET=SETSYS
SETSYS PROMPT$="$p$g"
goto out


PrintColor:
color red,black
print "C";
color yellow,black
print "o";
color gray,black
print "l";
color brown,black
print "o";
color white,black
print "r"
color green,black
return

out:
print "Ready..."
print


