; PROF.PRG: samples the GPC runtime's codePtr ($28/$29) and the RAM bank at every VSYNC IRQ,
; and writes the three bytes to x16emu's debug register $9FB9 (stdout "User debug 1: $xx").
; SYS 1792 installs it. It chains to the IRQ handler it replaces.

CINV    = $0314
RAMBANK = $00
CODEPTR = $28
DEBUG1  = $9FB9

        .segment "LOADADDR"
        .word   $0700
        .segment "CODE"

install:
        sei
        lda     CINV
        sta     chain
        lda     CINV+1
        sta     chain+1
        lda     #<irq
        sta     CINV
        lda     #>irq
        sta     CINV+1
        cli
        rts

irq:
        lda     RAMBANK
        sta     DEBUG1
        lda     CODEPTR
        sta     DEBUG1
        lda     CODEPTR+1
        sta     DEBUG1
        jmp     (chain)

chain:  .word   0
