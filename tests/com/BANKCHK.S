; BANKCHK: the program the BANKTRAP test runs. Its code starts at $0801, with no BASIC line. It
; selects RAM bank 7 and exits with the bank it started with.

.setcpu "65C02"

.include "api.inc"

RAM_BANK = $00

        lda RAM_BANK
        ldx #7
        stx RAM_BANK
        jsr API_EXIT
