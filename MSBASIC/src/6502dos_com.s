; MSBASIC.COM, the start of the 6502dos target: clears the screen, selects ROM
; bank 2 and jumps to BASIC's cold start at $C000. tools/build.py of the
; 6502DOS repo assembles it to run at $0801 and puts the load address $0801 in
; front. Trap: at most 15 bytes, DOS_STUB in defines_6502dos.s; the RAM data
; starts at $0810. QUIT ends BASIC through exit, so no RTS comes back here.

.setcpu "65C02"

.include "mem.inc"
.include "api.inc"

FF		= $0C			; con_out's form feed clears the screen

        lda     #FF
        jsr     API_CON_OUT
        lda     #2
        sta     ROM_BANK
        jmp     ROM
