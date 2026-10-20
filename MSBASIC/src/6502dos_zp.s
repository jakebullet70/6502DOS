; Zero page and RAM data of the 6502DOS target (docs/6502dos-zeropage.md).
; A program owns $22-$7F. A byte that a (zp),y, sty zp,x, sta 0,x or
; sty n,x reaches lives here in zero page, and so do CURLIN, VALTYP and
; EOLPNTR; the rest are RAM data at DOS_DATA.
; Trap: the order inside a group counts. JMPADRS is DSCLEN+1, FACEXTENSION
; is STRNG1+1, EXPSGN is LOWTR's high byte, VALTYP+1 is the integer flag,
; and REASON relies on zero page wrap from TEMP1 to FAC.

.feature org_per_seg
.zeropage

.org PROGRAM_ZP

LINNUM:
TXPSV:
	.res 2
EOLPNTR:
	.res 1
VALTYP:
	.res 2
TEMPST:
	.res 9
INDEX:
	.res 2
DEST:
	.res 2
RESULT:
	.res BYTES_FP
RESULT_LAST = RESULT + BYTES_FP-1
TXTTAB:
	.res 2
FRESPC:
	.res 2
CURLIN:
	.res 2
INPTR:
	.res 2
VARPNT:
	.res 2
FORPNT:
	.res 2
FNCNAM:
TEMP3:
	.res 2
DSCPTR:
	.res 3
TEMP1:
	.res 1
HIGHDS:
	.res 2
HIGHTR:
	.res 2
TEMP2:
	.res 1
INDX:
TMPEXP:
	.res 1
EXPON:
	.res 1
LOWTR:
LOWTRX:
	.res 1
EXPSGN:
	.res 1
FAC:
	.res BYTES_FP
FAC_LAST = FAC + BYTES_FP-1
FACSIGN:
	.res 1
SERLEN:
	.res 1
SHIFTSIGNEXT:
	.res 1
ARG:
	.res BYTES_FP
ARG_LAST = ARG + BYTES_FP-1
ARGSIGN:
	.res 1
STRNG1:
	.res 2
SGNCPR = STRNG1
FACEXTENSION = STRNG1+1
STRNG2:
	.res 2
CHRGET:
TXTPTR = <(GENERIC_TXTPTR-GENERIC_CHRGET + CHRGET)
CHRGOT = <(GENERIC_CHRGOT-GENERIC_CHRGET + CHRGET)
CHRGOT2 = <(GENERIC_CHRGOT2-GENERIC_CHRGET + CHRGET)
CHRGET_SIZE = 24 ; init.s copies GENERIC_CHRGET up to GENERIC_RNDSEED
	.res CHRGET_SIZE
KW_PTR:
	.res 2 ; keyword table pointer (CONFIG_KW16)
.assert * = PROGRAM_ZP_END + 1, error, "the zero page layout must end at $7F"

.segment "DOSDATA"
.org DOS_DATA

GORESTART:
	.res 3
GOSTROUT:
	.res 3
GOAYINT:
	.res 2
GOGIVEAYF:
	.res 2
USR:
	.res 3
Z15:
	.res 1
POSX:
	.res 1
Z17:
	.res 1
Z18:
	.res 1
CHARAC:
	.res 1
ENDCHR:
	.res 1
DIMFLG:
	.res 1
DATAFLG:
	.res 1
SUBFLG:
	.res 1
INPUTFLG:
	.res 1
CPRMASK:
	.res 1
Z14:
	.res 1
TEMPPT:
	.res 1
LASTPT:
	.res 2
VARTAB:
	.res 2
ARYTAB:
	.res 2
STREND:
	.res 2
FRETOP:
	.res 2
MEMSIZ:
	.res 2
OLDLIN:
	.res 2
OLDTEXT:
	.res 2
Z8C:
	.res 2
DATPTR:
	.res 2
VARNAM:
	.res 2
LASTOP:
	.res 2
CPRTYP:
	.res 1
DSCLEN:
	.res 2
JMPADRS := DSCLEN + 1
Z52:
	.res 1
ARGEXTENSION:
	.res 1
RNDSEED:
	.res BYTES_FP ; init.s copies GENERIC_RNDSEED here
CURDVC:
	.res 1 ; current logical file, 0 = console
Z96:
	.res 1 ; ST, status of the last file read
BLK_DEPTH:
	.res 1 ; block.s scan: nesting depth
BLK_LAST:
	.res 1 ; block.s scan: last token on the line
BLK_MODE:
	.res 1 ; block.s scan: TOKEN_ELSE, 0, TOKEN_LOOP or TOKEN_NEXT
POSY:
	.res 1 ; cursor line as in the sim; POS(1) reads con_cursor instead
.assert * <= INPUTBUFFER-5, error, "the RAM data runs into INPUTBUFFER"
