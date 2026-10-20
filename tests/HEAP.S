; HEAP: the string heap calls str_alloc, str_free, str_gc and str_heap, in VARBANK and in a
; program's own bank, and the floor and the drop that exec and exit give VARBANK, with
; tests/com/HEAPKID.S. Keeps each call's A, carry and X at RESULTS, 3 bytes a call, and copies
; of the heaps' first $78 bytes at SNAP1 to SNAP3, for HEAP.IN to dump.

.setcpu "65C02"

.include "api.inc"

RAM_BANK = $00
r0      = $02
r1      = $04
r2      = $06
r3      = $08
first   = $50                   ; a descriptor in the zero page
index   = $52                   ; the offset of the next result
count   = $53
RESULTS = $1800
SNAP1   = $1900                 ; VARBANK after HEAPKID
SNAP2   = $1980                 ; VARBANK after str_gc
SNAP3   = $1A00                 ; bank 22
second  = $1A80                 ; a descriptor in program RAM
stale   = $1A82                 ; a descriptor whose block is not its own
many    = $1B00                 ; 40 descriptors in bank 22
VARBANK = 11
SYSTEM  = $A00C                 ; the first system descriptor of VARBANK

.macro point register, address
        lda #<(address)
        sta register
        lda #>(address)
        sta register+1
.endmacro

        stz index
        point r0, first         ; 1: 5 bytes: A = 11, r1 = $A04E
        lda #5
        jsr API_STR_ALLOC
        jsr save
        jsr save_r1
        point r2, hello
        jsr put
        point r0, second        ; 2: 3 bytes: r1 = $A056
        lda #3
        jsr API_STR_ALLOC
        jsr save_r1
        point r2, abc
        jsr put
        point r0, $0001         ; 3: bad descriptors: error 9 each
        jsr API_STR_ALLOC
        jsr save
        point r0, $9F23
        jsr API_STR_ALLOC
        jsr save
        point r0, $C000
        jsr API_STR_ALLOC
        jsr save
        point r0, first         ; 4: first again: r1 = $A05C, HELLO is free
        lda #2
        jsr API_STR_ALLOC
        jsr save_r1
        point r2, xy
        jsr put
        jsr API_STR_GC          ; 5: ABC to $A04C, XY to $A052: r0 = $1FA9
        jsr save_r0
        lda first               ; $A054
        ldx first+1
        jsr save
        lda second              ; $A04E
        ldx second+1
        jsr save
        point r0, second        ; 6: free, free again, a stale descriptor: error 9
        jsr API_STR_FREE
        jsr save
        jsr API_STR_FREE
        jsr save
        point stale, $A054
        point r0, stale
        jsr API_STR_FREE
        jsr save
        point r0, SYSTEM        ; 7: a system string, SYS1: r1 = $A059
        lda #4
        jsr API_STR_ALLOC
        jsr save_r1
        point r2, sys1
        jsr put
        point r0, kid           ; 8: HEAPKID exits with the low byte of its free count, $91
        point r1, empty
        jsr API_EXEC
        jsr save
        jsr API_EXITCODE
        jsr save
        lda first               ; still $A054
        ldx first+1
        jsr save
        point r3, SNAP1         ; VARBANK: SYS2 at $A05E, the bump pointer $A065
        lda #VARBANK
        jsr snap
        jsr API_STR_GC          ; 9: XY, SYS1, SYS2 move down: r0 = $1FA1
        jsr save_r0
        lda first               ; $A04E
        ldx first+1
        jsr save
        point r3, SNAP2
        lda #VARBANK
        jsr snap
        lda #5                  ; 10: a save bank: error 9
        jsr API_STR_HEAP
        jsr save
        lda #22                 ; 11: bank 22, cleared, blocks from $A010
        sta RAM_BANK
        ldy #0
@clear:
        lda #0
        sta $A000,y
        iny
        bne @clear
        stz RAM_BANK
        point r0, $A010
        lda #22
        jsr API_STR_HEAP
        jsr save
        point r0, $A00C         ; a descriptor in bank 22: A = 22, r1 = $A012
        lda #2
        jsr API_STR_ALLOC
        jsr save
        jsr save_r1
        jsr API_STR_GC          ; r0 = $1FEB
        jsr save_r0
        stz count               ; 12: 255 bytes on a new descriptor each, to error 8: 31 more
        point r0, many
@fill:
        lda #255
        jsr API_STR_ALLOC
        bcs @full
        lda #22                 ; the first text byte: the count
        sta RAM_BANK
        lda count
        ldy #1
        sta (r1),y
        stz RAM_BANK
        inc count
        inc r0
        inc r0
        bra @fill
@full:
        ldx count
        jsr save
        point r0, many          ; 13: free the first, and the next takes its room
        jsr API_STR_FREE
        jsr save
        lda count
        asl
        sta r0
        lda #255
        jsr API_STR_ALLOC
        jsr save_r1
        lda many+2              ; the second string moved to $A015: its descriptor $A017,
        ldx many+3              ; its first text byte 1
        jsr save
        lda #22
        sta RAM_BANK
        lda $A018
        stz RAM_BANK
        jsr save
        point r3, SNAP3
        lda #22
        jsr snap
        lda #VARBANK            ; 14: back to VARBANK
        jsr API_STR_HEAP
        jsr save
        rts

; put: copies the text of the length-prefixed string at r2 after the length byte at r1, in
; VARBANK. Changes A and Y.
put:
        ldy RAM_BANK
        phy
        lda #VARBANK
        sta RAM_BANK
        lda (r2)
        tay
@char:
        lda (r2),y
        sta (r1),y
        dey
        bne @char
        pla
        sta RAM_BANK
        rts

; snap: copies $A000-$A077 of bank A to r3: past $A077 VARBANK holds bytes no block wrote.
; Changes A and Y.
snap:
        ldy RAM_BANK
        phy
        sta RAM_BANK
        ldy #$77
@byte:
        lda $A000,y
        sta (r3),y
        dey
        bpl @byte
        pla
        sta RAM_BANK
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

; save_r0: keeps r0, low byte, carry, high byte.
save_r0:
        php
        ldx r0+1
        lda r0
        plp
        bra save

hello:    .byte 5, "HELLO"
abc:      .byte 3, "ABC"
xy:       .byte 2, "XY"
sys1:     .byte 4, "SYS1"
kid:      .byte 12, "\HEAPKID.COM"
empty:    .byte 0
