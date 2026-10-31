rem ----------------------------------------------------------------- 
rem --
rem --  startup.cmd, runs at machine boot, think autoexec.bat
rem --
rem ----------------------------------------------------------------

PATH$ = "C:\sys;C:\"

rem -- get, set default console color if not set
REG THEME SILENT
IF P1$ = "" then REG THEME = DARK
rem -- setup default console color for system
CONCOLOR
cls

print "CMD Shell in ROM: BASICShell v0.1.1, setting path and binds"
print "And... Its in ";
gosub printcolor
print
print "Checking disk..."
diskinfo c:

print "Clearing dir stack..."
REM -- clear the PUSH - POP DIR stack from the REG
POPD -C

REM BIND LS FILES
BIND SET=SETSYS
BIND h=hdir
SETSYS PROMPT$="$p$g"

goto out


PrintColor:
color red
print "C";
color yellow
print "o";
color gray
print "l";
color brown
print "o";
color white
print "r";
CONCOLOR
return

out:
print
print "Ready...  (Andy is still a slacker...)"
print


