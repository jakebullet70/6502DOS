; The syscall gate: the call entries in RAM from GATE_ENTRIES, and the gate code at $0310.
;
; Entry n is JSR gate. The gate finds n from its return address, selects ROM bank 0 to read
; record n of api_table, selects the routine's bank, calls the routine and puts the caller's
; ROM bank back. jsrfar, for calls inside the ROM from one bank to another, ends in the same
; code at gate_far.

.setcpu "65C02"

.include "mem.inc"
.include "api.inc"
.include "far.inc"

.export gate_init, gate_far, jsrfar
.exportzp gate_a, gate_x, gate_vector
.import api_table
.import __GATE_LOAD__, __GATE_RUN__, __GATE_SIZE__

.segment "KERNELZP" : zeropage

gate_a:       .res 1
gate_x:       .res 1
gate_vector:  .res 2

.segment "CODE"

; gate_init: copies the gate code to RAM and writes the call entries. Changes A and X.
gate_init:
        ldx #0
@copy:
        lda __GATE_LOAD__,x
        sta __GATE_RUN__,x
        inx
        cpx #<__GATE_SIZE__
        bne @copy
        ldx #0
@entry:
        lda #$20                ; JSR
        sta GATE_ENTRIES,x
        lda #<gate
        sta GATE_ENTRIES+1,x
        lda #>gate
        sta GATE_ENTRIES+2,x
        inx
        inx
        inx
        cpx #CALL_COUNT * 3
        bne @entry
        rts

; jsrfar: JSRFAR in far.inc, for bank 0. FARCALL calls it.
jsrfar:
        JSRFAR

; Trap: this code runs in RAM, so it may write ROM_BANK. The low byte of an entry's return
; address, entry + 2, indexes api_table, whose records are 3 bytes as the entries are.
.segment "GATE"

gate:
        sta gate_a
        stx gate_x
        pla                     ; the low byte of entry n + 2
        tax
        pla                     ; the high byte: the gate page
        lda ROM_BANK
        pha                     ; the caller's ROM bank
        stz ROM_BANK            ; api_table is in bank 0
        lda api_table - <(GATE_ENTRIES + 2),x
        sta gate_vector
        lda api_table - <(GATE_ENTRIES + 2) + 1,x
        sta gate_vector+1
        lda api_table - <(GATE_ENTRIES + 2) + 2,x
; gate_far: jsrfar's way in. A = the routine's bank, gate_vector its address, gate_a and
; gate_x its A and X; the caller's bank is on the stack above the return address.
gate_far:
        sta ROM_BANK
        ldx gate_x
        lda gate_a
        jsr @call
        sta gate_a
        pla
        sta ROM_BANK
        lda gate_a              ; keeps carry
        rts
@call:
        jmp (gate_vector)

        .assert GATE_ENTRIES = $0340, error, "GATERAM in rom.cfg must end below GATE_ENTRIES"
