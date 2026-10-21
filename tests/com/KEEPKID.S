; KEEPKID: the program the KEEP test runs. Its code starts at $0801, with no BASIC line. It takes
; a run of 2 banks and ends with keep, code 7.

.setcpu "65C02"

.include "api.inc"

        lda #2
        jsr API_BANK_ALLOC
        lda #7
        jsr API_KEEP
