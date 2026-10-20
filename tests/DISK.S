; DISK: reads the test SD card through the gate: drives, a file read in parts, errors, and a
; directory search. Keeps each call's A, carry and X at RESULTS, 3 bytes a call, for DISK.IN
; to dump. LONG.TXT goes to $2000, and the find buffer of the last search to $1300.

.setcpu "65C02"

.include "api.inc"

r0      = $02
r1      = $04
index   = $50                   ; the offset of the next result
handle  = $51
count   = $52
RESULTS = $1200
FIND    = $1300
DATA    = $2000

.macro point register, address
        lda #<(address)
        sta register
        lda #>(address)
        sta register+1
.endmacro

        stz index
        jsr API_GETDRIVE        ; 1: the current drive: A = 2, C:
        jsr save
        lda #0                  ; 2: A: does not exist: error 15
        jsr API_SETDRIVE
        jsr save
        lda #2                  ; 3: C:: A = 4 drive letters
        jsr API_SETDRIVE
        jsr save
        point r0, long          ; 4: open LONG.TXT: X = 3
        lda #0
        jsr API_OPEN
        jsr save
        stx handle
        point r0, DATA          ; 5: read 1000 bytes: r1 = 1000
        point r1, 1000
        ldx handle
        jsr API_READ
        jsr save_r1
        point r0, DATA + 1000   ; 6: read up to 5000: r1 = 2200, the rest
        point r1, 5000
        ldx handle
        jsr API_READ
        jsr save_r1
        point r1, 10            ; 7: read at the end: r1 = 0
        ldx handle
        jsr API_READ
        jsr save_r1
        ldx handle              ; 8: close it
        jsr API_CLOSE
        jsr save
        point r0, hello         ; 9: open a file to write: error 5
        lda #2
        jsr API_OPEN
        jsr save
        point r0, no_dir        ; 10: a missing directory: error 3
        lda #0
        jsr API_OPEN
        jsr save
        point r0, no_drive      ; 11: a missing drive: error 15
        lda #0
        jsr API_OPEN
        jsr save
        point r0, wild          ; 12: open a wildcard: error 2
        lda #0
        jsr API_OPEN
        jsr save
        stz count               ; 13: the files in MANY: A = 33, then error 18
        point r0, many
        point r1, FIND
        lda #0
        jsr API_FINDFIRST
@count:
        bcs @counted
        inc count
        jsr API_FINDNEXT
        bra @count
@counted:
        jsr save
        lda count
        jsr save
        point r0, f33           ; 14: find F33.TXT: its find buffer at FIND
        lda #0
        jsr API_FINDFIRST
        jsr save
        point r0, nothing       ; 15: find a name that is not there: error 2
        lda #0
        jsr API_FINDFIRST
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

; save_r1: keeps r1, low byte, carry, high byte.
save_r1:
        php
        ldx r1+1
        lda r1
        plp
        bra save

long:     .byte 16, "C:\DOCS\LONG.TXT"
hello:    .byte 9, "HELLO.TXT"
no_dir:   .byte 11, "\NOPE\X.TXT"
no_drive: .byte 4, "Q:\X"
wild:     .byte 5, "*.TXT"
many:     .byte 9, "/MANY/*.*"
f33:      .byte 15, "c:\many\f33.txt"
nothing:  .byte 9, "\NONE.TXT"
