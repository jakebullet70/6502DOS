; The COM file that starts a program in ROM bank BANK: selects the bank and jumps to its start
; at $C000. tools/build.py assembles it with -D BANK=3 for ROMSHELL.COM and -D BANK=6 for DB.COM,
; to run at $0801, and puts the load address $0801 in front. The program's #DATA $0801 clears
; these bytes once it runs. Its exit ends it, so no RTS comes back here.

.setcpu "65C02"

.include "mem.inc"

        lda     #BANK
        sta     ROM_BANK
        jmp     ROM
