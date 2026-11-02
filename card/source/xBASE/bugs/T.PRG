


use bugs
on key f2 gosub go_filter
on key f3 gosub say_hi
set valid to popup(" open ; close ; hold ; closed ",status) 
sbrowse @ 5,10 to 20,70 title "Bugs" footer "F2-Filters F3-"
close
return

proc go_filter
  pick = MENU(8,30,"All;Open;Closed;Hold")
  if pick = 1
    set filter to
  endif
  if pick = 2
    set filter to INLIST("open",status)
  endif
  if pick = 3
    set filter to INLIST("closed",status)
  endif
  if pick > 0
    go top
  endif
endproc

proc say_hi
  wait
endproc








// lets begin
set deleted on
gosub opendb

set valid to POPUP("open;closed;hold;test",status) .and. _
             INLIST("N;L;M;H;",priority)
set fields to desc,status,priority
browse @ 5,10 to 20,70 TITLE "Bugs list" FOOTER "CTRL-ENTER -> Edit" 

close
return



// -------------
proc opendb
	use bugs
endproc

