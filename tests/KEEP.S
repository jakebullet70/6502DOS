; KEEP: keep, on x16emu's 64 banks: 62 are free at boot. tests/com/KEEPKID.S takes 2 banks and
; ends with keep; tests/com/BANKKID.S then exits at the same exec depth. Keeps each call's A,
; carry and X at RESULTS, 3 bytes a call, for KEEP.IN to dump.

.setcpu "65C02"

.include "api.inc"

r0      = $02
r1      = $04
index   = $50                   ; the offset of the next result
RESULTS = $1200

.macro point register, address
        lda #<(address)
        sta register
        lda #>(address)
        sta register+1
.endmacro

        stz index
        lda #0                  ; 1: the free count: 62
        jsr alloc
        lda #5                  ; 2: keep with no program running: error 1
        jsr API_KEEP
        jsr save
        point r0, keeper        ; 3: the save takes 1 to 5, KEEPKID takes 6 and 7: code 7
        point r1, empty
        jsr API_EXEC
        jsr save
        jsr API_EXITCODE        ; 4: 7, ended by keep: X = 3
        jsr save
        lda #0                  ; 5: 6 and 7 stay taken: 60
        jsr alloc
        point r0, kid           ; 6: BANKKID takes 8 and 9, then 10, and exits with 8
        jsr API_EXEC
        jsr save
        lda #0                  ; 7: its exit freed its banks, not 6 and 7: 60
        jsr alloc
        lda #6                  ; 8: a kept bank: error 9
        jsr API_BANK_FREE
        jsr save
        rts

alloc:
        jsr API_BANK_ALLOC
        ; fall through

; save: keeps A, carry and X at the next result. Changes A and Y.
save:
        php
        ldy index
        sta RESULTS,y
        pla
        and #$01                ; carry
        sta RESULTS+1,y
        txa
        sta RESULTS+2,y
        iny
        iny
        iny
        sty index
        rts

keeper:   .byte 12, "\KEEPKID.COM"
kid:      .byte 12, "\BANKKID.COM"
empty:    .byte 0
