.segment "EXTRA"

.ifdef CONFIG_CBM1_PATCHES
.include "cbm1_patches.s"
.endif

.ifdef SIM
.include "sim_extra.s"
.endif
.ifdef DOS6502
.include "6502dos_extra.s"
.endif

.ifdef CONFIG_HOSTED
; fold a-z in A to A-Z; keeps X and Y. The tokenizer uses it so keywords
; and variable names may be typed in lowercase (strings, REM and DATA stay).
UPPER:
        cmp     #'a'
        bcc     @keep
        cmp     #'z'+1
        bcs     @keep
        and     #$DF
@keep:
        rts
.endif

.ifdef CONFIG_HANDLE_IO
.include "handle_io.s"
.endif

.ifdef CONFIG_BLOCK
.include "block.s"
.endif

.ifdef CONFIG_INSTR
.include "instr.s"
.endif

.ifdef CONFIG_HEXBIN
.include "hexbin.s"
.endif

.ifdef CONFIG_RPT
.include "rpt.s"
.endif

.ifdef CONFIG_CASE
.include "casestr.s"
.endif

.ifdef CONFIG_TEXTAT
.include "textat.s"
.endif

.ifdef CONFIG_MOD
.include "mod.s"
.endif
.ifdef CONFIG_DEEK
.include "deek.s"
.endif
.ifdef CONFIG_PAUSE
.include "pause.s"
.endif
.ifdef CONFIG_VERA
.include "vera.s"
.endif

.ifdef CONFIG_BITFN
.include "bitfn.s"
.endif
.ifdef CONFIG_RADIX_LIT
.include "radixlit.s"
.endif

.ifdef CONFIG_LABELS
.include "labels.s"
.endif

.ifdef CONFIG_GOTO_CACHE
.include "gotocache.s"
.endif

.ifdef CONFIG_VAR_CACHE
.include "varcache.s"
.endif
