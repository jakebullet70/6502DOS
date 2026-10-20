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
        #rec lda, R_KEY, R_KEY.mods - R_KEY.rec_code
        #endtpl
        .endblock

tpl_count = len(tpl_all)
index   .word tpl_all
