; T-FILE.ASM -- OPEN, CLOSE, PRINT #, INPUT #, LINPUT #, EOF, READ and WRITE.
;
; PRINT #F%, "HI" is the load of F%, T_CHKOUT, the items as PRINT has them, T_CLRCHN.

; A/Y = the handle of the file whose whole DOS name is the string at A/Y, or NOFILE.
T_OPEN  .block
        #tpl
        #rec jsr, R_FILE
        #endtpl
        .endblock

; Close the handle in A.
T_CLOSE .block
        #tpl
        #rec jsr, R_FILE, R_FILE.close - R_FILE.rec_code
        #endtpl
        .endblock

; Send the output to the handle in A.
T_CHKOUT .block
        #tpl
        #rec jsr, R_FILE, R_FILE.chkout - R_FILE.rec_code
        #endtpl
        .endblock

; Send the output back to the screen.
T_CLRCHN .block
        #tpl
        #rec jsr, R_FILE, R_FILE.clrchn - R_FILE.rec_code
        #endtpl
        .endblock

; T_OPEN for O.READ: the first byte is read ahead.
T_FOPEN .block
        #tpl
        #rec jsr, R_FIN
        #endtpl
        .endblock

; Take the input from the handle in A.
T_CHKIN .block
        #tpl
        #rec jsr, R_FIN, R_FIN.chkin - R_FIN.rec_code
        #endtpl
        .endblock

; The block at A/Y = the next field of the input.
T_FINPUT .block
        #tpl
        #rec jsr, R_FIN, R_FIN.field - R_FIN.rec_code
        #endtpl
        .endblock

; The block at A/Y = the next line of the input.
T_FLINPUT .block
        #tpl
        #rec jsr, R_FIN, R_FIN.line - R_FIN.rec_code
        #endtpl
        .endblock

; C set when the handle in A has nothing more to read.
T_EOF   .block
        #tpl
        #rec jsr, R_FIN, R_FIN.eof - R_FIN.rec_code
        #endtpl
        .endblock

; A/Y = READ(handle, address, max): the handle and the address were pushed, the max is in A/Y.
T_READ  .block
        #tpl
        #rec jsr, R_FREAD
        #endtpl
        .endblock

; WRITE handle, address, count: the handle and the address were pushed, the count is in A/Y.
T_WRITE .block
        #tpl
        #rec jsr, R_FWRITE
        #endtpl
        .endblock
