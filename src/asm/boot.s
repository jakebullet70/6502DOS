; 6502DOS ROM bank 0: reset, the IRQ, the boot banner, the power-on screen and the boot shell.

.setcpu "65C02"

.include "mem.inc"
.include "api.inc"
.include "far.inc"

.import CHROUT, gate_init, kernel_init, heap_init, bank_init, monitor, monitor_brk, put_decimal
.import sd_ready
.importzp mon_number
.export boot_shell, irq
.exportzp ticks

.define SHELL_PATH "C:\ROMSHELL.COM"   ; starts the shell in ROM banks 3 and 4

.segment "KERNELZP" : zeropage

ticks:        .res 4            ; VSYNCs since boot

.segment "CODE"

reset:
        sei
        cld
        ldx #$FF
        txs
        ldx #$FF - KERNEL_ZP
@zero:
        stz KERNEL_ZP,x
        dex
        bpl @zero
        stz ROM_BANK            ; trap: reads back as noise until written
        stz RAM_BANK
        stz KBD_COUNT
        jsr gate_init
        jsr kernel_init
        jsr heap_init
        jsr bank_init
        sty r2                  ; the number of banks, for post
        stz PSP_BREAK           ; BREAK_OFF for the monitor
        lda #$01                ; VSYNC
        sta VERA_IEN
        cli
        lda boot_shell
        bne @post
        ldx #banner - texts
        jsr print
        bra @monitor
@post:
        ldx #<(logo - logo_end) ; the logo, then the banner
@logo:
        lda logo_end - $100,x   ; X counts up to 0
        jsr CHROUT
        inx
        bne @logo
        ldx #banner - texts
        jsr print
        jsr post
        bcs @monitor
        lda #>PSP               ; exec saves only boot's PSP and zero page
        sta PSP_TOP
@shell:
        ldx #.strlen(SHELL_PATH)
@copy:
        lda shell_path,x        ; to RAM: bank 1 opens the file and cannot read this bank
        sta MONITOR_LINE,x
        dex
        bpl @copy
        lda #<MONITOR_LINE
        sta r0
        lda #>MONITOR_LINE
        sta r0+1
        jsr API_EXEC            ; r1 = the tail post chose
        jsr no_tail             ; the shell runs again with no tail
        bcc @shell              ; the shell ended: run it again
        ldx #<MONITOR_OUT       ; exec failed: A = the error
        stx r0
        ldx #>MONITOR_OUT
        stx r0+1
        jsr API_ERRMSG
        ldx #cannot - texts
        jsr print
        ldy #0
@message:                       ; the length, then the message
        cpy MONITOR_OUT
        beq @end
        iny
        lda MONITOR_OUT,y
        jsr CHROUT
        bra @message
@end:
        ldx #banner_end - 2 - texts ; CR, LF
        jsr print
@monitor:                       ; no shell, a key chose the monitor, or exec failed
        lda #>PROGRAM_END
        sta PSP_TOP
        jmp monitor

; post: shows the power-on screen after the banner: the copyright, a count up to the banked
; RAM, the VERA version and the SD card, then counts 2 seconds down. Enter or Space ends the
; count at once, F5 gives the shell the tail -N and F8 the tail -S, F2 or Delete chooses the
; monitor. r2 = the number of banks, 0 for 256. Returns carry set for the monitor, else carry
; clear and r1 = the tail. Changes A, X, Y, r1 to r5 and MONITOR_OUT.
post:
        ldx #copyright - texts
        jsr print
        ldx #memory - texts
        jsr print
        stz r1                  ; r1 = the K counted, r3 = the banks counted
        stz r1+1
        stz r3
@frame:                         ; 8 banks, 64K, a frame
        lda ticks
@wait:
        cmp ticks
        beq @wait
        lda r3
        clc
        adc #8
        sta r3
        lda r1
        clc
        adc #64
        sta r1
        bcc @show
        inc r1+1
@show:
        ldy r1+1
        jsr print_word
        lda r3
        cmp r2
        beq @counted
@back:                          ; X = the digits
        lda #$08
        jsr CHROUT
        dex
        bne @back
        bra @frame
@counted:
        ldx #k_ok - texts
        jsr print
        lda #63 << 1            ; DCSEL 63: the version in DC_VIDEO to DC_BORDER
        sta VERA_CTRL
        ldx #3
@version:
        lda VERA_DC_VIDEO,x
        sta r4,x
        dex
        bpl @version
        stz VERA_CTRL           ; trap: bit 7 resets VERA, so never write it set here
        lda r4
        cmp #'V'
        bne @sd                 ; a VERA too old to give its version
        ldx #vera - texts
        jsr print
        lda r4+1
        jsr print_byte
        lda #'.'
        jsr CHROUT
        lda r4+2
        jsr print_byte
        lda #'.'
        jsr CHROUT
        lda r4+3
        jsr print_byte
        lda #$0D
        jsr CHROUT
@sd:
        ldx #sd_card - texts
        jsr print
        ldx #none - texts
        lda sd_ready
        beq @card
        ldx #ok - texts
@card:
        jsr print
        ldx #keys - texts
        jsr print
        jsr no_tail
        lda #'2'                ; r3 = the second shown
        sta r3
@second:
        lda r3
        jsr CHROUT
        lda ticks
        clc
        adc #60
        sta r2                  ; r2 = the tick that ends the second
@poll:
        sec
        jsr API_CON_GETKEY      ; A = the character, X = the scan code
        cmp #$0D
        beq @go
        cmp #' '
        beq @go
        txa
        ldx #post_tails_low - post_scans - 1
@key:
        cmp post_scans,x
        beq @found
        dex
        bpl @key
        lda ticks
        cmp r2
        bne @poll
        lda #$08
        jsr CHROUT
        dec r3
        lda r3
        cmp #'0'
        bne @second
        bra @go
@found:
        cpx #post_tails_high - post_tails_low
        bcs @end                ; F2 or Delete: carry set
        lda post_tails_low,x
        sta r1
        lda post_tails_high,x
        sta r1+1
@go:
        clc
@end:
        php
        lda #$0D
        jsr CHROUT
        plp
        rts

; no_tail: sets r1 to the empty tail. Keeps carry. Changes X.
no_tail:
        ldx #<tail_none
        stx r1
        ldx #>tail_none
        stx r1+1
        rts

; print_byte: writes A in decimal. print_word: writes A and Y, the high byte, in decimal. Both
; return X = the digits written. Change A, Y, mon_number and MONITOR_OUT.
print_byte:
        ldy #0
print_word:
        sta mon_number
        sty mon_number+1
        stz mon_number+2
        stz mon_number+3
        ldy #9
        jsr put_decimal
        ldx #0
@digit:
        iny
        inx
        lda MONITOR_OUT,y
        jsr CHROUT
        cpy #9
        bne @digit
        rts

; print: writes the text at texts + X, up to a 0. Changes A and X.
print:
        lda texts,x
        beq @done
        jsr CHROUT
        inx
        bra print
@done:
        rts

; irq: counts VSYNCs, the only VERA interrupt on. A BRK goes to the monitor. irq_entry jumps
; here with A and the interrupted ROM bank on the stack.
irq:
        phx
        tsx
        lda STACK+4,x           ; P as the interrupt pushed it
        and #$10                ; B
        beq @vsync
        plx
        pla                     ; the bank: the monitor runs in bank 0
        phx
        tsx
        jmp monitor_brk         ; X = S: X, A, P and PC above it
@vsync:
        lda #$01                ; VSYNC
        sta VERA_ISR
        inc ticks
        bne @done
        inc ticks+1
        bne @done
        inc ticks+2
        bne @done
        inc ticks+3
@done:
        plx
        jmp irq_exit

nmi:
        pha
        lda ROM_BANK            ; the interrupted bank
        pha
        jmp irq_exit

logo:                           ; a 6502 in CP437 box lines, cyan and red, at the top right
        .byte $1B, "[1;73H", $1B, "[36m", $DA
        .res 6, $C1
        .byte $BF
        .byte $1B, "[2;73H", $B4, $1B, "[31m 6502 ", $1B, "[36m", $C3
        .byte $1B, "[3;73H", $C0
        .res 6, $C2
        .byte $D9, $1B, "[m", $1B, "[H"
logo_end:
        .assert logo_end - logo <= 256, error, "the logo loop counts with X"

texts:                          ; print reaches each text from here
banner:
        .byte "6502DOS V", VERSION_TEXT, $0D, $0A
        .byte "For the Commander X16", $0D, $0A
banner_end:
tail_none:                      ; the banner's 0, an empty tail
        .byte 0
copyright:
        .byte "Copyright (c) 2026 Steven De George SR", $0D, $0D, 0
memory:
        .byte "Memory Test: ", 0
k_ok:
        .byte "K "
ok:
        .byte "OK", $0D, 0
vera:
        .byte "VERA V", 0
sd_card:
        .byte "SD card: ", 0
none:
        .byte "none", $0D, 0
keys:
        .byte $0D, "F5 Skip STARTUP.CMD  F8 Step  DEL Monitor", $0D
        .byte "Starting 6502DOS... ", 0
cannot:
        .byte "Cannot run ", SHELL_PATH, ": ", 0
        .assert * - texts <= 256, error, "print reaches the texts with X"

; The scan codes post takes: F5 and F8, which have the tails below, then F2 and Delete, which
; choose the monitor.
post_scans:
        .byte $3F, $42, $3C, $53
post_tails_low:
        .byte <tail_skip, <tail_step
post_tails_high:
        .byte >tail_skip, >tail_step
tail_skip:                      ; a tail starts with its space, as the shell's do
        .byte 3, " -N"
tail_step:
        .byte 3, " -S"

; boot_shell: 1 runs SHELL_PATH at boot, 0 goes to the monitor. tools/build.py clears it in
; build/TEST.ROM, the ROM the tests boot.
boot_shell:
        .byte 1
shell_path:
        .byte .strlen(SHELL_PATH), SHELL_PATH

.segment "FARIRQ0"

irq_entry:
        FAR_IRQ_ENTRY
irq_exit:
        FAR_IRQ_EXIT

.segment "SIGNATURE"

        .byte "MIST"            ; x16emu turns on -echo and its KERNAL hooks only with this

.segment "VECTORS"

        .word nmi
        .word reset
        .word irq_entry
