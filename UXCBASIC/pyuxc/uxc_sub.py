"""UXC-SUB.BL: SUB, FUNCTION, their ends, RETURN and calls.

    sb_scan()     the first pass: declare every SUB and FUNCTION from its header
    sb_sub()      SUB or FUNCTION in the second pass: the start of its body
    sb_endsub()   ENDSUB, ENDFUNCTION, END SUB or END FUNCTION
    sb_return()   RETURN, with the token at RETURN
    sb_call_keyword()    CALL name ( args ), with the token at CALL
    sb_call_statement()  in  g.sm_w   name ( args ), with the token at its (
    sb_function() in  g.sy_*     a call in an expression, with the token at the name
    sb_open()     at the end of the source, a SUB still open is an error
    sb_pools()    at link, place the pools of temps and locals
    sb_pool_of()  in  g.fx_ow    out g.sb_pool, the offset of that SUB's pool
"""

from uxc_code import emit
from uxc_defs import K_EK_REG, K_EX_DEPTH, K_FRAME_MAX, K_JP_LIST, K_NS_IFL, K_NS_MAX, \
    K_SB_DEPTH, K_SEC_BSS, K_SEC_CONST, K_SEC_LABEL, K_SEC_VAR, K_SK_CALL, K_SK_SUB, K_SK_VAR, \
    K_SY_END, \
    K_SY_LEVEL, K_SY_LIVE, K_SY_POOL, K_SY_SIGNED, K_SY_TEMP, K_SY_TEMPS, K_TT_EOL, K_TT_NAME, K_TT_OP, \
    K_TY_BYTE, K_TY_LONG, K_TY_STR, K_TY_WORD
import uxc_cond
import uxc_dead
import uxc_expr
import uxc_flow
import uxc_lex
import uxc_name
import uxc_str
import uxc_sym
import uxc_tpl as T
from uxc_state import er_missing_as, er_stop, er_syntax, g


def sb_scan():
    """SB.SCAN. Read the whole source, and declare each SUB or FUNCTION whose line starts
    with SUB or FUNCTION, so that a call may come before it. A BIND to a word of the
    language, or to a SUB declared above it outside a SUB body, is made here, so that it
    works on every line. FUNCT and ENDFUNCT are BINDs that every source has. The caller
    opens the source again after."""
    g.sb_current = 0
    g.sb_scan_in_sub = 0
    g.nm_current = 0
    g.nm_scope = 0
    g.nm_scan_path = ""
    g.nm_alias_name[0] = "FUNCT"
    g.nm_alias_target[0] = "FUNCTION"
    g.nm_alias_name[1] = "ENDFUNCT"
    g.nm_alias_target[1] = "ENDFUNCTION"
    g.nm_alias_count = 2
    while True:
        uxc_lex.lx_read()
        if g.lx_got == 0:
            break
        uxc_lex.lx_whole()
        uxc_lex.lx_next()
        if g.tk_t != K_TT_NAME:
            continue
        if g.tk_s == "SUB" or g.tk_s == "FUNCTION":
            g.sb_scan_in_sub = 1
            sb_header()
            continue
        if g.tk_s == "ENDSUB" or g.tk_s == "ENDFUNCTION":
            g.sb_scan_in_sub = 0
        uxc_name.nm_scan()
        if g.tk_t != K_TT_NAME:
            continue
        if g.tk_s == "SUB" or g.tk_s == "FUNCTION":
            g.sb_scan_in_sub = 0
        if g.tk_s == "BIND":
            uxc_name.nm_bind_scan()
    g.nm_current = 0


def sb_header():
    """SB.HEADER. SUB name ( [param, ...] ), or FUNCTION name[$] ( [param, ...] ) [AS type],
    with the token at SUB or FUNCTION. A FUNCTION needs a $ or an AS."""
    g.sb_header_function = 0
    if g.tk_s == "FUNCTION":
        g.sb_header_function = 1
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NAME:
        er_syntax()
    g.sb_sub_name = g.tk_s
    g.sb_result_type = g.tk_m
    g.sm_n = g.sb_sub_name
    uxc_name.nm_reserved()
    g.sy_name = g.sb_sub_name
    g.sy_ow = g.nm_current
    uxc_sym.sy_find()
    if g.sy_r != 0:
        sb_error_duplicate()
    g.sy_kind = K_SK_SUB
    g.sy_type = 0
    g.sy_val = 0
    g.sy_flags = 0
    uxc_sym.sy_add()
    g.sb_record = g.sy_r
    g.sb_count = 0
    g.sb_frame = 0
    uxc_lex.lx_next()
    if g.tk_t != K_TT_OP or g.tk_k != 40:
        sb_error_missing_open()
    uxc_lex.lx_next()
    if not (g.tk_t == K_TT_OP and g.tk_k == 41):
        while True:
            sb_parameter()
            if g.tk_t != K_TT_OP:
                er_syntax()
            if g.tk_k == 41:
                break
            if g.tk_k != 44:
                er_syntax()
            uxc_lex.lx_next()
    uxc_lex.lx_next()
    g.sm_n = g.sb_sub_name
    g.sb_type = g.sb_result_type
    sb_as()
    if g.tk_t != K_TT_EOL:
        er_syntax()
    if g.sb_header_function == 0 and g.sb_type != 0:
        er_stop("SUB WITH A TYPE: USE FUNCTION")
    if g.sb_header_function == 1 and g.sb_type == 0:
        er_missing_as()
    g.sy_r = g.sb_record
    uxc_sym.sy_get()
    g.sy_type = g.sb_type
    g.sy_flags = g.sb_signed * K_SY_SIGNED
    g.sy_np = g.sb_count
    uxc_sym.sy_set()
    g.sb_field = K_SY_POOL
    g.sb_word = g.sb_frame
    sb_field_set()


def sb_parameter():
    """SB.PARAMETER. One parameter of SUB g.sb_record: name$ or name AS type. It becomes the
    next record, a variable owned by the SUB. A STRING parameter is a WORD that holds the
    address of the caller's block, and its element count is 0."""
    if g.tk_t != K_TT_NAME:
        er_syntax()
    g.sb_parameter_name = g.tk_s
    g.sb_type = g.tk_m
    g.sm_n = g.sb_parameter_name
    uxc_name.nm_reserved()
    uxc_lex.lx_next()
    sb_as()
    if g.sb_type == 0:
        er_missing_as()
    g.sy_name = g.sb_parameter_name
    g.sy_ow = g.sb_record
    uxc_sym.sy_find()
    if g.sy_r != 0:
        sb_error_duplicate()
    g.ty_code = g.sb_type
    uxc_sym.ty_size()
    g.sb_place_size = g.ty_bytes
    sb_place_local()
    g.sy_kind = K_SK_VAR
    g.sy_type = g.sb_type
    g.sy_val = g.sb_place
    g.sy_flags = g.sb_signed * K_SY_SIGNED
    g.sy_cnt = 0
    uxc_sym.sy_add()
    g.sb_count = g.sb_count + 1


def sb_as():
    """SB.AS. An optional AS type after the name g.sm_n, whose type mark is g.sb_type. Out:
    g.sb_type, and g.sb_signed, 1 for a signed type."""
    g.sb_signed = 0
    if g.tk_t != K_TT_NAME:
        return
    if g.tk_s != "AS":
        return
    if g.sb_type != 0:
        er_stop("A MARK AND AS")
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NAME:
        er_syntax()
    uxc_name.nm_type_name()
    g.sb_type = g.nm_type_code
    g.sb_signed = g.nm_type_signed
    if g.sb_type == 0:
        er_syntax()
    uxc_lex.lx_next()


# The body

def sb_sub():
    """SB.SUB. With the token at SUB or FUNCTION. The header was read by the first pass, so
    the rest of the line is skipped. The FOR limits and REPEAT counts of the main program are
    put aside, so that the body has its own."""
    if g.sb_current != 0:
        er_stop("SUB INSIDE SUB")
    if g.ns_d != 0:
        er_stop("SUB INSIDE A BLOCK")
    uxc_lex.lx_next()
    g.sy_name = g.tk_s
    g.sy_ow = g.nm_current
    uxc_sym.sy_find()
    if g.sy_r == 0:
        er_syntax()
    g.sb_current = g.sy_r
    g.nm_scope = g.sy_r
    g.sb_sub_name = g.tk_s
    g.sb_sub_line = g.lx_no
    g.sb_sub_text = g.lx_l
    g.sb_has_value = 0
    g.jp_k = K_JP_LIST
    g.jp_h = 0
    g.jp_b = T.T_BRA
    uxc_cond.jp_br()
    g.sb_around = g.jp_h
    g.sy_r = g.sb_current
    uxc_sym.sy_get()
    g.sy_val = g.cb_n
    g.sy_flags = 1 + (g.sy_flags & (K_SY_SIGNED + K_SY_LIVE))
    # A SUB inside #KEEP ... #ENDKEEP is kept (UXC-DEAD.BL).
    if g.dd_region_line != 0 and (g.sy_flags & K_SY_LIVE) == 0:
        g.sy_flags = g.sy_flags + K_SY_LIVE
    uxc_sym.sy_set()
    g.sb_field = K_SY_POOL
    sb_field_get()
    g.sb_frame = g.sb_word
    for g.sb_i in range(0, K_NS_MAX + 1):
        g.sb_saved_hidden[g.sb_i] = g.hv_ad[g.sb_i]
        g.hv_ad[g.sb_i] = -1
    while g.tk_t != K_TT_EOL:
        uxc_lex.lx_next()


def sb_endsub():
    """SB.ENDSUB. With the token at ENDSUB or ENDFUNCTION, or at the SUB or FUNCTION of
    END SUB or END FUNCTION. The end must match the start. A body whose last statement is
    not a RETURN gets one: a FUNCTION gives 0."""
    g.sb_end_function = 0
    if g.tk_s == "FUNCTION" or g.tk_s == "ENDFUNCTION":
        g.sb_end_function = 1
    if g.sb_current == 0:
        g.er_m = "ENDSUB WITHOUT SUB"
        if g.sb_end_function == 1:
            g.er_m = "ENDFUNCTION WITHOUT FUNCTION"
        er_stop(g.er_m)
    g.sy_r = g.sb_current
    uxc_sym.sy_get()
    if g.sy_type == 0 and g.sb_end_function == 1:
        er_stop("ENDFUNCTION IN A SUB")
    if g.sy_type != 0 and g.sb_end_function == 0:
        er_stop("ENDSUB IN A FUNCTION")
    if g.ns_d != 0:
        if g.ns_k[g.ns_d] == K_NS_IFL:
            er_stop("BLOCK STATEMENT AFTER THEN")
        uxc_flow.ct_open()
    g.sy_r = g.sb_current
    g.sb_field = K_SY_POOL
    g.sb_word = g.sb_frame
    sb_field_set()
    uxc_sym.sy_get()
    if g.sy_type != 0 and g.sb_has_value == 0:
        er_stop("NO RETURN VALUE IN " + g.sb_sub_name)
    if g.sm_previous_return == 0:
        sb_fall_out()
    g.jp_l = g.sb_around
    uxc_cond.jp_here()
    g.sy_r = g.sb_current
    g.sb_field = K_SY_END
    g.sb_word = g.cb_n
    sb_field_set()
    for g.sb_i in range(0, K_NS_MAX + 1):
        g.hv_ad[g.sb_i] = g.sb_saved_hidden[g.sb_i]
    g.sb_current = 0
    g.nm_scope = g.nm_current
    uxc_lex.lx_next()


def sb_fall_out():
    """SB.FALL.OUT. The return at the end of a body, for the SUB in g.sy_*."""
    g.sl_s[0] = K_SEC_CONST
    g.sl_v[0] = 0
    if g.sy_type == K_TY_BYTE:
        emit(T.T_LDB_C)
    if g.sy_type == K_TY_WORD:
        emit(T.T_LDW_C)
    if g.sy_type == K_TY_LONG:
        emit(T.T_LDW_C)
        emit(T.T_LWIDEN)
    if g.sy_type == K_TY_STR:
        uxc_str.sg_return_empty()
    emit(T.T_RTS)


def sb_return():
    """SB.RETURN. RETURN in a SUB, or RETURN value in a FUNCTION."""
    if g.sb_current == 0:
        er_stop("RETURN OUTSIDE SUB")
    uxc_lex.lx_next()
    g.sy_r = g.sb_current
    uxc_sym.sy_get()
    g.sb_type = g.sy_type
    if g.sb_type == 0:
        g.sb_called_name = g.sb_sub_name
        if g.tk_t != K_TT_EOL:
            sb_error_no_value()
        emit(T.T_RTS)
        return
    if g.tk_t == K_TT_EOL:
        er_stop("RETURN NEEDS A VALUE")
    uxc_expr.ex_expr()
    if g.sb_type == K_TY_BYTE:
        uxc_expr.ex_tob()
    if g.sb_type == K_TY_WORD:
        uxc_expr.ex_tow()
    if g.sb_type == K_TY_LONG:
        uxc_expr.ex_tol()
    if g.sb_type == K_TY_STR:
        uxc_str.sg_tos()
    g.sb_has_value = 1
    emit(T.T_RTS)


# Calls

def sb_call_keyword():
    """SB.CALL.KEYWORD. CALL name ( args ), with the token at CALL."""
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NAME:
        er_syntax()
    g.sb_called_name = g.tk_s
    uxc_lex.lx_next()
    sb_call_named()


def sb_call_statement():
    """SB.CALL.STATEMENT. name ( args ) as a statement, with the token at its (."""
    g.sb_called_name = g.sm_w
    sb_call_named()


def sb_call_named():
    if g.tk_t != K_TT_OP or g.tk_k != 40:
        sb_error_missing_open()
    g.sm_n = g.sb_called_name
    uxc_name.nm_find()
    if g.sy_kind != K_SK_SUB:
        er_stop("NOT A SUB: " + g.sb_called_name)
    g.sb_called_record = g.sy_r
    sb_call()


def sb_function():
    """SB.FUNCTION. A call in an expression, with the token at the name. The result is a new
    K_EK_REG entry, or for a STRING result the entry sg_result makes. The call loses A/Y and
    the flags, so every entry under it is pushed first."""
    g.sb_called_name = g.tk_s
    g.sb_called_record = g.sy_r
    if g.sy_type == 0:
        sb_error_no_value()
    uxc_lex.lx_next()
    if g.tk_t != K_TT_OP or g.tk_k != 40:
        sb_error_missing_open()
    g.ex_fb = g.ex_vn
    uxc_expr.ex_flush()
    sb_call()
    if g.sb_call_type == K_TY_STR:
        uxc_str.sg_result()
        return
    g.ex_k = K_EK_REG
    g.ex_s = K_SEC_CONST
    g.ex_v = 0
    g.ex_ty = g.sb_call_type
    g.ex_sg = g.sb_call_signed
    uxc_expr.ex_pushv()


def sb_call():
    """SB.CALL. The call of SUB g.sb_called_record, with the token at its (. The token is
    left after the ). Out: g.sb_call_type, the SUB's result type, and g.sb_call_signed.

    WARNING: an argument with a call in it can run this same SUB before this call's JSR, as
    MAX%(A%, MAX%(B%, C%)) does, and that would overwrite the parameters already stored. So
    when a ( comes anywhere in the arguments, each argument but the last is pushed, and the
    pushes are popped into the parameters just before the JSR.

    An argument is an expression, and it can hold a call, so sb_call runs inside itself.
    What it keeps across an argument is in the g.sb_call_* arrays, one entry per depth."""
    if g.sb_called_record == g.sb_current:
        er_stop("A SUB CANNOT CALL ITSELF")
    sb_edge()
    sb_nest()
    g.sy_r = g.sb_called_record
    uxc_sym.sy_get()
    d = g.sb_depth
    g.sb_call_record[d] = g.sb_called_record
    g.sb_call_parameters[d] = g.sy_np
    g.sb_call_result[d] = g.sy_type
    if (g.sy_flags & K_SY_SIGNED) != 0:
        g.sb_call_result[d] = g.sy_type + 256
    g.sb_call_argument[d] = 0
    sb_look_ahead()
    g.sb_call_stacked[d] = g.sb_nested
    uxc_lex.lx_next()
    if not (g.tk_t == K_TT_OP and g.tk_k == 41):
        while True:
            g.sb_call_argument[d] = g.sb_call_argument[d] + 1
            if g.sb_call_argument[d] > g.sb_call_parameters[d]:
                sb_error_arguments()
            g.ex_op_base = g.ex_on
            g.ex_cm = 0
            uxc_expr.ex_expr()
            g.sy_r = g.sb_call_record[d] + g.sb_call_argument[d]
            uxc_sym.sy_get()
            g.sb_parameter_type = g.sy_type
            g.sb_parameter_address = g.sy_val
            if g.sb_parameter_type == K_TY_BYTE:
                uxc_expr.ex_tob()
            if g.sb_parameter_type == K_TY_WORD:
                uxc_expr.ex_tow()
            if g.sb_parameter_type == K_TY_LONG:
                uxc_expr.ex_tol()
            if g.sb_parameter_type == K_TY_STR:
                uxc_str.sg_pass()
            sb_call_pass()
            if g.tk_t != K_TT_OP:
                er_syntax()
            if g.tk_k == 41:
                break
            if g.tk_k != 44:
                er_syntax()
            uxc_lex.lx_next()
    if g.sb_call_argument[d] != g.sb_call_parameters[d]:
        sb_error_arguments()
    sb_call_pop()
    g.sl_s[0] = K_SEC_LABEL
    g.sl_v[0] = g.sb_call_record[d]
    emit(T.T_JSR)
    g.sb_call_signed = g.sb_call_result[d] // 256
    g.sb_call_type = g.sb_call_result[d] - 256 * g.sb_call_signed
    sb_unnest()
    uxc_lex.lx_next()


def sb_nest():
    """SB.NEST. One level deeper into the arguments of a call or a function. The operator
    stack, the brackets and the condition flag of the expression around are kept."""
    if g.sb_depth >= K_SB_DEPTH:
        er_stop("CALLS NESTED TOO DEEP")
    g.sb_depth = g.sb_depth + 1
    g.sb_saved_operators[g.sb_depth] = g.ex_on
    g.sb_saved_operator_base[g.sb_depth] = g.ex_op_base
    g.sb_saved_parentheses[g.sb_depth] = g.ex_pd
    g.sb_saved_condition[g.sb_depth] = g.ex_cm


def sb_unnest():
    """SB.UNNEST. Back out of sb_nest."""
    g.ex_on = g.sb_saved_operators[g.sb_depth]
    g.ex_op_base = g.sb_saved_operator_base[g.sb_depth]
    g.ex_pd = g.sb_saved_parentheses[g.sb_depth]
    g.ex_cm = g.sb_saved_condition[g.sb_depth]
    g.sb_depth = g.sb_depth - 1


def sb_call_pass():
    """SB.CALL.PASS. The argument in A or A/Y goes to its parameter g.sb_parameter_*: stored
    now, or pushed for sb_call_pop.
    WARNING: a parameter is in the frame of the SUB called, and fx_add takes a fixup's owner
    from g.sb_current. So g.sb_current is the SUB called while a store into a parameter is
    emitted, here and in sb_call_pop."""
    d = g.sb_depth
    g.sl_s[0] = K_SEC_VAR
    g.sl_v[0] = g.sb_parameter_address
    if g.sb_call_stacked[d] != 0 and g.sb_call_argument[d] != g.sb_call_parameters[d]:
        if g.sb_parameter_type == K_TY_BYTE:
            emit(T.T_PUSHB)
        if g.sb_parameter_type == K_TY_LONG:
            emit(T.T_PUSHL)
        if g.sb_parameter_type != K_TY_BYTE and g.sb_parameter_type != K_TY_LONG:
            emit(T.T_PUSH)
        g.ex_sd = g.ex_sd + 1
        if g.ex_sd > K_EX_DEPTH:
            er_stop("EXPRESSION TOO COMPLEX")
        return
    g.sb_caller = g.sb_current
    g.sb_current = g.sb_call_record[d]
    if g.sb_parameter_type == K_TY_BYTE:
        emit(T.T_STB_V)
    if g.sb_parameter_type == K_TY_LONG:
        emit(T.T_STL_V)
    if g.sb_parameter_type != K_TY_BYTE and g.sb_parameter_type != K_TY_LONG:
        emit(T.T_STW_V)
    g.sb_current = g.sb_caller


def sb_call_pop():
    """SB.CALL.POP. The pushed arguments into their parameters, the last pushed first."""
    d = g.sb_depth
    if g.sb_call_stacked[d] == 0:
        return
    g.sb_pop_argument = g.sb_call_parameters[d] - 1
    while g.sb_pop_argument >= 1:
        g.sy_r = g.sb_call_record[d] + g.sb_pop_argument
        uxc_sym.sy_get()
        g.sl_s[0] = K_SEC_VAR
        g.sl_v[0] = g.sy_val
        g.sb_caller = g.sb_current
        g.sb_current = g.sb_call_record[d]
        if g.sy_type == K_TY_BYTE:
            emit(T.T_POPB_V)
        if g.sy_type == K_TY_LONG:
            emit(T.T_POPL_V)
        if g.sy_type != K_TY_BYTE and g.sy_type != K_TY_LONG:
            emit(T.T_POPW_V)
        g.sb_current = g.sb_caller
        g.ex_sd = g.ex_sd - 1
        g.sb_pop_argument = g.sb_pop_argument - 1


def sb_look_ahead():
    """SB.LOOK.AHEAD. g.sb_nested = 1 when a ( comes before the first ) after the call's own
    (. The token is at that ( and is put back after, with g.lx_p."""
    g.sb_saved_position = g.lx_p
    g.sb_nested = 0
    while True:
        uxc_lex.lx_next()
        if g.tk_t == K_TT_EOL:
            break
        if g.tk_t != K_TT_OP:
            continue
        if g.tk_k == 41:
            break
        if g.tk_k == 40:
            g.sb_nested = 1
            break
    g.lx_p = g.sb_saved_position
    g.tk_t = K_TT_OP
    g.tk_k = 40
    g.tk_s = ""
    g.tk_m = 0
    g.tk_v = 0


# Placing variables

def sb_place_variable():
    """SB.PLACE.VARIABLE. g.sb_place, the value of a new variable of g.sb_place_size bytes: in
    the variables, or in the frame of the SUB being compiled."""
    if g.sb_current != 0:
        sb_place_local()
        return
    g.sb_place = g.vr_n
    g.vr_n = g.vr_n + g.sb_place_size
    g.dv_s = 0
    uxc_dead.dv_log()


def sb_place_block():
    """SB.PLACE.BLOCK. g.sb_place, the value of a new block of g.sb_place_size bytes: in the
    array space, or in the frame of the SUB being compiled."""
    if g.sb_current != 0:
        sb_place_local()
        return
    g.sb_place = g.bs_n
    g.bs_n = g.bs_n + g.sb_place_size
    g.dv_s = 1
    uxc_dead.dv_log()


def sb_place_local():
    """SB.PLACE.LOCAL. The frame g.sb_frame grows down from its pool's offset, so a local's
    value is 65536 less the frame's size with the local in it."""
    g.sb_frame = g.sb_frame + g.sb_place_size
    if g.sb_frame > K_FRAME_MAX:
        er_stop("LOCALS TOO BIG")
    g.sb_place = 65536 - g.sb_frame


def sb_open():
    """SB.OPEN. At the end of the source, a SUB or FUNCTION still open is an error at its
    line."""
    if g.sb_current == 0:
        return
    g.sy_r = g.sb_current
    uxc_sym.sy_get()
    g.lx_no = g.sb_sub_line
    g.lx_l = g.sb_sub_text
    g.er_m = "SUB WITHOUT ENDSUB"
    if g.sy_type != 0:
        g.er_m = "FUNCTION WITHOUT ENDFUNCTION"
    er_stop(g.er_m)


# The pools of temps and locals

def sb_edge():
    """SB.EDGE. Record that g.sb_current calls g.sb_called_record: a record of kind K_SK_CALL,
    owned by the caller. Its value is the SUB called, and its count is the line of the first
    such call. A call from the main program needs none."""
    if g.sb_current == 0:
        return
    g.sy_name = "%C" + uxc_str.basic_str(g.sb_called_record)
    g.sy_ow = g.sb_current
    uxc_sym.sy_find()
    if g.sy_r != 0:
        return
    g.sy_kind = K_SK_CALL
    g.sy_type = 0
    g.sy_val = g.sb_called_record
    g.sy_flags = 0
    g.sy_cnt = g.lx_no
    uxc_sym.sy_add()


def sb_pools():
    """SB.POOLS. At link, place the pools from g.bs_n up, and emit the max of each temp. Each
    SUB gets a level: at least 1, and 1 more than the level of each SUB that calls it. Two
    SUBs of one level are never active at once, so the frames and the temps of one level
    share one pool: the frames below the pool's offset, the temps from it up. The main
    program has a pool of its own, of temps only. Out: g.bs_n, the end of the pools.
    WARNING: two SUBs that call each other have no level; the link stops with an error."""
    g.sb_subs = 0
    g.sb_top_level = 0
    g.sb_main_need = 0
    g.sb_max_loaded = 0
    for g.sb_record in range(1, g.sy_n + 1):
        g.sy_r = g.sb_record
        uxc_sym.sy_get()
        if g.sy_kind == K_SK_SUB:
            sb_pools_start()
    g.sb_passes = 0
    while True:
        g.sb_changed = 0
        for g.sb_record in range(1, g.sy_n + 1):
            g.sy_r = g.sb_record
            uxc_sym.sy_get()
            if g.sy_kind == K_SK_CALL:
                sb_pools_raise()
        g.sb_passes = g.sb_passes + 1
        if g.sb_changed == 0:
            break
        if g.sb_passes >= g.sb_subs:
            sb_error_each_other()
    for g.sb_record in range(1, g.sy_n + 1):
        g.sy_r = g.sb_record
        uxc_sym.sy_get()
        if g.sy_kind == K_SK_VAR and (g.sy_flags & K_SY_TEMP) != 0:
            sb_pools_need()
    g.sb_main_pool = g.bs_n
    g.sb_pool_at = g.bs_n
    g.sb_pool_temps = g.sb_main_need
    sb_pools_maxes()
    g.bs_n = g.bs_n + g.sb_pool_temps
    for g.sb_level_now in range(1, g.sb_top_level + 1):
        sb_pools_level()


def sb_pools_start():
    """SB.POOLS.START. SUB g.sy_r has level 1 and needs no temps yet."""
    g.sb_subs = g.sb_subs + 1
    g.sb_top_level = 1
    uxc_sym.sy_at()
    g.ram[g.sy_ad + K_SY_LEVEL] = 1
    g.ram[g.sy_ad + K_SY_TEMPS] = 0


def sb_pools_raise():
    """SB.POOLS.RAISE. With the call record read: the SUB called is at least 1 level below its
    caller."""
    g.sb_callee = g.sy_val
    g.sb_call_line = g.sy_cnt
    g.sy_r = g.sy_owner
    sb_level_of()
    g.sb_caller_level = g.sb_level
    g.sy_r = g.sb_callee
    sb_level_of()
    if g.sb_level > g.sb_caller_level:
        return
    g.sb_level = g.sb_caller_level + 1
    g.ram[g.sy_ad + K_SY_LEVEL] = g.sb_level
    if g.sb_level > g.sb_top_level:
        g.sb_top_level = g.sb_level
    g.sb_changed = 1
    g.sb_each_other_line = g.sb_call_line


def sb_pools_need():
    """SB.POOLS.NEED. With a temp's record read: its owner's pool holds at least its block."""
    g.sb_need = g.sy_val + 257
    if g.sy_owner == 0:
        if g.sb_need > g.sb_main_need:
            g.sb_main_need = g.sb_need
        return
    g.sb_need = int(g.sb_need / 257 + 0.5)
    g.sy_r = g.sy_owner
    uxc_sym.sy_at()
    if g.ram[g.sy_ad + K_SY_TEMPS] >= g.sb_need:
        return
    g.ram[g.sy_ad + K_SY_TEMPS] = g.sb_need


def sb_pools_level():
    """SB.POOLS.LEVEL. The pool of level g.sb_level_now at g.bs_n: room below its offset for
    the biggest frame of its SUBs, and room from it up for the most temps any of them needs.
    Each of its SUBs gets the pool's offset in place of its frame bytes."""
    g.sb_pool_frame = 0
    g.sb_pool_temps = 0
    for g.sb_record in range(1, g.sy_n + 1):
        g.sy_r = g.sb_record
        uxc_sym.sy_get()
        if g.sy_kind == K_SK_SUB:
            sb_pools_measure()
    g.sb_pool_at = g.bs_n + g.sb_pool_frame
    for g.sb_record in range(1, g.sy_n + 1):
        g.sy_r = g.sb_record
        uxc_sym.sy_get()
        if g.sy_kind == K_SK_SUB:
            sb_pools_place()
    sb_pools_maxes()
    g.bs_n = g.sb_pool_at + g.sb_pool_temps


def sb_pools_measure():
    sb_level_of()
    if g.sb_level != g.sb_level_now:
        return
    g.sb_need = g.ram[g.sy_ad + K_SY_TEMPS] * 257
    if g.sb_need > g.sb_pool_temps:
        g.sb_pool_temps = g.sb_need
    g.sb_field = K_SY_POOL
    sb_field_get()
    if g.sb_word > g.sb_pool_frame:
        g.sb_pool_frame = g.sb_word


def sb_pools_place():
    sb_level_of()
    if g.sb_level != g.sb_level_now:
        return
    g.sb_field = K_SY_POOL
    g.sb_word = g.sb_pool_at
    sb_field_set()


def sb_pools_maxes():
    """SB.POOLS.MAXES. The max, 255, of each temp from g.sb_pool_at, g.sb_pool_temps bytes."""
    g.sb_slot = 0
    while g.sb_slot < g.sb_pool_temps:
        if g.sb_max_loaded == 0:
            g.sl_s[0] = K_SEC_CONST
            g.sl_v[0] = 255
            emit(T.T_LDB_C)
            g.sb_max_loaded = 1
        g.sl_s[0] = K_SEC_BSS
        g.sl_v[0] = g.sb_pool_at + g.sb_slot
        emit(T.T_STB_V)
        g.sb_slot = g.sb_slot + 257


def sb_pool_of():
    """SB.POOL.OF. g.sb_pool, the offset in the array space of the pool of SUB g.fx_ow, or of
    the main program's pool when g.fx_ow is 0."""
    g.sb_pool = g.sb_main_pool
    if g.fx_ow == 0:
        return
    g.sy_r = g.fx_ow
    g.sb_field = K_SY_POOL
    sb_field_get()
    g.sb_pool = g.sb_word


def sb_level_of():
    """SB.LEVEL.OF. g.sb_level, the level of SUB g.sy_r; 0 for the main program, g.sy_r = 0.
    When g.sy_r is a SUB, g.sy_ad is its record, with its bank selected."""
    g.sb_level = 0
    if g.sy_r == 0:
        return
    uxc_sym.sy_at()
    g.sb_level = g.ram[g.sy_ad + K_SY_LEVEL]


def sb_field_get():
    """SB.FIELD.GET. g.sb_word, the word at offset g.sb_field of record g.sy_r."""
    uxc_sym.sy_at()
    g.sb_word = g.ram[g.sy_ad + g.sb_field] + 256 * g.ram[g.sy_ad + g.sb_field + 1]


def sb_field_set():
    """SB.FIELD.SET. The word at offset g.sb_field of record g.sy_r is g.sb_word."""
    uxc_sym.sy_at()
    g.sb_high = g.sb_word // 256
    g.ram[g.sy_ad + g.sb_field] = g.sb_word - g.sb_high * 256
    g.ram[g.sy_ad + g.sb_field + 1] = g.sb_high


def sb_error_duplicate():
    er_stop("DUPLICATE NAME " + g.sm_n)


def sb_error_missing_open():
    er_stop("MISSING (")


def sb_error_no_value():
    er_stop("SUB " + g.sb_called_name + " HAS NO VALUE")


def sb_error_arguments():
    er_stop("WRONG NUMBER OF ARGUMENTS")


def sb_error_each_other():
    g.lx_no = g.sb_each_other_line
    g.lx_l = ""
    er_stop("SUBS CALL EACH OTHER")
