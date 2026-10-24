; The monitor: the bring-up tool in ROM, with commands named after MS-DOS DEBUG.
;
;   D [start [end]]   dump, 128 bytes from start, or on from the last dump
;   E addr list       enter the list at addr
;   F start end list  fill start to end with the list, repeated
;   G addr            go: JSR addr; RTS prints CR LF and comes back to the prompt
;   DIR [path]        list the names that match path; a path that ends in \ lists a directory
;   TYPE path         print a file
;   RUN path [tail]   run a program, with the rest of the line as its command tail; its end
;                     prints CR LF, as G does
;
; Numbers are hex, up to 4 digits. A list is hex bytes and strings in " or '. Spaces and commas
; separate. A command is its first letter: DIR is D followed by I, R is RUN and T is TYPE. A BRK shows
; the registers and comes back to the prompt. The monitor reads and writes through the API and
; prints the message of an API error.

.setcpu "65C02"

.include "mem.inc"
.include "api.inc"

.export monitor, monitor_brk
.import to_upper

MONITOR_TEXT  = MONITOR_LINE + 2
LINE_MAX      = 79              ; the prompt, then 78 characters
DUMP_TEXT     = 55              ; the column of a dump line's characters
DIR_COLUMNS   = 23              ; a DIR line: the name, then the size or <DIR> up to column 22
MONITOR_FIND  = MONITOR_OUT + $20 ; DIR's find buffer, past DIR's line
TYPE_CHUNK    = 128             ; TYPE reads this many bytes to MONITOR_OUT at a time

.segment "KERNELZP" : zeropage

mon_value:    .res 2            ; the last number get_hex read
mon_start:    .res 2
mon_end:      .res 2
mon_number    = mon_start       ; 4 bytes, mon_start and mon_end: put_decimal's number
mon_dump:     .res 2            ; where D goes on from
mon_mark:     .res 1
mon_count:    .res 1            ; the bytes in the list
mon_quote:    .res 1
mon_byte:     .res 1
brk_pc:       .res 2            ; the address of the BRK
brk_a:        .res 1            ; brk_a to brk_s in the order of reg_names
brk_x:        .res 1
brk_y:        .res 1
brk_p:        .res 1
brk_s:        .res 1

.segment "CODE"

monitor:
        ldx #$FF
        txs
        ldy #0
        lda #'>'
        jsr put_char
        jsr put_char
        jsr print
        lda #LINE_MAX
        sta MONITOR_LINE
        lda #<MONITOR_LINE
        sta r0
        lda #>MONITOR_LINE
        sta r0+1
        jsr API_CON_LINE
        ldx #0
        jsr skip
        cmp #$0D
        beq monitor
        jsr to_upper
        ldy #command_routines - commands - 1
@find:
        cmp commands,y
        beq @run
        dey
        bpl @find
        bra error
@run:
        inx
        tya
        asl
        tay
        lda command_routines+1,y
        pha
        lda command_routines,y
        pha
        rts                     ; to the command routine

; error: shows ^ Error under the character at X, then the prompt.
error:
        ldy #0
        lda #' '
        inx
@space:
        jsr put_char            ; X + 2 spaces: the prompt is 2 columns
        dex
        bpl @space
        ldx #<text_error
        jsr put_text
        jsr print_line
        bra monitor

; monitor_brk: the IRQ handler jumps here on BRK, with X = S and the stack holding X, A, P and
; the address after the BRK's signature byte.
monitor_brk:
        sty brk_y
        lda STACK+1,x
        sta brk_x
        lda STACK+2,x
        sta brk_a
        lda STACK+3,x
        sta brk_p
        lda STACK+4,x
        sec
        sbc #2
        sta brk_pc
        lda STACK+5,x
        sbc #0
        sta brk_pc+1
        txa
        clc
        adc #5
        sta brk_s
        cld
        cli
        ldy #0
        ldx #<text_pc
        jsr put_text
        lda brk_pc+1
        jsr put_hex
        lda brk_pc
        jsr put_hex
        ldx #0
@register:
        lda #' '
        jsr put_char
        lda reg_names,x
        jsr put_char
        lda #'='
        jsr put_char
        lda brk_a,x
        jsr put_hex
        inx
        cpx #brk_s - brk_a + 1
        bne @register
        jsr print_line
        jmp monitor

dump:
        lda MONITOR_TEXT,x
        jsr to_upper
        cmp #'I'
        bne @dump
        jmp dir
@dump:
        jsr skip
        cmp #$0D
        bne @start
        lda mon_dump
        sta mon_start
        lda mon_dump+1
        sta mon_start+1
        bra @default_end
@start:
        jsr get_start
        jsr skip
        cmp #$0D
        beq @default_end
        jsr get_end
        jsr need_end
        bra @line
@default_end:
        lda mon_start
        clc
        adc #$7F
        sta mon_end
        lda mon_start+1
        adc #0
        sta mon_end+1
        bcc @line
        lda #$FF                ; no further than $FFFF
        sta mon_end
        sta mon_end+1
@line:
        ldy #DUMP_TEXT + 15
        jsr blank
        iny
        lda mon_start+1
        jsr put_hex
        lda mon_start
        jsr put_hex
        ldy #6
        ldx #0
@byte:
        cpx #8
        bne @hex
        lda #'-'
        sta MONITOR_OUT-1,y
@hex:
        lda (mon_start)
        sta mon_byte
        jsr put_hex
        iny
        lda mon_byte
        cmp #' '
        bcc @dot
        cmp #$7F
        bcc @show
@dot:
        lda #'.'
@show:
        sta MONITOR_OUT + DUMP_TEXT,x
        inx
        jsr start_step
        bcs @last
        cpx #16
        bne @byte
        ldy #DUMP_TEXT + 16
        jsr print_line
        bra @line
@last:
        txa
        adc #DUMP_TEXT - 1      ; carry set
        tay
        jsr print_line
        lda mon_start
        clc
        adc #1
        sta mon_dump
        lda mon_start+1
        adc #0
        sta mon_dump+1
        jmp monitor

enter:
        jsr get_start
        jsr get_list
        ldy #0
@byte:
        lda MONITOR_OUT,y
        sta (mon_start),y
        iny
        cpy mon_count
        bne @byte
        jmp monitor

fill:
        jsr get_start
        jsr get_end
        jsr get_list
        ldy #0
@byte:
        lda MONITOR_OUT,y
        sta (mon_start)
        iny
        cpy mon_count
        bne @step
        ldy #0
@step:
        jsr start_step
        bcc @byte
        jmp monitor

dir:
        jsr skip_word
        jsr get_path
        stz mon_count
        jsr find_buffer
        lda #$16                ; directories, hidden and system files
        jsr API_FINDFIRST
@entry:
        bcs @end
        ldy #DIR_COLUMNS - 1
        jsr blank
        ldx MONITOR_FIND + FIND_NAME
@name:
        dex
        bmi @size
        lda MONITOR_FIND + FIND_NAME + 1,x
        sta MONITOR_OUT,x
        bra @name
@size:
        ldy #DIR_COLUMNS - 5
        lda MONITOR_FIND + FIND_ATTR
        and #$10
        beq @file
        ldx #<text_dir
        jsr put_text
        bra @print
@file:
        ldx #3
@copy:
        lda MONITOR_FIND + FIND_SIZE,x
        sta mon_number,x
        dex
        bpl @copy
        ldy #DIR_COLUMNS - 1
        jsr put_decimal
@print:
        ldy #DIR_COLUMNS
        jsr print_line
        inc mon_count
        jsr find_buffer
        jsr API_FINDNEXT
        bra @entry
@end:
        cmp #ERR_NO_MORE_FILES
        bne api_error
        ldy #5                  ; the count of names
        jsr blank
        lda mon_count
        sta mon_number
        stz mon_number+1
        stz mon_number+2
        stz mon_number+3
        ldy #5
        jsr put_decimal
        ldy #6
        ldx #<text_files
        jsr put_text
        jsr print_line
        jmp monitor

        .assert DIR_COLUMNS + 2 <= $20 && MONITOR_FIND + FIND_BUFFER_SIZE <= GATE_PAGE, error, "DIR's line and find buffer fit"

; find_buffer: points r1 at MONITOR_FIND. Keeps A.
find_buffer:
        ldx #<MONITOR_FIND
        stx r1
        ldx #>MONITOR_FIND
        stx r1+1
        rts

; api_error: prints the message of error A, then the prompt.
api_error:
        ldx #<MONITOR_LINE    ; the message goes over the input line
        stx r0
        ldx #>MONITOR_LINE
        stx r0+1
        jsr API_ERRMSG
        lda MONITOR_LINE        ; the length
        sta r1
        stz r1+1
        inc r0                  ; the text
        .assert <MONITOR_LINE <> $FF, error, "inc r0 reaches MONITOR_LINE's text"
        ldx #1                  ; stdout
        jsr API_WRITE
        ldy #0
        jsr print_line
        jmp monitor

type:
        jsr skip_word
        jsr get_path
        lda #0                  ; read
        jsr API_OPEN
        bcs api_error
        stx mon_byte
        lda #$0A
        sta mon_quote           ; the last byte printed
@chunk:
        lda #<MONITOR_OUT
        sta r0
        lda #>MONITOR_OUT
        sta r0+1
        lda #TYPE_CHUNK
        sta r1
        stz r1+1
        ldx mon_byte
        jsr API_READ
        bcs @fault
        lda r1
        beq @close
        tay
        lda MONITOR_OUT-1,y
        sta mon_quote
        ldx #1                  ; stdout
        jsr API_WRITE
        bra @chunk
@close:
        ldx mon_byte
        jsr API_CLOSE
        lda mon_quote
        cmp #$0A
        beq @prompt
        ldy #0
        jsr print_line          ; the file ends mid-line
@prompt:
        jmp monitor
@fault:
        pha
        ldx mon_byte
        jsr API_CLOSE
        pla
        bra api_error

run:
        jsr skip_word
        jsr get_word
        ldy #0                  ; the tail: the rest of the line, from the space after the path
@tail:
        lda MONITOR_TEXT,x
        cmp #$0D
        beq @end
        iny
        sta MONITOR_OUT,y
        inx
        bra @tail
@end:
        sty MONITOR_OUT
        lda #<MONITOR_OUT
        sta r1
        lda #>MONITOR_OUT
        sta r1+1
        jsr API_EXEC
        bcc new_line
        jmp api_error

go:
        jsr get_hex
        jsr need_end
        jsr go_jump
new_line:
        ldy #0
        jsr print_line          ; CR LF before the prompt, as MS-DOS COMMAND does
        jmp monitor
go_jump:
        jmp (mon_value)

; get_start: reads a number into mon_start.
get_start:
        jsr get_hex
        lda mon_value
        sta mon_start
        lda mon_value+1
        sta mon_start+1
        rts

; get_end: reads a number into mon_end. Goes to error when it is below mon_start.
get_end:
        jsr get_hex
        lda mon_value
        sta mon_end
        cmp mon_start
        lda mon_value+1
        sta mon_end+1
        sbc mon_start+1
        bcs @done
        ldx mon_mark            ; the error points at the number
        bra to_error
@done:
        rts

; need_end: goes to error unless only spaces and commas are left on the line.
need_end:
        jsr skip
        cmp #$0D
        bne to_error
        rts

to_error:
        jmp error

; get_hex: reads a hex number at X, after spaces and commas, into mon_value. Goes to error
; when there is none. Changes A and Y.
get_hex:
        jsr skip
        stz mon_value
        stz mon_value+1
        stx mon_mark
@digit:
        lda MONITOR_TEXT,x
        jsr to_upper
        eor #'0'                ; '0'-'9' to 0-9, 'A'-'F' to $71-$76
        cmp #10
        bcc @add
        adc #$88                ; carry set: $71-$76 to $FA-$FF
        cmp #$FA
        bcc @end
        and #$0F
@add:
        ldy #4
@shift:
        asl mon_value
        rol mon_value+1
        dey
        bne @shift
        ora mon_value
        sta mon_value
        inx
        bra @digit
@end:
        cpx mon_mark
        beq to_error
        rts

; get_list: reads hex bytes and quoted strings to the end of the line into MONITOR_OUT, and
; their number into mon_count. Goes to error when there are none.
get_list:
        stz mon_count
@item:
        jsr skip
        cmp #$0D
        beq @end
        cmp #'"'
        beq @quote
        cmp #$27                ; '
        beq @quote
        jsr get_hex
        lda mon_value
        jsr @add
        bra @item
@quote:
        sta mon_quote
        inx
@char:
        lda MONITOR_TEXT,x
        cmp #$0D
        beq to_error
        inx
        cmp mon_quote
        beq @item
        jsr @add
        bra @char
@end:
        lda mon_count
        beq to_error
        rts
@add:
        ldy mon_count
        sta MONITOR_OUT,y
        inc mon_count
        rts

; skip_word: moves X past the letters at X.
skip_word:
        lda MONITOR_TEXT,x
        jsr to_upper
        cmp #'A'
        bcc @done
        cmp #'Z' + 1
        bcs @done
        inx
        bra skip_word
@done:
        rts

; get_path: get_word, then goes to error when more follows on the line.
get_path:
        jsr get_word
        jmp need_end

; get_word: makes the text at X, after spaces and commas and up to a space, a length-prefixed
; string at r0: its length goes in the byte before it. Moves X past it.
get_word:
        jsr skip
        stx mon_mark
@char:
        lda MONITOR_TEXT,x
        cmp #' ' + 1            ; a space or the CR ends it
        bcc @end
        inx
        bra @char
@end:
        txa
        sec
        sbc mon_mark
        ldy mon_mark
        sta MONITOR_TEXT - 1,y
        tya
        clc
        adc #<(MONITOR_TEXT - 1)
        sta r0
        lda #>(MONITOR_TEXT - 1)
        sta r0+1
        rts
        .assert <(MONITOR_TEXT - 1) + LINE_MAX < 256, error, "get_word keeps r0 in one page"

; skip: moves X past spaces and commas. Returns the character at X in A.
skip:
        lda MONITOR_TEXT,x
        cmp #' '
        beq @next
        cmp #','
        bne @done
@next:
        inx
        bra skip
@done:
        rts

; start_step: returns carry set when mon_start = mon_end. Else moves mon_start on by 1 and
; returns carry clear. Changes A.
start_step:
        lda mon_start
        cmp mon_end
        bne @next
        lda mon_start+1
        cmp mon_end+1
        beq @done
@next:
        inc mon_start
        bne @clear
        inc mon_start+1
@clear:
        clc
@done:
        rts

; blank: puts spaces at MONITOR_OUT to MONITOR_OUT + Y. Returns Y = $FF. Changes A.
blank:
        lda #' '
@space:
        sta MONITOR_OUT,y
        dey
        bpl @space
        rts

; put_decimal: puts mon_number in decimal with its last digit at MONITOR_OUT + Y, and moves Y
; back past the digits. Changes A, X, Y and mon_number.
put_decimal:
        lda #0                  ; mon_number / 10, the remainder in A
        ldx #32
@bit:
        asl mon_number
        rol mon_number+1
        rol mon_number+2
        rol mon_number+3
        rol
        cmp #10
        bcc @low
        sbc #10
        inc mon_number
@low:
        dex
        bne @bit
        ora #'0'
        sta MONITOR_OUT,y
        dey
        lda mon_number
        ora mon_number+1
        ora mon_number+2
        ora mon_number+3
        bne put_decimal
        rts

; put_text: puts the text at texts + X, ended by 0, at MONITOR_OUT + Y. Changes A, X and Y.
put_text:
        lda texts,x
        beq @done
        jsr put_char
        inx
        bra put_text
@done:
        rts

; put_hex: puts A as two hex digits at MONITOR_OUT + Y. Moves Y on by 2. Changes A.
put_hex:
        pha
        lsr
        lsr
        lsr
        lsr
        jsr @digit
        pla
        and #$0F
@digit:
        cmp #10
        bcc @number
        adc #'A' - '0' - 10 - 1 ; carry set
@number:
        adc #'0'
        ; fall through

; put_char: puts A at MONITOR_OUT + Y and moves Y on by 1.
put_char:
        sta MONITOR_OUT,y
        iny
        rts

; print_line: puts CR and LF, then prints.
print_line:
        lda #$0D
        jsr put_char
        lda #$0A
        jsr put_char
        ; fall through

; print: writes the Y bytes at MONITOR_OUT to handle 1. Changes A and Y.
print:
        sty r1
        stz r1+1
        lda #<MONITOR_OUT
        sta r0
        lda #>MONITOR_OUT
        sta r0+1
        phx
        ldx #1                  ; stdout
        jsr API_WRITE
        plx
        rts

.segment "RODATA"

commands:
        .byte "DEFGRT"
command_routines:
        .word dump - 1, enter - 1, fill - 1, go - 1, run - 1, type - 1

reg_names:
        .byte "AXYPS"

texts:
text_error = * - texts
        .byte "^ Error", 0
text_pc = * - texts
        .byte "PC=", 0
text_dir = * - texts
        .byte "<DIR>", 0
text_files = * - texts
        .byte " File(s)", 0
