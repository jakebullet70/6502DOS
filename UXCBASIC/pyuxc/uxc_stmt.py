"""UXC-STMT.BL: one line of the second pass, and the statements.

    sm_line()       compile the line in g.lx_l
    sm_stmt()       compile the statement that starts at the token
    sm_var()        in  g.sm_n    the name must be a declared variable: its record in g.sy_*
    sm_var_kind()   the same check, on a record nm_find gave

A statement starts with the first token of lx_next, and leaves the token after its last one.
sm_line then wants the end of the line. UXC-STMT.BL lists the statements and the module of
each. The ASM, SYS, INPUT and WRITE statements are not ported yet.
"""

import sys

from uxc_code import emit
from uxc_defs import K_EK_ADDR, K_EK_CONST, K_SEC_BSS, K_SEC_CONST, K_SK_ARRAY, K_SK_LABEL, \
    K_SK_VAR, K_SY_SIGNED, K_TOP, K_TT_EOL, K_TT_NAME, K_TT_OP, K_TY_BYTE, K_TY_LONG, \
    K_TY_RECORD, K_TY_STR, K_TY_WORD
import uxc_case
import uxc_dead
import uxc_expr
import uxc_flow
import uxc_fold
import uxc_for
import uxc_lex
import uxc_asm
import uxc_name
import uxc_record
import uxc_select
import uxc_str
import uxc_sub
import uxc_sym
import uxc_tpl as T
from uxc_state import er_mismatch, er_missing_as, er_stop, er_syntax, g

# The flow statements, and the module and routine of each. The routines are found when called,
# because uxc_flow imports this module.
_FLOW = {
    "IF": ("uxc_flow", "ct_if"), "ELSEIF": ("uxc_flow", "ct_elseif"),
    "ELSE": ("uxc_flow", "ct_else"), "ENDIF": ("uxc_flow", "ct_endif"),
    "DO": ("uxc_flow", "ct_do"), "LOOP": ("uxc_flow", "ct_loop"),
    "FOR": ("uxc_for", "ct_for"), "NEXT": ("uxc_for", "ct_next"),
    "REPEAT": ("uxc_flow", "ct_repeat"), "ENDREPEAT": ("uxc_flow", "ct_endrep"),
    "ON": ("uxc_case", "cs_on"), "CASE": ("uxc_case", "cs_case"),
    "ENDCASE": ("uxc_case", "cs_end"), "SELECT": ("uxc_select", "sl_select"),
    "ENDSELECT": ("uxc_select", "sl_end"), "EXIT": ("uxc_flow", "ct_exit"),
    "CONTINUE": ("uxc_flow", "ct_cont"), "GOTO": ("uxc_flow", "ct_goto"),
}


def sm_line():
    uxc_lex.lx_whole()
    uxc_lex.lx_next()
    if g.as_block != 0:
        uxc_asm.as_line()
    elif g.nm_enum_record != 0:
        uxc_name.nm_enum_members()
    elif g.rd_type_record != 0:
        uxc_record.rd_fields()
    elif g.tk_t == K_TT_OP and g.tk_k == 35:
        uxc_dead.dd_keep_line()
    else:
        sm_stmt()
    if g.tk_t != K_TT_EOL:
        er_syntax()


def sm_stmt():
    """SM.STMT. One statement. IF c THEN statement comes back here for its statement.
    g.sm_previous_return is 1 when the statement before this one was a RETURN outside any
    block, so that ENDSUB knows the end of the body cannot be reached. g.sm_previous_jump is
    the same for sm_unreached."""
    g.ex_vn = 0
    g.ex_sd = 0
    g.ex_op_base = 0
    g.sg_n = 0
    g.sg_pointers = 0
    if g.tk_t == K_TT_EOL:
        return
    g.sm_previous_return = g.sm_last_return
    g.sm_last_return = 0
    g.sm_previous_jump = g.sm_last_jump
    g.sm_last_jump = 0
    if g.tk_t != K_TT_NAME:
        er_syntax()
    g.sm_w = g.tk_s
    if g.cs_wait != 0:
        uxc_case.cs_before()
    if g.sb_current == 0 and g.nm_current != 0:
        uxc_name.nm_body()
    if g.sm_w == "PRINT":
        sm_print()
        return
    if g.sm_w == "DIM" or g.sm_w == "VAR":
        sm_dim()
        return
    if g.sm_w == "POKE":
        sm_poke()
        return
    if g.sm_w == "CONTENTSAT" or g.sm_w == "CONTENTSATW":
        sm_contents()
        return
    if g.sm_w == "POS":
        sm_pos()
        return
    if g.sm_w == "ASM":
        uxc_asm.as_asm()
        return
    if g.sm_w == "ENDASM":
        uxc_asm.as_stray()
    if g.sm_w == "SYS":
        uxc_asm.as_sys()
        return
    if g.sm_w == "CLOSE":
        sm_close()
        return
    if g.sm_w == "WRITE":
        uxc_str.sg_write()
        return
    if g.sm_w == "INPUT" or g.sm_w == "LINPUT":
        uxc_str.sg_input()
        return
    if g.sm_w == "END":
        sm_end()
        return
    if g.sm_w == "ERRORS":
        sm_errors()
        return
    if g.sm_w in _FLOW:
        module, routine = _FLOW[g.sm_w]
        getattr(sys.modules[module], routine)()
        return
    if g.sm_w == "SUB" or g.sm_w == "FUNCTION":
        uxc_sub.sb_sub()
        return
    if g.sm_w == "ENDSUB" or g.sm_w == "ENDFUNCTION":
        uxc_sub.sb_endsub()
        return
    if g.sm_w == "RETURN":
        uxc_sub.sb_return()
        sm_returned()
        return
    if g.sm_w == "CALL":
        uxc_sub.sb_call_keyword()
        return
    uxc_name.nm_declaration()
    if g.nm_declared != 0:
        return
    uxc_lex.lx_next()
    if g.tk_t == K_TT_OP and g.tk_k == 58:
        sm_label()
        uxc_lex.lx_next()
        return
    if g.tk_t == K_TT_OP and g.tk_k == 61:
        sm_let()
        return
    if g.tk_t == K_TT_OP and g.tk_k == 40:
        sm_bracket()
        return
    er_syntax()


def sm_bracket():
    """SM.BRACKET. name( -- an array element to store into, or a SUB to call."""
    g.sm_n = g.sm_w
    uxc_name.nm_find()
    if g.sy_kind == K_SK_ARRAY and g.sy_type >= K_TY_RECORD:
        uxc_record.rd_let_element()
        return
    if g.sy_kind == K_SK_ARRAY:
        sm_let_element()
        return
    uxc_sub.sb_call_statement()


def sm_errors():
    """SM.ERRORS. ERRORS ON / ERRORS OFF: the array index checks in the code after it."""
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NAME:
        er_syntax()
    if g.tk_s != "ON" and g.tk_s != "OFF":
        er_syntax()
    g.sm_errors_on = 0
    if g.tk_s == "ON":
        g.sm_errors_on = 1
    uxc_lex.lx_next()


def sm_returned():
    """SM.RETURNED. A RETURN outside any block is the last statement of its path."""
    if g.ns_d == 0:
        g.sm_last_return = 1
    sm_jumped()


def sm_jumped():
    """SM.JUMPED. The statement ends in a jump, an RTS or an exit, so the code after it is not
    reached from it. g.sm_last_jump is the depth of the block it is in, plus 1. A statement
    after IF c THEN is one deeper than the IF."""
    g.sm_last_jump = g.ns_d + 1


def sm_unreached():
    """SM.UNREACHED. in g.ct_i, a block. g.sm_skip is 1 when the statement before this one
    ended in a jump in that block, so the body it ends needs no jump out. The stock table
    keeps the jump, so that compare.py matches the GPC UXC."""
    g.sm_skip = 0
    if g.target == "uxdos16" and g.sm_previous_jump == g.ct_i + 1:
        g.sm_skip = 1


def sm_end():
    """SM.END. END [code], END IF, END REPEAT, END CASE, END SELECT, END SUB, END FUNCTION, END
    NAMESPACE; a stray END ENUM, END TYPE, END ASM. The code is a BYTE expression, the exit
    code; END alone exits with 0. A constant code is 0 to 255."""
    uxc_lex.lx_next()
    if g.tk_t == K_TT_NAME:
        if g.tk_s == "IF":
            uxc_flow.ct_endif()
            return
        if g.tk_s == "REPEAT":
            uxc_flow.ct_endrep()
            return
        if g.tk_s == "CASE":
            uxc_case.cs_end()
            return
        if g.tk_s == "SELECT":
            uxc_select.sl_end()
            return
        if g.tk_s == "SUB" or g.tk_s == "FUNCTION":
            uxc_sub.sb_endsub()
            return
        if g.tk_s == "NAMESPACE":
            uxc_name.nm_end()
            return
        if g.tk_s == "ENUM":
            uxc_name.nm_error_end_enum()
        if g.tk_s == "TYPE":
            er_stop("END TYPE WITHOUT TYPE")
        if g.tk_s == "ASM":
            uxc_asm.as_stray()
    if g.tk_t == K_TT_EOL:
        emit(T.T_END)
        sm_jumped()
        return
    uxc_expr.ex_expr()
    g.ex_i = g.ex_vn - 1
    if g.ex_vk[g.ex_i] == K_EK_CONST and g.ex_vt[g.ex_i] != K_TY_STR:
        if g.ex_vv[g.ex_i] < 0 or g.ex_vv[g.ex_i] > 255:
            er_stop("EXIT CODE OUT OF RANGE")
    uxc_expr.ex_tob()
    emit(T.T_ENDCODE)
    sm_jumped()


def sm_var():
    uxc_name.nm_find()
    sm_var_kind()


def sm_var_kind():
    if g.sy_kind != K_SK_VAR:
        er_stop("NOT A VARIABLE: " + g.sm_n)


def sm_dim():
    """SM.DIM. DIM A AS UBYTE, B(10) AS UWORD, S$ / DIM P AS UBYTE AT $030F. A number needs
    AS. DIM R AS ITEM [AT address] is in UXC-RECORD.BL."""
    while True:
        uxc_lex.lx_next()
        if g.tk_t != K_TT_NAME:
            er_syntax()
        g.sm_n = g.tk_s
        g.sm_ty = g.tk_m
        uxc_name.nm_reserved()
        uxc_lex.lx_next()
        g.sm_cnt = 0
        if g.tk_t == K_TT_OP and g.tk_k == 40:
            sm_dim_count()
        if g.tk_t == K_TT_NAME and g.tk_s == "AS":
            uxc_name.nm_as_type()
        if g.sm_ty >= K_TY_RECORD:
            uxc_record.rd_dim()
        else:
            sm_dim_one()
        # SM.DIM.NEXT
        if g.tk_t != K_TT_OP or g.tk_k != 44:
            return


def sm_dim_one():
    """One name of a DIM, with no record type."""
    if g.tk_t == K_TT_OP and g.tk_k != 44 and g.tk_k != 61 and g.sm_ty != K_TY_STR:
        er_syntax()
    if g.sm_ty == 0:
        er_missing_as()
    if g.tk_t == K_TT_NAME:
        uxc_name.nm_at()
        return
    if g.sm_ty == K_TY_STR:
        uxc_str.sg_dim()
        return
    if g.tk_t == K_TT_OP and g.tk_k == 61:
        er_stop("NOT YET: A START VALUE")
    g.sy_name = g.sm_n
    g.sy_ow = g.nm_scope
    uxc_sym.sy_find()
    if g.sy_r != 0:
        er_stop("DUPLICATE NAME " + g.sm_n)
    g.sy_type = g.sm_ty
    g.sy_flags = g.nm_type_signed * K_SY_SIGNED
    g.sy_cnt = g.sm_cnt
    g.ty_code = g.sm_ty
    uxc_sym.ty_size()
    if g.sm_cnt == 0:
        g.sb_place_size = g.ty_bytes
        uxc_sub.sb_place_variable()
        g.sy_kind = K_SK_VAR
        g.sy_val = g.sb_place
        uxc_sym.sy_add()
    else:
        g.sb_place_size = g.sm_cnt * g.ty_bytes
        uxc_sub.sb_place_block()
        g.sy_kind = K_SK_ARRAY
        g.sy_val = g.sb_place
        uxc_sym.sy_add()
        if g.bs_n > K_TOP:
            er_stop("ARRAYS TOO BIG")


def sm_dim_count():
    """SM.DIM.COUNT. (n) after a name in DIM: an array of n elements, 0 to n - 1. n is a
    constant. The expression can overwrite g.sm_n."""
    g.sm_dim_name = g.sm_n
    uxc_lex.lx_next()
    uxc_expr.ex_expr()
    g.sm_n = g.sm_dim_name
    g.ex_i = g.ex_vn - 1
    if g.ex_vk[g.ex_i] != K_EK_CONST:
        er_stop("ARRAY SIZE NOT A CONSTANT")
    uxc_fold.ex_const_word()
    g.sm_cnt = g.ex_vv[g.ex_i]
    g.ex_vn = g.ex_vn - 1
    if g.sm_cnt == 0:
        er_stop("ARRAY SIZE 0")
    if g.tk_t != K_TT_OP or g.tk_k != 41:
        er_stop("MISSING )")
    uxc_lex.lx_next()


def sm_label():
    """SM.LABEL. name: -- the label is the code offset of the next statement. A label in a
    SUB belongs to the SUB, so no GOTO crosses into or out of one."""
    if g.tk_m != 0:
        er_syntax()
    g.sm_n = g.sm_w
    uxc_name.nm_reserved()
    g.sy_name = g.sm_n
    g.sy_ow = g.sb_current
    uxc_sym.sy_find()
    if g.sy_r == 0:
        g.sy_kind = K_SK_LABEL
        g.sy_type = 0
        g.sy_val = g.cb_n
        g.sy_flags = 1
        uxc_sym.sy_add()
        return
    # A GOTO can name a label before it is placed.
    uxc_sym.sy_get()
    if g.sy_kind != K_SK_LABEL or (g.sy_flags & 1) != 0:
        er_stop("DUPLICATE NAME " + g.sm_n)
    g.sy_val = g.cb_n
    g.sy_flags = 1
    uxc_sym.sy_set()


def sm_let():
    """SM.LET. name = expr; record = record in UXC-RECORD.BL."""
    g.sm_n = g.sm_w
    sm_var()
    if g.sy_type == K_TY_STR:
        uxc_str.sg_let()
        return
    if g.sy_type >= K_TY_RECORD:
        uxc_record.rd_let()
        return
    uxc_record.rd_section()
    g.sm_ty = g.sy_type
    g.sm_ad = g.sy_val
    g.sm_sec = g.rd_sec
    uxc_lex.lx_next()
    uxc_expr.ex_expr()
    sm_store()


def sm_store():
    """SM.STORE. The value on the expression stack into the g.sm_ty at g.sm_sec g.sm_ad."""
    if g.sm_ty == K_TY_LONG:
        uxc_expr.ex_tol()
        g.sl_s[0] = g.sm_sec
        g.sl_v[0] = g.sm_ad
        emit(T.T_STL_V)
        return
    if g.sm_ty == K_TY_BYTE:
        uxc_expr.ex_tob()
        g.sl_s[0] = g.sm_sec
        g.sl_v[0] = g.sm_ad
        emit(T.T_STB_V)
    else:
        uxc_expr.ex_tow()
        g.sl_s[0] = g.sm_sec
        g.sl_v[0] = g.sm_ad
        emit(T.T_STW_V)


def sm_let_element():
    """SM.LET.ELEMENT. name(i) = expr, with the array's record in g.sy_*. A constant index is
    a store to the element. A BYTE array with a BYTE index pushes the index; any other index
    pushes the element's address."""
    g.sm_ty = g.sy_type
    g.sm_ad = g.sy_val
    g.sm_sec = K_SEC_BSS
    g.sm_cnt = g.sy_cnt
    uxc_lex.lx_next()
    uxc_expr.ex_expr()
    if g.tk_t != K_TT_OP or g.tk_k != 41:
        er_stop("MISSING )")
    uxc_lex.lx_next()
    if g.tk_t != K_TT_OP or g.tk_k != 61:
        er_syntax()
    g.ex_i = g.ex_vn - 1
    if g.ex_vk[g.ex_i] == K_EK_CONST:
        if g.ex_vv[g.ex_i] >= g.sm_cnt:
            er_stop("BAD SUBSCRIPT")
        g.ty_code = g.sm_ty
        uxc_sym.ty_size()
        g.sm_ad = g.sm_ad + g.ex_vv[g.ex_i] * g.ty_bytes
        g.ex_vn = g.ex_vn - 1
        uxc_lex.lx_next()
        uxc_expr.ex_expr()
        sm_store()
        return
    if g.sm_ty == K_TY_BYTE and g.ex_vt[g.ex_i] != K_TY_WORD and g.ex_vt[g.ex_i] != K_TY_LONG:
        uxc_expr.ex_tob()
        if g.sm_errors_on == 1 and g.sm_cnt < 256:
            g.sl_s[0] = K_SEC_CONST
            g.sl_v[0] = g.sm_cnt
            emit(T.T_CHKB)
        emit(T.T_PUSHB)
        g.ex_sd = g.ex_sd + 1
        uxc_lex.lx_next()
        uxc_expr.ex_expr()
        uxc_expr.ex_tob()
        g.sl_s[0] = K_SEC_BSS
        g.sl_v[0] = g.sm_ad
        emit(T.T_STB_SY)
        g.ex_sd = g.ex_sd - 1
        return
    uxc_expr.ex_tow()
    if g.sm_errors_on == 1:
        g.sl_s[0] = K_SEC_CONST
        g.sl_v[0] = g.sm_cnt
        emit(T.T_CHKW)
    g.sl_s[0] = K_SEC_BSS
    g.sl_v[0] = g.sm_ad
    if g.sm_ty == K_TY_BYTE:
        emit(T.T_IDXB)
    if g.sm_ty == K_TY_WORD:
        emit(T.T_IDXW)
    if g.sm_ty == K_TY_LONG:
        emit(T.T_IDXL)
    sm_store_through()


def sm_store_through():
    """SM.STORE.THROUGH. The address in A/Y is pushed, and the value after the next token is
    stored through it as a g.sm_ty."""
    emit(T.T_PUSH)
    g.ex_sd = g.ex_sd + 1
    uxc_lex.lx_next()
    uxc_expr.ex_expr()
    if g.sm_ty == K_TY_BYTE:
        uxc_expr.ex_tob()
        emit(T.T_POKE)
    elif g.sm_ty == K_TY_LONG:
        uxc_expr.ex_tol()
        emit(T.T_POKEL)
    else:
        uxc_expr.ex_tow()
        emit(T.T_POKEW)
    g.ex_sd = g.ex_sd - 1


def sm_contents():
    """SM.CONTENTS. ContentsAt(a) = v stores a BYTE, as POKE a, v does. ContentsAtW(a) = v
    stores a WORD."""
    g.sm_ty = K_TY_BYTE
    if g.sm_w == "CONTENTSATW":
        g.sm_ty = K_TY_WORD
    uxc_lex.lx_next()
    if g.tk_t != K_TT_OP or g.tk_k != 40:
        er_stop("MISSING ( AFTER " + g.sm_w)
    uxc_lex.lx_next()
    uxc_expr.ex_expr()
    if g.tk_t != K_TT_OP or g.tk_k != 41:
        er_stop("MISSING )")
    uxc_lex.lx_next()
    if g.tk_t != K_TT_OP or g.tk_k != 61:
        er_syntax()
    sm_poke_address()


def sm_pos():
    """SM.POS. POS(0) = v moves the cursor to column v. POS(1) = v moves it to row v."""
    uxc_expr.ex_pos_axis(1, "POS NEEDS 0 OR 1")
    uxc_lex.lx_next()
    if g.tk_t != K_TT_OP or g.tk_k != 61:
        er_syntax()
    uxc_lex.lx_next()
    uxc_expr.ex_expr()
    uxc_expr.ex_tob()
    if g.ex_pos_row == 0:
        emit(T.T_POSSETCOL)
    if g.ex_pos_row == 1:
        emit(T.T_POSSETROW)


def sm_poke():
    """SM.POKE. POKE a, v -- a constant address, or @name, is the operand of the store. Any
    other address is pushed, and T_POKE stores through it."""
    g.sm_ty = K_TY_BYTE
    uxc_lex.lx_next()
    uxc_expr.ex_expr()
    if g.tk_t != K_TT_OP or g.tk_k != 44:
        er_syntax()
    sm_poke_address()


def sm_poke_address():
    """SM.POKE.ADDRESS. The address is the top entry, and the token before the value is the
    token. The value is stored as a g.sm_ty."""
    g.ex_i = g.ex_vn - 1
    g.sm_k = g.ex_vk[g.ex_i]
    if g.ex_vt[g.ex_i] == K_TY_STR:
        er_mismatch()
    if g.sm_k == K_EK_CONST or g.sm_k == K_EK_ADDR:
        if g.sm_k == K_EK_CONST:
            uxc_fold.ex_const_word()
        g.sm_sec = g.ex_vs[g.ex_i]
        g.sm_ad = g.ex_vv[g.ex_i]
        g.ex_vn = g.ex_vn - 1
        uxc_lex.lx_next()
        uxc_expr.ex_expr()
        sm_store()
        return
    uxc_expr.ex_tow()
    sm_store_through()


def sm_print():
    """SM.PRINT. PRINT a; b, c ... as MS BASIC does: ; joins two items, a comma moves to the
    next print zone, and two items with nothing between them are joined as by ;. A trailing
    ; or comma leaves the cursor on the line."""
    g.sm_nl = 1
    g.sm_file = 0
    uxc_lex.lx_next()
    if g.tk_t == K_TT_OP and g.tk_k == 35:
        sm_print_handle()
    while True:
        if g.tk_t == K_TT_EOL:
            break
        if g.tk_t == K_TT_NAME and g.tk_s == "ELSE":
            break
        if g.tk_t == K_TT_OP and g.tk_k == 59:
            g.sm_nl = 0
            uxc_lex.lx_next()
            continue
        if g.tk_t == K_TT_OP and g.tk_k == 44:
            g.sm_nl = 0
            sm_print_comma()
            uxc_lex.lx_next()
            continue
        g.sm_nl = 1
        sm_print_one()
    if g.sm_nl != 0:
        emit(T.T_PRNL)
    if g.sm_file == 1:
        emit(T.T_CLRCHN)


def sm_print_handle():
    """SM.PRINT.HANDLE. #handle and the comma after it, with the token at the #. A constant
    handle 0-2 is the screen and needs no code."""
    uxc_lex.lx_next()
    uxc_expr.ex_expr()
    g.ex_i = g.ex_vn - 1
    if g.ex_vk[g.ex_i] == K_EK_CONST and g.ex_vv[g.ex_i] <= 2:
        g.ex_vn = g.ex_vn - 1
    else:
        uxc_expr.ex_tob()
        emit(T.T_CHKOUT)
        g.sm_file = 1
    if g.tk_t == K_TT_EOL:
        return
    if g.tk_t != K_TT_OP or g.tk_k != 44:
        er_syntax()
    uxc_lex.lx_next()


def sm_print_comma():
    """SM.PRINT.COMMA. The next print zone on the screen. In a file, a ",", so that INPUT #
    reads the items back as fields."""
    if g.sm_file == 0:
        emit(T.T_PRCOMMA)
        return
    g.sl_s[0] = K_SEC_CONST
    g.sl_v[0] = 44
    emit(T.T_LDB_C)
    emit(T.T_PRCHR)


def sm_close():
    """SM.CLOSE. CLOSE handle."""
    uxc_lex.lx_next()
    uxc_expr.ex_expr()
    uxc_expr.ex_tob()
    emit(T.T_CLOSE)


def sm_print_one():
    """SM.PRINT.ONE. One item. sg_print_item prints a string."""
    uxc_str.sg_print_item()
    if g.sg_printed == 1:
        return
    if g.ex_vt[g.ex_vn - 1] == K_TY_LONG:
        g.sm_print_signed = g.ex_vg[g.ex_vn - 1]
        uxc_expr.ex_tol()
        if g.sm_print_signed == 0:
            emit(T.T_PRLONG)
        if g.sm_print_signed == 1:
            emit(T.T_PRSLONG)
        return
    if g.ex_vg[g.ex_vn - 1] == 1:
        uxc_expr.ex_tow()
        emit(T.T_PRSWORD)
        return
    if g.ex_vt[g.ex_vn - 1] == K_TY_BYTE:
        uxc_expr.ex_tob()
        emit(T.T_PRBYTE)
    else:
        uxc_expr.ex_tow()
        emit(T.T_PRWORD)
