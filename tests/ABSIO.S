; ABSIO: absread and abswrite on the test SD card. Keeps each call's A, carry and X at RESULTS,
; 3 bytes a call, for ABSIO.IN to dump. The MBR goes to $2000, the volume's boot sector to
; $2200, the MBR read again after the write to $2400, sectors 0 and 1 to $2600, and the first
; bytes of LONG.TXT to $3000.

.setcpu "65C02"

.include "api.inc"

r0      = $02
r1      = $04
r2      = $06
index   = $50                   ; the offset of the next result
RESULTS = $1200
MBR     = $2000
BOOT    = $2200
AGAIN   = $2400
PAIR    = $2600
TEXT    = $3000
MARK    = $1B0                  ; a byte of the MBR's boot code, which the card does not use

.macro point register, address
        lda #<(address)
        sta register
        lda #>(address)
        sta register+1
.endmacro

        stz index
        point r0, MBR           ; 1: the MBR: carry clear
        stz r1
        stz r1+1
        stz r2
        stz r2+1
        lda #2
        ldx #1
        jsr API_ABSREAD
        jsr save
        ldx #3                  ; the volume's first sector, from the first partition entry
@lba:
        lda MBR + $1BE + 8,x
        sta r1,x
        dex
        bpl @lba
        point r0, BOOT          ; 2: the volume's boot sector: carry clear
        lda #2
        ldx #1
        jsr API_ABSREAD
        jsr save
        lda #0                  ; 3: A: does not exist: error 15
        ldx #1
        jsr API_ABSREAD
        jsr save
        lda #0                  ; 4: a count of 0, even on A:: carry clear
        ldx #0
        jsr API_ABSWRITE
        jsr save
        stz r1                  ; 5: the MBR with $5A at MARK, written: carry clear
        stz r1+1
        stz r2
        stz r2+1
        point r0, MBR
        lda #$5A
        sta MBR + MARK
        lda #2
        ldx #1
        jsr API_ABSWRITE
        jsr save
        point r0, AGAIN         ; 6: the MBR read again: $5A at MARK
        lda #2
        ldx #1
        jsr API_ABSREAD
        jsr save
        point r0, PAIR          ; 7: sectors 0 and 1
        lda #2
        ldx #2
        jsr API_ABSREAD
        jsr save
        point r0, long          ; 8: LONG.TXT still opens and reads
        lda #0
        jsr API_OPEN
        jsr save
        point r0, TEXT
        point r1, 16
        jsr API_READ
        jsr save
        rts

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

long:     .byte 16, "C:\DOCS\LONG.TXT"
