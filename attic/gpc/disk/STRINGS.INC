' The string library. Add #INCLUDE "STRINGS.INC" to a program to use it.
' STR.name is the built-in function name: STR.MID$ is MID$.
' LEFT$ and RIGHT$ are SUBs, declared before the namespace that binds them.

' LEFT$(S$, N) is the first N characters of S$, or all of S$ when it is shorter.
' The ASM uses r0 ($02-$03) as the pointer to S$.
SUB LEFT$(S$, N)
  DIM R$ * 255
  DIM P%
  P% = @S$
  ASM
      lda @P%
      sta $02
      lda @P% + 1
      sta $03
      ldy #1
      lda ($02),y         ' the length of S$
      cmp @N
      bcc keep
      lda @N
keep:   sta @R$ + 1
      tay
      beq done
      iny                 ' Y is the offset of the last character
copy:   lda ($02),y
      sta @R$,y
      dey
      cpy #1
      bne copy
done:
  END ASM
  RETURN R$
ENDSUB

' RIGHT$(S$, N) is the last N characters of S$, or all of S$ when it is shorter.
' The ASM uses r0 ($02-$03) as the pointer to S$, and r1 ($04) for its length.
SUB RIGHT$(S$, N)
  DIM R$ * 255
  DIM P%
  P% = @S$
  ASM
      lda @P%
      sta $02
      lda @P% + 1
      sta $03
      ldy #1
      lda ($02),y         ' the length of S$
      sta $04
      cmp @N
      bcc keep
      lda @N
keep:   sta @R$ + 1
      lda $04             ' move the pointer on by the characters left out
      sec
      sbc @R$ + 1
      clc
      adc $02
      sta $02
      bcc moved
      inc $03
moved:  ldy @R$ + 1
      beq done
      iny                 ' Y is the offset of the last character
copy:   lda ($02),y
      sta @R$,y
      dey
      cpy #1
      bne copy
done:
  END ASM
  RETURN R$
ENDSUB

NAMESPACE STR
  BIND LEN LEN        ' STR.LEN(S$)                  the length of S$
  BIND ASC ASC        ' STR.ASC(S$)                  the code of the first character
  BIND VAL VAL        ' STR.VAL(S$)                  the number in S$
  BIND CHR$ CHR$      ' STR.CHR$(N)                  the character with code N
  BIND STR$ STR$      ' STR.STR$(N)                  N as a string
  BIND MID$ MID$      ' STR.MID$(S$, START[, COUNT]) COUNT characters from START
  BIND INSTR INSTR    ' STR.INSTR(S$, F$[, START])   the position of F$ in S$, or 0
  BIND LEFT$ LEFT$    ' STR.LEFT$(S$, N)             the first N characters of S$
  BIND RIGHT$ RIGHT$  ' STR.RIGHT$(S$, N)            the last N characters of S$
END NAMESPACE
