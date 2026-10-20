; Ctrl+C on 6502DOS. The cold start sets break mode BREAK_CATCH: con_status
; reads a waiting key, drops a Ctrl+C and sets the break flag, and con_break
; returns the flag and clears it. A key read goes over I2C and is slow, so
; one call in 256 looks; K_JIFFY makes the next call look.
; Trap: a key typed ahead stays waiting, and con_status reads no more keys
; until the program takes it, so a Ctrl+C after it is not seen.
; Ctrl+C: Z and carry set, on into STOP, which breaks.
ISCNTC:
        dec     DOS_POLL
        bne     RET2
        jsr     API_CON_STATUS
        sec
        jsr     API_CON_BREAK		; X = the flag
        dex
        bne     RET2
        sec
