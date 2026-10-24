"""UXC-SUB.BL: SUB, FUNCTION, their ends, RETURN and calls.

    sb_scan()     the first pass: declare every SUB and FUNCTION from its header
    sb_sub()      SUB or FUNCTION in the second pass: the start of its body
    sb_endsub()   ENDSUB, ENDFUNCTION, END SUB or END FUNCTION
    sb_return()   RETURN, with the token at RETURN
    sb_call_keyword()    CALL name ( args ), with the token at CALL
    sb_call_statement()  in  g.sm_w   name ( args ), with the token at its (
    sb_function() in  g.sy_*     a call in an expression, with the token at the name
    sb_pointer_function()  CALL pointer WITH ( args ) in an expression, with the token at CALL
    sb_declare()  DECLARE SUB or DECLARE FUNCTION in the second pass
    sb_at_sub()   in  g.sy_*     @name of a SUB, where a pointer is wanted
    sb_sig_of()   in  g.sy_r     out g.sb_sig, the signature of a pointer variable, else 0
    sb_open()     at the end of the source, a SUB still open is an error
    sb_pools()    at link, place the pools of temps and locals
    sb_pool_of()  in  g.fx_ow    out g.sb_pool, the offset of that SUB's pool
"""

from uxc_code import emit
from uxc_defs import K_EK_ADDR, K_EK_CONST, K_EK_REG, K_EX_DEPTH, K_FRAME_MAX, K_JP_LIST, K_NS_IFL, K_NS_MAX, \
    K_SB_DEFAULTS, K_SB_DEPTH, K_SEC_BSS, K_SEC_CONST, K_SEC_LABEL, K_SEC_VAR, K_SK_ARRAY, K_SK_CALL, K_SK_SIG, \
    K_SK_SUB, K_SK_TARGET, K_SK_VAR, K_SY_ENUM_PARAMETER, K_SY_ENUM_TYPE, K_SY_SIGNATURE, \
    K_SY_LEVEL, K_SY_LIVE, K_SY_POOL, K_SY_READ_ONLY, K_SY_SIGNED, K_SY_TEMP, K_SY_TEMPS, K_TT_EOL, K_TT_NAME, K_TT_OP, \
    K_TT_STR, K_TY_BYTE, K_TY_LONG, K_TY_STR, K_TY_WORD
import uxc_cond
import uxc_dead
import uxc_expr
import uxc_flow
import uxc_lex
import uxc_name
import uxc_ramreg
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
        if g.tk_t == K_TT_OP and g.tk_k == 35:
            uxc_dead.dd_place_scan()
            continue
        if g.tk_t != K_TT_NAME:
            continue
        if g.tk_s == "SUB" or g.tk_s == "FUNCTION":
            g.sb_scan_in_sub = 1
            g.sb_header_kind = K_SK_SUB
            sb_header()
            continue
        if g.tk_s == "DECLARE":
            uxc_lex.lx_next()
            if g.tk_t != K_TT_NAME or (g.tk_s != "SUB" and g.tk_s != "FUNCTION"):
                er_syntax()
            g.sb_header_kind = K_SK_SIG
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
        if g.tk_s == "ENUM":
            uxc_name.nm_enum_scan()
    g.nm_current = 0


def sb_header():
    """SB.HEADER. SUB name ( [param, ...] ), or FUNCTION name[$] ( [param, ...] ) [AS type],
    with the token at SUB or FUNCTION. A FUNCTION needs a $ or an AS. The record is of kind
    g.sb_header_kind: K_SK_SUB, or K_SK_SIG after DECLARE."""
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
    g.sy_kind = g.sb_header_kind
    g.sy_type = 0
    g.sy_val = 0
    g.sy_flags = 0
    uxc_sym.sy_add()
    g.sb_record = g.sy_r
    g.sb_count = 0
    g.sb_frame = 0
    g.sb_header_default = 0
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
    """SB.PARAMETER. One parameter of SUB g.sb_record: name$, name$ AS CONST or name AS type,
    then = default. It becomes the next record, a variable owned by the SUB. A STRING parameter
    is a WORD that holds the address of the caller's block, and its element count is 0. After a
    parameter with a default, each parameter needs one."""
    if g.tk_t != K_TT_NAME:
        er_syntax()
    g.sb_parameter_name = g.tk_s
    g.sb_type = g.tk_m
    g.sm_n = g.sb_parameter_name
    uxc_name.nm_reserved()
    uxc_lex.lx_next()
    g.sb_read_only = 0
    if g.sb_type == K_TY_STR and g.tk_t == K_TT_NAME and g.tk_s == "AS":
        uxc_lex.lx_next()
        if g.tk_t != K_TT_NAME or g.tk_s != "CONST":
            er_stop("A MARK AND AS")
        g.sb_read_only = K_SY_READ_ONLY
        uxc_lex.lx_next()
    sb_as()
    if g.sb_type == 0:
        er_missing_as()
    g.sb_default = 0
    if g.tk_t == K_TT_OP and g.tk_k == 61:
        sb_default_read()
        g.sb_header_default = 1
    if g.sb_default == 0 and g.sb_header_default != 0:
        er_stop("NO DEFAULT: " + g.sb_parameter_name)
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
    g.sy_flags = g.sb_signed * K_SY_SIGNED + g.sb_read_only
    g.sy_cnt = 0
    uxc_sym.sy_add()
    g.sy_np = g.sb_default
    uxc_sym.sy_set()
    g.sb_field = K_SY_ENUM_TYPE
    g.sb_word = g.sb_enum + g.sb_sig
    sb_field_set()
    g.sb_count = g.sb_count + 1


def sb_default_read():
    """SB.DEFAULT.READ. The default of parameter g.sb_parameter_name, with the token at its =.
    Its text, up to the , or ) after it, goes into g.sb_default_text. Out: g.sb_default, its
    number, and the token at that , or ). A default has no (, so it holds no call. A STRING
    parameter's default is one string literal."""
    if g.sb_default_count >= K_SB_DEFAULTS:
        er_stop("TOO MANY DEFAULTS")
    g.sb_default_start = g.lx_p
    g.sb_default_tokens = 0
    while True:
        g.sb_default_end = g.lx_p
        uxc_lex.lx_next()
        if g.tk_t == K_TT_EOL:
            break
        if g.tk_t == K_TT_OP and (g.tk_k == 44 or g.tk_k == 41):
            break
        if g.tk_t == K_TT_OP and g.tk_k == 40:
            sb_error_default()
        if g.sb_type == K_TY_STR and g.tk_t != K_TT_STR:
            sb_error_default()
        g.sb_default_tokens = g.sb_default_tokens + 1
    if g.sb_default_tokens == 0:
        sb_error_default()
    if g.sb_type == K_TY_STR and g.sb_default_tokens != 1:
        sb_error_default()
    g.sb_default_count = g.sb_default_count + 1
    g.sb_default = g.sb_default_count
    g.sb_default_text[g.sb_default] = g.lx_l[g.sb_default_start - 1:g.sb_default_end - 1]


def sb_as():
    """SB.AS. An optional AS type after the name g.sm_n, whose type mark is g.sb_type. Out:
    g.sb_type, g.sb_signed, 1 for a signed type, g.sb_enum, the ENUM's record for AS
    ENUM.name, else 0, and g.sb_sig, the signature's record for a pointer, else 0."""
    g.sb_signed = 0
    g.sb_enum = 0
    g.sb_sig = 0
    if g.tk_t != K_TT_NAME:
        return
    if g.tk_s != "AS":
        return
    if g.sb_type != 0:
        er_stop("A MARK AND AS")
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NAME:
        er_syntax()
    g.nm_scope = g.nm_current
    uxc_name.nm_type_name()
    g.nm_scope = 0
    g.sb_type = g.nm_type_code
    g.sb_signed = g.nm_type_signed
    if g.sb_type == 0:
        er_syntax()
    g.sb_enum = g.nm_type_enum
    g.sb_sig = g.nm_type_sig
    if g.sb_enum != 0:
        g.sy_r = g.sb_enum
        uxc_sym.sy_get()
        g.sy_flags = g.sy_flags | K_SY_ENUM_PARAMETER
        uxc_sym.sy_set()
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
    g.jp_base = g.cb_n
    g.sy_r = g.sb_current
    uxc_sym.sy_get()
    g.sy_val = g.cb_n
    g.sy_flags = 1 + (g.sy_flags & (K_SY_SIGNED + K_SY_LIVE))
    # A SUB inside #KEEP ... #ENDKEEP is kept (UXC-DEAD.BL).
    if g.dd_region_line != 0 and (g.sy_flags & K_SY_LIVE) == 0:
        g.sy_flags = g.sy_flags + K_SY_LIVE
    uxc_sym.sy_set()
    uxc_ramreg.rg_sub()
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
    g.sy_end = g.cb_n
    uxc_sym.sy_end_set()
    g.jp_base = g.cb_n
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
        uxc_ramreg.rg_pin_from()
        uxc_str.sg_return_empty()
        uxc_ramreg.rg_pin_to(0)
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
        uxc_ramreg.rg_pin_from()
        uxc_str.sg_tos()
        uxc_ramreg.rg_pin_to(0)
    g.sb_has_value = 1
    emit(T.T_RTS)


# Calls

def sb_call_keyword():
    """SB.CALL.KEYWORD. CALL name ( args ), or CALL pointer WITH ( args ), with the token at
    CALL."""
    g.sb_pointer_at = g.lx_p
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NAME:
        er_syntax()
    g.sb_called_name = g.tk_s
    g.sm_n = g.sb_called_name
    uxc_name.nm_find()
    if g.sy_kind == K_SK_VAR or g.sy_kind == K_SK_ARRAY:
        sb_pointer_find()
        sb_call()
        return
    g.sb_pointer_at = 0
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
    sb_function_result()


def sb_function_result():
    """SB.FUNCTION.RESULT. The result of the call just made, of type g.sb_call_type, goes on
    the value stack."""
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
    when an argument calls a SUB or FUNCTION (sb_look_ahead), each argument but the last is
    pushed, and the pushes are popped into the parameters just before the JSR.

    An argument is an expression, and it can hold a call, so sb_call runs inside itself.
    What it keeps across an argument is in the g.sb_call_* arrays, one entry per depth."""
    if g.sb_called_record == g.sb_current:
        er_stop("A SUB CANNOT CALL ITSELF")
    sb_edge()
    sb_nest()
    g.sy_r = g.sb_called_record
    uxc_sym.sy_get()
    d = g.sb_depth
    g.sb_call_at[d] = g.sb_pointer_at
    g.sb_pointer_at = 0
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
            sb_call_argument()
            if g.tk_t != K_TT_OP:
                er_syntax()
            if g.tk_k == 41:
                break
            if g.tk_k != 44:
                er_syntax()
            uxc_lex.lx_next()
    while g.sb_call_argument[d] < g.sb_call_parameters[d]:
        g.sb_call_argument[d] = g.sb_call_argument[d] + 1
        sb_call_default()
    sb_call_pop()
    if g.sb_call_at[d] != 0:
        sb_pointer_load()
        emit(T.T_ICALL)
    else:
        g.sl_s[0] = K_SEC_LABEL
        g.sl_v[0] = g.sb_call_record[d]
        emit(T.T_JSR)
    g.sb_call_signed = g.sb_call_result[d] // 256
    g.sb_call_type = g.sb_call_result[d] - 256 * g.sb_call_signed
    sb_unnest()
    uxc_lex.lx_next()


def sb_call_argument():
    """SB.CALL.ARGUMENT. Argument g.sb_call_argument of the call at g.sb_depth, with the token
    at its start, into its parameter. The token is left after it. In a default, a number must
    be a constant."""
    d = g.sb_depth
    g.sy_r = g.sb_call_record[d] + g.sb_call_argument[d]
    sb_sig_of()
    g.sb_call_sig[d] = g.sb_sig
    g.sy_r = g.sb_call_record[d] + g.sb_call_argument[d]
    g.sb_field = K_SY_ENUM_TYPE
    sb_field_get()
    g.sb_call_enum[d] = g.sb_word - g.sb_sig
    g.ex_op_base = g.ex_on
    g.ex_cm = 0
    g.ex_const_record = 0
    g.sb_call_pin[d] = g.cb_n
    uxc_expr.ex_expr()
    g.sy_r = g.sb_call_record[d] + g.sb_call_argument[d]
    uxc_sym.sy_get()
    g.sb_parameter_type = g.sy_type
    g.sb_parameter_address = g.sy_val
    g.sg_read_only = g.sy_flags & K_SY_READ_ONLY
    if g.sb_filling != 0 and g.sb_parameter_type != K_TY_STR and g.ex_vk[g.ex_vn - 1] != K_EK_CONST:
        sb_error_default()
    g.sb_word = g.sb_call_enum[d]
    if g.sb_word != 0:
        sb_call_member()
    if g.sb_parameter_type == K_TY_BYTE:
        uxc_expr.ex_tob()
    if g.sb_parameter_type == K_TY_WORD:
        uxc_expr.ex_tow()
    if g.sb_parameter_type == K_TY_LONG:
        uxc_expr.ex_tol()
    if g.sb_parameter_type == K_TY_STR:
        uxc_ramreg.rg_forward(g.sb_call_record[d])
        uxc_str.sg_pass()
        g.rg_pin_from = g.sb_call_pin[d]
        uxc_ramreg.rg_pin_to(g.sb_call_record[d])
    sb_call_pass()


def sb_call_default():
    """SB.CALL.DEFAULT. Argument g.sb_call_argument, left out of the call, is its parameter's
    default. The default's text is read in place of the line, with names looked for from the
    namespace of the SUB called. The token is left at the call's ) again.
    Trap: one saved line serves, as a default holds no call."""
    d = g.sb_depth
    g.sy_r = g.sb_call_record[d] + g.sb_call_argument[d]
    uxc_sym.sy_get()
    if g.sy_np == 0:
        sb_error_arguments()
    g.sb_default = g.sy_np
    g.sb_parameter_name = ""
    for g.sb_i in range(g.ram[g.sy_ad + 7]):
        g.sb_parameter_name = g.sb_parameter_name + chr(g.ram[g.sy_ad + 8 + g.sb_i])
    g.sy_r = g.sb_call_record[d]
    uxc_sym.sy_get()
    g.sb_filling_line = g.lx_l
    g.sb_filling_position = g.lx_p
    g.sb_filling_length = g.lx_n
    g.sb_filling_scope = g.nm_scope
    g.nm_scope = g.sy_owner
    g.lx_l = g.sb_default_text[g.sb_default]
    g.lx_p = 1
    g.lx_n = len(g.lx_l)
    g.sb_filling = 1
    uxc_lex.lx_next()
    sb_call_argument()
    if g.tk_t != K_TT_EOL:
        sb_error_default()
    g.sb_filling = 0
    g.nm_scope = g.sb_filling_scope
    g.lx_l = g.sb_filling_line
    g.lx_p = g.sb_filling_position
    g.lx_n = g.sb_filling_length
    g.tk_t = K_TT_OP
    g.tk_k = 41
    g.tk_s = ""
    g.tk_m = 0
    g.tk_v = 0


def sb_call_member():
    """SB.CALL.MEMBER. A constant argument to a parameter of ENUM g.sb_word must be one of
    its members: g.ex_const_record, the last CONST the expression read, owned by that ENUM
    and of the value the expression gave. A variable passes unchecked."""
    g.ex_i = g.ex_vn - 1
    if g.ex_vk[g.ex_i] != K_EK_CONST:
        return
    if g.ex_const_record != 0:
        g.sy_r = g.ex_const_record
        uxc_sym.sy_get()
        if g.sy_owner == g.sb_word and g.sy_val == g.ex_vv[g.ex_i]:
            return
    g.sy_r = g.sb_word
    uxc_sym.sy_at()
    g.sb_member_enum = ""
    for g.sb_member_i in range(g.ram[g.sy_ad + 7]):
        g.sb_member_enum = g.sb_member_enum + chr(g.ram[g.sy_ad + 8 + g.sb_member_i])
    er_stop("NOT A MEMBER OF " + g.sb_member_enum)


def sb_nest():
    """SB.NEST. One level deeper into the arguments of a call or a function. The operator
    stack, the brackets and the condition flag of the expression around are kept."""
    if g.sb_depth >= K_SB_DEPTH:
        er_stop("CALLS NESTED TOO DEEP")
    g.sb_depth = g.sb_depth + 1
    g.sb_call_enum[g.sb_depth] = 0
    g.sb_call_sig[g.sb_depth] = 0
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
    """SB.LOOK.AHEAD. g.sb_nested = 1 when the arguments, up to the call's own ), call a SUB or
    FUNCTION: a name before a ( that is a SUB's, or CALL. An array or a built-in function
    before a ( is no call. The token is at the call's ( and is put back after, with g.lx_p.
    Clobbers g.sy_* and g.nm_*."""
    g.sb_saved_position = g.lx_p
    g.sb_saved_name = g.sm_n
    g.sb_nested = 0
    g.sb_look_depth = 0
    g.sb_look_name = ""
    while g.sb_nested == 0:
        uxc_lex.lx_next()
        if g.tk_t == K_TT_EOL:
            break
        if g.tk_t == K_TT_OP and g.tk_k == 41:
            if g.sb_look_depth == 0:
                break
            g.sb_look_depth = g.sb_look_depth - 1
        if g.tk_t == K_TT_OP and g.tk_k == 40:
            g.sb_look_depth = g.sb_look_depth + 1
            if g.sb_look_name != "":
                g.sm_n = g.sb_look_name
                g.nm_find_quiet = 1
                uxc_name.nm_find()
                g.nm_find_quiet = 0
                if g.sy_r != 0 and g.sy_kind == K_SK_SUB:
                    g.sb_nested = 1
        g.sb_look_name = ""
        if g.tk_t == K_TT_NAME:
            g.sb_look_name = g.tk_s
            if g.tk_s == "CALL":
                g.sb_nested = 1
    g.sm_n = g.sb_saved_name
    g.lx_p = g.sb_saved_position
    g.tk_t = K_TT_OP
    g.tk_k = 40
    g.tk_s = ""
    g.tk_m = 0
    g.tk_v = 0


# Pointers

def sb_declare():
    """SB.DECLARE. DECLARE SUB or DECLARE FUNCTION in the second pass. The first pass made the
    signature, so the rest of the line is skipped."""
    if g.sb_current != 0:
        er_stop("DECLARE IN A SUB")
    while g.tk_t != K_TT_EOL:
        uxc_lex.lx_next()


def sb_sig_of():
    """SB.SIG.OF. In g.sy_r, a variable, an array or a parameter. Out: g.sb_sig, the record of
    its signature when it is a pointer, else 0. Clobbers g.sy_*."""
    g.sb_field = K_SY_SIGNATURE
    sb_field_get()
    g.sb_sig = g.sb_word
    if g.sb_sig == 0:
        return
    g.sy_r = g.sb_sig
    uxc_sym.sy_get()
    if g.sy_kind != K_SK_SIG:
        g.sb_sig = 0


def sb_at_sub():
    """SB.AT.SUB. @name of a SUB or FUNCTION, with its record in g.sy_*, where a pointer of
    the signature g.sb_call_sig(g.sb_depth) is wanted: the address of its code. The SUB must
    match the signature. A K_SK_TARGET record ties the two for SB.POOLS."""
    g.sb_target = g.sy_r
    g.sb_sig = g.sb_call_sig[g.sb_depth]
    if g.sb_sig == 0:
        er_stop("NO POINTER TYPE FOR @" + g.sm_n)
    sb_match()
    g.sy_name = "%T" + uxc_str.basic_str(g.sb_target)
    g.sy_ow = g.sb_sig
    uxc_sym.sy_find()
    if g.sy_r == 0:
        g.sy_kind = K_SK_TARGET
        g.sy_type = 0
        g.sy_val = g.sb_target
        g.sy_flags = 0
        g.sy_cnt = g.lx_no
        uxc_sym.sy_add()
    g.ex_k = K_EK_ADDR
    g.ex_s = K_SEC_LABEL
    g.ex_v = g.sb_target
    g.ex_ty = K_TY_WORD
    uxc_expr.ex_pushv()
    uxc_lex.lx_next()


def sb_match():
    """SB.MATCH. SUB g.sb_target matches signature g.sb_sig: the same result type, and
    parameters of the same number, types, signs, AS CONST and ENUM or signature. The names
    and the defaults may differ."""
    g.sy_r = g.sb_sig
    uxc_sym.sy_get()
    g.sb_match_type = g.sy_type
    g.sb_match_flags = g.sy_flags & K_SY_SIGNED
    g.sb_match_count = g.sy_np
    g.sy_r = g.sb_target
    uxc_sym.sy_get()
    if g.sy_type != g.sb_match_type or (g.sy_flags & K_SY_SIGNED) != g.sb_match_flags or \
            g.sy_np != g.sb_match_count:
        sb_error_match()
    for g.sb_i in range(1, g.sb_match_count + 1):
        g.sy_r = g.sb_sig + g.sb_i
        uxc_sym.sy_get()
        g.sb_match_type = g.sy_type
        g.sb_match_flags = g.sy_flags & (K_SY_SIGNED + K_SY_READ_ONLY)
        g.sb_field = K_SY_ENUM_TYPE
        sb_field_get()
        g.sb_match_word = g.sb_word
        g.sy_r = g.sb_target + g.sb_i
        uxc_sym.sy_get()
        sb_field_get()
        if g.sy_type != g.sb_match_type or \
                (g.sy_flags & (K_SY_SIGNED + K_SY_READ_ONLY)) != g.sb_match_flags or \
                g.sb_word != g.sb_match_word:
            sb_error_match()


def sb_pointer_find():
    """SB.POINTER.FIND. CALL pointer WITH ( args ), with the variable or array of the pointer
    in g.sy_*, and the token at its name. g.sb_called_record is its signature. The token is
    left at the ( after WITH. The pointer is compiled after the arguments, by sb_pointer_load,
    so it may hold no call."""
    sb_sig_of()
    if g.sb_sig == 0:
        er_stop("NOT A POINTER: " + g.sb_called_name)
    g.sb_called_record = g.sb_sig
    g.sb_look_depth = 0
    g.sb_look_name = ""
    while True:
        uxc_lex.lx_next()
        if g.tk_t == K_TT_EOL:
            er_stop("MISSING WITH")
        if g.tk_t == K_TT_OP and g.tk_k == 41:
            g.sb_look_depth = g.sb_look_depth - 1
        if g.tk_t == K_TT_OP and g.tk_k == 40:
            g.sb_look_depth = g.sb_look_depth + 1
            if g.sb_look_name != "":
                g.sm_n = g.sb_look_name
                g.nm_find_quiet = 1
                uxc_name.nm_find()
                g.nm_find_quiet = 0
                if g.sy_r != 0 and g.sy_kind == K_SK_SUB:
                    sb_error_pointer_call()
        g.sb_look_name = ""
        if g.tk_t == K_TT_NAME:
            if g.tk_s == "WITH" and g.sb_look_depth == 0:
                break
            if g.tk_s == "CALL":
                sb_error_pointer_call()
            g.sb_look_name = g.tk_s
    uxc_lex.lx_next()
    if g.tk_t != K_TT_OP or g.tk_k != 40:
        sb_error_missing_open()


def sb_pointer_load():
    """SB.POINTER.LOAD. The pointer of the call at g.sb_depth into A/Y, with the token at the
    call's ). Its text, from g.sb_call_at(g.sb_depth) to WITH, is read again; the token is
    left at the ) again, as sb_call_default leaves it."""
    g.sb_pointer_end = g.lx_p
    g.lx_p = g.sb_call_at[g.sb_depth]
    uxc_lex.lx_next()
    g.ex_op_base = g.ex_on
    g.ex_cm = 0
    uxc_expr.ex_expr()
    uxc_expr.ex_tow()
    g.lx_p = g.sb_pointer_end
    g.tk_t = K_TT_OP
    g.tk_k = 41
    g.tk_s = ""
    g.tk_m = 0
    g.tk_v = 0


def sb_pointer_function():
    """SB.POINTER.FUNCTION. CALL pointer WITH ( args ) in an expression, with the token at
    CALL. The pointer's signature is a FUNCTION. The result is pushed as sb_function pushes
    it."""
    g.sb_pointer_at = g.lx_p
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NAME:
        er_syntax()
    g.sb_called_name = g.tk_s
    g.sm_n = g.sb_called_name
    uxc_name.nm_find()
    if g.sy_kind != K_SK_VAR and g.sy_kind != K_SK_ARRAY:
        er_stop("NOT A POINTER: " + g.sb_called_name)
    sb_pointer_find()
    g.sy_r = g.sb_called_record
    uxc_sym.sy_get()
    if g.sy_type == 0:
        sb_error_no_value()
    g.ex_fb = g.ex_vn
    uxc_expr.ex_flush()
    sb_call()
    sb_function_result()


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
    A signature is placed as a SUB is. A call through a pointer is a call of its signature,
    and each SUB whose @ was taken for a signature is at the signature's level, so its
    parameters are where the caller stored them.
    WARNING: two SUBs that call each other have no level; the link stops with an error."""
    g.sb_subs = 0
    g.sb_top_level = 0
    g.sb_main_need = 0
    g.sb_max_loaded = 0
    for g.sb_record in range(1, g.sy_n + 1):
        g.sy_r = g.sb_record
        uxc_sym.sy_get()
        if g.sy_kind == K_SK_SUB or g.sy_kind == K_SK_SIG:
            sb_pools_start()
    g.sb_passes = 0
    while True:
        g.sb_changed = 0
        for g.sb_record in range(1, g.sy_n + 1):
            g.sy_r = g.sb_record
            uxc_sym.sy_get()
            if g.sy_kind == K_SK_CALL:
                sb_pools_raise()
            if g.sy_kind == K_SK_TARGET:
                sb_pools_tie()
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


def sb_pools_tie():
    """SB.POOLS.TIE. With a K_SK_TARGET record read: the SUB and its signature are at the
    higher of their two levels. A SUB left out is not tied."""
    g.sb_tie_sig = g.sy_owner
    g.sb_call_line = g.sy_cnt
    g.sy_r = g.sy_val
    uxc_sym.sy_get()
    if g.sy_kind != K_SK_SUB:
        return
    g.sb_tie_target = g.sy_r
    sb_level_of()
    g.sb_caller_level = g.sb_level
    g.sy_r = g.sb_tie_sig
    sb_level_of()
    if g.sb_level == g.sb_caller_level:
        return
    if g.sb_level < g.sb_caller_level:
        g.sb_level = g.sb_caller_level
    else:
        g.sy_r = g.sb_tie_target
        uxc_sym.sy_at()
    g.ram[g.sy_ad + K_SY_LEVEL] = g.sb_level
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
        if g.sy_kind == K_SK_SUB or g.sy_kind == K_SK_SIG:
            sb_pools_measure()
    g.sb_pool_at = g.bs_n + g.sb_pool_frame
    for g.sb_record in range(1, g.sy_n + 1):
        g.sy_r = g.sb_record
        uxc_sym.sy_get()
        if g.sy_kind == K_SK_SUB or g.sy_kind == K_SK_SIG:
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


def sb_error_default():
    er_stop("BAD DEFAULT: " + g.sb_parameter_name)


def sb_error_match():
    g.sy_r = g.sb_sig
    uxc_sym.sy_at()
    g.sb_match_name = ""
    for g.sb_i in range(g.ram[g.sy_ad + 7]):
        g.sb_match_name = g.sb_match_name + chr(g.ram[g.sy_ad + 8 + g.sb_i])
    er_stop(g.sm_n + " DOES NOT MATCH " + g.sb_match_name)


def sb_error_pointer_call():
    er_stop("A CALL IN A POINTER")


def sb_error_each_other():
    g.lx_no = g.sb_each_other_line
    g.lx_l = ""
    er_stop("SUBS CALL EACH OTHER")
