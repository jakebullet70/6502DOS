; I/O layer: the entry points the interpreter uses for files and channels.
;
; Every target already provides MONCOUT, MONRDKEY and ISCNTC. Targets with
; CONFIG_FILE (PRINT#, INPUT#, GET#, CMD) also provide the IO_* routines
; below and the statements OPEN, CLOSE, SYS (and on CBM LOAD, SAVE, VERIFY).
; On CBM these are KERNAL routines; the KERNAL also parses the statement
; arguments itself. CONFIG_HANDLE_IO targets get them from handle_io.s.
;
; Register rules come from how the interpreter calls them:
;
; IO_CHKIN   X = logical file number; input now comes from that file.
;            Keeps X (the caller stores it in CURDVC). Errors do not return.
; IO_CHKOUT  X = logical file number; output now goes to that file.
;            Keeps X. Errors do not return.
; IO_CLRCH   Input and output back to the console. Keeps X (ERROR holds
;            the error number in X).
; IO_CHRIN   Returns the next input character in A. From the console this
;            is a line: its characters, then CR. Keeps X (INLIN keeps the
;            buffer index in X).
; IO_CLALL   Close all files, then as IO_CLRCH (RUN, NEW, CLR).
; MONCOUT    Writes A to the current output. Keeps A, X and Y (unless
;            CONFIG_MONCOUT_DESTROYS_Y).
; MONRDKEY   GET: returns a character from the current input in A.
; Z96        ST, status of the last file read: bit 6 end of file, bit 1
;            read error (INPUT# stops and skips the rest of the statement).

.ifdef CONFIG_CBM_ALL
IO_CHKIN	:= CHKIN
IO_CHKOUT	:= CHKOUT
IO_CLRCH	:= CLRCH
IO_CHRIN	:= CHRIN
IO_CLALL	:= CLALL
.endif
