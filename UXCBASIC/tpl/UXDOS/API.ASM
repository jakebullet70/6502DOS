; API.ASM -- the UXDOS16 calls the UXDOS16 table uses. UXDOS16's docs/API.md lists them all.
;
; A call is a JSR to its entry. Carry set on return: an error, its number in A. A call changes
; A, X, Y and the flags, and keeps r0-r15 except the registers it lists as out. A path is a
; length-prefixed string. A handle goes in X.

API_R0  = $02           ; word: r0
API_R1  = $04           ; word: r1

API_CREATE = $0340      ; r0 path, A attributes. X = the handle
API_OPEN   = $0343      ; r0 path, A access: 0 read, 1 write. X = the handle
API_CLOSE  = $0346      ; X handle
API_READ   = $0349      ; X handle, r0 buffer, r1 count. r1 = the count read, 0 at the end
API_WRITE  = $034c      ; X handle, r0 buffer, r1 count
API_SEEK   = $034f      ; X handle, A from: 1 the position, 2 the end; r0 r1 offset
API_IOCTL  = $035e      ; X handle, A 6: input status. r0 = $ff when a read gives a byte
API_LINE   = $0385      ; con_line: r0 buffer [max][len][text], ended by CR; echoes CR LF
API_STATUS = $0388      ; con_status: A = $ff when a key waits, else 0
API_EXIT   = $038e      ; exit: A exit code. Does not return
API_IN     = $03bb      ; con_in: A = the next key, no echo
API_CURSOR = $03be      ; con_cursor: C set gets the row in X and the column in Y; C clear sets them

; The handles every program starts with.
STDOUT  = 1
