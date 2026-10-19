.segment "CODE"
; ----------------------------------------------------------------------------
; SEE IF CONTROL-C TYPED
; ----------------------------------------------------------------------------
.ifndef CONFIG_CBM_ALL
.include "cbm_iscntc.s"
.endif
.ifdef SIM
.include "sim_iscntc.s"
.endif
;!!! runs into "STOP"
