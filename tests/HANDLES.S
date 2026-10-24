; HANDLES: opens, writes, reads and closes devices through the gate, and keeps each call's
; A, carry and X at RESULTS, 3 bytes a call, for HANDLES.IN to dump.

.setcpu "65C02"

.include "api.inc"

r0      = $02
r1      = $04
index   = $50                   ; the offset of the next result
handle  = $51
RESULTS = $1200
MESSAGE = $1280                 ; errmsg's buffer, 128 bytes

.macro point address
        lda #<address
        sta r0
        lda #>address
        sta r0+1
.endmacro

.macro count bytes
        lda #bytes
        sta r1
        stz r1+1
.endmacro

        stz index
        point nul               ; 1: open NUL to write: X = 3
        lda #1
        jsr API_OPEN
        jsr save
        stx handle
        point abc               ; 2: write 3 bytes to NUL: A = r1 = 3
        count 3
        jsr API_WRITE
        lda r1
        jsr save
        ldx handle              ; 3: read NUL, open to write: error 5
        jsr API_READ
        jsr save
        ldx handle              ; 4: close it
        jsr API_CLOSE
        jsr save
        point con               ; 5: open CON by a path: X = 3
        lda #2
        jsr API_OPEN
        jsr save
        stx handle
        point hello             ; 6: write to it
        count 7
        ldx handle
        jsr API_WRITE
        jsr save
        ldx handle              ; 7: close it
        jsr API_CLOSE
        jsr save
        point foo               ; 8: open a name with no device: error 2
        lda #0
        jsr API_OPEN
        jsr save
        point nul               ; 9: open with access 3: error 12
        lda #3
        jsr API_OPEN
        jsr save
        ldx #9                  ; 10: close a closed handle: error 6
        jsr API_CLOSE
        jsr save
        ldx #20                 ; 11: write to handle 20: error 6
        jsr API_WRITE
        jsr save
        point MESSAGE           ; 12: the message of error 18, written to handle 1
        lda #18
        jsr API_ERRMSG
        jsr save
        point (MESSAGE + 1)
        lda MESSAGE
        sta r1
        stz r1+1
        ldx #1
        jsr API_WRITE
        lda #99                 ; 13: the message of error 99: error 1
        jsr API_ERRMSG
        jsr save
        jsr API_VERSION         ; 14: A, X = major, minor
        jsr save
        lda #0                  ; 15: a call not written yet: error 1
        jsr API_ATTRIB
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

nul:    .byte 3, "NUL"
con:    .byte 14, "c:\dev/con.txt"
foo:    .byte 3, "FOO"
abc:    .byte "abc"
hello:  .byte "Hello", $0D, $0A
