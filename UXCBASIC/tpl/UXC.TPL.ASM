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
        ldy #0
        #hi ldx, S2             ; the whole pages
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

; #REGION_SLOT: the records below are 6502DOS only. The stock table assembles them with these
; placeholders, and pyuxc never emits them for it.
        .if UXDOS == 0
API_R0  = $02
API_R1  = $04
API_BANK_ALLOC = 0
API_BANK_CALL = 0
API_EXEC_REST = 0
        .endif
; The end of low RAM: exec loads a program up to here, and exec_rest reads the rest of the file.
LOW_END = $9f00

; #REGION_SLOT: the gate between low RAM and one region, one a region, in low RAM. A T_FARCALL
; enters with the SUB's address in A/Y. bank_call calls it with the region's bank selected, then
; selects the caller's bank again. Keeps X; returns A, Y and C, and N and Z from A. A call out of
; a region to a SUB in low RAM goes through the region's own gate, so a SUB that selects another
; bank returns to the region.
; Trap: the operand of the lda, at byte 5, is the region's bank, which T_RGLOAD writes at
; startup.
T_RGGATE .block
        #tpl
        sta API_R0
        sty API_R0+1
        lda #0
        jmp API_BANK_CALL
        #endtpl
        .endblock

; #REGION_SLOT, first at startup: ZP_PTR = S0, where the first region's image starts. The images
; follow each other.
T_RGFROM .block
        #tpl
        #lo lda, S0
        sta ZP_PTR
        #hi lda, S0
        sta ZP_PTR+1
        #endtpl
        .endblock

; #REGION_SLOT, at startup, one a region after T_RGFROM: copy the region's S0 bytes into a RAM
; bank, then put the bank at S1, the bank byte of the region's T_RGGATE.
T_RGLOAD .block
        #tpl
        #lo lda, S0
        #hi ldy, S0
        #rec jsr, R_RGLOAD
        #ab sta, S1
        #endtpl
        .endblock

; #REGION_SLOT: take a RAM bank and copy A/Y bytes, 1 or more, from ZP_PTR to $A000 there.
; The bytes from LOW_END on come from the program's file, by exec_rest. Out: A the bank, ZP_PTR
; just past the bytes copied, at most LOW_END. No bank free stops with OUT OF MEMORY, and a read
; fault with LOAD ERROR. Keeps X and the caller's bank. Changes r0 and r1.
; Trap: the images lie where the array space, the temps and the data records go, so nothing may
; write there before the last copy ends.
R_RGLOAD .block
        #tpl
        phx
        ldx $00
        phx                     ; the caller's bank
        sta API_R1              ; the size
        sty API_R1+1
        lda #1
        jsr API_BANK_ALLOC
        bcc got
        #rec jsr, R_EMEM
got     sta $00
        stz ZP_DST
        lda #$a0
        sta ZP_DST+1
        sec                     ; r0: the bytes from ZP_PTR to LOW_END, at most the size
        lda #<LOW_END
        sbc ZP_PTR
        tax
        lda #>LOW_END
        sbc ZP_PTR+1
        cmp API_R1+1
        bcc less
        bne all
        cpx API_R1
        bcc less
all     ldx API_R1
        lda API_R1+1
less    stx API_R0
        sta API_R0+1
        sec                     ; r1: the bytes the file holds
        lda API_R1
        sbc API_R0
        sta API_R1
        lda API_R1+1
        sbc API_R0+1
        sta API_R1+1
        ldy #0
        ldx API_R0+1            ; the whole pages
page    beq part
whole   lda (ZP_PTR),y
        sta (ZP_DST),y
        iny
        bne whole
        inc ZP_PTR+1
        inc ZP_DST+1
        dex
        bra page
part    ldx API_R0              ; the rest
        beq done
rest    lda (ZP_PTR),y
        sta (ZP_DST),y
        iny
        dex
        bne rest
        tya                     ; ZP_PTR past the rest
        clc
        adc ZP_PTR
        sta ZP_PTR
        bcc done
        inc ZP_PTR+1
done    lda API_R1
        ora API_R1+1
        beq loaded
        sty API_R0              ; the read goes on where the copy ended
        lda ZP_DST+1
        sta API_R0+1
        jsr API_EXEC_REST
        bcc loaded
        #rec jsr, R_ERROR
        .byte 10
        .text "LOAD ERROR"
loaded  lda $00
        plx
        stx $00
        plx
        rts
        #endtpl
        .endblock

R_EMEM  .block
        #tpl
        #rec jsr, R_ERROR
        .byte 13
        .text "OUT OF MEMORY"
        #endtpl
        .endblock

; R_ERROR for a program with #REGION_SLOT: a site in the region prints as $<bank>:<site>. pyuxc
; places it in R_ERROR's stead.
R_ERRORB .block
        #tpl
        #error_body 1
        #endtpl
        .endblock

; A = the BYTE at the address in the WORD variable S0, plus the BYTE variable S1:
; ContentsAt(P + B).
T_PEEK_VB .block
        #tpl
        #ab lda, S0
        sta ZP_PTR
        #ab lda, S0, 1
        sta ZP_PTR+1
        #ab ldy, S1
        lda (ZP_PTR),y
        #endtpl
        .endblock

; The BYTE at the address in the WORD variable S0, plus the BYTE variable S1, = A:
; ContentsAt(P + B) = A.
T_POKE_VB .block
        #tpl
        #ab ldy, S0
        sty ZP_PTR
        #ab ldy, S0, 1
        sty ZP_PTR+1
        #ab ldy, S1
        sta (ZP_PTR),y
        #endtpl
        .endblock

; A = the BYTE at the address S0, plus the BYTE variable S1: ContentsAt(@X + B).
T_PEEK_AB .block
        #tpl
        #ab ldy, S1
        #aby lda, S0
        #endtpl
        .endblock

; The BYTE at the address S0, plus the BYTE variable S1, = A: ContentsAt(@X + B) = A.
T_POKE_AB .block
        #tpl
        #ab ldy, S1
        #aby sta, S0
        #endtpl
        .endblock

; A/Y = the WORD array S0, element A. A is below 128. The flags are Y's.
T_LDW_AY .block
        #tpl
        asl a
        tay
        #aby lda, S0, 1
        pha
        #aby lda, S0
        ply
        #endtpl
        .endblock

; The WORD array S0, at the BYTE index popped off the expression stack, = A/Y. The index is
; below 128.
T_STW_SY .block
        #tpl
        dex
        dex
        phy
        asl ESTK,x
        ldy ESTK,x
        #aby sta, S0
        pla
        #aby sta, S0, 1
        #endtpl
        .endblock

; #REGION_SLOT, at startup after the last T_RGLOAD: closes the program's file, which exec leaves
; open when it fills low RAM. It returns error 6 when the file is not open.
T_RGEND .block
        #tpl
        stz API_R1
        stz API_R1+1
        jsr API_EXEC_REST
        #endtpl
        .endblock

tpl_count = len(tpl_all)
index   .word tpl_all
