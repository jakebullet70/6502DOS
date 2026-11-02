// T2.PRG: BROWSE cases. Each prints what to try and what to see. Esc ends each BROWSE.
use bugs
on key f2 gosub say_hi

// 1
set fields to desc:20 "Description", status:1 "Status", priority "fp!"
cls
? "1 SET FIELDS, :width and column name"
? "See: Description 20 wide, S 1 wide, fp! 3 wide. Values cut to fit."
? "Ctrl+Enter: desc no edit, status no edit, priority edits. Esc it."
wait
browse

// 2
set fields to
set fields to desc:10 "Description", status "Status name", owner:12 "Who"
cls
? "2 Name and width against the field"
? "See: Descriptio 10 wide, Status name 11 wide, Who 12 wide."
? "Ctrl+Enter: desc no edit, status edits, owner edits. Esc it."
wait
browse

// 3
set fields to
set fields to recno():6 "Rec", id "Num"
set fields to desc:20 "Added by a second SET FIELDS"
cls
? "3 RECNO() and two SET FIELDS lines"
? "See: Rec, then the id field as Num, then Added by a second SE."
? "Rec is the only record number. Ctrl+Enter on Rec: no edit."
wait
browse

// 4
set fields to
set fields to id, desc:10 "From SET"
cls
? "4 BROWSE FIELDS over SET FIELDS"
? "First BROWSE: Who 4 wide and PROJECT, its own list."
? "Second BROWSE: ID and From SET, the SET FIELDS list back."
wait
browse fields owner:4 "Who", project
browse

// 5
set fields to
cls
? "5 SET FIELDS TO alone clears the list"
? "See: every field, record numbers at the left, field names as columns."
wait
browse

// 6
cls
? "6 Box and list. These lines go under the box and come back at Esc."
? "See: Description 20 wide, Status 6 wide, Box on top, Esc-out at bottom."
? "Row 2"
? "Row 3"
? "Row 4"
wait
browse @ 1,10 to 16,70 fields desc:20 "Description", status "Status" title "Box" footer "Esc-out"
? "Lines above are back, cursor here."
wait

// 7
cls
? "7 NOEDIT and Enter"
? "Keys row has no Ctrl+Enter edit. Ctrl+U does nothing."
? "Go down to a record, press Enter. See: the BROWSE ends, 13 and its record."
wait
browse noedit
? lastkey()
? recno()
wait

// 8
cls
? "8 NOEDIT and Ctrl+Enter, the same with a list"
? "Go down to a record, press Ctrl+Enter. See: the BROWSE ends, 13 and its record."
wait
go top
browse fields desc:20 "Description", status noedit
? lastkey()
? recno()
wait

// 9
cls
? "9 NOEDIT and Esc"
? "Go down to a record, press Esc. See: 27 and its record."
wait
go top
browse noedit
? lastkey()
? recno()
wait

// 10
cls
? "10 FREEZE 1"
? "Tab and Right to the last field. See: ID stays at the left, the rest move."
? "Left back. See: the rest move back."
wait
go top
browse fields id, desc, status, project, owner, priority, opened freeze 1

// 11
cls
? "11 FREEZE 2 with a width and a name"
? "Tab to the last field. See: ID and Description stay, 20 wide."
wait
go top
browse fields id, desc:20 "Description", status, project, owner, priority, opened freeze 2

// 12
cls
? "12 FIND with a list"
? "Tab to Status, Ctrl+F, type hold, Enter. See: the next hold record."
wait
go top
browse fields desc:20 "Description", status "Status" find

// 13
cls
? "13 ON KEY, full screen, a list"
? "Go down, Tab to Status, F2. See: the page stays and WAITING shows."
? "Press a key. See: the page drawn again, the same row and field."
wait
go top
browse fields desc:20 "Description", status "Status"

// 14
cls
? "14 ON KEY, a box. These lines come back at Esc."
? "Go down, Tab to Status, F2. See: box and page stay and WAITING shows."
? "Press a key. See: the same row and field. Esc: these lines back."
? "Row 3"
? "Row 4"
wait
go top
browse @ 1,10 to 16,70 fields desc:20 "Description", status "Status" title "Box"
? "Lines above are back, cursor here."
wait

// 15
on key f2
cls
? "15 ON KEY F2 cleared"
? "F2: nothing happens."
wait
go top
browse noedit

cls
? "Done. Type these at the prompt, each gives an error:"
? "  sbrowse"
? "  browse append"
? "  set fields to nosuch"
return

proc say_hi
  wait
endproc
