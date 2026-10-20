; BANKKID: the program the BANKS test runs. Its code starts at $0801, with no BASIC line. It takes
; a run of 2 banks, then a run of 1, frees neither, and exits with the first bank of the run of 2.

.setcpu "65C02"

.include "api.inc"

        lda #2
        jsr API_BANK_ALLOC
        pha
        lda #1
        jsr API_BANK_ALLOC
        pla
        jsr API_EXIT
