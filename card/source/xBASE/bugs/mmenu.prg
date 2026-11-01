cls
set deleted on
use bugs

@ 5,18 prompt " List all "
@ 6,18 prompt " Add new  "
@ 7,18 prompt " Quit     "
menu to mpick

do while .t.
	if mpick = 1 do browse
	if mpick = 2 do addnew
	if mpick = 3 return
	if mpick = 0 return
end do
