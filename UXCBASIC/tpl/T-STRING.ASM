; T-STRING.ASM -- the string templates.
;
; A string is a block of [max][len][data], and its value is the block's address in A/Y. A
; string variable is S0, the address of its block. A temp is a block of max 255 that holds the
; result of +, MID$, CHR$ or STR$; the compiler loads its address when the value is needed.
;
; A$ = B$ is the load of B$, then T_SCOPY. A$ = "" is T_SCLEAR. X$ + Y$ is X$, T_SCOPY into a
; temp, Y$, T_SCAT onto the temp. A compare is the left side, T_PUSH, the right side, a core,
; then the tail or the branch of a WORD compare:
;
;   op    core          tail
;   =     SCMP_LR       ZTRUE
;   <>    SCMP_LR       ZFALSE
;   >=    SCMP_LR       CTRUE
;   <     SCMP_LR       CFALSE
;   <=    SCMP_RL       CTRUE
;   >     SCMP_RL       CFALSE

; The block S0 = the string at A/Y, cut at the max of S0.
T_SCOPY .block
        #tpl
        #rec jsr, R_SCAT
        #dw S0
        #endtpl
        .endblock

; The block whose address is in the WORD variable S0, a STRING parameter, = the string at A/Y.
T_SCOPY_P .block
        #tpl
        sta ZP_PTR
        sty ZP_PTR+1
        #ab lda, S0
        #ab ldy, S0, 1
        clc
        #rec jsr, R_SCAT, R_SCAT.block - R_SCAT.rec_code
        #endtpl
        .endblock

; The block S0 = "": its length byte is 0.
T_SCLEAR .block
        #tpl
        #ab stz, S0, 1
        #endtpl
        .endblock

; The block S0 += the string at A/Y, cut at the max of S0.
T_SCAT  .block
        #tpl
        #rec jsr, R_SCAT, R_SCAT.append - R_SCAT.rec_code
        #dw S0
        #endtpl
        .endblock

; C = left >= A/Y, Z = left = A/Y. Pops the left side.
T_SCMP_LR .block
        #tpl
        clc
        #rec jsr, R_SCMP
        #endtpl
        .endblock

; C = A/Y >= left, Z = left = A/Y. Pops the left side.
T_SCMP_RL .block
        #tpl
        sec
        #rec jsr, R_SCMP
        #endtpl
        .endblock

; A = LEN of the string at A/Y. LEN of a variable is T_LDB_V of its address + 1.
T_SLEN  .block
        #tpl
        sta ZP_PTR
        sty ZP_PTR+1
        ldy #1
        lda (ZP_PTR),y
        #endtpl
        .endblock

; A = ASC of the string at A/Y: its first character, or 0 when it is empty.
T_ASC   .block
        #tpl
        sta ZP_PTR
        sty ZP_PTR+1
        ldy #1
        lda (ZP_PTR),y
        beq done
        iny
        lda (ZP_PTR),y
done
        #endtpl
        .endblock

; The block S0 = CHR$(A).
T_CHR   .block
        #tpl
        #ab sta, S0, 2
        lda #1
        #ab sta, S0, 1
        #endtpl
        .endblock

; The block S0 = STR$(A/Y).
T_STR   .block
        #tpl
        sta ZP_TMP
        sty ZP_TMP+1
        #lo lda, S0
        #hi ldy, S0
        #rec jsr, R_STR
        #endtpl
        .endblock

; A/Y = VAL of the string at A/Y.
T_VAL   .block
        #tpl
        #rec jsr, R_VAL
        #endtpl
        .endblock

; The block S0 = MID$(string, start, A/Y). The string and the start were pushed. MID$ with no
; length passes 255.
T_MID   .block
        #tpl
        #rec jsr, R_MID
        #dw S0
        #endtpl
        .endblock

; A = INSTR(string, find, A/Y). The string and find were pushed. INSTR with no start passes 1.
T_INSTR .block
        #tpl
        #rec jsr, R_INSTR
        #endtpl
        .endblock

; The block at A/Y = the field typed, after a "? " prompt. The rest of the line is dropped.
T_INPUT .block
        #tpl
        sec
        #rec jsr, R_INPUT
        #endtpl
        .endblock

; The block at A/Y = the first of several fields typed, after a "? " prompt.
T_INPUT_FIRST .block
        #tpl
        clc
        #rec jsr, R_INPUT
        #endtpl
        .endblock

; The block at A/Y = the next field typed.
T_INPUT_NEXT .block
        #tpl
        clc
        #rec jsr, R_INPUT, R_INPUT.field - R_INPUT.rec_code
        #endtpl
        .endblock

; The block at A/Y = the last field typed. The rest of the line is dropped.
T_INPUT_LAST .block
        #tpl
        sec
        #rec jsr, R_INPUT, R_INPUT.field - R_INPUT.rec_code
        #endtpl
        .endblock

; The block at A/Y = a line typed.
T_LINPUT .block
        #tpl
        #rec jsr, R_INPUT, R_INPUT.line - R_INPUT.rec_code
        #endtpl
        .endblock

; The block S0 = STR$(A/Y), signed.
T_SSTR  .block
        #tpl
        sta ZP_TMP
        sty ZP_TMP+1
        #lo lda, S0
        #hi ldy, S0
        #rec jsr, R_SSTR
        #endtpl
        .endblock

; The block S0 = STR$(A/Y/ZP_HI)
T_LSTR  .block
        #tpl
        pha
        #lo lda, S0
        sta ZP_DST
        #hi lda, S0
        sta ZP_DST+1
        pla
        #rec jsr, R_LSTR
        #endtpl
        .endblock

; The block S0 = STR$(A/Y/ZP_HI), signed
T_SLSTR .block
        #tpl
        pha
        #lo lda, S0
        sta ZP_DST
        #hi lda, S0
        sta ZP_DST+1
        pla
        #rec jsr, R_SLSTR
        #endtpl
        .endblock

; A/Y/ZP_HI = VAL of the string at A/Y, in 32 bits
T_LVAL  .block
        #tpl
        #rec jsr, R_LVAL
        #endtpl
        .endblock

; The block S0 = LEFT$(string, A/Y). The string was pushed.
T_LEFT  .block
        #tpl
        #rec jsr, R_LEFT
        #dw S0
        #endtpl
        .endblock

; The block S0 = RIGHT$(string, A/Y). The string was pushed.
T_RIGHT .block
        #tpl
        #rec jsr, R_RIGHT
        #dw S0
        #endtpl
        .endblock

; The block S0 = UCASE$ of the string at A/Y.
T_UCASE .block
        #tpl
        #rec jsr, R_CASE, R_CASE.upper - R_CASE.rec_code
        #dw S0
        #endtpl
        .endblock

; The block S0 = LCASE$ of the string at A/Y.
T_LCASE .block
        #tpl
        #rec jsr, R_CASE, R_CASE.lower - R_CASE.rec_code
        #dw S0
        #endtpl
        .endblock

; The block at A/Y = UCASE$ of itself.
T_UCASE_SELF .block
        #tpl
        sec
        #rec jsr, R_CASE
        #endtpl
        .endblock

; The block at A/Y = LCASE$ of itself.
T_LCASE_SELF .block
        #tpl
        clc
        #rec jsr, R_CASE
        #endtpl
        .endblock

; The block S0 = TRIM$ of the string at A/Y.
T_TRIM  .block
        #tpl
        #rec jsr, R_TRIM
        #dw S0
        #endtpl
        .endblock

; The block S0 = LTRIM$ of the string at A/Y.
T_LTRIM .block
        #tpl
        #rec jsr, R_TRIM, R_TRIM.ltrim - R_TRIM.rec_code
        #dw S0
        #endtpl
        .endblock

; The block S0 = RTRIM$ of the string at A/Y.
T_RTRIM .block
        #tpl
        #rec jsr, R_TRIM, R_TRIM.rtrim - R_TRIM.rec_code
        #dw S0
        #endtpl
        .endblock
