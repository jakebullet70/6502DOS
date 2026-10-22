; BANKTRAP: calls made with a RAM bank selected. Takes a bank, copies the paths and the text to
; $A000 in it, keeps the buffers there, and makes the calls with it selected. Keeps $00 and the
; carry after each call at RESULTS, 2 bytes a call, for BANKTRAP.IN to dump: each $00 must be
; the bank. The console shows the text that write, read, findfirst and getcwd moved through the
; bank. tests/com/BANKCHK.S exits with the bank it starts with, kept at KID_BANK.

.setcpu "65C02"

.include "api.inc"

RAM_BANK = $00
r0      = $02
r1      = $04
index   = $50                   ; the offset of the next result
first   = $51                   ; the bank selected at the start
handle  = $52
RESULTS = $1400
KID_BANK = $1480
STRING  = $1482                 ; a string descriptor
WINDOW  = $A000

TEXT    = WINDOW + (text - image)
NAME    = WINDOW + (name - image)
NAME2   = WINDOW + (name2 - image)
FOLDER  = WINDOW + (folder - image)
PATTERN = WINDOW + (pattern - image)
KID     = WINDOW + (kid - image)
TAIL    = WINDOW + (tail - image)
COPY    = $A060                 ; 8 bytes
FIND    = $A070                 ; 83 bytes
CWD     = $A100                 ; 256 bytes

.macro point register, address
        lda #<(address)
        sta register
        lda #>(address)
        sta register+1
.endmacro

        lda RAM_BANK
        sta first
        stz index
        lda #1
        jsr API_BANK_ALLOC
        sta RAM_BANK
        ldx #IMAGE_SIZE - 1
@copy:
        lda image,x
        sta WINDOW,x
        dex
        bpl @copy
        point r0, TEXT          ; 1: write the text to the console
        point r1, 8
        ldx #1
        jsr API_WRITE
        jsr save
        point r0, NAME          ; 2: create
        lda #0
        jsr API_CREATE
        jsr save
        stx handle
        point r0, TEXT          ; 3: write the text to the file
        ldx handle
        jsr API_WRITE
        jsr save
        lda #0                  ; 4: filetime, get
        ldx handle
        jsr API_FILETIME
        jsr save
        stz r0                  ; 5: seek to 0
        stz r0+1
        stz r1
        stz r1+1
        lda #0
        ldx handle
        jsr API_SEEK
        jsr save
        point r0, COPY          ; 6: read it back
        point r1, 8
        ldx handle
        jsr API_READ
        jsr save
        ldx handle              ; 7: close
        jsr API_CLOSE
        jsr save
        ldx #1                  ; 8: write the copy to the console
        jsr API_WRITE
        jsr save
        point r0, NAME          ; 9: rename
        point r1, NAME2
        jsr API_RENAME
        jsr save
        point r0, NAME2         ; 10: attrib, get
        lda #0
        jsr API_ATTRIB
        jsr save
        jsr API_DELETE          ; 11: delete
        jsr save
        point r0, PATTERN       ; 12, 13: findfirst, then write the name it found
        point r1, FIND
        lda #0
        jsr API_FINDFIRST
        jsr save
        point r0, FIND + 51
        lda FIND + 50
        sta r1
        stz r1+1
        ldx #1
        jsr API_WRITE
        jsr save
        jsr newline             ; 14, 15: CR LF
        point r1, FIND          ; 16: findnext: error 18
        jsr API_FINDNEXT
        jsr save
        point r0, FOLDER        ; 17: mkdir
        jsr API_MKDIR
        jsr save
        jsr API_CHDIR           ; 18: chdir
        jsr save
        point r0, CWD           ; 19, 20: getcwd, then write it
        lda #0
        jsr API_GETCWD
        jsr save
        point r0, CWD + 1
        lda CWD
        sta r1
        stz r1+1
        ldx #1
        jsr API_WRITE
        jsr save
        jsr newline
        point r0, root          ; 23: chdir back, from low RAM
        jsr API_CHDIR
        jsr save
        point r0, FOLDER        ; 24: rmdir
        jsr API_RMDIR
        jsr save
        jsr API_GETDRIVE        ; 25
        jsr save
        lda #0                  ; 26
        jsr API_DISKFREE
        jsr save
        jsr API_CON_STATUS      ; 27
        jsr save
        lda #2                  ; 28: setdrive C:
        jsr API_SETDRIVE
        jsr save
        sec                     ; 29
        jsr API_CON_CURSOR
        jsr save
        sec                     ; 30
        jsr API_CON_COLOUR
        jsr save
        sec                     ; 31
        jsr API_CON_BREAK
        jsr save
        lda #0                  ; 32: the free count
        jsr API_BANK_ALLOC
        jsr save
        jsr API_GETDATE         ; 33
        jsr save
        jsr API_GETTIME         ; 34
        jsr save
        jsr API_VERSION         ; 35
        jsr save
        jsr API_TICKS           ; 36
        jsr save
        lda #2                  ; 37
        jsr API_ERRMSG
        jsr save
        lda #0                  ; 38
        jsr API_GETVECT
        jsr save
        lda #0                  ; 39: ioctl 0 on the console
        ldx #1
        jsr API_IOCTL
        jsr save
        ldx #1                  ; 40: dup the console, then close the copy
        jsr API_DUP
        jsr save
        jsr API_CLOSE           ; 41
        jsr save
        point r0, STRING        ; 42: str_alloc, in low RAM
        lda #5
        jsr API_STR_ALLOC
        jsr save
        jsr API_STR_GC          ; 43
        jsr save
        point r0, STRING        ; 44
        jsr API_STR_FREE
        jsr save
        point r0, KID           ; 45: exec BANKCHK, then its exit code
        point r1, TAIL
        jsr API_EXEC
        jsr save
        jsr API_EXITCODE        ; 46
        sta KID_BANK
        jsr save
        lda RAM_BANK            ; 47: free the bank
        jsr API_BANK_FREE
        jsr save
        lda first
        sta RAM_BANK
        rts

; newline: writes CR and LF with con_out, 2 results.
newline:
        lda #13
        jsr API_CON_OUT
        jsr save
        lda #10
        jsr API_CON_OUT
        ; fall through

; save: keeps $00 and the carry at the next result. Changes A and Y.
save:
        php
        ldy index
        lda RAM_BANK
        sta RESULTS,y
        pla
        and #$01                ; carry
        sta RESULTS+1,y
        iny
        iny
        sty index
        rts

root:     .byte 1, "\"

image:
text:     .byte "BANKED", 13, 10
name:     .byte 9, "\TRAP.TMP"
name2:    .byte 10, "\TRAP2.TMP"
folder:   .byte 8, "\TRAPDIR"
pattern:  .byte 16, "\DOCS\README.TXT"
kid:      .byte 12, "\BANKCHK.COM"
tail:     .byte 0
IMAGE_SIZE = * - image
        .assert IMAGE_SIZE <= COPY - WINDOW, error, "the image runs into COPY"
