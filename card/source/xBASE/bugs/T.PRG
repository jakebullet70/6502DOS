

// lets begin
set deleted on
use bugs
set valid to POPUP("open;closed;hold;test",status) .and. _
             INLIST("N;L;M;H;",priority)
set fields to desc,status,priority
browse @ 5,10 to 20,70 TITLE "Bugs list" FOOTER "CTRL-ENTER -> Edit" 

close