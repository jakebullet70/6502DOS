"""UXC-STR.BL: strings.

    sg_print_item()  one PRINT item. Out: g.sg_printed, 1 when it was a string and is printed
    sg_literal()     a literal as an operand
    sg_function()    LEN, ASC, VAL, LVAL, CHR$, STR$, MID$, LEFT$, RIGHT$, INSTR, OPEN, EOF or
                     READ as an operand. Out: g.sg_found
    sg_at()          @name of a string, with g.ex_* made for a variable
    sg_left()        the left side of a +, before its right side is parsed
    sg_binary()      + or a compare on the two top entries, when either is a string
    sg_tos()         the top entry, a string, into A/Y
    sg_dim()         DIM name$ * n, with the token after the type
    sg_let()         name$ = expr, with the variable's record in g.sy_* and the token at the =
    sg_pass()        the top entry as the argument of a STRING parameter, into A/Y
    sg_result()      the result of a STRING SUB, in A/Y after its JSR, as a new entry
    sg_return_empty()  A/Y = the address of "", for a STRING SUB that ends with no RETURN
    sg_input()       INPUT or LINPUT, from the keyboard or #handle, with the token at the keyword
    sg_write()       WRITE handle, address, count, with the token at WRITE
    sg_maxes()       at link, emit the max of each string variable's block

UXC-STR.BL has the layout of a string block, the temps, and when a + skips its temp.
"""

from uxc_code import emit, sp_add
from uxc_defs import K_EK_ADDR, K_EK_CMP, K_EK_CONST, K_EK_MEM, K_EK_REG, K_EO_ADD, K_EO_EQ, \
    K_EO_GE, K_EO_GT, K_EO_LE, K_EO_LT, K_EO_NE, K_EX_DEPTH, K_FRAME_BASE, K_OP_GE, K_OP_NE, \
    K_SEC_BSS, K_SEC_CONST, K_SEC_STR, K_SEC_TEMP, K_SEC_VAR, K_SK_ARRAY, K_SK_VAR, K_SY_TEMP, \
    K_TEMP_PRINTED, K_TT_EOL, K_TT_NAME, K_TT_NUM, K_TT_OP, K_TT_STR, K_TY_BYTE, K_TY_LONG, \
    K_TY_RECORD, K_TY_STR, K_TY_WORD
import uxc_expr
import uxc_fold
import uxc_lex
import uxc_name
import uxc_record
import uxc_stmt
import uxc_sub
import uxc_sym
import uxc_tpl as T
from uxc_state import er_mismatch, er_stop, er_syntax, g


def sg_dim():
    """SG.DIM. A block of n + 2 bytes in the array space. g.sm_n is the name and g.sm_cnt its
    element count."""
    if g.sm_cnt != 0:
        er_stop("NOT YET: STRING ARRAYS")
    if g.tk_t != K_TT_OP or g.tk_k != 42:
        er_stop("NO SIZE FOR " + g.sm_n)
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NUM:
        sg_error_size()
    if g.tk_v < 1 or g.tk_v > 255:
        sg_error_size()
    g.sg_size = g.tk_v
    uxc_lex.lx_next()
    if g.tk_t == K_TT_OP and g.tk_k == 61:
        er_stop("NOT YET: A START VALUE")
    g.sy_name = g.sm_n
    g.sy_ow = g.nm_scope
    uxc_sym.sy_find()
    if g.sy_r != 0:
        er_stop("DUPLICATE NAME " + g.sm_n)
    g.sb_place_size = g.sg_size + 2
    uxc_sub.sb_place_block()
    g.sy_kind = K_SK_VAR
    g.sy_type = K_TY_STR
    g.sy_val = g.sb_place
    g.sy_flags = 0
    g.sy_cnt = g.sg_size
    uxc_sym.sy_add()
    if g.sb_current != 0:
        sg_empty_local()


def sg_empty_local():
    """SG.EMPTY.LOCAL. A string DIM in a SUB sets its block to empty each time it runs: the
    max is g.sg_size and the length 0. A global block gets its max once, at startup."""
    g.sl_s[0] = K_SEC_CONST
    g.sl_v[0] = g.sg_size
    emit(T.T_LDW_C)
    g.sl_s[0] = K_SEC_BSS
    g.sl_v[0] = g.sb_place
    emit(T.T_STW_V)


def sg_let():
    """SG.LET. The text is copied into the block, cut at its max. A$ = A$ copies nothing.
    A$ = "" stores 0 in the length byte."""
    uxc_record.rd_section()
    g.sg_destination = g.sy_val
    g.sg_section = g.rd_sec
    g.sg_template = T.T_SCOPY
    if g.sy_cnt == 0:
        g.sg_template = T.T_SCOPY_P
    uxc_lex.lx_next()
    g.sg_appending = 0
    if g.sy_cnt > 0:
        g.sg_whole = g.sm_n
        sg_base_of()
        g.sg_scan_name = g.sg_base_name
        g.sg_scan_item = 0
        sg_scan()
        if g.sg_scan_count == 1 and g.sg_scan_call == 0:
            g.sg_appending = 1
    g.sg_base = g.ex_vn
    g.sg_depth = g.sb_depth
    uxc_expr.ex_expr()
    g.sg_appending = 0
    sg_is_destination()
    if g.sg_same == 1:
        g.ex_vn = g.ex_vn - 1
        return
    if g.sg_section != K_SEC_VAR:
        g.ex_i = g.ex_vn - 1
        sg_is_empty()
        if g.sg_empty == 1:
            sg_take_literal()
            g.ex_vn = g.ex_vn - 1
            g.sl_s[0] = g.sg_section
            g.sl_v[0] = g.sg_destination
            emit(T.T_SCLEAR)
            return
    sg_tos()
    g.sl_s[0] = g.sg_section
    g.sl_v[0] = g.sg_destination
    emit(g.sg_template)


def sg_is_destination():
    """SG.IS.DESTINATION. g.sg_same = 1 when the top entry is the block g.sg_destination of
    section g.sg_section."""
    g.sg_same = 0
    g.ex_i = g.ex_vn - 1
    if g.sg_section == K_SEC_VAR or g.ex_vt[g.ex_i] != K_TY_STR:
        return
    if g.ex_vk[g.ex_i] != K_EK_ADDR or g.ex_vs[g.ex_i] != g.sg_section:
        return
    if g.ex_vv[g.ex_i] == g.sg_destination:
        g.sg_same = 1


def sg_print_item():
    """SG.PRINT.ITEM. The string temps are free again after the item."""
    g.sg_n = 0
    g.sg_pointers = 0
    g.sg_chr_end = -1
    g.sg_scan_name = ""
    g.sg_scan_item = 1
    sg_scan()
    g.sg_printing = 0
    if g.sg_scan_call == 0 and g.sg_scan_compare == 0:
        g.sg_printing = 1
    g.sg_base = g.ex_vn
    g.sg_depth = g.sb_depth
    uxc_expr.ex_expr()
    g.sg_printing = 0
    g.sg_printed = 0
    g.ex_i = g.ex_vn - 1
    if g.ex_vt[g.ex_i] != K_TY_STR:
        return
    g.sg_printed = 1
    if g.ex_vs[g.ex_i] == K_SEC_TEMP and g.ex_vv[g.ex_i] == K_TEMP_PRINTED:
        g.ex_vn = g.ex_vn - 1
        return
    # CHR$(x) with no code after its T_CHR: A still holds x.
    if g.ex_vs[g.ex_i] == K_SEC_TEMP and g.ex_vv[g.ex_i] == g.sg_chr_temp \
            and g.cb_n == g.sg_chr_end:
        g.cb_n = g.sg_chr_start
        g.fx_n = g.sg_chr_fixups
        g.ex_vn = g.ex_vn - 1
        emit(T.T_PRCHR)
        return
    g.sg_was_literal = 0
    if len(g.sg_last_text) == 1:
        sg_take_literal()
    if g.sg_was_literal == 1:
        g.ex_r = ord(g.sg_last_text)
        uxc_expr.ex_setc()
        uxc_expr.ex_tob()
        emit(T.T_PRCHR)
        return
    sg_tos()
    emit(T.T_PRSTR)


def sg_scan():
    """SG.SCAN. Read the rest of the statement, or of the PRINT item when g.sg_scan_item = 1.
    In: g.sg_scan_name, a name with no namespace. Out: g.sg_scan_count, the names that end in
    it; g.sg_scan_call = 1 when a name before a ( is not an array; g.sg_scan_compare = 1 when
    there is a compare. The token and g.lx_p are put back after."""
    g.sg_saved_p = g.lx_p
    g.sg_saved_t = g.tk_t
    g.sg_saved_k = g.tk_k
    g.sg_saved_v = g.tk_v
    g.sg_saved_m = g.tk_m
    g.sg_saved_s = g.tk_s
    g.sg_scan_count = 0
    g.sg_scan_call = 0
    g.sg_scan_compare = 0
    g.sg_scan_depth = 0
    g.sg_scan_unknown = 0
    while g.tk_t != K_TT_EOL:
        if g.tk_t == K_TT_NAME:
            if g.sg_scan_depth == 0 and g.tk_s == "ELSE":
                break
            g.sg_whole = g.tk_s
            sg_base_of()
            if g.sg_base_name == g.sg_scan_name:
                g.sg_scan_count = g.sg_scan_count + 1
            g.sg_scan_last = g.tk_s
            sg_scan_known()
            uxc_lex.lx_next()
            continue
        if g.tk_t == K_TT_OP:
            if g.sg_scan_item == 1 and g.sg_scan_depth == 0 and (g.tk_k == 59 or g.tk_k == 44):
                break
            if g.tk_k == 40 and g.sg_scan_unknown == 1:
                sg_scan_array()
            if g.tk_k == 40:
                g.sg_scan_depth = g.sg_scan_depth + 1
            if g.tk_k == 41:
                g.sg_scan_depth = g.sg_scan_depth - 1
            if g.tk_k == 60 or g.tk_k == 61 or g.tk_k == 62:
                g.sg_scan_compare = 1
            if g.tk_k >= K_OP_NE and g.tk_k <= K_OP_GE:
                g.sg_scan_compare = 1
        g.sg_scan_unknown = 0
        uxc_lex.lx_next()
    g.lx_p = g.sg_saved_p
    g.tk_t = g.sg_saved_t
    g.tk_k = g.sg_saved_k
    g.tk_v = g.sg_saved_v
    g.tk_m = g.sg_saved_m
    g.tk_s = g.sg_saved_s


def sg_scan_array():
    """SG.SCAN.ARRAY. g.sg_scan_call = 1 unless g.sg_scan_last, the name before the (, is an
    array. Clobbers g.sy_* and the nm_find state; g.sm_n is kept."""
    g.sg_scan_saved_n = g.sm_n
    g.sm_n = g.sg_scan_last
    uxc_name.nm_find()
    g.sm_n = g.sg_scan_saved_n
    if g.sy_kind != K_SK_ARRAY:
        g.sg_scan_call = 1


def sg_scan_known():
    """SG.SCAN.KNOWN. g.sg_scan_unknown = 1 when the name in g.tk_s is not a function or an
    operator of the compiler, so that a ( after it may be a SUB call or an array.
    A new built-in function in ex_operand goes in this list too, or sg_scan_array reports it
    as UNDECLARED NAME."""
    g.sg_scan_unknown = 1
    if g.tk_s in ("LEN", "ASC", "VAL", "CHR$", "STR$", "MID$", "LEFT$", "RIGHT$", "PEEK", "NOT", "INSTR", "POS",
                  "LVAL", "AND", "OR", "XOR", "MOD", "GETKEY", "OPEN", "EOF", "READ", "ADDROF",
                  "CONTENTSAT", "CONTENTSATW", "GETEXTKEY", "WAITKEY", "KEYMODS"):
        g.sg_scan_unknown = 0


def sg_base_of():
    """SG.BASE.OF. g.sg_base_name is the last part of the name g.sg_whole, after its last
    dot. GPC UXC calls it SG.BASE$."""
    g.sg_base_at = len(g.sg_whole)
    while g.sg_base_at != 0:
        if g.sg_whole[g.sg_base_at - 1] == ".":
            break
        g.sg_base_at = g.sg_base_at - 1
    g.sg_base_name = g.sg_whole[g.sg_base_at:]


# Operands

def sg_literal():
    g.sg_text = g.tk_s
    sg_push_literal()
    uxc_lex.lx_next()


def sg_push_literal():
    """SG.PUSH.LITERAL. g.sg_text as a new literal entry. g.sg_last_text, g.sg_last_offset and
    g.sg_last_new keep it for sg_take_literal. g.sg_empty_offset is the offset of "", while
    g.sg_empty_known = 1."""
    g.sp_s = g.sg_text
    sp_add()
    g.sg_last_text = g.sg_text
    g.sg_last_offset = g.sp_v
    g.sg_last_new = g.sp_new
    if g.sg_text == "":
        g.sg_empty_offset = g.sp_v
    if g.sg_text == "":
        g.sg_empty_known = 1
    g.ex_k = K_EK_ADDR
    g.ex_s = K_SEC_STR
    g.ex_v = g.sp_v
    g.ex_ty = K_TY_STR
    uxc_expr.ex_pushv()


def sg_take_literal():
    """SG.TAKE.LITERAL. g.sg_was_literal = 1 when entry g.ex_i is the literal pushed last. The
    caller folds its value into a constant, so a literal that sp_add kept for it alone is
    taken back out of the strings."""
    g.sg_was_literal = 0
    if g.ex_vk[g.ex_i] != K_EK_ADDR or g.ex_vs[g.ex_i] != K_SEC_STR:
        return
    if g.ex_vv[g.ex_i] != g.sg_last_offset:
        return
    g.sg_was_literal = 1
    if g.sg_last_new == 0:
        return
    g.sp_n = g.sg_last_offset
    g.sg_last_new = 0
    if g.sg_empty_offset == g.sg_last_offset:
        g.sg_empty_known = 0


def sg_is_empty():
    """SG.IS.EMPTY. g.sg_empty = 1 when entry g.ex_i is the literal ""."""
    g.sg_empty = 0
    if g.sg_empty_known == 0:
        return
    if g.ex_vk[g.ex_i] != K_EK_ADDR or g.ex_vs[g.ex_i] != K_SEC_STR:
        return
    if g.ex_vv[g.ex_i] == g.sg_empty_offset:
        g.sg_empty = 1


def sg_at():
    """SG.AT. The address a STRING parameter holds."""
    if g.sy_cnt == 0:
        g.ex_k = K_EK_MEM


# The functions

def sg_function():
    """SG.FUNCTION. With the token at a name. Each argument is parsed as an expression of its
    own, nested as a SUB call's arguments are, and g.sg_called keeps the function's name for
    each depth."""
    g.sg_found = 0
    if uxc_lex.instr("|LEN|ASC|VAL|LVAL|CHR$|STR$|MID$|LEFT$|RIGHT$|INSTR|OPEN|EOF|READ|",
                     "|" + g.tk_s + "|") == 0:
        return
    g.sg_name = g.tk_s
    uxc_lex.lx_next()
    if g.tk_t != K_TT_OP or g.tk_k != 40:
        er_stop("MISSING ( AFTER " + g.sg_name)
    if g.sg_name == "LEN":
        uxc_record.rd_len()
        if g.rd_len_found != 0:
            g.sg_found = 1
            return
    uxc_sub.sb_nest()
    g.sg_called[g.sb_depth] = g.sg_name
    sg_argument()
    g.sg_name = g.sg_called[g.sb_depth]
    if g.sg_name == "MID$":
        sg_mid()
    elif g.sg_name == "LEFT$" or g.sg_name == "RIGHT$":
        sg_left_right()
    elif g.sg_name == "INSTR":
        sg_instr()
    else:
        sg_one()
    g.sg_found = 1


def sg_argument():
    """SG.ARGUMENT. One argument, with the token at the ( or the , before it."""
    uxc_lex.lx_next()
    g.ex_op_base = g.ex_on
    g.ex_cm = 0
    uxc_expr.ex_expr()


def sg_close():
    """SG.CLOSE. The ) after the last argument."""
    if g.tk_t != K_TT_OP or g.tk_k != 41:
        er_stop("MISSING )")
    uxc_sub.sb_unnest()
    uxc_lex.lx_next()


def sg_one():
    """SG.ONE. A function of one argument, g.sg_name, on the top entry."""
    if g.sg_name == "OPEN":
        sg_open()
        return
    if g.sg_name == "READ":
        sg_read()
        return
    sg_close()
    g.ex_i = g.ex_vn - 1
    if g.sg_name == "LEN":
        sg_len()
    elif g.sg_name == "ASC":
        sg_asc()
    elif g.sg_name == "VAL":
        sg_val()
    elif g.sg_name == "LVAL":
        sg_lval()
    elif g.sg_name == "CHR$":
        sg_chr()
    elif g.sg_name == "EOF":
        sg_eof()
    else:
        sg_str()


def sg_eof():
    """SG.EOF. A compare: C is set when the handle has nothing more to read."""
    uxc_expr.ex_tob()
    emit(T.T_EOF)
    g.ex_k = K_EK_CMP
    g.ex_s = K_SEC_CONST
    g.ex_v = T.T_CTRUE
    g.ex_ty = K_TY_BYTE
    uxc_expr.ex_pushv()


def sg_len():
    """SG.LEN. LEN of a literal is a constant."""
    if g.ex_vt[g.ex_i] != K_TY_STR:
        er_mismatch()
    sg_take_literal()
    if g.sg_was_literal == 1:
        g.ex_r = len(g.sg_last_text)
        uxc_expr.ex_setc()
        return
    sg_length()


def sg_length():
    """SG.LENGTH. The string on top becomes its length, a BYTE. A block at a known address
    becomes its length byte, with no code."""
    g.ex_i = g.ex_vn - 1
    if g.ex_vk[g.ex_i] == K_EK_ADDR:
        g.ex_vk[g.ex_i] = K_EK_MEM
        g.ex_vv[g.ex_i] = g.ex_vv[g.ex_i] + 1
        g.ex_vt[g.ex_i] = K_TY_BYTE
        return
    sg_tos()
    emit(T.T_SLEN)
    sg_push_byte()


def sg_asc():
    """SG.ASC. ASC of a literal is a constant: its first character, or 0 when it is empty."""
    if g.ex_vt[g.ex_i] != K_TY_STR:
        er_mismatch()
    sg_take_literal()
    if g.sg_was_literal == 1:
        g.ex_r = 0
        if g.sg_last_text != "":
            g.ex_r = ord(g.sg_last_text[0])
        uxc_expr.ex_setc()
        return
    sg_tos()
    emit(T.T_ASC)
    sg_push_byte()


def sg_val():
    sg_tos()
    emit(T.T_VAL)
    g.ex_ty = K_TY_WORD
    sg_push_register()


def sg_lval():
    sg_tos()
    emit(T.T_LVAL)
    g.ex_ty = K_TY_LONG
    sg_push_register()


def sg_chr():
    """SG.CHR. CHR$ of a constant is a literal."""
    if g.ex_vk[g.ex_i] == K_EK_CONST:
        g.sg_text = chr(g.ex_vv[g.ex_i] - (g.ex_vv[g.ex_i] // 256) * 256)
        g.ex_vn = g.ex_vn - 1
        sg_push_literal()
        return
    uxc_expr.ex_tob()
    sg_new_temp()
    g.sl_s[0] = K_SEC_TEMP
    g.sl_v[0] = g.sg_temp
    g.sg_chr_start = g.cb_n
    g.sg_chr_fixups = g.fx_n
    emit(T.T_CHR)
    g.sg_chr_end = g.cb_n
    g.sg_chr_temp = g.sg_temp
    sg_push_temp()


def sg_str():
    """SG.STR. STR$ of a constant is a literal."""
    g.sg_str_signed = g.ex_vg[g.ex_i]
    if g.ex_vk[g.ex_i] == K_EK_CONST:
        uxc_fold.ex_whole()
        uxc_fold.ex_text()
        g.sg_text = g.ex_text_result
        g.ex_vn = g.ex_vn - 1
        sg_push_literal()
        return
    g.sg_str_long = 0
    if g.ex_vt[g.ex_i] == K_TY_LONG:
        g.sg_str_long = 1
    if g.sg_str_long == 0:
        uxc_expr.ex_tow()
    if g.sg_str_long == 1:
        uxc_expr.ex_tol()
    sg_new_temp()
    g.sl_s[0] = K_SEC_TEMP
    g.sl_v[0] = g.sg_temp
    g.sg_str_template = T.T_STR
    if g.sg_str_signed == 1:
        g.sg_str_template = T.T_SSTR
    if g.sg_str_long == 1:
        g.sg_str_template = T.T_LSTR
    if g.sg_str_long == 1 and g.sg_str_signed == 1:
        g.sg_str_template = T.T_SLSTR
    emit(g.sg_str_template)
    sg_push_temp()


def sg_mid():
    """SG.MID. MID$(string, start[, length]): the string and the start are pushed, and the
    length is in A/Y, 255 when it is left out."""
    sg_tos()
    sg_stack()
    if g.tk_t != K_TT_OP or g.tk_k != 44:
        er_syntax()
    sg_argument()
    uxc_expr.ex_tow()
    sg_stack()
    g.sg_default = 255
    sg_last_word()
    sg_new_temp()
    g.sl_s[0] = K_SEC_TEMP
    g.sl_v[0] = g.sg_temp
    emit(T.T_MID)
    g.ex_sd = g.ex_sd - 2
    sg_push_temp()


def sg_left_right():
    """SG.LEFT.RIGHT. LEFT$(string, length) and RIGHT$(string, length), as g.sg_name: the string is
    pushed, and the length is in A/Y."""
    record = T.T_LEFT
    if g.sg_name == "RIGHT$":
        record = T.T_RIGHT
    sg_tos()
    sg_stack()
    if g.tk_t != K_TT_OP or g.tk_k != 44:
        er_syntax()
    sg_argument()
    uxc_expr.ex_tow()
    sg_close()
    sg_new_temp()
    g.sl_s[0] = K_SEC_TEMP
    g.sl_v[0] = g.sg_temp
    emit(record)
    g.ex_sd = g.ex_sd - 1
    sg_push_temp()


def sg_instr():
    """SG.INSTR. INSTR(string, find[, start]): the string and find are pushed, and the start
    is in A/Y, 1 when it is left out."""
    sg_tos()
    sg_stack()
    if g.tk_t != K_TT_OP or g.tk_k != 44:
        er_syntax()
    sg_argument()
    sg_tos()
    sg_stack()
    g.sg_default = 1
    sg_last_word()
    emit(T.T_INSTR)
    g.ex_sd = g.ex_sd - 2
    sg_push_byte()


def sg_last_word():
    """SG.LAST.WORD. An optional last argument into A/Y as a WORD, g.sg_default when it is
    left out. Then the )."""
    if g.tk_t == K_TT_OP and g.tk_k == 44:
        sg_argument()
        uxc_expr.ex_tow()
    else:
        g.sl_s[0] = K_SEC_CONST
        g.sl_v[0] = g.sg_default
        emit(T.T_LDW_C)
    sg_close()


def sg_open():
    """SG.OPEN. OPEN(name$, mode): the handle, a WORD. The mode is a name, so the whole DOS
    name is known here: name,S,R for O.READ, @:name,S,W for O.WRITE, name,S,A for O.APPEND. On
    UXDOS16 the name is followed by the mode's letter only: R, W or A. A literal name is joined
    at compile time."""
    g.ex_i = g.ex_vn - 1
    if g.ex_vt[g.ex_i] != K_TY_STR:
        er_mismatch()
    if g.tk_t != K_TT_OP or g.tk_k != 44:
        er_syntax()
    uxc_lex.lx_next()
    g.sg_open_prefix = ""
    g.sg_open_suffix = ""
    if g.tk_t == K_TT_NAME:
        if g.tk_s == "O.READ":
            g.sg_open_suffix = ",S,R"
        if g.tk_s == "O.WRITE":
            g.sg_open_suffix = ",S,W"
        if g.tk_s == "O.APPEND":
            g.sg_open_suffix = ",S,A"
    if g.sg_open_suffix == "":
        er_stop("MODE MUST BE O.READ, O.WRITE OR O.APPEND")
    if g.sg_open_suffix == ",S,W":
        g.sg_open_prefix = "@:"
    reading = g.sg_open_suffix == ",S,R"
    if g.target == "uxdos16":
        g.sg_open_prefix = ""
        g.sg_open_suffix = g.sg_open_suffix[-1]
    uxc_lex.lx_next()
    sg_close()
    g.ex_i = g.ex_vn - 1
    sg_take_literal()
    if g.sg_was_literal == 1:
        g.ex_vn = g.ex_vn - 1
        g.sg_text = g.sg_open_prefix + g.sg_last_text + g.sg_open_suffix
        sg_push_literal()
    else:
        sg_open_join()
    sg_tos()
    if reading:
        emit(T.T_FOPEN)
    else:
        emit(T.T_OPEN)
    g.ex_ty = K_TY_WORD
    sg_push_register()


def sg_read():
    """SG.READ. READ(handle, address, max): A/Y = the count of bytes read."""
    sg_block_arguments()
    sg_close()
    emit(T.T_READ)
    g.ex_ty = K_TY_WORD
    sg_push_register()


def sg_write():
    """SG.WRITE. WRITE handle, address, count, with the token at WRITE."""
    sg_argument()
    sg_block_arguments()
    emit(T.T_WRITE)


def sg_block_arguments():
    """SG.BLOCK.ARGUMENTS. With the handle on top: the handle and the address after the next
    comma are pushed, and the count after the comma after that is in A/Y."""
    uxc_expr.ex_tow()
    sg_stack()
    if g.tk_t != K_TT_OP or g.tk_k != 44:
        er_syntax()
    sg_argument()
    uxc_expr.ex_tow()
    sg_stack()
    if g.tk_t != K_TT_OP or g.tk_k != 44:
        er_syntax()
    sg_argument()
    uxc_expr.ex_tow()
    g.ex_sd = g.ex_sd - 2


def sg_open_join():
    """SG.OPEN.JOIN. The name on top, between the prefix and the suffix, into a new temp that
    takes its place."""
    sg_new_temp()
    g.sg_open_temp = g.sg_temp
    if g.sg_open_prefix == "":
        sg_tos()
        g.sl_s[0] = K_SEC_TEMP
        g.sl_v[0] = g.sg_open_temp
        emit(T.T_SCOPY)
    else:
        g.sg_text = g.sg_open_prefix
        sg_push_literal()
        sg_tos()
        g.sl_s[0] = K_SEC_TEMP
        g.sl_v[0] = g.sg_open_temp
        emit(T.T_SCOPY)
        sg_tos()
        g.sl_s[0] = K_SEC_TEMP
        g.sl_v[0] = g.sg_open_temp
        emit(T.T_SCAT)
    g.sg_text = g.sg_open_suffix
    sg_push_literal()
    sg_tos()
    g.sl_s[0] = K_SEC_TEMP
    g.sl_v[0] = g.sg_open_temp
    emit(T.T_SCAT)
    g.sg_temp = g.sg_open_temp
    sg_push_temp()


def sg_stack():
    """SG.STACK. Push A/Y."""
    emit(T.T_PUSH)
    g.ex_sd = g.ex_sd + 1
    if g.ex_sd > K_EX_DEPTH:
        er_stop("EXPRESSION TOO COMPLEX")


# Operators

def sg_left():
    """SG.LEFT. A string on the left of a + that is not a temp yet is copied into one, so that
    the right side can be appended to it. The first operand of the statement may skip that."""
    g.ex_i = g.ex_vn - 1
    if g.ex_vt[g.ex_i] != K_TY_STR:
        return
    if g.ex_vs[g.ex_i] == K_SEC_TEMP:
        return
    if g.ex_i != g.sg_base or g.sb_depth != g.sg_depth:
        sg_copy()
        return
    if g.sg_appending == 1:
        sg_is_destination()
        if g.sg_same == 1:
            return
    if g.sg_printing == 0:
        sg_copy()
        return
    sg_tos()
    emit(T.T_PRSTR)
    g.sg_temp = K_TEMP_PRINTED
    sg_push_temp()


def sg_binary():
    """SG.BINARY. g.ex_o on g.ex_il and g.ex_ir. A compare pushes the left side, and R_SCMP
    leaves the flags as CMP does, so the tails of a WORD compare give the value."""
    if g.ex_vt[g.ex_il] != K_TY_STR or g.ex_vt[g.ex_ir] != K_TY_STR:
        er_mismatch()
    if g.ex_o == K_EO_ADD:
        sg_join()
        return
    if g.ex_o < K_EO_EQ or g.ex_o > K_EO_GE:
        er_mismatch()
    g.ex_i = g.ex_ir
    sg_is_empty()
    if g.sg_empty == 1:
        sg_empty_test()
        return
    g.ex_i = g.ex_il
    sg_is_empty()
    if g.sg_empty == 1:
        sg_empty_left()
        return
    g.ex_fb = g.ex_il
    uxc_expr.ex_flush()
    g.ex_i = g.ex_il
    uxc_expr.ex_spill()
    g.ex_i = g.ex_ir
    g.ex_wd = 1
    uxc_expr.ex_load()
    g.sg_core = T.T_SCMP_LR
    if g.ex_o == K_EO_LE or g.ex_o == K_EO_GT:
        g.sg_core = T.T_SCMP_RL
    emit(g.sg_core)
    g.ex_sd = g.ex_sd - 1
    g.sg_tail = T.T_ZTRUE
    if g.ex_o == K_EO_NE:
        g.sg_tail = T.T_ZFALSE
    if g.ex_o == K_EO_GE or g.ex_o == K_EO_LE:
        g.sg_tail = T.T_CTRUE
    if g.ex_o == K_EO_LT or g.ex_o == K_EO_GT:
        g.sg_tail = T.T_CFALSE
    g.ex_vn = g.ex_vn - 1
    g.ex_vk[g.ex_il] = K_EK_CMP
    g.ex_vs[g.ex_il] = K_SEC_CONST
    g.ex_vv[g.ex_il] = g.sg_tail
    g.ex_vt[g.ex_il] = K_TY_BYTE


def sg_empty_left():
    """SG.EMPTY.LEFT. "" on the left: the sides swap, and so does the compare."""
    g.ex_j = g.ex_ir
    uxc_expr.ex_swap()
    g.sg_mirror = g.ex_o
    if g.ex_o == K_EO_LT:
        g.sg_mirror = K_EO_GT
    if g.ex_o == K_EO_GT:
        g.sg_mirror = K_EO_LT
    if g.ex_o == K_EO_LE:
        g.sg_mirror = K_EO_GE
    if g.ex_o == K_EO_GE:
        g.sg_mirror = K_EO_LE
    g.ex_o = g.sg_mirror
    sg_empty_test()


def sg_empty_test():
    """SG.EMPTY.TEST. A compare with "" on the right is the same compare of the length with
    0."""
    g.ex_i = g.ex_ir
    sg_take_literal()
    g.ex_vn = g.ex_vn - 1
    sg_length()
    g.ex_k = K_EK_CONST
    g.ex_s = K_SEC_CONST
    g.ex_v = 0
    g.ex_ty = 0
    uxc_expr.ex_pushv()
    uxc_expr.ex_binary()


def sg_join():
    """SG.JOIN. The right side appended to the left side, which sg_left made a temp or left as
    the block sg_let stores into. Onto a part already printed, the right side is printed."""
    g.ex_fb = g.ex_ir
    uxc_expr.ex_flush()
    g.ex_i = g.ex_ir
    g.ex_wd = 1
    uxc_expr.ex_load()
    g.ex_vn = g.ex_vn - 1
    if g.ex_vs[g.ex_il] == K_SEC_TEMP and g.ex_vv[g.ex_il] == K_TEMP_PRINTED:
        emit(T.T_PRSTR)
        return
    g.sl_s[0] = g.ex_vs[g.ex_il]
    g.sl_v[0] = g.ex_vv[g.ex_il]
    emit(T.T_SCAT)


# Values

def sg_tos():
    g.ex_i = g.ex_vn - 1
    if g.ex_vt[g.ex_i] != K_TY_STR:
        er_mismatch()
    g.ex_fb = g.ex_i
    uxc_expr.ex_flush()
    g.ex_i = g.ex_vn - 1
    g.ex_wd = 1
    uxc_expr.ex_load()
    g.ex_vn = g.ex_vn - 1


def sg_pass():
    """SG.PASS. A literal or a STRING result is copied into a temp first, so that the SUB
    cannot write into it."""
    g.ex_i = g.ex_vn - 1
    if g.ex_vt[g.ex_i] != K_TY_STR:
        er_mismatch()
    if g.ex_vs[g.ex_i] == K_SEC_STR:
        sg_copy()
    g.ex_i = g.ex_vn - 1
    sg_is_result()
    if g.sg_result_found == 1:
        sg_copy()
    sg_tos()


def sg_result():
    """SG.RESULT. After the JSR of a STRING SUB, with the address of its result in A/Y and the
    token after the ). A call later in the statement may write that block, so then it is
    copied into a temp. Else the address is kept in the statement's next %P word, and the
    entry reads the block through it, as it reads a STRING parameter. Clobbers g.sy_*."""
    g.sg_scan_name = ""
    g.sg_scan_item = 0
    sg_scan()
    if g.sg_scan_call == 1:
        sg_new_temp()
        g.sl_s[0] = K_SEC_TEMP
        g.sl_v[0] = g.sg_temp
        emit(T.T_SCOPY)
        sg_push_temp()
        return
    g.sg_pointers = g.sg_pointers + 1
    g.sy_name = "%P" + basic_str(g.sg_pointers)
    sg_pointer_word()
    g.ex_k = K_EK_MEM
    g.ex_s = K_SEC_VAR
    g.ex_v = g.sg_pointer
    g.ex_ty = K_TY_STR
    uxc_expr.ex_pushv()


def sg_pointer_word():
    """SG.POINTER.WORD. A/Y is stored in the hidden WORD g.sy_name of the SUB being compiled,
    made when it is new. Out: g.sg_pointer, its value. Clobbers g.sy_*."""
    g.sy_ow = g.sb_current
    uxc_sym.sy_find()
    if g.sy_r == 0:
        g.sy_kind = K_SK_VAR
        g.sy_type = K_TY_WORD
        g.sb_place_size = 2
        uxc_sub.sb_place_variable()
        g.sy_val = g.sb_place
        g.sy_flags = 0
        g.sy_cnt = 0
        uxc_sym.sy_add()
    else:
        uxc_sym.sy_get()
    g.sg_pointer = g.sy_val
    g.sl_s[0] = K_SEC_VAR
    g.sl_v[0] = g.sg_pointer
    emit(T.T_STW_V)


def sg_is_result():
    """SG.IS.RESULT. g.sg_result_found = 1 when entry g.ex_i reads its block through one of the
    statement's %P words. Clobbers g.sy_*."""
    g.sg_result_found = 0
    if g.ex_vk[g.ex_i] != K_EK_MEM or g.ex_vs[g.ex_i] != K_SEC_VAR:
        return
    if g.sg_pointers == 0:
        return
    g.sg_result_i = 1
    while g.sg_result_i <= g.sg_pointers:
        g.sy_name = "%P" + basic_str(g.sg_result_i)
        g.sy_ow = g.sb_current
        uxc_sym.sy_find()
        if g.sy_r != 0:
            uxc_sym.sy_get()
        if g.sy_r != 0 and g.sy_val == g.ex_vv[g.ex_i]:
            g.sg_result_found = 1
        g.sg_result_i = g.sg_result_i + 1


def sg_return_empty():
    """SG.RETURN.EMPTY. A/Y is the address of "", for a STRING SUB whose body ends with no
    RETURN."""
    g.sg_text = ""
    sg_push_literal()
    sg_tos()


def sg_copy():
    """SG.COPY. The string on top is copied into a new temp, which takes its place."""
    sg_tos()
    sg_new_temp()
    g.sl_s[0] = K_SEC_TEMP
    g.sl_v[0] = g.sg_temp
    emit(T.T_SCOPY)
    sg_push_temp()


def sg_push_temp():
    g.ex_k = K_EK_ADDR
    g.ex_s = K_SEC_TEMP
    g.ex_v = g.sg_temp
    g.ex_ty = K_TY_STR
    uxc_expr.ex_pushv()


def sg_push_byte():
    g.ex_ty = K_TY_BYTE
    sg_push_register()


def sg_push_register():
    g.ex_k = K_EK_REG
    g.ex_s = K_SEC_CONST
    g.ex_v = 0
    uxc_expr.ex_pushv()


def sg_new_temp():
    """SG.NEW.TEMP. The statement's next temp. Out: g.sg_temp, its offset in its owner's
    pool."""
    g.sg_n = g.sg_n + 1
    g.sy_name = "%T" + basic_str(g.sg_n)
    g.sy_ow = g.sb_current
    uxc_sym.sy_find()
    if g.sy_r != 0:
        uxc_sym.sy_get()
        g.sg_temp = g.sy_val
        return
    g.sg_temp = (g.sg_n - 1) * 257
    g.sy_kind = K_SK_VAR
    g.sy_type = K_TY_STR
    g.sy_val = g.sg_temp
    g.sy_flags = K_SY_TEMP
    g.sy_cnt = 255
    uxc_sym.sy_add()


# Input

def sg_input():
    """SG.INPUT. INPUT ["prompt";] var, var ... or LINPUT var, with the token at the keyword.
    INPUT #handle, var ... and LINPUT #handle, var read a file. A var is a BYTE, WORD or
    STRING variable. A number is read into a temp, and VAL of the temp is stored."""
    g.sg_input_first = 1
    g.sg_input_file = 0
    uxc_lex.lx_next()
    if g.tk_t == K_TT_OP and g.tk_k == 35:
        sg_input_handle()
    if g.tk_t == K_TT_STR and g.sm_w == "INPUT" and g.sg_input_file == 0:
        sg_print_item()
        if g.tk_t != K_TT_OP or g.tk_k != 59:
            er_syntax()
        uxc_lex.lx_next()
    while True:
        if g.tk_t != K_TT_NAME:
            er_syntax()
        g.sm_n = g.tk_s
        uxc_stmt.sm_var()
        uxc_record.rd_section_value()
        g.sg_input_type = g.sy_type
        g.sg_input_value = g.sy_val
        g.sg_input_section = g.rd_sec
        g.ex_k = K_EK_MEM
        g.ex_s = K_SEC_VAR
        g.ex_v = g.sy_val
        g.ex_ty = K_TY_STR
        if g.sy_type == K_TY_STR and g.sy_cnt > 0:
            g.ex_k = K_EK_ADDR
            g.ex_s = g.sg_input_section
        if g.sy_type != K_TY_STR:
            sg_input_temp()
        uxc_lex.lx_next()
        g.sg_input_more = 0
        if g.tk_t == K_TT_OP and g.tk_k == 44 and g.sm_w == "INPUT":
            g.sg_input_more = 1
        sg_input_pick()
        uxc_expr.ex_pushv()
        sg_tos()
        emit(g.sg_input_template)
        if g.sg_input_type != K_TY_STR:
            sg_input_store()
        if g.sg_input_more == 0:
            break
        g.sg_input_first = 0
        uxc_lex.lx_next()
    if g.sg_input_file == 1:
        emit(T.T_CLRCHN)


def sg_input_handle():
    """SG.INPUT.HANDLE. #handle and the comma after it, with the token at the #."""
    uxc_lex.lx_next()
    uxc_expr.ex_expr()
    uxc_expr.ex_tob()
    emit(T.T_CHKIN)
    g.sg_input_file = 1
    if g.tk_t != K_TT_OP or g.tk_k != 44:
        er_syntax()
    uxc_lex.lx_next()


def sg_input_pick():
    """SG.INPUT.PICK. The template for one var. From the keyboard, the first field prints the
    prompt and the last field drops the rest of the line. From a file, the rest is kept."""
    if g.sg_input_file == 1:
        g.sg_input_template = T.T_FINPUT
        if g.sm_w == "LINPUT":
            g.sg_input_template = T.T_FLINPUT
        return
    g.sg_input_template = T.T_LINPUT
    if g.sm_w == "LINPUT":
        return
    if g.sg_input_first == 1 and g.sg_input_more == 0:
        g.sg_input_template = T.T_INPUT
    if g.sg_input_first == 1 and g.sg_input_more == 1:
        g.sg_input_template = T.T_INPUT_FIRST
    if g.sg_input_first == 0 and g.sg_input_more == 1:
        g.sg_input_template = T.T_INPUT_NEXT
    if g.sg_input_first == 0 and g.sg_input_more == 0:
        g.sg_input_template = T.T_INPUT_LAST


def sg_input_temp():
    """SG.INPUT.TEMP. A number is read into the statement's first temp. Clobbers g.sy_*."""
    if g.sm_w == "LINPUT":
        er_mismatch()
    g.sg_n = 0
    sg_new_temp()
    g.ex_k = K_EK_ADDR
    g.ex_s = K_SEC_TEMP
    g.ex_v = g.sg_temp
    g.ex_ty = K_TY_STR


def sg_input_store():
    """SG.INPUT.STORE. VAL of the temp R_INPUT returns in A/Y, stored into the variable. A LONG
    is read in 32 bits."""
    if g.sg_input_type == K_TY_LONG:
        emit(T.T_LVAL)
        g.ex_ty = K_TY_LONG
    else:
        emit(T.T_VAL)
        g.ex_ty = K_TY_WORD
    sg_push_register()
    g.sm_ty = g.sg_input_type
    g.sm_ad = g.sg_input_value
    g.sm_sec = g.sg_input_section
    uxc_stmt.sm_store()


def sg_error_size():
    er_stop("BAD STRING SIZE")


def basic_str(n):
    """STR$(n) of a whole number: a space or a -, then the digits."""
    if n < 0:
        return str(n)
    return " " + str(n)


def sg_maxes():
    """SG.MAXES. A max is loaded only when it differs from the one before."""
    g.sg_record = 1
    g.sg_loaded = 0
    while g.sg_record <= g.sy_n:
        g.sy_r = g.sg_record
        uxc_sym.sy_get()
        if (g.sy_kind == K_SK_VAR or g.sy_kind == K_SK_ARRAY) and g.sy_type >= K_TY_RECORD:
            uxc_record.rd_maxes()
        elif g.sy_kind != K_SK_VAR or g.sy_type != K_TY_STR or g.sy_cnt == 0:
            pass
        elif (g.sy_flags & K_SY_TEMP) != 0:
            pass
        elif g.sy_val < K_FRAME_BASE:
            sg_max()
        g.sg_record = g.sg_record + 1


def sg_max():
    g.sl_s[0] = K_SEC_CONST
    g.sl_v[0] = g.sy_cnt
    if g.sy_cnt != g.sg_loaded:
        emit(T.T_LDB_C)
    g.sg_loaded = g.sy_cnt
    g.sl_s[0] = K_SEC_BSS
    g.sl_v[0] = g.sy_val
    emit(T.T_STB_V)
