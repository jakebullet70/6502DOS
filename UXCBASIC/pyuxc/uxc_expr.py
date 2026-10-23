"""UXC-EXPR.BL: expressions.

    ex_expr()    compile the expression that starts at the token, and leave the token after
                 it. The value is the top entry of the value stack.
    ex_tob()     emit the code that puts the value in A as a BYTE, and drop the entry
    ex_tow()     the same into A/Y as a WORD
    ex_tol()     the same into A/Y/ZP_HI as a LONG
    ex_test()    emit the code that sets Z when the top entry is 0

The value stack is g.ex_vk, g.ex_vs, g.ex_vv, g.ex_vt and g.ex_vg, g.ex_vn entries. The
operator stack is g.ex_op, g.ex_on entries from g.ex_op_base. UXC-EXPR.BL has the kinds of an
entry and the rules of the types.

GPC UXC parses with GOTOs between EX.OPERAND and EX.OPERATOR. Here ex_operand and ex_operator
each return the next state, and ex_expr loops on it.
"""

from uxc_code import emit
from uxc_defs import K_EK_ADDR, K_EK_CMP, K_EK_CONST, K_EK_JMP, K_EK_MEM, K_EK_REG, K_EK_STK, \
    K_EO_ADD, K_EO_AND, K_EO_DIV, K_EO_EQ, K_EO_GE, K_EO_GT, K_EO_INDEX, K_EO_LAND, K_EO_LE, \
    K_EO_LOR, K_EO_LT, K_EO_MINUS, K_EO_MOD, K_EO_MUL, K_EO_NE, K_EO_NOT, K_EO_OR, K_EO_PAR, \
    K_EO_PEEK, K_EO_SHL, K_EO_SHR, K_EO_STRINGAT, K_EO_SUB, K_EO_WORDPEEK, K_EO_XOR, K_EX_DEPTH, K_EX_MAX, \
    K_OP_GE, K_OP_LE, K_OP_NE, K_OP_SHL, K_OP_SHR, K_SEC_BSS, K_SEC_CONST, K_SK_ARRAY, \
    K_SK_CONST, K_SK_SUB, K_SY_SIGNED, K_TT_NAME, K_TT_NUM, K_TT_OP, K_TT_STR, K_TY_BYTE, \
    K_TY_LONG, K_TY_RECORD, K_TY_STR, K_TY_WORD
import uxc_cond
import uxc_fold
import uxc_index
import uxc_lex
import uxc_long
import uxc_name
import uxc_record
import uxc_stmt
import uxc_str
import uxc_sub
import uxc_sym
import uxc_tpl as T
from uxc_state import er_mismatch, er_stop, er_syntax, g

_OPERAND = 1
_OPERATOR = 2
_DONE = 3


def ex_expr():
    g.ex_on = g.ex_op_base
    g.ex_pd = 0
    state = _OPERAND
    while state != _DONE:
        if state == _OPERAND:
            state = ex_operand()
        else:
            state = ex_operator()


def ex_operand():
    """EX.OPERAND."""
    if g.tk_t == K_TT_NUM:
        g.ex_k = K_EK_CONST
        g.ex_s = K_SEC_CONST
        g.ex_v = g.tk_v
        return ex_operand_push()
    if g.tk_t == K_TT_OP:
        if g.tk_k == 40:
            g.ex_o = K_EO_PAR
            ex_pusho()
            g.ex_pd = g.ex_pd + 1
            uxc_lex.lx_next()
            return _OPERAND
        if g.tk_k == 45:
            g.ex_o = K_EO_MINUS
            ex_pusho()
            uxc_lex.lx_next()
            return _OPERAND
        if g.tk_k == 64:
            # EX.AT: @name.
            ex_at_name()
            return _OPERATOR
        er_syntax()
    if g.tk_t == K_TT_STR:
        uxc_str.sg_literal()
        return _OPERATOR
    if g.tk_t != K_TT_NAME:
        er_syntax()
    if g.tk_s == "NOT":
        g.ex_o = K_EO_NOT
        ex_pusho()
        uxc_lex.lx_next()
        return _OPERAND
    g.ex_peek_operator = 0
    if g.tk_s == "PEEK" or g.tk_s == "CONTENTSAT":
        g.ex_peek_operator = K_EO_PEEK
    if g.tk_s == "CONTENTSATW":
        g.ex_peek_operator = K_EO_WORDPEEK
    if g.tk_s == "STRINGAT":
        g.ex_peek_operator = K_EO_STRINGAT
    if g.ex_peek_operator != 0:
        uxc_lex.lx_next()
        if g.tk_t != K_TT_OP or g.tk_k != 40:
            er_syntax()
        g.ex_o = g.ex_peek_operator
        ex_pusho()
        g.ex_o = K_EO_PAR
        ex_pusho()
        g.ex_pd = g.ex_pd + 1
        uxc_lex.lx_next()
        return _OPERAND
    if g.tk_s == "ADDROF":
        return ex_addrof()
    if g.tk_s == "CALL":
        uxc_sub.sb_pointer_function()
        return _OPERATOR
    if g.tk_s == "GETKEY":
        return ex_key(T.T_GETKEY, K_TY_BYTE)
    if g.tk_s == "GETEXTKEY":
        return ex_key(T.T_GETEXTKEY, K_TY_WORD)
    if g.tk_s == "WAITKEY":
        return ex_key(T.T_WAITKEY, K_TY_WORD)
    if g.tk_s == "KEYMODS":
        return ex_key(T.T_KEYMODS, K_TY_BYTE)
    if g.tk_s == "POS":
        return ex_pos()
    if g.tk_s == "NOFILE":
        g.ex_k = K_EK_CONST
        g.ex_s = K_SEC_CONST
        g.ex_v = 65535
        return ex_operand_push()
    uxc_str.sg_function()
    if g.sg_found == 1:
        return _OPERATOR
    g.sm_n = g.tk_s
    ex_enum_member()
    if g.sy_r == 0:
        uxc_name.nm_find()
    if g.sy_kind == K_SK_CONST and g.sy_type == K_TY_STR:
        uxc_name.nm_const_get()
        g.sg_text = g.nm_const_got
        uxc_str.sg_push_literal()
        uxc_lex.lx_next()
        return _OPERATOR
    if g.sy_kind == K_SK_CONST:
        g.ex_const_record = g.sy_r
        g.ex_k = K_EK_CONST
        g.ex_s = K_SEC_CONST
        g.ex_v = g.sy_val + 65536 * g.sy_cnt
        if (g.sy_flags & K_SY_SIGNED) != 0:
            g.ex_sg = 1
        return ex_operand_push()
    if g.sy_kind == K_SK_SUB:
        uxc_sub.sb_function()
        return _OPERATOR
    if g.sy_kind == K_SK_ARRAY:
        return ex_element()
    uxc_stmt.sm_var_kind()
    uxc_record.rd_section_value()
    g.ex_k = K_EK_MEM
    g.ex_s = g.rd_sec
    g.ex_v = g.sy_val
    g.ex_ty = g.sy_type
    if (g.sy_flags & K_SY_SIGNED) != 0:
        g.ex_sg = 1
    if g.ex_ty == K_TY_STR and g.sy_cnt > 0:
        g.ex_k = K_EK_ADDR
    ex_pushv()
    uxc_lex.lx_next()
    return _OPERATOR


def ex_enum_member():
    """EX.ENUM.MEMBER. In an argument to a parameter of an ENUM's type, a name without a dot
    is first looked for among that ENUM's members. Out: g.sy_r, the member's record, read, or
    0."""
    g.sy_r = 0
    if g.sb_call_enum[g.sb_depth] == 0:
        return
    if uxc_lex.instr(g.sm_n, ".") != 0:
        return
    g.sy_name = g.sm_n
    g.sy_ow = g.sb_call_enum[g.sb_depth]
    uxc_sym.sy_find()
    if g.sy_r != 0:
        uxc_sym.sy_get()


def ex_operand_push():
    g.ex_cg = g.ex_sg
    g.ex_r = g.ex_v
    ex_pushv()
    g.ex_i = g.ex_vn - 1
    ex_setc()
    uxc_lex.lx_next()
    return _OPERATOR


def ex_addrof():
    """EX.ADDROF. AddrOf(name): @name inside its own brackets."""
    uxc_lex.lx_next()
    if g.tk_t != K_TT_OP or g.tk_k != 40:
        er_stop("MISSING ( AFTER ADDROF")
    ex_at_name()
    if g.tk_t != K_TT_OP or g.tk_k != 41:
        er_stop("MISSING )")
    uxc_lex.lx_next()
    return _OPERATOR


def ex_at_name():
    """EX.AT.NAME. Push the address of the name after the token, and leave the token after
    the name. A DIM ... AT address is in K_SEC_CONST."""
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NAME:
        er_syntax()
    g.sm_n = g.tk_s
    uxc_name.nm_find()
    if g.sy_kind == K_SK_SUB:
        uxc_sub.sb_at_sub()
        return
    if g.sy_kind == K_SK_ARRAY and g.sy_type >= K_TY_RECORD:
        uxc_record.rd_at_element()
        return
    g.ex_s = K_SEC_BSS
    if g.sy_kind != K_SK_ARRAY:
        uxc_stmt.sm_var_kind()
        uxc_record.rd_section()
        g.ex_s = g.rd_sec
    g.ex_k = K_EK_ADDR
    g.ex_v = g.sy_val
    g.ex_ty = K_TY_WORD
    if g.sy_type == K_TY_STR:
        uxc_str.sg_at()
    ex_pushv()
    uxc_lex.lx_next()


def ex_element():
    """EX.ELEMENT. name(i): an array element. INDEX waits under the ( for its ), as PEEK
    does."""
    g.ex_array = g.sy_r
    uxc_lex.lx_next()
    if g.tk_t != K_TT_OP or g.tk_k != 40:
        er_stop("MISSING ( AFTER " + g.sm_n)
    g.ex_o = K_EO_INDEX
    ex_pusho()
    g.ex_oa[g.ex_on - 1] = g.ex_array
    g.ex_o = K_EO_PAR
    ex_pusho()
    g.ex_pd = g.ex_pd + 1
    uxc_lex.lx_next()
    return _OPERAND


def ex_key(template, result_type):
    """EX.KEY. GETKEY(), GETEXTKEY(), WAITKEY() and KEYMODS(): template leaves the result in
    A, or A/Y when result_type is K_TY_WORD. Like a SUB call, it loses A/Y and the flags."""
    g.ex_key_name = g.tk_s
    uxc_lex.lx_next()
    if g.tk_t != K_TT_OP or g.tk_k != 40:
        er_stop("MISSING ( AFTER " + g.ex_key_name)
    uxc_lex.lx_next()
    if g.tk_t != K_TT_OP or g.tk_k != 41:
        er_stop("MISSING )")
    g.ex_fb = g.ex_vn
    ex_flush()
    emit(template)
    g.ex_k = K_EK_REG
    g.ex_s = K_SEC_CONST
    g.ex_v = 0
    g.ex_ty = result_type
    ex_pushv()
    uxc_lex.lx_next()
    return _OPERATOR


def ex_pos():
    """EX.POS. POS(0): the cursor column in A. POS(1): the cursor row. POS(2): the screen's
    rows. POS(3): the screen's columns. It loses A and the flags."""
    ex_pos_axis(3, "POS NEEDS 0 TO 3")
    g.ex_fb = g.ex_vn
    ex_flush()
    if g.ex_pos_row == 0:
        emit(T.T_POSCOL)
    if g.ex_pos_row == 1:
        emit(T.T_POSROW)
    if g.ex_pos_row == 2:
        emit(T.T_POSROWS)
    if g.ex_pos_row == 3:
        emit(T.T_POSCOLS)
    g.ex_k = K_EK_REG
    g.ex_s = K_SEC_CONST
    g.ex_v = 0
    g.ex_ty = K_TY_BYTE
    ex_pushv()
    uxc_lex.lx_next()
    return _OPERATOR


def ex_pos_axis(last, message):
    """EX.POS.AXIS. Read the number after POS(, 0 to last, into g.ex_pos_row, and leave the )
    as the token. Any other axis stops the compile with message. The axis must be a number,
    so the compiler picks the template."""
    uxc_lex.lx_next()
    if g.tk_t != K_TT_OP or g.tk_k != 40:
        er_stop("MISSING ( AFTER POS")
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NUM or g.tk_v > last:
        er_stop(message)
    g.ex_pos_row = g.tk_v
    uxc_lex.lx_next()
    if g.tk_t != K_TT_OP or g.tk_k != 41:
        er_stop("MISSING )")


def ex_operator():
    """EX.OPERATOR. After an operand: a binary operator, a ), or the end of the
    expression."""
    g.ex_new = 0
    if g.tk_t == K_TT_OP:
        if g.tk_k == 41:
            return ex_close()
        if g.tk_k == 43:
            g.ex_new = K_EO_ADD
        if g.tk_k == 45:
            g.ex_new = K_EO_SUB
        if g.tk_k == 42:
            g.ex_new = K_EO_MUL
        if g.tk_k == 47:
            g.ex_new = K_EO_DIV
        if g.tk_k == 61:
            g.ex_new = K_EO_EQ
        if g.tk_k == 60:
            g.ex_new = K_EO_LT
        if g.tk_k == 62:
            g.ex_new = K_EO_GT
        if g.tk_k == K_OP_NE:
            g.ex_new = K_EO_NE
        if g.tk_k == K_OP_LE:
            g.ex_new = K_EO_LE
        if g.tk_k == K_OP_GE:
            g.ex_new = K_EO_GE
        if g.tk_k == K_OP_SHL:
            g.ex_new = K_EO_SHL
        if g.tk_k == K_OP_SHR:
            g.ex_new = K_EO_SHR
    if g.tk_t == K_TT_NAME:
        if g.tk_s == "AND":
            g.ex_new = K_EO_AND
        if g.tk_s == "OR":
            g.ex_new = K_EO_OR
        if g.tk_s == "XOR":
            g.ex_new = K_EO_XOR
        if g.tk_s == "MOD":
            g.ex_new = K_EO_MOD
    if g.ex_new == 0:
        return ex_end()
    # In a condition, AND and OR outside brackets are jumps (UXC-COND.BL).
    if g.ex_cm == 1 and g.ex_pd == 0:
        if g.ex_new == K_EO_AND:
            g.ex_new = K_EO_LAND
        if g.ex_new == K_EO_OR:
            g.ex_new = K_EO_LOR
    g.ex_p = g.ex_new
    ex_prec()
    g.ex_pn = g.ex_pr
    # EX.OPERATOR.POP: every operator is binary, and all are left to right.
    while g.ex_on != g.ex_op_base:
        g.ex_p = g.ex_op[g.ex_on - 1]
        ex_prec()
        if g.ex_pr < g.ex_pn:
            break
        ex_reduce()
    # EX.OPERATOR.PUSH
    if g.ex_new >= K_EO_LOR:
        uxc_cond.cn_left()
    if g.ex_new == K_EO_ADD:
        uxc_str.sg_left()
    g.ex_o = g.ex_new
    ex_pusho()
    uxc_lex.lx_next()
    return _OPERAND


def ex_close():
    """EX.CLOSE. ) closes the innermost (. With none open, the ) is not part of the
    expression."""
    while True:
        if g.ex_on == g.ex_op_base:
            return ex_end()
        if g.ex_op[g.ex_on - 1] == K_EO_PAR:
            break
        uxc_index.ex_vb_test()
        if g.ex_vb == 1 and g.ex_poke_vb == 1 and g.ex_on - 2 == g.ex_poke_at:
            # ContentsAt(P + B) = v: sm_contents takes the two entries.
            g.ex_vb = 2
            g.ex_on = g.ex_on - 2
            g.ex_pd = g.ex_pd - 1
            uxc_lex.lx_next()
            return _DONE
        if g.ex_vb == 1 and g.ex_on - 3 >= g.ex_op_base and g.ex_op[g.ex_on - 3] == K_EO_PEEK:
            uxc_index.ex_peek_vb()
            return _OPERATOR
        ex_reduce()
    g.ex_on = g.ex_on - 1
    g.ex_pd = g.ex_pd - 1
    uxc_lex.lx_next()
    if g.ex_on == g.ex_poke_at:
        return _DONE
    if g.ex_on == g.ex_op_base:
        return _OPERATOR
    if g.ex_op[g.ex_on - 1] == K_EO_PEEK or g.ex_op[g.ex_on - 1] == K_EO_WORDPEEK:
        g.ex_on = g.ex_on - 1
        uxc_index.ex_peek()
        return _OPERATOR
    if g.ex_op[g.ex_on - 1] == K_EO_STRINGAT:
        g.ex_on = g.ex_on - 1
        uxc_str.sg_string_at()
        return _OPERATOR
    if g.ex_op[g.ex_on - 1] == K_EO_INDEX:
        g.ex_on = g.ex_on - 1
        uxc_index.ex_index()
    return _OPERATOR


def ex_end():
    while g.ex_on != g.ex_op_base:
        if g.ex_op[g.ex_on - 1] == K_EO_PAR:
            er_stop("MISSING )")
        ex_reduce()
    return _DONE


def ex_prec():
    """EX.PREC. The precedence of operator g.ex_p in g.ex_pr, higher binds tighter. PAR, PEEK,
    STRINGAT and INDEX are 0, so no binary operator takes them off the stack."""
    if g.ex_p >= K_EO_LOR:
        g.ex_pr = g.ex_p - K_EO_LOR + 1
        return
    g.ex_pr = 0
    if g.ex_p <= K_EO_XOR:
        g.ex_pr = 1
        return
    if g.ex_p == K_EO_AND:
        g.ex_pr = 2
        return
    if g.ex_p == K_EO_NOT:
        g.ex_pr = 3
        return
    if g.ex_p <= K_EO_GE:
        g.ex_pr = 4
        return
    if g.ex_p <= K_EO_SHR:
        g.ex_pr = 5
        return
    if g.ex_p <= K_EO_SUB:
        g.ex_pr = 6
        return
    if g.ex_p <= K_EO_MOD:
        g.ex_pr = 7
        return
    if g.ex_p == K_EO_MINUS:
        g.ex_pr = 8


def ex_pusho():
    if g.ex_on >= K_EX_MAX:
        ex_complex()
    g.ex_op[g.ex_on] = g.ex_o
    g.ex_on = g.ex_on + 1


def ex_complex():
    er_stop("EXPRESSION TOO COMPLEX")


def ex_pushv():
    """EX.PUSHV. A new operand g.ex_k g.ex_s g.ex_v g.ex_ty, signed when g.ex_sg = 1. g.ex_sg
    is 0 after it. It emits no code, so a value in A/Y below it stays there until code is
    needed."""
    if g.ex_vn >= K_EX_MAX:
        ex_complex()
    g.ex_vk[g.ex_vn] = g.ex_k
    g.ex_vs[g.ex_vn] = g.ex_s
    g.ex_vv[g.ex_vn] = g.ex_v
    g.ex_vt[g.ex_vn] = g.ex_ty
    g.ex_vg[g.ex_vn] = g.ex_sg
    g.ex_sg = 0
    g.ex_jt[g.ex_vn] = 0
    g.ex_jf[g.ex_vn] = 0
    g.ex_vn = g.ex_vn + 1


def ex_load():
    """EX.LOAD. Emit the code that puts entry g.ex_i in A (g.ex_wd = 0), in A/Y (g.ex_wd = 1)
    or in A/Y/ZP_HI (g.ex_wd = 2). A signed BYTE is widened with its sign."""
    if g.ex_wd == 2:
        uxc_long.ex_long_load()
        return
    g.ex_lk = g.ex_vk[g.ex_i]
    g.ex_lt = g.ex_vt[g.ex_i]
    g.sl_s[0] = g.ex_vs[g.ex_i]
    g.sl_v[0] = g.ex_vv[g.ex_i]
    if g.ex_lt == K_TY_LONG and g.ex_lk == K_EK_CONST:
        g.sl_v[0] = g.ex_vv[g.ex_i] - g.ex_vv[g.ex_i] // 65536 * 65536
    if g.ex_lk == K_EK_CONST or g.ex_lk == K_EK_ADDR:
        if g.ex_wd == 0:
            emit(T.T_LDB_C)
            return
        emit(T.T_LDW_C)
        return
    if g.ex_lk == K_EK_MEM:
        if g.ex_wd == 0:
            emit(T.T_LDB_V)
            return
        if g.ex_lt != K_TY_BYTE:
            emit(T.T_LDW_V)
            return
        if g.ex_vg[g.ex_i] == 0:
            emit(T.T_LDW_B)
            return
        emit(T.T_LDB_V)
        emit(T.T_SWIDEN)
        return
    if g.ex_lk == K_EK_CMP:
        g.ex_tl = g.ex_vv[g.ex_i]
        emit(g.ex_tl)
        g.ex_lt = K_TY_BYTE
    if g.ex_wd == 0 or g.ex_lt == K_TY_WORD or g.ex_lt == K_TY_LONG:
        return
    if g.ex_vg[g.ex_i] == 0:
        emit(T.T_WIDEN)
    if g.ex_vg[g.ex_i] == 1:
        emit(T.T_SWIDEN)


def ex_spill():
    """EX.SPILL. Emit the code that pushes entry g.ex_i, as its own type; it becomes
    K_EK_STK. A BYTE is pushed with a 0 high byte. A signed BYTE is pushed widened with its
    sign. A LONG's high word goes to R_ESTKH."""
    g.ex_wd = 0
    if g.ex_vt[g.ex_i] == K_TY_WORD or g.ex_vt[g.ex_i] == K_TY_STR:
        g.ex_wd = 1
    if g.ex_vg[g.ex_i] == 1:
        g.ex_wd = 1
    if g.ex_vt[g.ex_i] == K_TY_LONG:
        g.ex_wd = 2
    ex_load()
    if g.ex_wd == 1:
        emit(T.T_PUSH)
    if g.ex_wd == 0:
        emit(T.T_PUSHB)
    if g.ex_wd == 2:
        emit(T.T_PUSHL)
    if g.ex_vk[g.ex_i] == K_EK_CMP:
        g.ex_vt[g.ex_i] = K_TY_BYTE
    g.ex_vk[g.ex_i] = K_EK_STK
    g.ex_sd = g.ex_sd + 1
    if g.ex_sd > K_EX_DEPTH:
        ex_complex()


def ex_flush():
    """EX.FLUSH. Push every entry under g.ex_fb that is not on the run-time stack, from the
    bottom up. A K_EK_JMP entry has no value to push, and a string needs no push."""
    g.ex_i = 0
    while g.ex_i < g.ex_fb:
        if g.ex_vk[g.ex_i] != K_EK_STK and g.ex_vk[g.ex_i] != K_EK_JMP \
                and g.ex_vt[g.ex_i] != K_TY_STR:
            ex_spill()
        g.ex_i = g.ex_i + 1


def ex_setc():
    """EX.SETC. Entry g.ex_i becomes the constant with the bits g.ex_r, 16 or 32 of them,
    signed when g.ex_cg = 1. g.ex_cg is 0 after it."""
    g.ex_setc_long = 0
    if g.ex_r > 65535:
        uxc_long.ex_long_const()
    g.ex_vk[g.ex_i] = K_EK_CONST
    g.ex_vs[g.ex_i] = K_SEC_CONST
    g.ex_vv[g.ex_i] = g.ex_r
    g.ex_vt[g.ex_i] = 0
    if g.ex_r > 255:
        g.ex_vt[g.ex_i] = K_TY_WORD
    if g.ex_cg == 1 and g.ex_r >= 65408:
        g.ex_vt[g.ex_i] = 0
    if g.ex_setc_long == 1:
        g.ex_vt[g.ex_i] = K_TY_LONG
    g.ex_vg[g.ex_i] = g.ex_cg
    g.ex_cg = 0


def ex_tol():
    g.ex_wd = 2
    ex_to()


def ex_tob():
    g.ex_wd = 0
    ex_to()


def ex_tow():
    g.ex_wd = 1
    ex_to()


def ex_to():
    g.ex_i = g.ex_vn - 1
    if g.ex_vt[g.ex_i] == K_TY_STR:
        er_mismatch()
    g.ex_fb = g.ex_i
    g.ex_keep = g.ex_wd
    ex_flush()
    g.ex_i = g.ex_vn - 1
    g.ex_wd = g.ex_keep
    ex_load()
    g.ex_vn = g.ex_vn - 1


def ex_reduce():
    """EX.REDUCE. Apply the operator on top of the operator stack."""
    g.ex_on = g.ex_on - 1
    g.ex_o = g.ex_op[g.ex_on]
    if g.ex_o == K_EO_MINUS or g.ex_o == K_EO_NOT:
        ex_unary()
        return
    if g.ex_o >= K_EO_LOR:
        uxc_cond.cn_logic()
        return
    ex_binary()


def ex_unary():
    """EX.UNARY. Unary - and NOT, on the top entry. Unary - gives a signed value: a BYTE for a
    signed BYTE, a LONG for a LONG, else a WORD."""
    g.ex_i = g.ex_vn - 1
    g.ex_lk = g.ex_vk[g.ex_i]
    g.ex_a = g.ex_vv[g.ex_i]
    if g.ex_vt[g.ex_i] == K_TY_STR:
        er_mismatch()
    if g.ex_lk == K_EK_CONST and g.ex_o == K_EO_MINUS:
        uxc_fold.ex_fold_negate()
        ex_setc()
        return
    if g.ex_lk == K_EK_CONST:
        # EX.UNARY.NOT
        g.ex_r = 0
        if g.ex_a == 0:
            g.ex_r = 1
        ex_setc()
        return
    if g.ex_lk == K_EK_CMP and g.ex_o == K_EO_NOT:
        ex_flip()
        return
    # NOT x is a test of x for 0: a compare, whose tail gives the 0 or 1.
    if g.ex_o == K_EO_NOT:
        ex_test()
        g.ex_vk[g.ex_i] = K_EK_CMP
        g.ex_vs[g.ex_i] = K_SEC_CONST
        g.ex_vv[g.ex_i] = T.T_ZTRUE
        g.ex_vt[g.ex_i] = K_TY_BYTE
        g.ex_vg[g.ex_i] = 0
        return
    g.ex_fb = g.ex_i
    ex_flush()
    g.ex_i = g.ex_vn - 1
    g.ex_wd = 0
    if g.ex_vt[g.ex_i] == K_TY_WORD:
        g.ex_wd = 1
    if g.ex_vg[g.ex_i] == 0:
        g.ex_wd = 1
    if g.ex_vt[g.ex_i] == K_TY_LONG:
        g.ex_wd = 2
    ex_load()
    if g.ex_wd == 0:
        emit(T.T_NEGB)
    if g.ex_wd == 1:
        emit(T.T_NEGW)
    if g.ex_wd == 2:
        emit(T.T_NEGL)
    g.ex_vk[g.ex_i] = K_EK_REG
    g.ex_vt[g.ex_i] = K_TY_BYTE
    if g.ex_wd == 1:
        g.ex_vt[g.ex_i] = K_TY_WORD
    if g.ex_wd == 2:
        g.ex_vt[g.ex_i] = K_TY_LONG
    g.ex_vg[g.ex_i] = 1


def ex_test():
    """EX.TEST. Emit the code that sets Z when the top entry is 0, and leave it in g.ex_i. A
    BYTE variable needs only its load."""
    g.ex_i = g.ex_vn - 1
    if g.ex_vt[g.ex_i] == K_TY_STR:
        er_mismatch()
    g.ex_fb = g.ex_i
    ex_flush()
    g.ex_i = g.ex_vn - 1
    g.ex_lk = g.ex_vk[g.ex_i]
    if g.ex_vt[g.ex_i] == K_TY_LONG:
        uxc_long.ex_long_test()
        return
    if g.ex_lk == K_EK_MEM:
        g.sl_s[0] = g.ex_vs[g.ex_i]
        g.sl_v[0] = g.ex_vv[g.ex_i]
        if g.ex_vt[g.ex_i] == K_TY_WORD:
            emit(T.T_TSTW_V)
            return
        emit(T.T_LDB_V)
        return
    g.ex_wd = 0
    if g.ex_vt[g.ex_i] == K_TY_WORD:
        g.ex_wd = 1
    ex_load()
    if g.ex_wd == 0:
        emit(T.T_TSTB)
        return
    emit(T.T_TSTW)


def ex_flip():
    """EX.FLIP. NOT of a compare: the opposite tail."""
    g.ex_tl = g.ex_vv[g.ex_i]
    if g.ex_tl == T.T_CTRUE:
        g.ex_vv[g.ex_i] = T.T_CFALSE
    if g.ex_tl == T.T_CFALSE:
        g.ex_vv[g.ex_i] = T.T_CTRUE
    if g.ex_tl == T.T_ZTRUE:
        g.ex_vv[g.ex_i] = T.T_ZFALSE
    if g.ex_tl == T.T_ZFALSE:
        g.ex_vv[g.ex_i] = T.T_ZTRUE


def ex_binary():
    """EX.BINARY. A binary operator, on the two top entries."""
    g.ex_il = g.ex_vn - 2
    g.ex_ir = g.ex_vn - 1
    if g.ex_vt[g.ex_il] == K_TY_STR or g.ex_vt[g.ex_ir] == K_TY_STR:
        uxc_str.sg_binary()
        return
    g.ex_kl = g.ex_vk[g.ex_il]
    g.ex_kr = g.ex_vk[g.ex_ir]
    g.ex_yl = g.ex_vt[g.ex_il]
    g.ex_yr = g.ex_vt[g.ex_ir]
    g.ex_z = 0
    if g.ex_o == K_EO_DIV or g.ex_o == K_EO_MOD:
        g.ex_z = 1
    if g.ex_z == 1 and g.ex_kr == K_EK_CONST and g.ex_vv[g.ex_ir] == 0:
        er_stop("DIVISION BY ZERO")
    if g.ex_kl == K_EK_CONST and g.ex_kr == K_EK_CONST:
        uxc_fold.ex_fold()
        return
    if g.ex_z == 1 and g.ex_kr == K_EK_CONST:
        ex_power()
    if g.ex_kl == K_EK_ADDR and g.ex_kr == K_EK_CONST:
        if g.ex_o == K_EO_ADD or g.ex_o == K_EO_SUB:
            uxc_fold.ex_fold_address()
            return
    # The width: g.ex_w for the result, g.ex_cw for the code. g.ex_g = 1 for a signed
    # operator.
    g.ex_w = 0
    if g.ex_yl == K_TY_WORD or g.ex_yr == K_TY_WORD:
        g.ex_w = 1
    if g.ex_yl == K_TY_LONG or g.ex_yr == K_TY_LONG:
        g.ex_w = 2
    g.ex_sh = 0
    if g.ex_o == K_EO_SHL or g.ex_o == K_EO_SHR:
        g.ex_sh = 1
    g.ex_g = 0
    if g.ex_vg[g.ex_il] == 1 or g.ex_vg[g.ex_ir] == 1:
        g.ex_g = 1
    if g.ex_sh == 1:
        g.ex_g = g.ex_vg[g.ex_il]
    if g.ex_g == 1 and g.ex_w == 0 and g.ex_sh == 0:
        ex_mixed()
    if g.ex_sh == 1:
        g.ex_w = 1
    if g.ex_sh == 1 and g.ex_yl == K_TY_BYTE:
        g.ex_w = 0
    if g.ex_sh == 1 and g.ex_yl == K_TY_LONG:
        g.ex_w = 2
    g.ex_cw = g.ex_w
    if g.ex_o >= K_EO_MUL and g.ex_o <= K_EO_MOD and g.ex_w == 0:
        g.ex_cw = 1
    if g.ex_kl != K_EK_STK and g.ex_sh == 0:
        ex_fast()
        if g.ex_fd == 1:
            return
    # The left side on the run-time stack, with every entry under it first.
    g.ex_fb = g.ex_il
    ex_flush()
    if g.ex_kl != K_EK_STK:
        g.ex_i = g.ex_il
        ex_spill()
    if g.ex_cw == 2 and g.ex_yl != K_TY_LONG:
        uxc_long.ex_long_stack()
    # The right side in A or A/Y. A shift count is a BYTE.
    g.ex_i = g.ex_ir
    g.ex_wd = g.ex_cw
    if g.ex_sh == 1:
        g.ex_wd = 0
    ex_load()
    ex_opcode()
    g.ex_sd = g.ex_sd - 1
    g.ex_vn = g.ex_vn - 1
    g.ex_i = g.ex_il
    g.ex_vk[g.ex_i] = g.ex_rk
    g.ex_vt[g.ex_i] = g.ex_rt
    g.ex_vs[g.ex_i] = K_SEC_CONST
    g.ex_vv[g.ex_i] = g.ex_rv
    g.ex_vg[g.ex_i] = g.ex_rg


def ex_power():
    """EX.POWER. An unsigned / or MOD by a constant power of 2 from 2 up becomes >> or AND, so
    the divide routine is not linked."""
    if g.ex_vg[g.ex_il] == 1 or g.ex_vg[g.ex_ir] == 1:
        return
    g.ex_pv = g.ex_vv[g.ex_ir]
    if g.ex_pv < 2:
        return
    if g.ex_pv & (g.ex_pv - 1) != 0:
        return
    if g.ex_o == K_EO_MOD:
        g.ex_o = K_EO_AND
        g.ex_z = 0
        g.ex_vv[g.ex_ir] = g.ex_pv - 1
        return
    g.ex_o = K_EO_SHR
    g.ex_z = 0
    g.ex_pc = 0
    while g.ex_pv > 1:
        g.ex_pv = g.ex_pv >> 1
        g.ex_pc = g.ex_pc + 1
    g.ex_vv[g.ex_ir] = g.ex_pc
    g.ex_vt[g.ex_ir] = K_TY_BYTE


def ex_mixed():
    """EX.MIXED. A signed side, with an unsigned BYTE or a constant from 128 to 255 on the
    other side: the operator works as WORD, so g.ex_w = 1."""
    if g.ex_vg[g.ex_il] == 0 and g.ex_yl == K_TY_BYTE:
        g.ex_w = 1
    if g.ex_vg[g.ex_ir] == 0 and g.ex_yr == K_TY_BYTE:
        g.ex_w = 1
    if g.ex_vg[g.ex_il] == 0 and g.ex_kl == K_EK_CONST and g.ex_vv[g.ex_il] > 127:
        g.ex_w = 1
    if g.ex_vg[g.ex_ir] == 0 and g.ex_kr == K_EK_CONST and g.ex_vv[g.ex_ir] > 127:
        g.ex_w = 1


def ex_fast():
    """EX.FAST. A compare, + or - whose right side needs no code: the left side is loaded
    into A or A/Y, and the right side is the operand of the template. g.ex_fd = 1 when it
    was done. UXC-EXPR.BL has how > and <= are turned round."""
    if g.ex_cw == 2:
        uxc_long.ex_long_fast()
        return
    g.ex_fd = 0
    if g.ex_o == K_EO_ADD or g.ex_o == K_EO_SUB:
        ex_fast_add()
        return
    if g.ex_o < K_EO_EQ or g.ex_o > K_EO_GE:
        return
    g.ex_i = g.ex_ir
    ex_fast_ok()
    if g.ex_ok == 0:
        return
    g.ex_oc = g.ex_o
    if g.ex_oc == K_EO_GT or g.ex_oc == K_EO_LE:
        if g.ex_kr == K_EK_CONST:
            ex_fast_next()
            if g.ex_ok == 0:
                return
            if g.ex_oc == K_EO_GT:
                g.ex_oc = K_EO_GE
            else:
                g.ex_oc = K_EO_LT
            ex_fast_cmp()
            return
        g.ex_i = g.ex_il
        ex_fast_ok()
        if g.ex_ok == 0:
            return
        g.ex_i = g.ex_il
        g.ex_j = g.ex_ir
        ex_swap()
        if g.ex_oc == K_EO_GT:
            g.ex_oc = K_EO_LT
        else:
            g.ex_oc = K_EO_GE
    ex_fast_cmp()


def ex_fast_cmp():
    ex_fast_left()
    g.ex_c = 0
    if g.ex_vk[g.ex_ir] == K_EK_MEM:
        g.ex_c = 1
    g.ex_qe = 0
    if g.ex_oc == K_EO_EQ or g.ex_oc == K_EO_NE:
        g.ex_qe = 1
    if g.ex_cw == 0 and g.ex_c == 0:
        g.ex_tp = T.T_CMPB_C
    if g.ex_cw == 0 and g.ex_c == 1:
        g.ex_tp = T.T_CMPB_V
    if g.ex_cw == 1 and g.ex_c == 0:
        g.ex_tp = T.T_CMPW_C
        if g.ex_qe == 1:
            g.ex_tp = T.T_CMPW_EQC
    if g.ex_cw == 1 and g.ex_c == 1:
        g.ex_tp = T.T_CMPW_V
        if g.ex_qe == 1:
            g.ex_tp = T.T_CMPW_EQV
    if g.ex_g == 1 and g.ex_qe == 0:
        ex_fast_signed()
    emit(g.ex_tp)
    g.ex_rk = K_EK_CMP
    g.ex_rt = K_TY_BYTE
    g.ex_rg = 0
    if g.ex_oc == K_EO_EQ:
        g.ex_rv = T.T_ZTRUE
    if g.ex_oc == K_EO_NE:
        g.ex_rv = T.T_ZFALSE
    if g.ex_oc == K_EO_GE:
        g.ex_rv = T.T_CTRUE
    if g.ex_oc == K_EO_LT:
        g.ex_rv = T.T_CFALSE
    ex_fast_done()


def ex_fast_add():
    g.ex_kr = g.ex_vk[g.ex_ir]
    if g.ex_kr != K_EK_CONST and g.ex_kr != K_EK_ADDR:
        return
    ex_fast_left()
    g.ex_tp = T.T_ADDB_C
    if g.ex_cw == 1:
        g.ex_tp = T.T_ADDW_C
    if g.ex_o == K_EO_SUB:
        g.ex_tp = T.T_SUBB_C
        if g.ex_cw == 1:
            g.ex_tp = T.T_SUBW_C
    emit(g.ex_tp)
    g.ex_rk = K_EK_REG
    g.ex_rv = 0
    g.ex_rt = K_TY_BYTE
    if g.ex_w == 1:
        g.ex_rt = K_TY_WORD
    g.ex_rg = g.ex_g
    ex_fast_done()


def ex_fast_done():
    g.ex_vn = g.ex_vn - 1
    g.ex_i = g.ex_il
    g.ex_vk[g.ex_i] = g.ex_rk
    g.ex_vt[g.ex_i] = g.ex_rt
    g.ex_vs[g.ex_i] = K_SEC_CONST
    g.ex_vv[g.ex_i] = g.ex_rv
    g.ex_vg[g.ex_i] = g.ex_rg
    g.ex_fd = 1


def ex_fast_left():
    """EX.FAST.LEFT. The left side into A or A/Y, and the right side into slot 0."""
    g.ex_fb = g.ex_il
    ex_flush()
    g.ex_i = g.ex_il
    g.ex_wd = g.ex_cw
    ex_load()
    g.sl_s[0] = g.ex_vs[g.ex_ir]
    g.sl_v[0] = g.ex_vv[g.ex_ir]


def ex_fast_ok():
    """EX.FAST.OK. g.ex_ok = 1 when entry g.ex_i can be the operand of a compare template of
    width g.ex_cw. g.ex_kr is its kind."""
    g.ex_ok = 0
    g.ex_kr = g.ex_vk[g.ex_i]
    if g.ex_kr == K_EK_CONST or g.ex_kr == K_EK_ADDR:
        g.ex_ok = 1
        return
    if g.ex_kr != K_EK_MEM:
        return
    if g.ex_cw == 0 and g.ex_vt[g.ex_i] == K_TY_BYTE:
        g.ex_ok = 1
    if g.ex_cw == 1 and g.ex_vt[g.ex_i] == K_TY_WORD:
        g.ex_ok = 1


def ex_fast_next():
    """EX.FAST.NEXT. The constant on the right made 1 more, at the width g.ex_cw, signed when
    g.ex_g = 1. g.ex_ok = 0, and the constant is left as it was, when it is the top of its
    range."""
    g.ex_ok = 0
    g.ex_m = 255
    if g.ex_cw == 1:
        g.ex_m = 65535
    g.ex_n = g.ex_vv[g.ex_ir]
    if g.ex_cw == 0:
        g.ex_n = g.ex_n - g.ex_n // 256 * 256
    if g.ex_g == 1:
        g.ex_m = g.ex_m // 2
        if g.ex_n > g.ex_m:
            g.ex_n = g.ex_n - 2 * g.ex_m - 2
    if g.ex_n >= g.ex_m:
        return
    g.ex_n = g.ex_n + 1
    if g.ex_n < 0:
        g.ex_n = g.ex_n + 65536
    g.ex_vv[g.ex_ir] = g.ex_n
    g.ex_ok = 1


def ex_fast_signed():
    if g.ex_cw == 0 and g.ex_c == 0:
        g.ex_tp = T.T_SCMPB_C
    if g.ex_cw == 0 and g.ex_c == 1:
        g.ex_tp = T.T_SCMPB_V
    if g.ex_cw == 1 and g.ex_c == 0:
        g.ex_tp = T.T_SCMPW_C
    if g.ex_cw == 1 and g.ex_c == 1:
        g.ex_tp = T.T_SCMPW_V


def ex_swap():
    """EX.SWAP. Entries g.ex_i and g.ex_j change places."""
    i = g.ex_i
    j = g.ex_j
    for stack in (g.ex_vk, g.ex_vs, g.ex_vt, g.ex_vv, g.ex_vg):
        g.ex_t = stack[i]
        stack[i] = stack[j]
        stack[j] = g.ex_t


def ex_opcode():
    """EX.OPCODE. Emit operator g.ex_o, and give the result's kind g.ex_rk, type g.ex_rt,
    sign g.ex_rg and, for a compare, the tail g.ex_rv."""
    g.ex_rk = K_EK_REG
    g.ex_rv = 0
    g.ex_rg = g.ex_g
    g.ex_rt = K_TY_BYTE
    if g.ex_w == 1:
        g.ex_rt = K_TY_WORD
    if g.ex_w == 2:
        uxc_long.ex_long_opcode()
        return
    if g.ex_o == K_EO_MUL:
        emit(T.T_MUL)
        return
    if g.ex_o == K_EO_DIV and g.ex_g == 1:
        emit(T.T_DIVS)
        return
    if g.ex_o == K_EO_MOD and g.ex_g == 1:
        emit(T.T_MODS)
        return
    if g.ex_o == K_EO_DIV:
        emit(T.T_DIV)
        return
    if g.ex_o == K_EO_MOD:
        emit(T.T_MOD)
        return
    if g.ex_o == K_EO_ADD:
        g.ex_pb = T.T_ADDB
        g.ex_pw = T.T_ADDW
    if g.ex_o == K_EO_SUB:
        g.ex_pb = T.T_SUBB
        g.ex_pw = T.T_SUBW
    if g.ex_o == K_EO_AND:
        g.ex_pb = T.T_ANDB
        g.ex_pw = T.T_ANDW
    if g.ex_o == K_EO_OR:
        g.ex_pb = T.T_ORB
        g.ex_pw = T.T_ORW
    if g.ex_o == K_EO_XOR:
        g.ex_pb = T.T_XORB
        g.ex_pw = T.T_XORW
    if g.ex_o == K_EO_SHL:
        g.ex_pb = T.T_SHLB
        g.ex_pw = T.T_SHLW
    if g.ex_o == K_EO_SHR:
        g.ex_pb = T.T_SHRB
        g.ex_pw = T.T_SHRW
    if g.ex_o == K_EO_SHR and g.ex_g == 1:
        g.ex_pb = T.T_SARB
        g.ex_pw = T.T_SARW
    if g.ex_o >= K_EO_EQ and g.ex_o <= K_EO_GE:
        ex_compare()
    if g.ex_w == 0:
        emit(g.ex_pb)
        return
    emit(g.ex_pw)


def ex_compare():
    """EX.COMPARE. The core now, and the tail when the value is wanted. IF and the loops
    branch on the flag instead."""
    g.ex_rk = K_EK_CMP
    g.ex_rt = K_TY_BYTE
    if g.ex_o == K_EO_EQ:
        g.ex_pb = T.T_CMPB_RL
        g.ex_pw = T.T_CMPW_EQ
        g.ex_rv = T.T_ZTRUE
    if g.ex_o == K_EO_NE:
        g.ex_pb = T.T_CMPB_RL
        g.ex_pw = T.T_CMPW_EQ
        g.ex_rv = T.T_ZFALSE
    if g.ex_o == K_EO_GE:
        g.ex_pb = T.T_CMPB_LR
        g.ex_pw = T.T_CMPW_LR
        g.ex_rv = T.T_CTRUE
    if g.ex_o == K_EO_LT:
        g.ex_pb = T.T_CMPB_LR
        g.ex_pw = T.T_CMPW_LR
        g.ex_rv = T.T_CFALSE
    if g.ex_o == K_EO_LE:
        g.ex_pb = T.T_CMPB_RL
        g.ex_pw = T.T_CMPW_RL
        g.ex_rv = T.T_CTRUE
    if g.ex_o == K_EO_GT:
        g.ex_pb = T.T_CMPB_RL
        g.ex_pw = T.T_CMPW_RL
        g.ex_rv = T.T_CFALSE
    g.ex_rg = 0
    if g.ex_g == 0:
        return
    if g.ex_pb == T.T_CMPB_LR:
        g.ex_pb = T.T_SCMPB_LR
        g.ex_pw = T.T_SCMPW_LR
    if g.ex_pw == T.T_CMPW_RL:
        g.ex_pb = T.T_SCMPB_RL
        g.ex_pw = T.T_SCMPW_RL
