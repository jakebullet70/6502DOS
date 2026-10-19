.segment "EXTRA"

; ----------------------------------------------------------------------------
; I/O for sim65 through its paravirtualization calls.
; PVRead/PVWrite use the cc65 calling convention: fd and buffer are pushed on
; the C stack at (SIM_CSP), the count is passed in A/X, the result comes back
; in A/X. Every call rebuilds the 4-byte parameter frame in SIMPARM.
; ----------------------------------------------------------------------------

SIMCHAR:
        .res    1
SIMPARM:
        .res    4               ; buf lo, buf hi, fd lo, fd hi

; set up a frame for one byte at SIMCHAR on fd A; returns count 1 in A/X
SIMFRAME:
        sta     SIMPARM+2
        lda     #0
        sta     SIMPARM+3
        lda     #<SIMCHAR
        sta     SIMPARM
        lda     #>SIMCHAR
        sta     SIMPARM+1
        lda     #<SIMPARM
        sta     SIM_CSP
        lda     #>SIMPARM
        sta     SIM_CSP+1
        lda     #1
        ldx     #0
        rts

SIMECHO:
        .byte   $FF             ; $FF: not checked yet, 0: no echo, 1: echo

; Echo is on when sim65 gets any argument after the program file
; ("sim65 sim.bin echo"). An interactive console already echoes what is
; typed; tests feed stdin from a file and want it in the transcript.
; PVArgs copies the arguments below the C stack pointer, so point it at
; free RAM under RAMSTART2 first. It returns argc (program name included).
SIMARGS:
        lda     #<SIM_ARGS_TOP
        sta     SIM_CSP
        lda     #>SIM_ARGS_TOP
        sta     SIM_CSP+1
        lda     #<SIMPARM       ; argv pointer lands here, unused
        ldx     #>SIMPARM
        jsr     SIM_PV_ARGS
        ldy     #0
        cpx     #0
        bne     @echo
        cmp     #2
        bcc     @set
@echo:
        iny
@set:
        sty     SIMECHO
        rts

; ----------------------------------------------------------------------------
; Handle primitives for handle_io.s. sim65 handles are host file descriptors.
; Text conversion on every handle: BASIC uses CR, host files use LF.
; ----------------------------------------------------------------------------

SIMRSAVE:
        .res    2               ; X, Y in K_READ
SIMWSAVE:
        .res    2               ; X, Y in K_WRITE

; X = handle. Returns carry clear and the byte in A, or carry set at end of
; file. Keeps X and Y. LF becomes CR; CR is dropped, so CRLF files work.
; Console (K_STDIN): end of file exits sim65 with code 0. With echo on,
; characters go to stdout like a terminal would, so stdout is a full
; session transcript. BASIC prints the newline itself.
K_READ:
        stx     SIMRSAVE
        sty     SIMRSAVE+1
        cpx     #K_STDIN
        bne     @again
        bit     SIMECHO
        bpl     @again
        jsr     SIMARGS
@again:
        lda     SIMRSAVE
        jsr     SIMFRAME
        jsr     SIM_PV_READ
        cmp     #1
        bne     @eof
        lda     SIMCHAR
        cmp     #$0D
        beq     @again
        cmp     #$0A
        bne     @echo
        lda     #$0D
        bne     @done
@echo:
        ldx     SIMRSAVE
        cpx     #K_STDIN
        bne     @done
        ldy     SIMECHO
        beq     @done
        ldx     #K_STDOUT
        jsr     K_WRITE
@done:
        ldx     SIMRSAVE
        ldy     SIMRSAVE+1
        clc
        rts
@eof:
        ldx     SIMRSAVE
        cpx     #K_STDIN
        bne     @fileeof
        lda     #0
        jmp     SIM_PV_EXIT
@fileeof:
        ldy     SIMRSAVE+1
        sec
        rts

; X = handle, A = byte. Keeps A, X and Y. CR becomes LF; LF is dropped
; (BASIC sends CR LF).
K_WRITE:
        cmp     #$0A
        beq     @skip
        pha
        sta     SIMCHAR
        stx     SIMWSAVE
        sty     SIMWSAVE+1
        cmp     #$0D
        bne     @out
        lda     #$0A
        sta     SIMCHAR
@out:
        txa
        jsr     SIMFRAME
        jsr     SIM_PV_WRITE
        ldx     SIMWSAVE
        ldy     SIMWSAVE+1
        pla
@skip:
        rts

.ifdef CONFIG_PAUSE
; Waits one jiffy (1/60 s) for PAUSE. sim65 has no clock, so this is a busy
; loop of about 16700 cycles (one jiffy at 1 MHz). Changes X and Y.
K_JIFFY:
        ldx     #13
@loop:
        dey
        bne     @loop
        dex
        bne     @loop
        rts
.endif

.ifdef CONFIG_VERA
; Video stubs for VPEEK, VPOKE and SCREEN: the sim has no video chip.
; K_VPEEK: A = bank, LINNUM = address; returns the byte in A (always 0).
; K_VPOKE: A = bank, LINNUM = address, X = byte; does nothing.
; K_SCREEN: X = mode; does nothing.
K_VPEEK:
        lda     #$00
K_SCREEN:
K_VPOKE:
        rts
.endif

; open(name, flags): cc65 calls open() as a variadic function, so the
; parameters are on the C stack and Y holds their size in bytes.
; Read: O_RDONLY. Write: O_WRONLY|O_CREAT|O_TRUNC. Append: O_WRONLY|O_CREAT|O_APPEND.
SIMOPENFLAGS:
        .byte   $01, $32, $52

; Name at HIO_NAME, A = mode. Returns carry clear and the handle in A, or
; carry set.
K_OPEN:
        tax
        lda     SIMOPENFLAGS,x
        sta     SIMPARM
        lda     #0
        sta     SIMPARM+1
        lda     #<HIO_NAME
        sta     SIMPARM+2
        lda     #>HIO_NAME
        sta     SIMPARM+3
        lda     #<SIMPARM
        sta     SIM_CSP
        lda     #>SIMPARM
        sta     SIM_CSP+1
        ldy     #4
        jsr     SIM_PV_OPEN
        cpx     #$FF            ; -1: failed
        beq     @fail
        clc
        rts
@fail:
        sec
        rts

; X = handle.
K_CLOSE:
        txa
        ldx     #0
        jmp     SIM_PV_CLOSE

; fold a-z in A to A-Z; keeps X and Y. The tokenizer uses it so keywords
; and variable names may be typed in lowercase (strings, REM and DATA stay).
SIM_UPPER:
        cmp     #'a'
        bcc     @keep
        cmp     #'z'+1
        bcs     @keep
        and     #$DF
@keep:
        rts
