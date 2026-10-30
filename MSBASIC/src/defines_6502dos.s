; 6502DOS target: BASIC in ROM bank 2 of the 6502DOS ROM, $C000-$FFFF.
; BASIC.COM at $0801 selects bank 2 and calls $C000. Console and files go
; through the 6502DOS API (6502dos_extra.s): the console is handle 0 for
; input and handle 1 for output. 65C02 opcodes are allowed.
; The zero page and the RAM data are in 6502dos_zp.s.

.include "mem.inc"
.include "api.inc"
.include "far.inc"

; configuration
CONFIG_2C := 1

CONFIG_SCRTCH_ORDER := 2
CONFIG_HOSTED := 1 ; runs under an operating system (see defines_sim.s)
CONFIG_FILE := 1 ; PRINT#, INPUT#, GET#, CMD, OPEN, CLOSE, SYS
CONFIG_HANDLE_IO := 1 ; files and console through handles (handle_io.s)
CONFIG_BLOCK := 1 ; block IF/ELSE/END IF, DO/LOOP (block.s); needs CONFIG_HANDLE_IO
CONFIG_NO_LET := 1 ; no LET keyword (A=1 still works); keeps the keyword table small
CONFIG_NO_SPC := 1 ; no SPC( (RPT$(32,n) does the same)
CONFIG_KW16 := 1 ; tokenizer and LIST walk the keyword table with KW_PTR (any length)
CONFIG_FAST_FIN := 1 ; FIN reads digits as an integer and floats it once
CONFIG_SAFE_NAMENOTFOUND := 1 ; check both bytes of PTRGET's caller
CONFIG_INSTR := 1 ; INSTR([start,] a$, b$) function
CONFIG_HEXBIN := 1 ; HEX$ and BIN$ functions (hexbin.s)
CONFIG_RPT := 1 ; RPT$(a$ or code, n) function (rpt.s)
CONFIG_CASE := 1 ; UCASE$ and LCASE$ functions (casestr.s)
CONFIG_TEXTAT := 1 ; TEXTAT statement (textat.s); con_cursor and con_colour here
CONFIG_MOD := 1 ; MOD operator (mod.s)
CONFIG_RADIX_LIT := 1 ; $hex and %binary literals (radixlit.s)
CONFIG_PI := 1 ; PI constant keyword
CONFIG_BITFN := 1 ; XOR, SHL and SHR functions (bitfn.s)
CONFIG_DEEK := 1 ; DEEK function and DOKE statement (deek.s)
CONFIG_PAUSE := 1 ; PAUSE jiffies statement, like SLEEP on the X16 (pause.s)
CONFIG_SCREEN := 1 ; CLS and LOCATE by ANSI codes, COLOR by con_colour (textat.s)
CONFIG_VERA := 1 ; VPEEK function and VPOKE statement (vera.s)
CONFIG_QUIT := 1 ; QUIT [n] statement, back to the shell with exit code n (6502dos_extra.s)
CONFIG_HELP := 1 ; HELP [topic] statement, direct mode only, from basic\HELPBAS.HLP in BASIC.COM's folder (6502dos_extra.s)
CONFIG_POS_LINE := 1 ; POS(1) gives the cursor row from con_cursor
CONFIG_PEEK_SAVE_LINNUM := 1 ; PEEK keeps LINNUM, so POKE A,PEEK(B) works
CONFIG_NAME_NOCRUNCH := 1 ; no keyword search inside a name: BORDER is not B,OR,DER
CONFIG_LABELS := 1 ; GOTO name, GOSUB name, RESTORE name with "name:" lines (labels.s)
CONFIG_GOTO_CACHE := 1 ; cache GOTO/GOSUB targets (gotocache.s)
CONFIG_VAR_CACHE := 1 ; cache simple variable addresses (varcache.s)
; LINNUM is not in front of INPUTBUFFER, so program.s copies the line number
; there, as for a buffer at $0200.
CONFIG_INPUTBUFFER_0200 := 1

; constants
SPACE_FOR_GOSUB  := $33
WIDTH            := 80 ; the console is 80x30
WIDTH2           := 70 ; last comma tab stop, as BASIC derives it for width 80

; memory layout, page $08: BASIC.COM, the RAM data, INPUTBUFFER.
; Trap: INPUTBUFFER must not cross a page (INPUTBUFFERX,x), and no program
; text or string may share its page: flow1.s and string.s test #>INPUTBUFFER
; for direct mode.
DOS_STUB         := PROGRAM ; BASIC.COM, at most 15 bytes
DOS_DATA         := $0810 ; the RAM data of 6502dos_zp.s
INPUTBUFFER      := $0860 ; 5 bytes in front, LINE_MAX+1 bytes, CR included
LINE_MAX         := 80 ; longest typed line, one screen row
RAMSTART2        := $0900 ; a 0 byte, then the program text at $0901
.import __IORAM_RUN__ ; segment IORAM, $9C00 in 6502dos.cfg; BASIC's RAM ends below it
.assert >(INPUTBUFFER-5) = >(INPUTBUFFER+LINE_MAX), error, "INPUTBUFFER crosses a page"
.assert >(INPUTBUFFER+LINE_MAX) < >RAMSTART2, error, "INPUTBUFFER shares a page with the program"

; console handles
K_STDIN          := 0
K_STDOUT         := 1
