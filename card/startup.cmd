print "CMD Shell in ROM: BASICShell v0.1.0, setting path and binds"
print "And... Its in "; 
gosub printcolor
print
PATH$ = "C:\sys;C:\sys\themes;C:\;c:\help"
print "Checking disk..."
diskinfo c:

REM -- clear the PUSH - POP DIR stack from REG
POPD -C

REM BIND LS FILES
BIND SET=SETSYS
BIND h=hdir
SETSYS PROMPT$="$p$g"

REM --- sets theme
REG THEME = DARK
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
print "r";
color green,black
return

out:
print
print "Ready...  (Andy is still a slacker...)"
print


