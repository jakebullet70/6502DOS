; ZP.ASM -- the zero page of a compiled program.
;
; $02-$21 are the KERNAL's r0-r15. The runtime uses them as scratch between KERNAL calls.
; $50-$7F are free for the user (ASM, POKE).

ZP_PTR  = $22           ; word: a runtime pointer
ZP_TMP  = $24           ; word: a runtime temporary
ZP_SP   = $26           ; byte: the stack pointer at startup, for END
        .if UXDOS == 0
ZP_MODE = $27           ; byte, stock table only: $0372 at startup, the charset and the ISO bit
        .endif
ZP_DST  = $28           ; word: the destination block of a string routine
ZP_FILE = $2A           ; byte: the handle the input comes from
ZP_OUT  = $2B           ; byte: the handle the output goes to, set by S_INIT
ZP_HI   = $2C           ; word: the high word of a LONG, whose low word is in A/Y
ZP_GOT  = $2E           ; byte: the byte S_CHROUT writes or R_FIN.getc reads

; The LONG routines work in the KERNAL's r0-r5, and call no KERNAL routine meanwhile.
ZP_LR   = $02           ; 4 bytes: the right side
ZP_LL   = $06           ; 4 bytes: the left side, then the quotient
ZP_LX   = $0A           ; 4 bytes: the product, the remainder

; The expression stack: 16 words at $30-$4F, low byte first. X is the offset of the next free
; word, so X = 2 x depth. Every runtime routine keeps X. A LONG's high word is at R_ESTKH,x.
ESTK    = $30
