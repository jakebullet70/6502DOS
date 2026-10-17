; T-CORE.ASM -- start and end, loads, stores, the expression stack, POKE and PEEK.
;
; An expression's value is in A (a BYTE), or in A low and Y high (a WORD or an address).
; Assignment is a load then a store: N% = 5 is T_LDW_C then T_STW_V. POKE to a constant
; address is T_STB_V with the address as the slot.

; The BASIC line 10 SYS 2061, for a program at $0801.
T_STUB  .block
        #tpl
        .word $080b, 10
        .text $9e, "2061", 0
        .word 0
        #endtpl
        .endblock

; Startup: keep the stack pointer for END, switch the screen to CP437, and empty the
; expression stack.
T_START .block
        #tpl
        tsx
        stx ZP_SP
        #rec jsr, S_INIT
        ldx #0
        #endtpl
        .endblock

; END, from anywhere, even inside a SUB: S_EXIT ends the program with exit code 0.
T_END   .block
        #tpl
        #rec jmp, S_EXIT
        #endtpl
        .endblock

; A = the BYTE constant S0
T_LDB_C .block
        #tpl
        #lo lda, S0
        #endtpl
        .endblock

; A/Y = the WORD constant S0, or the address S0 (@name, a string)
T_LDW_C .block
        #tpl
        #lo lda, S0
        #hi ldy, S0
        #endtpl
        .endblock

; A = the BYTE variable S0
T_LDB_V .block
        #tpl
        #ab lda, S0
        #endtpl
        .endblock

; A/Y = the WORD variable S0
T_LDW_V .block
        #tpl
        #ab lda, S0
        #ab ldy, S0, 1
        #endtpl
        .endblock

; A/Y = the BYTE variable S0, made a WORD
T_LDW_B .block
        #tpl
        #ab lda, S0
        ldy #0
        #endtpl
        .endblock

; The BYTE in A made a WORD in A/Y
T_WIDEN .block
        #tpl
        ldy #0
        #endtpl
        .endblock

; The BYTE variable S0 = A. Also POKE to the constant address S0.
T_STB_V .block
        #tpl
        #ab sta, S0
        #endtpl
        .endblock

; The WORD variable S0 = A/Y
T_STW_V .block
        #tpl
        #ab sta, S0
        #ab sty, S0, 1
        #endtpl
        .endblock

; Push A/Y on the expression stack.
T_PUSH  .block
        #tpl
        sta ESTK,x
        sty ESTK+1,x
        inx
        inx
        #endtpl
        .endblock

; POKE: the address was pushed, the BYTE value is in A. Pops the address.
T_POKE  .block
        #tpl
        dex
        dex
        sta (ESTK,x)
        #endtpl
        .endblock

; PEEK: A = the byte at the address in A/Y. PEEK of a constant address is T_LDB_V.
T_PEEK  .block
        #tpl
        sta ZP_PTR
        sty ZP_PTR+1
        lda (ZP_PTR)
        #endtpl
        .endblock

; JSR to the address S0: a SUB.
T_JSR   .block
        #tpl
        #ab jsr, S0
        #endtpl
        .endblock

; Push the BYTE in A as a WORD. The left side of an operator is pushed before the right
; side's type is known, so a BYTE goes on the stack with a zero high byte.
T_PUSHB .block
        #tpl
        sta ESTK,x
        stz ESTK+1,x
        inx
        inx
        #endtpl
        .endblock

; Return from a SUB.
T_RTS   .block
        #tpl
        rts
        #endtpl
        .endblock

; Pop a word off the expression stack into the BYTE variable S0: its low byte.
T_POPB_V .block
        #tpl
        dex
        dex
        lda ESTK,x
        #ab sta, S0
        #endtpl
        .endblock

; Pop a word off the expression stack into the WORD variable S0.
T_POPW_V .block
        #tpl
        dex
        dex
        lda ESTK,x
        #ab sta, S0
        lda ESTK+1,x
        #ab sta, S0, 1
        #endtpl
        .endblock

; The signed BYTE in A made a WORD in A/Y
T_SWIDEN .block
        #tpl
        ldy #0
        cmp #$80
        bcc done
        dey
done
        #endtpl
        .endblock

; A LONG is in A/Y, the low word, and ZP_HI, the high word.

; A/Y/ZP_HI = the LONG constant S0 + 65536 x S1
T_LDL_C .block
        #tpl
        #lo lda, S1
        sta ZP_HI
        #hi lda, S1
        sta ZP_HI+1
        #lo lda, S0
        #hi ldy, S0
        #endtpl
        .endblock

; A/Y/ZP_HI = the LONG variable S0
T_LDL_V .block
        #tpl
        #ab lda, S0, 2
        sta ZP_HI
        #ab lda, S0, 3
        sta ZP_HI+1
        #ab lda, S0
        #ab ldy, S0, 1
        #endtpl
        .endblock

; The LONG variable S0 = A/Y/ZP_HI. A is lost.
T_STL_V .block
        #tpl
        #ab sta, S0
        #ab sty, S0, 1
        lda ZP_HI
        #ab sta, S0, 2
        lda ZP_HI+1
        #ab sta, S0, 3
        #endtpl
        .endblock

; The WORD in A/Y made a LONG
T_LWIDEN .block
        #tpl
        stz ZP_HI
        stz ZP_HI+1
        #endtpl
        .endblock

; The signed WORD in A/Y made a LONG
T_LSWIDEN .block
        #tpl
        pha
        tya
        ora #$7f                ; $FF when the sign is set
        bmi +
        lda #0
+       sta ZP_HI
        sta ZP_HI+1
        pla
        #endtpl
        .endblock

; Push A/Y/ZP_HI on the expression stack.
T_PUSHL .block
        #tpl
        sta ESTK,x
        sty ESTK+1,x
        lda ZP_HI
        #recx sta, R_ESTKH
        lda ZP_HI+1
        #recx sta, R_ESTKH, 1
        inx
        inx
        #endtpl
        .endblock

; Pop a LONG off the expression stack into the LONG variable S0.
T_POPL_V .block
        #tpl
        dex
        dex
        lda ESTK,x
        #ab sta, S0
        lda ESTK+1,x
        #ab sta, S0, 1
        #recx lda, R_ESTKH
        #ab sta, S0, 2
        #recx lda, R_ESTKH, 1
        #ab sta, S0, 3
        #endtpl
        .endblock

; The WORD on top of the expression stack made a LONG. Keeps A, Y and ZP_HI.
T_STKWIDEN .block
        #tpl
        #recx stz, R_ESTKH, $fffe
        #recx stz, R_ESTKH, $ffff
        #endtpl
        .endblock

; The signed WORD on top of the expression stack made a LONG. Keeps A, Y and ZP_HI.
T_STKSWIDEN .block
        #tpl
        pha
        lda ESTK-1,x
        ora #$7f                ; $FF when the sign is set
        bmi +
        lda #0
+       #recx sta, R_ESTKH, $fffe
        #recx sta, R_ESTKH, $ffff
        pla
        #endtpl
        .endblock

; END code, from anywhere: the exit code is the BYTE in A. The stock ROM has no exit code.
T_ENDCODE .block
        #tpl
        .if UXDOS != 0
        jmp API_EXIT
        .else
        #rec jmp, S_EXIT
        .endif
        #endtpl
        .endblock
