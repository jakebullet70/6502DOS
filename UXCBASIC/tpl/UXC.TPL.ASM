; UXC.TPL.ASM -- the template table of the UXCBASIC compiler.
;
; Built by tpl/MKTPL.PY with 64tass into UXC.TPL.BIN. MACROS.ASM describes the format.
; A record's id is its place in this file, so add new records at the end of a file, and
; rebuild the compiler after any change here.
;
; UXDOS is 0 for the stock ROM's table, tpl/UXC.TPL.BIN, and 1 for the 6502DOS table,
; tpl/UXDOS/UXC.TPL.BIN. The 6502DOS table takes SYS.ASM and R-FILE.ASM from tpl/UXDOS. Both
; tables hold the same records in the same order, so a record has one id in both.

        .cpu "65c02"
        .include "MACROS.ASM"
        .include "ZP.ASM"
        .if UXDOS != 0
        .include "UXDOS/API.ASM"
        .endif

        .text "UXT"
        .byte 1                 ; the format version
        .word tpl_count
        .word index

        .include "T-CORE.ASM"
        .include "T-PRINT.ASM"
        .include "R-PRINT.ASM"
        .if UXDOS != 0
        .include "UXDOS/SYS.ASM"
        .else
        .include "SYS.ASM"
        .endif
        .include "T-EXPR.ASM"
        .include "R-MATH.ASM"
        .include "R-ERROR.ASM"
        .include "T-FLOW.ASM"
        .include "T-ARRAY.ASM"
        .include "T-STRING.ASM"
        .include "R-STRING.ASM"
        .include "T-FILE.ASM"
        .if UXDOS != 0
        .include "UXDOS/R-FILE.ASM"
        .else
        .include "R-FILE.ASM"
        .endif
        .include "T-RECORD.ASM"

; At startup, for 6502DOS only: the high byte of S0, the end of the program, into PSP_TOP, byte 2
; of the PSP. exec saves the program's pages up to that one. pyuxc emits it only for 6502DOS.
T_TOP   .block
        #tpl
        #hi lda, S0
        sta $0702
        #endtpl
        .endblock

; An F_REC fixup holds a record id in one byte, so a record that #rec names needs an id below 256.
; Ids 256 and up go to records that no #rec names, here.

; A = the screen's rows. POS(2) uses it. 6502DOS's con_cursor returns them in r0L.
T_POSROWS .block
        #tpl
        phx
        sec
        #rec jsr, S_PLOT
        lda $02
        plx
        #endtpl
        .endblock

; A = the screen's columns. POS(3) uses it. 6502DOS's con_cursor returns them in r0H.
T_POSCOLS .block
        #tpl
        phx
        sec
        #rec jsr, S_PLOT
        lda $03
        plx
        #endtpl
        .endblock

; A = the next key, or 0 when no key is waiting.
T_GETKEY .block
        #tpl
        phx
        #rec jsr, S_GETIN
        plx
        #endtpl
        .endblock

; GETEXTKEY(): A/Y = the waiting key, or 0 when no key waits.
T_GETEXTKEY .block
        #tpl
        sec
        #rec jsr, R_KEY
        #endtpl
        .endblock

; WAITKEY(): A/Y = the next key. It waits for one, the cursor blinking.
T_WAITKEY .block
        #tpl
        clc
        #rec jsr, R_KEY
        #endtpl
        .endblock

; KEYMODS(): A = the modifiers of the last GETEXTKEY() or WAITKEY().
T_KEYMODS .block
        #tpl
        #rec lda, R_KEYMODS
        #endtpl
        .endblock

; The data records, RAM outside the file (MACROS.ASM).

; The modifiers of the last key R_KEY returned, 0 before the first.
R_KEYMODS .block
        #data 1, 1
        .endblock

; R_PRLONG's digits: [max][len], a sign and 10 digits.
R_LBUF  .block
        #data 13, 0
        .endblock

; S_CHRIN's line.
R_LINE  .block
        #data 84, 1
next    = 0                     ; the offset in line of the next character, 0 when none is left
line    = 1                     ; [max][len], the text, the CR
        .endblock

; At startup: the first byte of the data record S0 = 0.
T_STZ   .block
        #tpl
        #ab stz, S0
        #endtpl
        .endblock

; T_OPEN for O.APPEND, 6502DOS only.
T_OPENA .block
        #tpl
        #rec jsr, R_FILE, R_FILE.append - R_FILE.rec_code
        #endtpl
        .endblock

; At startup, with #DATA: copy S2 bytes, 1 or more, from S0 to S1. The string literals go from
; the file to the data area, where the kernel reads them from any ROM bank. Keeps X.
T_LITCOPY .block
        #tpl
        #lo lda, S0
        sta ZP_PTR
        #hi lda, S0
        sta ZP_PTR+1
        #lo lda, S1
        sta ZP_DST
        #hi lda, S1
        sta ZP_DST+1
        phx
        #hi ldx, S2             ; the whole pages
        ldy #0
page    beq part
whole   lda (ZP_PTR),y
        sta (ZP_DST),y
        iny
        bne whole
        inc ZP_PTR+1
        inc ZP_DST+1
        dex
        bra page
part    #lo ldx, S2             ; the rest
        beq done
rest    lda (ZP_PTR),y
        sta (ZP_DST),y
        iny
        dex
        bne rest
done    plx
        #endtpl
        .endblock

; #ROMBANKS: T_FAR's word, the address of the SUB it calls.
R_FARVEC .block
        #data 2, 0
        .endblock

; #ROMBANKS: the call into the other ROM bank. pyuxc places it at K_FAR in both banks, so that
; its 23 bytes end at $FFA0, where the IRQ entry starts. S0 is the other bank. A T_FARCALL
; enters with the SUB's address in A/Y. Keeps X; returns A, Y and C, and N and Z from A.
; Trap: a write to ROM_BANK goes on at the next address in the other bank, so both copies must
; lie at one address with one layout.
T_FAR   .block
        #tpl
        #rec sta, R_FARVEC
        #rec sty, R_FARVEC, 1
        #lo lda, S0
        sta $01                 ; ROM_BANK: the other bank's copy goes on at the jsr
        #self jsr, jump
        pha
        #lo lda, S0             ; seen from the bank called, the caller's bank
        sta $01
        pla
        rts
jump    #recind R_FARVEC
        #endtpl
        .endblock

; #ROMBANKS: the veneer of a SUB in the other ROM bank, which a call to it reaches. A/Y = S0, the
; SUB's address there, then a jump to T_FAR at S1.
T_FARCALL .block
        #tpl
        #lo lda, S0
        #hi ldy, S0
        #ab jmp, S1
        #endtpl
        .endblock

tpl_count = len(tpl_all)
index   .word tpl_all
