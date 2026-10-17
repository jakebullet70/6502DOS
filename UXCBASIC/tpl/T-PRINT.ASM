; T-PRINT.ASM -- PRINT. Each item is loaded into A or A/Y first, then printed.
;
; PRINT "HI"; N% is T_LDW_C (the string's address), T_PRSTR, T_LDW_V, T_PRWORD, T_PRNL.
; A trailing ; leaves out T_PRNL.

; Print the string whose block address is in A/Y.
T_PRSTR .block
        #tpl
        #rec jsr, R_PRSTR
        #endtpl
        .endblock

; Print the character in A. PRINT "X" and PRINT CHR$(x) use it in place of T_PRSTR.
T_PRCHR .block
        #tpl
        #rec jsr, S_CHROUT
        #endtpl
        .endblock

; Print the WORD in A/Y in decimal.
T_PRWORD .block
        #tpl
        #rec jsr, R_PRWORD
        #endtpl
        .endblock

; Print the BYTE in A in decimal.
T_PRBYTE .block
        #tpl
        ldy #0
        #rec jsr, R_PRWORD
        #endtpl
        .endblock

; End the line.
T_PRNL  .block
        #tpl
        #rec jsr, R_PRNL
        #endtpl
        .endblock

; Move to the next print zone.
T_PRCOMMA .block
        #tpl
        #rec jsr, R_PRCOMMA
        #endtpl
        .endblock

; A = the cursor column. POS(0) uses it.
T_POSCOL .block
        #tpl
        phx
        sec
        #rec jsr, S_PLOT        ; Y = the column
        tya
        plx
        #endtpl
        .endblock

; A = the cursor row. POS(1) uses it.
T_POSROW .block
        #tpl
        phx
        sec
        #rec jsr, S_PLOT        ; X = the row
        txa
        plx
        #endtpl
        .endblock

; Move the cursor to the column in A. POS(0) = v uses it.
T_POSSETCOL .block
        #tpl
        #rec jsr, R_POSSETCOL
        #endtpl
        .endblock

; Move the cursor to the row in A. POS(1) = v uses it.
T_POSSETROW .block
        #tpl
        #rec jsr, R_POSSETROW
        #endtpl
        .endblock

; Print the signed WORD in A/Y in decimal.
T_PRSWORD .block
        #tpl
        #rec jsr, R_PRSWORD
        #endtpl
        .endblock

; Print the LONG in A/Y/ZP_HI in decimal.
T_PRLONG .block
        #tpl
        #rec jsr, R_PRLONG
        #endtpl
        .endblock

; Print the signed LONG in A/Y/ZP_HI in decimal.
T_PRSLONG .block
        #tpl
        #rec jsr, R_PRSLONG
        #endtpl
        .endblock
