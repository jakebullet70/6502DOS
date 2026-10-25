; 6502DOS ROM bank 0: reset, the IRQ, the boot banner and the boot shell.

.setcpu "65C02"

.include "mem.inc"
.include "api.inc"
.include "far.inc"

.import CHROUT, gate_init, kernel_init, heap_init, bank_init, monitor, monitor_brk
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
        stz PSP_BREAK           ; BREAK_OFF for the monitor
        lda #$01                ; VSYNC
        sta VERA_IEN
        cli
        ldx #0
        jsr print
        lda boot_shell
        beq @monitor
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
        lda #<banner_end        ; the tail: the banner's 0, an empty tail
        sta r1
        lda #>banner_end
        sta r1+1
        jsr API_EXEC
        bcc @shell              ; the shell ended: run it again
        ldx #<MONITOR_OUT       ; exec failed: A = the error
        stx r0
        ldx #>MONITOR_OUT
        stx r0+1
        jsr API_ERRMSG
        ldx #cannot - banner
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
        ldx #banner_end - 2 - banner ; CR, LF
        jsr print
@monitor:                       ; no shell, or exec failed
        lda #>PROGRAM_END
        sta PSP_TOP
        jmp monitor

; print: writes the text at banner + X, up to a 0. Changes A and X.
print:
        lda banner,x
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

banner:
        .byte "6502DOS V", VERSION_TEXT, $0D, $0A
        .byte "For the Commander X16", $0D, $0A
banner_end:
        .byte 0
cannot:                         ; print reaches it from banner: the texts fit in 256 bytes
        .byte "Cannot run ", SHELL_PATH, ": ", 0

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
