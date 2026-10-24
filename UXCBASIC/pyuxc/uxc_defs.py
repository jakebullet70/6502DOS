"""The compiler's constants, from UXC-DEFS.BL. K.ORG there is K_ORG here."""

# The program: the default start, and the first address it may not reach.
K_ORG = 0x0801
K_TOP = 0x9F00

# #ROMBANKS: each bank's file ends at K.FAR.END, where the ROM's IRQ entry starts, with T_FAR's
# 23 bytes at K.FAR.
K_FAR_END = 0xFFA0
K_FAR = 0xFF89

# Token types, in TK.T.
K_TT_EOL = 0
K_TT_NUM = 1
K_TT_STR = 2
K_TT_NAME = 3
K_TT_OP = 4

# Types: a name's type mark, and a variable's type. TY.SIZE gives a type's size.
# Trap: an expression entry of type 0 is a constant that fits a BYTE.
K_TY_BYTE = 1
K_TY_WORD = 2
K_TY_STR = 3
K_TY_LONG = 4
# A record's type is K.TY.RECORD plus its TYPE's number, below K.RD.TYPES.
K_TY_RECORD = 16
K_RD_TYPES = 240

# Symbol kinds.
K_SK_VAR = 1
K_SK_LABEL = 2
K_SK_SUB = 3
K_SK_ARRAY = 4
K_SK_SPACE = 5
K_SK_BIND = 6
K_SK_CALL = 7
K_SK_CONST = 8
K_SK_ENUM = 9
K_SK_TYPE = 10
K_SK_FIELD = 11
# A SUB that UXC-DEAD.BL left out, and the call records and temps it owned.
K_SK_DEAD = 12
# A signature: DECLARE SUB or DECLARE FUNCTION. Its parameters are records after it, as a SUB's
# are, and it has a level and a pool as a SUB has, but no code.
K_SK_SIG = 13
# A SUB whose address @name gave as a pointer of a signature: owned by the signature, its value
# the SUB. SB.POOLS puts the two at one level, so that the SUB's parameters are the signature's.
K_SK_TARGET = 14

# A symbol flag of a STRING parameter: it is AS CONST. A literal argument is passed with no copy,
# and the SUB may not assign to it.
K_SY_READ_ONLY = 1
# A symbol flag: the variable is DIM ... AT, and its value is its address.
K_SY_FIXED = 2
# A symbol flag: the variable is a string temp, and its value is its offset in its owner's
# pool of temps.
K_SY_TEMP = 4
# A symbol flag: the BIND or ENUM was made by the first pass, and the second pass has not met it.
K_SY_SCANNED = 8
# A symbol flag of an ENUM: a parameter or a FUNCTION result is of its type, so it must stay BYTE.
K_SY_ENUM_PARAMETER = 4
# A symbol flag: the variable is a record in the block space, and its value is its offset there.
K_SY_BLOCK = 16
# A symbol flag: NM.FIND gave a field of a record variable, not a record of the table.
K_SY_MEMBER = 32
# A symbol flag: the variable, array, field, parameter or FUNCTION result is signed, or the
# CONST is below 0.
K_SY_SIGNED = 64
# A symbol flag: the SUB is reached from the main program through calls (UXC-DEAD.BL).
K_SY_LIVE = 128
# The field of a record variable's record that holds its TYPE's record (word).
K_SY_RECORD_TYPE = 30
# The field of a parameter's record that holds its ENUM's record (word), 0 for none.
K_SY_ENUM_TYPE = 30
# The field of a variable's, an array's or a parameter's record that holds its signature's
# record (word), for a pointer: DIM P AS name, where name is a DECLARE.
K_SY_SIGNATURE = 30

# The fields of a SUB record the link step uses (UXC-SYM.BL): its level in the call graph
# (byte), the number of temps it needs (byte), and the bytes of its frame, then the offset
# of its pool (word).
# Trap: the level and the temps overlay K.SY.END, the code offset where the SUB's code ends
# (word), which UXC-DEAD.BL reads before SB.POOLS writes them.
K_SY_LEVEL = 28
K_SY_END = 28
K_SY_TEMPS = 29
K_SY_POOL = 30

# A VAR or BSS value from K.FRAME.BASE up is a local in its owner's frame: 65536 less its
# distance below the owner's pool. A frame holds at most K.FRAME.MAX bytes.
K_FRAME_BASE = 49152
K_FRAME_MAX = 16384

# Sections: what a slot value or a fixup value is counted from. CONST is a plain number and
# is never left for the link step. BSS is the array space after the end of the PRG. TEMP is
# a string temp, counted from the start of its owner's pool, which the link step places
# after the array space. RGDATA is a literal or a global variable moved into region 1, counted
# from the start of the region's data, after its code. LOW, only in g.rg_fix, is a code offset
# in low RAM named from a region's code; rg_place makes it CODE.
K_SEC_CONST = 0
K_SEC_CODE = 1
K_SEC_REC = 2
K_SEC_STR = 3
K_SEC_VAR = 4
K_SEC_LABEL = 5
K_SEC_BSS = 6
K_SEC_TEMP = 7
K_SEC_RGDATA = 8
K_SEC_LOW = 9

# The value of a K.SEC.TEMP entry for a part of a PRINT item already printed (UXC-STR.BL).
K_TEMP_PRINTED = 65535

# Fixup kinds, the same numbers as F_* in tpl/MACROS.ASM.
K_F_ABS = 1
K_F_LO = 2
K_F_HI = 3
K_F_SELF = 4
K_F_REC = 5
K_F_REC_HI = 6

# Banked RAM, in banks from BANKMGR. The code buffer and the fixups take a bank each time
# they fill one. K.RAM.BANKS is the free banks of a 2 MB X16: 256 less bank 0 and VARBANK.
K_SYM_BANKS = 8
K_RAM_BANKS = 254
# A fixup keeps a code offset in 2 bytes, so the code is at most 64 KB.
K_CODE_MAX = 65536

# The runtime record table, in bank RT.BANK, for at most 1024 records: a byte per record
# that is 1 once it is used, the used ids in order as words, and each record's address.
K_RT_USED = 0xA000
K_RT_LIST = 0xA800
K_RT_ADDR = 0xB000

# The fixup count of a data record in UXC.TPL.BIN, + 1 when the startup sets its first byte to
# 0. Its length byte is its size.
K_TP_DATA = 254

# The symbol table: bucket heads, then 32-byte records.
# Checklist: K_SY_MAX is (K_SYM_BANKS * 8192 - K_SY_HEADS) / 32.
K_SY_HEADS = 512
K_SY_MAX = 2032

# The most SUBs UXC-DEAD.BL can leave out of one program.
K_DD_MAX = 512
# The most global variables UXC-DEAD.BL logs in each of the variables and the array space.
# A program with more keeps every variable.
K_DV_MAX = 1024
# The most string literals UXC-DEAD.BL logs. A literal takes at least 2 of the 8192 bytes.
K_DS_MAX = 4096

# The two-character operators, in TK.K. A one-character operator is its character.
K_OP_NE = 256
K_OP_LE = 257
K_OP_GE = 258
K_OP_SHL = 259
K_OP_SHR = 260

# The kinds of an entry on the expression parser's value stack.
K_EK_CONST = 1
K_EK_MEM = 2
K_EK_ADDR = 3
K_EK_REG = 4
K_EK_STK = 5
K_EK_CMP = 6
K_EK_JMP = 7

# The expression operators, in the order of their precedence groups (EX.PREC). PAR is an
# open bracket, PEEK the function and INDEX an array element, waiting on the operator
# stack for their ). INDEX keeps its array's record in EX.OA%().
K_EO_OR = 1
K_EO_XOR = 2
K_EO_AND = 3
K_EO_NOT = 4
K_EO_EQ = 5
K_EO_NE = 6
K_EO_LT = 7
K_EO_GT = 8
K_EO_LE = 9
K_EO_GE = 10
K_EO_SHL = 11
K_EO_SHR = 12
K_EO_ADD = 13
K_EO_SUB = 14
K_EO_MUL = 15
K_EO_DIV = 16
K_EO_MOD = 17
K_EO_MINUS = 18
K_EO_PAR = 19
K_EO_PEEK = 20
K_EO_INDEX = 21
K_EO_WORDPEEK = 22
K_EO_STRINGAT = 23
# AND and OR between compares in a condition: jumps, not values (UXC-FLOW.BL). They are
# the last two.
K_EO_LOR = 24
K_EO_LAND = 25

# The expression stacks: entries in each, and words on the run-time stack.
K_EX_MAX = 32
K_EX_DEPTH = 16

# The kinds of an entry on the nesting stack of IF, ON CASE, SELECT CASE and the loops. IFL is
# a one-line IF. The loops are the kinds from K.NS.DO up: NS.FIND counts on it.
K_NS_IFB = 1
K_NS_IFL = 2
K_NS_CASE = 3
K_NS_SEL = 4
K_NS_DO = 5
K_NS_FOR = 6
K_NS_REP = 7
K_NS_MAX = 16
# ON CASE: the targets of the ON CASE at depth d are 256 words at (d - 1) * K.CS.SIZE in
# CS.BANK. K.NS.MAX of them fill the bank.
K_CS_SIZE = 512

# The texts of the string CONSTs, at most, in bytes, in CN.BANK.
K_CN_SIZE = 2048

# A jump target, in JP.K: a known code offset, a list of jumps still to patch, a label.
K_JP_CODE = 1
K_JP_LIST = 2
K_JP_LABEL = 3

# SUB calls nested inside the arguments of SUB calls, at most.
K_SB_DEPTH = 8

# Default parameter values in a source, at most. A parameter's record holds the number of its
# default, 1 up, in the byte of a SUB's parameter count; 0 is none.
K_SB_DEFAULTS = 255

# BINDs to a word of the language, at most.
K_ALIASES = 64

# ASM blocks: the labels of one block, and the uses of a label further down. Kinds of use:
# the offset byte of a branch, and the address word of JMP or JSR.
K_ASM_LABELS = 32
K_ASM_BRANCH = 1
K_ASM_WORD = 2
