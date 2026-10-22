"""UXC-ASM.BL: ASM, 65C02 instructions and bytes put straight into the code.

    as_asm()      ASM b, b, ... or ASM alone, with the token at ASM
    as_sys()      SYS a, with the token at SYS
    as_line()     a line inside an ASM block, with the token at its start
    as_stray()    stop: END ASM with no block open
    as_open()     at the end of the source, a block still open is an error

g.as_block is 1 between ASM alone and its END ASM. sm_line then sends each line to as_line.
A line in a block is an optional label, name:, then an instruction or a list of bytes. A
line whose first word is a 65C02 mnemonic is an instruction.
The code must keep X: it is the expression stack.

The addressing modes are letters, in the table and in g.as_mode:
  A implied    B A          C #n         D zp         E zp,X       F zp,Y
  G abs        H abs,X      I abs,Y      J (zp)       K (zp,X)     L (zp),Y
  M (abs)      N (abs,X)    O a branch   P zp and a branch (BBR, BBS)
The operand forms are numbers, in g.as_form:
  0 none  1 A  2 #n  3 n  4 n,X  5 n,Y  6 (n)  7 (n,X)  8 (n),Y

GPC's PEEK(AS.A + AS.P) is g.as_table[g.as_p - 1]: AS.P counts from 1.
"""

from uxc_code import cb_add, cb_put, emit, fx_add
from uxc_defs import K_ASM_BRANCH, K_ASM_LABELS, K_ASM_WORD, K_EK_ADDR, K_EK_CONST, K_F_ABS, \
    K_F_HI, K_F_LO, K_SEC_CODE, K_SEC_CONST, K_TT_EOL, K_TT_NAME, K_TT_OP, K_TY_STR
import uxc_expr
import uxc_fold
import uxc_lex
import uxc_ramreg
import uxc_tpl as T
from uxc_state import er_mismatch, er_stop, er_syntax, g

# The opcode table, in 6 parts. An entry is /, the mnemonic, then a mode letter and two hex
# digits for each opcode.
_TABLE = (
    "/ADCC69D65E75G6DH7DI79K61L71J72/ANDC29D25E35G2DH3DI39K21L31J32/ASLB0AD06E16G0EH1E/BBRP0F"
    "/BBSP8F/BCCO90/BCSOB0/BEQOF0/BITC89D24E34G2CH3C/BMIO30/BNEOD0",
    "/BPLO10/BRAO80/BRKA00/BVCO50/BVSO70/CLCA18/CLDAD8/CLIA58/CLVAB8/CMPCC9DC5ED5GCDHDDID9KC1"
    "LD1JD2/CPXCE0DE4GEC/CPYCC0DC4GCC/DECB3ADC6ED6GCEHDE/DEXACA",
    "/DEYA88/EORC49D45E55G4DH5DI59K41L51J52/INCB1ADE6EF6GEEHFE/INXAE8/INYAC8/JMPG4CM6CN7C"
    "/JSRG20/LDACA9DA5EB5GADHBDIB9KA1LB1JB2/LDXCA2DA6FB6GAEIBE",
    "/LDYCA0DA4EB4GACHBC/LSRB4AD46E56G4EH5E/NOPAEA/ORAC09D05E15G0DH1DI19K01L11J12/PHAA48"
    "/PHPA08/PHXADA/PHYA5A/PLAA68/PLPA28/PLXAFA/PLYA7A/RMBD07",
    "/ROLB2AD26E36G2EH3E/RORB6AD66E76G6EH7E/RTIA40/RTSA60/SBCCE9DE5EF5GEDHFDIF9KE1LF1JF2"
    "/SECA38/SEDAF8/SEIA78/SMBD87/STAD85E95G8DH9DI99K81L91J92/STPADB",
    "/STXD86F96G8E/STYD84E94G8C/STZD64E74G9CH9E/TAXAAA/TAYAA8/TRBD14G1C/TSBD04G0C/TSXABA"
    "/TXAA8A/TXSA9A/TYAA98/WAIACB",
)


def as_asm():
    """AS.ASM. ASM b, b, ... with the token at ASM. ASM alone opens a block, up to END ASM
    or ENDASM."""
    uxc_lex.lx_next()
    if g.tk_t != K_TT_EOL:
        as_items()
        return
    g.as_block = 1
    g.as_no = g.lx_no
    g.as_text = g.lx_l
    g.as_label_count = 0
    g.as_reference_count = 0


def as_sys():
    """AS.SYS. SYS a. T_SYS calls a with A, X, Y and P from $030C-$030F, and stores the four
    back."""
    uxc_lex.lx_next()
    uxc_expr.ex_expr()
    uxc_expr.ex_tow()
    emit(T.T_SYS)


def as_line():
    if g.tk_t == K_TT_NAME and g.tk_m == 0:
        g.as_name = g.tk_s
        uxc_lex.lx_next()
        if g.tk_t == K_TT_OP and g.tk_k == 58:
            as_label_define()
            uxc_lex.lx_next()
        else:
            # Not a label: the line is read again from its first word.
            uxc_lex.lx_whole()
            uxc_lex.lx_next()
    as_body()


def as_body():
    if g.tk_t == K_TT_EOL:
        return
    if g.tk_t != K_TT_NAME:
        as_items()
        return
    if g.tk_s == "END":
        uxc_lex.lx_next()
        if g.tk_t != K_TT_NAME:
            er_syntax()
        if g.tk_s != "ASM":
            er_syntax()
        as_end()
        return
    if g.tk_s == "ENDASM":
        as_end()
        return
    as_lookup()
    if g.as_entry == 0:
        as_items()
        return
    as_instruction()


def as_end():
    as_resolve()
    g.as_block = 0
    uxc_lex.lx_next()


def as_items():
    """AS.ITEMS. A list of bytes, with the token at the first. A constant of 0-255 is one
    byte. A constant of 256-65535 is two, low byte first. @name is two, fixed up at link."""
    while True:
        as_value()
        if g.as_k == K_EK_CONST:
            as_constant()
        if g.as_k == K_EK_ADDR:
            as_word()
        if g.tk_t != K_TT_OP or g.tk_k != 44:
            return
        uxc_lex.lx_next()


def as_constant():
    g.as_high = g.as_v // 256
    g.cb_b = g.as_v - g.as_high * 256
    cb_add()
    if g.as_high == 0:
        return
    g.cb_b = g.as_high
    cb_add()


def as_value():
    """AS.VALUE. A constant or an @name, with the token at its start. Out: g.as_k, g.as_v,
    g.as_s, and g.as_known = 1 when g.as_v is the value itself and needs no fixup."""
    g.ex_vn = 0
    g.ex_sd = 0
    g.ex_op_base = 0
    uxc_expr.ex_expr()
    g.ex_i = g.ex_vn - 1
    g.as_k = g.ex_vk[g.ex_i]
    g.as_v = g.ex_vv[g.ex_i]
    g.as_s = g.ex_vs[g.ex_i]
    if g.ex_vt[g.ex_i] == K_TY_STR:
        er_mismatch()
    if g.as_k != K_EK_CONST and g.as_k != K_EK_ADDR:
        as_error_constant()
    if g.as_k == K_EK_CONST:
        uxc_fold.ex_const_word()
    g.as_known = 0
    if g.as_k == K_EK_CONST or g.as_s == K_SEC_CONST:
        g.as_known = 1


def as_word():
    """AS.WORD. g.as_v as two bytes, low byte first. A value not known now is a K_F_ABS
    fixup."""
    if g.as_known == 1:
        g.as_high = g.as_v // 256
        g.cb_b = g.as_v - g.as_high * 256
        cb_add()
        g.cb_b = g.as_high
        cb_add()
        return
    g.fx_at = g.cb_n
    g.fx_k = K_F_ABS
    g.fx_s = g.as_s
    g.fx_v = g.as_v
    fx_add()
    g.cb_b = 0
    cb_add()
    g.cb_b = 0
    cb_add()


def as_byte():
    """AS.BYTE. One byte: g.as_v, or its low byte when g.as_part is 1, or its high byte when
    2. A value not known now takes a K_F_LO or K_F_HI fixup, and needs g.as_part."""
    if g.as_known == 0:
        if g.as_part == 0:
            as_error_byte()
        g.fx_at = g.cb_n
        g.fx_k = K_F_LO
        if g.as_part == 2:
            g.fx_k = K_F_HI
        g.fx_s = g.as_s
        g.fx_v = g.as_v
        fx_add()
        g.cb_b = 0
        cb_add()
        return
    g.as_high = g.as_v // 256
    if g.as_part == 0 and g.as_high != 0:
        as_error_byte()
    g.cb_b = g.as_v - g.as_high * 256
    if g.as_part == 2:
        g.cb_b = g.as_high
    cb_add()


# ---- instructions ----

def as_lookup():
    """AS.LOOKUP. The mnemonic in g.tk_s. Out: g.as_entry, the place of its entry in
    g.as_table, or 0 when g.tk_s is not a mnemonic. g.as_bit is the bit number times 16 of
    RMB, SMB, BBR and BBS."""
    g.as_entry = 0
    g.as_bit = 0
    g.as_has_bit = 0
    g.as_mnemonic = g.tk_s
    if len(g.as_mnemonic) == 4:
        as_lookup_bit()
    if len(g.as_mnemonic) != 3:
        return
    g.as_key = "/" + g.as_mnemonic
    g.as_chunk = 1
    while True:
        as_table_chunk()
        g.as_entry = g.as_table.find(g.as_key) + 1
        if g.as_entry != 0:
            break
        g.as_chunk = g.as_chunk + 1
        if g.as_chunk > 6:
            return
    g.as_bit_family = 0
    if g.as_mnemonic == "RMB" or g.as_mnemonic == "SMB":
        g.as_bit_family = 1
    if g.as_mnemonic == "BBR" or g.as_mnemonic == "BBS":
        g.as_bit_family = 1
    if g.as_bit_family != g.as_has_bit:
        g.as_entry = 0


def as_lookup_bit():
    g.as_digit = ord(g.as_mnemonic[-1]) - 48
    if g.as_digit < 0 or g.as_digit > 7:
        return
    g.as_bit = g.as_digit * 16
    g.as_has_bit = 1
    g.as_mnemonic = g.as_mnemonic[:3]


def as_table_chunk():
    """AS.TABLE.CHUNK. Part g.as_chunk of the opcode table, in g.as_table."""
    g.as_table = _TABLE[g.as_chunk - 1]


def as_opcode():
    """AS.OPCODE. The opcode of the mnemonic at g.as_entry in mode g.as_mode, in g.as_code,
    or -1 when the mnemonic has no such mode."""
    g.as_code = -1
    g.as_n = len(g.as_table)
    g.as_p = g.as_entry + 4
    while True:
        if g.as_p > g.as_n:
            return
        g.as_c = g.as_table[g.as_p - 1]
        if g.as_c == "/":
            return
        if g.as_c == g.as_mode:
            break
        g.as_p = g.as_p + 3
    g.as_p = g.as_p + 1
    as_hex_digit()
    g.as_code = g.as_h * 16 + g.as_bit
    g.as_p = g.as_p + 1
    as_hex_digit()
    g.as_code = g.as_code + g.as_h


def as_hex_digit():
    g.as_h = ord(g.as_table[g.as_p - 1]) - 48
    if g.as_h > 9:
        g.as_h = g.as_h - 7


def as_instruction():
    """AS.INSTRUCTION. An instruction, with the token at its mnemonic."""
    g.as_operand_p = g.lx_p
    uxc_lex.lx_next()
    g.as_mode = "O"
    as_opcode()
    if g.as_code >= 0:
        as_branch()
        return
    g.as_mode = "P"
    as_opcode()
    if g.as_code >= 0:
        as_bit_branch()
        return
    g.as_jumped = 0
    if g.as_mnemonic == "JMP" or g.as_mnemonic == "JSR":
        as_jump()
    if g.as_jumped == 1:
        return
    as_operand()
    as_choose()
    uxc_ramreg.rg_asm()
    g.cb_b = g.as_code
    cb_add()
    if g.as_mode == "A" or g.as_mode == "B":
        return
    if g.as_mode in "GHIMN":
        as_word()
        return
    as_byte()


def as_operand():
    """AS.OPERAND. The operand, with the token after the mnemonic. Out: g.as_form,
    g.as_part, and the value from as_value."""
    g.as_form = 0
    g.as_part = 0
    if g.tk_t == K_TT_EOL:
        return
    if g.tk_t == K_TT_NAME and g.tk_s == "A":
        g.as_form = 1
        uxc_lex.lx_next()
        return
    if g.tk_t == K_TT_OP and g.tk_k == 35:
        as_immediate()
        return
    if g.tk_t == K_TT_OP and g.tk_k == 40:
        as_indirect()
        return
    as_value()
    g.as_form = 3
    if g.tk_t != K_TT_OP or g.tk_k != 44:
        return
    as_index()
    if g.as_register == "X":
        g.as_form = 4
    if g.as_register == "Y":
        g.as_form = 5


def as_immediate():
    """#n, #<n or #>n. < and > take the low and the high byte."""
    g.as_form = 2
    uxc_lex.lx_next()
    if g.tk_t == K_TT_OP and g.tk_k == 60:
        g.as_part = 1
    if g.tk_t == K_TT_OP and g.tk_k == 62:
        g.as_part = 2
    if g.as_part != 0:
        uxc_lex.lx_next()
    as_value()


def as_indirect():
    """(n), (n,X) or (n),Y, with the token at the (."""
    uxc_lex.lx_next()
    as_value()
    g.as_form = 6
    if g.tk_t == K_TT_OP and g.tk_k == 44:
        as_index()
        if g.as_register != "X":
            er_syntax()
        g.as_form = 7
    if g.tk_t != K_TT_OP or g.tk_k != 41:
        as_error_parenthesis()
    uxc_lex.lx_next()
    if g.as_form == 7:
        return
    if g.tk_t != K_TT_OP or g.tk_k != 44:
        return
    as_index()
    if g.as_register != "Y":
        er_syntax()
    g.as_form = 8


def as_index():
    """AS.INDEX. ,X or ,Y with the token at the comma. Out: g.as_register."""
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NAME:
        er_syntax()
    g.as_register = g.tk_s
    if g.as_register != "X" and g.as_register != "Y":
        er_syntax()
    uxc_lex.lx_next()


def as_choose():
    """AS.CHOOSE. The mode for g.as_form, in g.as_mode, and its opcode. The short mode, the
    zero page one, is taken when the value is known and below 256 and the mnemonic has it."""
    if g.as_form < 3 or (g.as_known == 1 and g.as_v < 256):
        g.as_mode = "ABCDEFJKL"[g.as_form]
        as_opcode()
        if g.as_code >= 0:
            return
    g.as_mode = "BBCGHIMN-"[g.as_form]
    as_opcode()
    if g.as_code < 0:
        as_error_mode()


# ---- labels and branches ----

def as_branch():
    """AS.BRANCH. A branch to a label, with the token after the mnemonic."""
    g.cb_b = g.as_code
    cb_add()
    as_target()


def as_bit_branch():
    """AS.BIT.BRANCH. BBRn or BBSn zp, label."""
    g.cb_b = g.as_code
    cb_add()
    g.as_part = 0
    as_value()
    as_byte()
    if g.tk_t != K_TT_OP or g.tk_k != 44:
        er_syntax()
    uxc_lex.lx_next()
    as_target()


def as_target():
    """AS.TARGET. The offset byte of a branch, with the token at the label. A label further
    down is patched at END ASM."""
    if g.tk_t != K_TT_NAME or g.tk_m != 0:
        as_error_target()
    g.as_name = g.tk_s
    uxc_lex.lx_next()
    as_label_find()
    if g.as_found < 0:
        g.as_kind = K_ASM_BRANCH
        as_reference_add()
        g.cb_b = 0
        cb_add()
        return
    g.as_at = g.cb_n
    g.as_to = g.as_label_at[g.as_found]
    as_offset()
    if g.as_far == 1:
        as_error_range()
    cb_add()


def as_offset():
    """AS.OFFSET. The offset in g.cb_b of a branch whose offset byte is at g.as_at, to
    g.as_to. g.as_far = 1 when the label is out of reach."""
    g.as_far = 0
    g.as_distance = g.as_to - g.as_at - 1
    if g.as_distance < -128 or g.as_distance > 127:
        g.as_far = 1
    if g.as_distance < 0:
        g.as_distance = g.as_distance + 256
    g.cb_b = g.as_distance


def as_jump():
    """AS.JUMP. JMP label or JSR label, with the token after the mnemonic. A name alone on
    the rest of the line is a label. g.as_jumped = 1 when it was one; else the operand is
    read again from g.as_operand_p."""
    if g.tk_t != K_TT_NAME or g.tk_m != 0:
        return
    g.as_name = g.tk_s
    uxc_lex.lx_next()
    if g.tk_t != K_TT_EOL:
        g.lx_p = g.as_operand_p
        uxc_lex.lx_next()
        return
    g.as_jumped = 1
    g.as_mode = "G"
    as_opcode()
    g.cb_b = g.as_code
    cb_add()
    g.as_at = g.cb_n
    g.cb_b = 0
    cb_add()
    g.cb_b = 0
    cb_add()
    as_label_find()
    if g.as_found < 0:
        g.as_kind = K_ASM_WORD
        as_reference_add()
        return
    g.as_to = g.as_label_at[g.as_found]
    as_label_word()


def as_label_word():
    """AS.LABEL.WORD. A K_F_ABS fixup at g.as_at to the code at g.as_to."""
    g.fx_at = g.as_at
    g.fx_k = K_F_ABS
    g.fx_s = K_SEC_CODE
    g.fx_v = g.as_to
    fx_add()


def as_label_define():
    as_label_find()
    if g.as_found >= 0:
        as_error_duplicate()
    if g.as_label_count == K_ASM_LABELS:
        as_error_labels()
    g.as_label_name[g.as_label_count] = g.as_name
    g.as_label_at[g.as_label_count] = g.cb_n
    g.as_label_count = g.as_label_count + 1


def as_label_find():
    """AS.LABEL.FIND. The label g.as_name of this block. Out: g.as_found, its index, or -1."""
    g.as_found = g.as_label_count - 1
    while g.as_found >= 0:
        if g.as_label_name[g.as_found] == g.as_name:
            return
        g.as_found = g.as_found - 1


def as_reference_add():
    """AS.REFERENCE.ADD. The label g.as_name, not yet defined, is wanted at g.cb_n, or at
    g.as_at for a K_ASM_WORD."""
    if g.as_reference_count == K_ASM_LABELS:
        as_error_labels()
    g.as_reference_name[g.as_reference_count] = g.as_name
    g.as_reference_at[g.as_reference_count] = g.cb_n
    if g.as_kind == K_ASM_WORD:
        g.as_reference_at[g.as_reference_count] = g.as_at
    g.as_reference_kind[g.as_reference_count] = g.as_kind
    g.as_reference_no[g.as_reference_count] = g.lx_no
    g.as_reference_count = g.as_reference_count + 1


def as_resolve():
    """AS.RESOLVE. At END ASM, every branch and jump to a label further down."""
    g.as_r = 0
    while g.as_r < g.as_reference_count:
        g.as_name = g.as_reference_name[g.as_r]
        as_label_find()
        if g.as_found < 0:
            as_error_unknown()
        g.as_at = g.as_reference_at[g.as_r]
        g.as_to = g.as_label_at[g.as_found]
        if g.as_reference_kind[g.as_r] == K_ASM_BRANCH:
            as_offset()
            if g.as_far == 1:
                as_error_far()
            g.cb_at = g.as_at
            cb_put()
        if g.as_reference_kind[g.as_r] == K_ASM_WORD:
            as_label_word()
        g.as_r = g.as_r + 1


# ---- errors ----

def as_error_constant():
    er_stop("ASM TAKES A CONSTANT OR @NAME")


def as_error_byte():
    er_stop("NOT A BYTE")


def as_error_mode():
    er_stop("NO SUCH ADDRESS MODE")


def as_error_parenthesis():
    er_stop("MISSING )")


def as_error_target():
    er_stop("BRANCH TAKES A LABEL")


def as_error_range():
    er_stop("BRANCH OUT OF RANGE")


def as_error_duplicate():
    er_stop("DUPLICATE LABEL " + g.as_name)


def as_error_labels():
    er_stop("TOO MANY ASM LABELS")


# The errors found at END ASM name the line of the branch. The text printed is empty.
def as_error_unknown():
    g.lx_no = g.as_reference_no[g.as_r]
    g.lx_l = ""
    er_stop("LABEL NOT FOUND: " + g.as_name)


def as_error_far():
    g.lx_no = g.as_reference_no[g.as_r]
    g.lx_l = ""
    as_error_range()


def as_stray():
    er_stop("END ASM WITHOUT ASM")


def as_open():
    if g.as_block == 0:
        return
    g.lx_no = g.as_no
    g.lx_l = g.as_text
    er_stop("ASM WITHOUT END ASM")
