; MACROS.ASM -- the record format of UXC.TPL.BIN, and the macros that write it.
;
; The file:
;   "UXT", version, count (word), index offset (word)
;   the records
;   the index: one word per record, the file offset of record <id>
;
; A record:
;   code length (byte), fixup count (byte)
;   the code
;   the fixups, three bytes each: offset in the code, kind, argument
;
; A data record:
;   its size (byte), $FF when the startup sets its first byte to 0, else $FE
;
; The compiler copies a record's code into the program and then applies its fixups. A record
; is used inline (a template, T_) or placed once at the end of the program (a runtime routine,
; R_, or a system table entry, S_). Records reach each other through F_REC fixups, so linking
; one record links every record it needs.
;
; A data record is RAM that runtime routines write. The compiler places it after the array
; space and the temps, outside the file. Its bytes start undefined, except that the startup
; sets the first byte to 0 when the record asks for it. A record's code is never written, so
; that the program can run from ROM.
;
; Each record sits in its own .block, which keeps its labels local:
;
;   R_NAME  .block
;           #tpl
;           ...code...
;           #endtpl
;           .endblock
;
; Write an operand that the compiler fills with one of the macros below, never by hand. Each
; macro forces a 16 bit operand where it needs one, so 64tass cannot pick zero page.

; Fixup kinds.
F_ABS   = 1             ; the word at the offset += the value of slot <arg>
F_LO    = 2             ; the byte at the offset = the low byte of slot <arg>
F_HI    = 3             ; the byte at the offset = the high byte of slot <arg>
F_SELF  = 4             ; the word at the offset += the address this record's code is placed at
F_REC   = 5             ; the word at the offset += the address of record <arg>
F_REC_HI = 6            ; the word at the offset += the address of record <arg> + 256

; Slots: the operands the compiler passes to a template. A slot's value is an address (a
; variable, a string, a label) or a constant.
S0      = 0
S1      = 1
S2      = 2
S3      = 3

tpl_all := []           ; the file offset of every record, in id order
tpl_fix := []           ; the fixups of the open record

; Open a record. rec_id is its id, for F_REC fixups from other records.
tpl     .segment
rec_id  = len(tpl_all)
        tpl_all ::= tpl_all .. [*]
        tpl_fix ::= []
        .byte rec_fix - rec_code
        .byte (rec_end - rec_fix) / 3
rec_code
        .endsegment

; A data record of size bytes, 1 to 255. zero is 1 when the startup sets its first byte to 0,
; else 0. It takes no #endtpl. Name its fields with = inside its .block: out = 0.
data    .segment size, zero
rec_id  = len(tpl_all)
        tpl_all ::= tpl_all .. [*]
        .cerror \size < 1 || \size > 255, "a data record is 1 to 255 bytes"
        .byte \size, $fe + \zero
        .endsegment

; Close a record: write its fixups.
endtpl  .segment
rec_fix
        .cerror rec_fix - rec_code > 255, "a record's code is more than 255 bytes"
        .for f in tpl_fix
        .byte f[0], f[1], f[2]
        .endfor
rec_end
        .endsegment

; op <slot> + add, absolute.
ab      .segment op, slot, add=0
        tpl_fix ::= tpl_fix .. [(* + 1 - rec_code, F_ABS, \slot)]
        \op @w \add
        .endsegment

; op <slot> + add, y: absolute, indexed by Y.
aby     .segment op, slot, add=0
        tpl_fix ::= tpl_fix .. [(* + 1 - rec_code, F_ABS, \slot)]
        \op @w \add, y
        .endsegment

; op #<slot
lo      .segment op, slot
        tpl_fix ::= tpl_fix .. [(* + 1 - rec_code, F_LO, \slot)]
        \op #0
        .endsegment

; op #>slot
hi      .segment op, slot
        tpl_fix ::= tpl_fix .. [(* + 1 - rec_code, F_HI, \slot)]
        \op #0
        .endsegment

; op <label in this record>
self    .segment op, target
        tpl_fix ::= tpl_fix .. [(* + 1 - rec_code, F_SELF, 0)]
        \op @w \target - rec_code
        .endsegment

; op <label in this record>,x
selfx   .segment op, target
        tpl_fix ::= tpl_fix .. [(* + 1 - rec_code, F_SELF, 0)]
        \op @w \target - rec_code, x
        .endsegment

; A branch, op b??, to the offset in slot <slot>. The compiler puts the offset in the slot as
; a constant, 0-255, counted from the end of the branch as the 65C02 counts it.
rel     .segment op, slot
        tpl_fix ::= tpl_fix .. [(* + 1 - rec_code, F_LO, \slot)]
        \op * + 2
        .endsegment

; op <another record> + add, usually JSR or JMP. add is an entry point after the start. A record
; past id 255 takes F_REC_HI, F_REC + 1.
rec     .segment op, target, add=0
        tpl_fix ::= tpl_fix .. [(* + 1 - rec_code, F_REC + \target.rec_id / 256, \target.rec_id % 256)]
        \op @w \add
        .endsegment

; op <another record> + add, x: R_ESTKH, the high words of the expression stack.
recx    .segment op, target, add=0
        tpl_fix ::= tpl_fix .. [(* + 1 - rec_code, F_REC + \target.rec_id / 256, \target.rec_id % 256)]
        \op @w \add, x
        .endsegment

; A data word, the address of a label in this record.
selfdw  .segment target
        tpl_fix ::= tpl_fix .. [(* - rec_code, F_SELF, 0)]
        .word \target - rec_code
        .endsegment

; A data word, the address of another record + add: a field of a data record.
recdw   .segment target, add=0
        tpl_fix ::= tpl_fix .. [(* - rec_code, F_REC + \target.rec_id / 256, \target.rec_id % 256)]
        .word \add
        .endsegment

; A data word, <slot> + add: the data a runtime routine reads after its JSR.
dw      .segment slot, add=0
        tpl_fix ::= tpl_fix .. [(* - rec_code, F_ABS, \slot)]
        .word \add
        .endsegment

; A data byte, <slot.
db      .segment slot
        tpl_fix ::= tpl_fix .. [(* - rec_code, F_LO, \slot)]
        .byte 0
        .endsegment
