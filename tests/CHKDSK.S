; CHKDSK: selects the SD card's fast read loop with ioctl subfunction 5 before CHKDSK.IN runs
; CHKDSK. Keeps each call's A, carry and r1 low byte at RESULTS, 3 bytes a call, for CHKDSK.IN
; to dump.

.setcpu "65C02"

.include "api.inc"

r0      = $02
r1      = $04
index   = $50                   ; the offset of the next result
RESULTS = $1200

        stz index
        lda #<fast              ; 1: A: does not exist: error 15
        sta r0
        lda #>fast
        sta r0+1
        lda #1
        sta r1
        stz r1+1
        ldx #1
        jsr control
        stz r1                  ; 2: a count of 0, the current drive: carry clear, r1 0
        ldx #0
        jsr control
        inc r1                  ; 3: the fast read loop on C:: carry clear, r1 1
        ldx #3
        ; fall through

; control: makes ioctl subfunction 5 on drive X and keeps A, carry and r1 at the next result.
; Changes A and Y.
control:
        lda #5
        jsr API_IOCTL
        php
        ldy index
        sta RESULTS,y
        pla
        and #$01                ; carry
        sta RESULTS+1,y
        lda r1
        sta RESULTS+2,y
        iny
        iny
        iny
        sty index
        rts

fast:     .byte 1
