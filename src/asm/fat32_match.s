; The FAT32 library's name encoding and matching, in ROM bank 1.
;
; Ported from x16-rom, fat32/match.s, github.com/X16Community/x16-rom, master fbe32a6.
; Changed: the code is in segment B1CODE and the variables in FATBSS; fat32_regs.inc
; replaces regs.inc; match_name takes Windows wildcards: '*' matches any run of characters.
;
; Original header:
;----------------------------------------------------------------------
; CMDR-DOS Character Encoding, Name Matching
;----------------------------------------------------------------------
; (C)2020 Michael Steil, License: 2-clause BSD
;
; fat32/README.md gives the licence: Copyright 2020 Frank van den Hoef, Michael Steil,
; 2-clause BSD.
;
; Redistribution and use in source and binary forms, with or without
; modification, are permitted provided that the following conditions are met:
;
; 1. Redistributions of source code must retain the above copyright notice, this
;    list of conditions and the following disclaimer.
; 2. Redistributions in binary form must reproduce the above copyright notice,
;    this list of conditions and the following disclaimer in the documentation
;    and/or other materials provided with the distribution.
;
; THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
; ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
; WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
; DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
; ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
; (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
; ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
; (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
; SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

.include "fat32_regs.inc"

.export filename_char_ucs2_to_internal, filename_char_internal_to_ucs2
.export filename_cp437_to_internal, filename_char_internal_to_cp437
.export match_name, match_type

.import fat32_dirent
.import to_lower
.import skip_mask

.segment "FATBSS"

char_tmp:
	.byte 0
star_pattern:			; match_name: the pattern index after the last '*'
	.byte 0
star_name:			; match_name: the name index that '*' matched up to
	.byte 0

.segment "B1CODE"

;-----------------------------------------------------------------------------
; filename_char_ucs2_to_internal
;
; Convert UCS-2 character to internal 8 bit encoding (ISO-8859-15)
;
; In:   a  16 bit char high
;       x  16 bit char low
; Out:  a  8 bit char
;-----------------------------------------------------------------------------
filename_char_ucs2_to_internal:
	cmp #0
	beq @from_latin_1

	; non ISO-8859-1 Unicode
	cmp #$20
	bne @not_20
	cpx #$ac
	bne @unsupported

	lda #$a4 ; U20AC '€'
	rts

@not_20:
	cmp #$01
	bne @unsupported

	cpx #$60
	bne @1
	lda #$a6 ; U0160 'Š'
	rts
@1:	cpx #$61
	bne @2
	lda #$a8 ; U0161 'š'
	rts
@2:	cpx #$7d
	bne @3
	lda #$b4 ; U017D 'Ž'
	rts
@3:	cpx #$7e
	bne @4
	lda #$b8 ; U017E 'ž'
	rts
@4:	cpx #$52
	bne @5
	lda #$bc ; U0152 'Œ'
	rts
@5:	cpx #$53
	bne @6
	lda #$bd ; U0153 'œ'
	rts
@6:	cpx #$78
	bne @unsupported
	lda #$be ; U0178 'Ÿ'
	rts


@from_latin_1:
	cpx #$a4 ; U00A4 '¤'
	beq @unsupported
	cpx #$a6 ; U00A6 '¦'
	beq @unsupported
	cpx #$a8 ; U00A8 '¨'
	beq @unsupported
	cpx #$b4 ; U00B4 '´'
	beq @unsupported
	cpx #$b8 ; U00B8 '¸'
	beq @unsupported
	cpx #$bc ; U00BC '¼'
	beq @unsupported
	cpx #$bd ; U00BD '½'
	beq @unsupported
	cpx #$be ; U00BE '¾'
	beq @unsupported

	; characters that are allowed in VFAT filenames 
	; but not in CMDR-DOS
	cpx #$2c ; U002C ','
	beq @unsupported
	
	; codes where ISO-8859-1 == ISO-8859-15
	txa
	rts

@unsupported:
	lda #'?'
	rts

;-----------------------------------------------------------------------------
; filename_char_internal_to_ucs2
;
; Convert character in internal 8 bit encoding (ISO-8859-15) to UCS-2
;
; In:   a  8 bit char
; Out:  a  16 bit char low
;       x  16 bit char high
;-----------------------------------------------------------------------------
filename_char_internal_to_ucs2:
	cmp #$a4
	bne @1
	lda #$ac
	ldx #$20 ; U20AC '€'
	rts
@1:	cmp #$a6
	bne @2
	lda #$60
	ldx #$01 ; U0160 'Š'
	rts
@2:	cmp #$a8
	bne @3
	lda #$61
	ldx #$01 ; U0161 'š'
	rts
@3:	cmp #$b4
	bne @4
	lda #$7d
	ldx #$01 ; U017D 'Ž'
	rts
@4:	cmp #$b8
	bne @5
	lda #$7e
	ldx #$01 ; U017E 'ž'
	rts
@5:	cmp #$bc
	bne @6
	lda #$52
	ldx #$01 ; U0152 'Œ'
	rts
@6:	cmp #$bd
	bne @7
	lda #$53
	ldx #$01 ; U0153 'œ'
	rts
@7:	cmp #$be
	bne @8
	lda #$78
	ldx #$01 ; U0178 'Ÿ'
	rts
@8:
	; ISO-8859-1 matches ISO-8859-15
	ldx #0
	rts

;-----------------------------------------------------------------------------
; filename_cp437_to_internal
;
; Convert CP437 character to internal 8 bit encoding (ISO-8859-15)
;
; In:   a  CP437 char
; Out:  a  8 bit char (0= no mapping exists)
;-----------------------------------------------------------------------------
filename_cp437_to_internal:
	cmp #$80
	bcs @5
	cmp #$20
	bcs @2
	cmp #$14
	bne @1
	lda #$b6
	rts
@1:	cmp #$15
	bne @3
	lda #$a7
	rts
@2:	cmp #$7f
	bne @4
@3:	lda #0
@4:	rts
@5:	tax
	lda cp437_to_iso8859_15_tab - $80,x
	rts

;-----------------------------------------------------------------------------
; filename_char_internal_to_cp437
;
; Convert character in internal 8 bit encoding (ISO-8859-15) to CP437
;
; In:   a  8 bit char
; Out:  a  CP437 char (0= no mapping exists)
;-----------------------------------------------------------------------------
filename_char_internal_to_cp437:
	cmp #$20
	bcs @1
	lda #0
	rts
@1:	cmp #$b6
	bne @2
	lda #$14
	rts
@2:	cmp #$a7
	bne @4
	lda #$15
@3:	rts
@4:	cmp #$7f
	bcc @3
	ldx #$80
@5:	cmp cp437_to_iso8859_15_tab - $80,x
	beq @6
	inx
	bne @5
@6:	txa
	rts

cp437_to_iso8859_15_tab:
	.byte $C7,$FC,$E9,$E2,$E4,$E0,$E5,$E7,$EA,$EB,$E8,$EF,$EE,$EC,$C4,$C5
	.byte $C9,$E6,$C6,$F4,$F6,$F2,$FB,$F9,$FF,$D6,$DC,$A2,$A3,$A5,$00,$00
	.byte $E1,$ED,$F3,$FA,$F1,$D1,$AA,$BA,$BF,$00,$AC,$00,$00,$A1,$AB,$BB
	.byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	.byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	.byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
	.byte $00,$DF,$00,$00,$00,$00,$B5,$00,$00,$00,$00,$00,$00,$00,$00,$00
	.byte $00,$B1,$00,$00,$00,$00,$F7,$00,$B0,$00,$B7,$00,$00,$B2,$00,$A0

;-----------------------------------------------------------------------------
; match_name
;
; Check if name matches. '*' matches any run of characters, '.' too, and '?'
; one character. A pattern that ends in '.' or '.*' also matches at the end
; of a name with no dot. The pattern ends at 0 or '/'.
;
; In:   fat32_ptr   name
;       y           name offset
; Out:  c           =1: matched; y at the end of the pattern
;-----------------------------------------------------------------------------
match_name:
	ldx #0
	stz star_pattern ; 0: no '*' yet
@char:	lda (fat32_ptr), y
	cmp #'*'
	beq @asterisk
	lda fat32_dirent + dirent::name, x
	beq @name_end
	lda (fat32_ptr), y
	beq @retry
	cmp #'/'
	beq @retry
	cmp #'?'
	beq @char_match
	jsr to_lower
	sta char_tmp
	lda fat32_dirent + dirent::name, x
	jsr to_lower
	cmp char_tmp
	bne @retry
@char_match:
	inx
	iny
	bra @char

@asterisk:
	iny
	sty star_pattern
	stx star_name
	bra @char

; Mismatch: the last '*' takes one more character
@retry:	lda star_pattern
	beq @no
	tay
	inc star_name
	ldx star_name
	bra @char

@name_end:
	lda (fat32_ptr), y
	cmp #'.'
	bne @end
	ldx #0		; the name must have no dot
@scan:	lda fat32_dirent + dirent::name, x
	beq @dot
	inx
	cmp #'.'
	bne @scan
	bra @no
@dot:	iny
	lda (fat32_ptr), y
	cmp #'*'
	beq @dot
@end:	cmp #'/'
	beq @yes
	cmp #0
	beq @yes
@no:
	clc
	rts
@yes:
	sec
	rts

;---------------------------------------------------------------
; match_type
;
; In:   a   type
; Out:  c   =1: matched
;---------------------------------------------------------------
match_type:
	bit skip_mask
	beq @yes
	clc
	rts
@yes:	sec
	rts

;
; This is the CP437 -> Unicode mapping
;
; 0,263A,263B,2665,2666,2663,2660,2022,25D8,25CB,25D9,2642,2640,266A,266B,263C,25BA
; 25C4,2195,203C,B6,A7,25AC,21A8,2191,2193,2192,2190,221F,2194,25B2,25BC,20,21,22,23
; 24,25,26,27,28,29,2A,2B,2C,2D,2E,2F,30,31,32,33,34,35,36,37,38,39,3A,3B,3C,3D,3E,3F
; 40,41,42,43,44,45,46,47,48,49,4A,4B,4C,4D,4E,4F,50,51,52,53,54,55,56,57,58,59,5A,5B
; 5C,5D,5E,5F,60,61,62,63,64,65,66,67,68,69,6A,6B,6C,6D,6E,6F,70,71,72,73,74,75,76,77
; 78,79,7A,7B,7C,7D,7E,2302,C7,FC,E9,E2,E4,E0,E5,E7,EA,EB,E8,EF,EE,EC,C4,C5,C9,E6,C6
; F4,F6,F2,FB,F9,FF,D6,DC,A2,A3,A5,20A7,192,E1,ED,F3,FA,F1,D1,AA,BA,BF,2310,AC,BD,BC
; A1,AB,BB,2591,2592,2593,2502,2524,2561,2562,2556,2555,2563,2551,2557,255D,255C,255B
; 2510,2514,2534,252C,251C,2500,253C,255E,255F,255A,2554,2569,2566,2560,2550,256C
; 2567,2568,2564,2565,2559,2558,2552,2553,256B,256A,2518,250C,2588,2584,258C,2590
; 2580,3B1,DF,393,3C0,3A3,3C3,B5,3C4,3A6,398,3A9,3B4,221E,3C6,3B5,2229,2261,B1,2265
; 2264,2320,2321,F7,2248,B0,2219,B7,221A,207F,B2,25A0,A0
