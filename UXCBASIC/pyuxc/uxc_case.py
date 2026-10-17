"""UXC-CASE.BL: ON CASE, a jump table on a BYTE.

    ON CASE b          b is a BYTE
    CASE 1, 2, 5       constants from 0 to 255, each in one CASE only
    CASE ELSE          last; a value with no CASE comes here
    END CASE           or ENDCASE

The code, with min and max the lowest and the highest value of any CASE:

    b into A : JMP dispatch
    body : JMP out                 for each CASE, and CASE ELSE; a body before another CASE
                                   that ends in a jump has no JMP out
    low: the low byte of the target of each value from min to max
    high: the high bytes
    dispatch: [SBC min] [CMP count : BCS default] T_CASE_JMP low, high
    out:

The default is the CASE ELSE body, or else the last body's JMP out. A value from min to max
with no CASE goes to the default too. The code never moves, so a table entry is the address
g.lk_org + offset, written with no fixup.

The entry on the nesting stack: g.ns_fl[] is the jump to the dispatch, g.ns_ex[] the jumps
out, g.ns_p[] the count of CASEs, g.ns_el[] 1 after CASE ELSE and g.ns_top[] its body,
g.ns_va[] and g.ns_lv[] the lowest and the highest value so far. The targets are words in
g.cs_bank at g.cs_base, 0 for none.

    cs_on() cs_case() cs_end()    the statements
    cs_before()                   the first statement after ON CASE must be a CASE
"""

from uxc_code import cb_add, cs_clear, cs_get, cs_put, emit
from uxc_defs import K_CS_SIZE, K_EK_CONST, K_JP_LIST, K_NS_CASE, K_NS_SEL, K_SEC_CODE, K_SEC_CONST, \
    K_TT_NAME, K_TT_OP, K_TY_BYTE
import uxc_cond
import uxc_expr
import uxc_flow
import uxc_lex
import uxc_select
import uxc_stmt
import uxc_tpl as T
from uxc_state import er_stop, er_syntax, g


def cs_on():
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NAME or g.tk_s != "CASE":
        er_syntax()
    uxc_lex.lx_next()
    uxc_expr.ex_expr()
    g.ex_i = g.ex_vn - 1
    if g.ex_vt[g.ex_i] != 0 and g.ex_vt[g.ex_i] != K_TY_BYTE:
        er_stop("ON CASE NEEDS A BYTE")
    uxc_expr.ex_tob()
    g.ns_kn = K_NS_CASE
    uxc_flow.ns_push()
    g.ct_i = g.ns_d
    g.jp_k = K_JP_LIST
    g.jp_h = 0
    g.jp_b = T.T_BRA
    uxc_cond.jp_br()
    g.ns_fl[g.ct_i] = g.jp_h
    g.ns_va[g.ct_i] = 256
    g.ns_lv[g.ct_i] = -1
    g.cs_at = (g.ct_i - 1) * K_CS_SIZE
    cs_clear()
    g.cs_wait = 1


def cs_before():
    if g.sm_w == "CASE" or g.sm_w == "END" or g.sm_w == "ENDCASE" or g.sm_w == "ENDSELECT":
        return
    er_stop("STATEMENT BEFORE CASE")


def cs_case():
    if g.ns_d != 0 and g.ns_k[g.ns_d] == K_NS_SEL:
        uxc_select.sl_case()
        return
    g.ct_w = "CASE WITHOUT ON CASE"
    g.ns_kn = K_NS_CASE
    uxc_flow.ns_topk()
    if g.ns_el[g.ct_i] != 0:
        er_stop("CASE AFTER CASE ELSE")
    uxc_stmt.sm_unreached()
    if g.sm_skip == 0:
        cs_body_end()
    g.cs_wait = 0
    g.ns_p[g.ct_i] = g.ns_p[g.ct_i] + 1
    uxc_lex.lx_next()
    if g.tk_t == K_TT_NAME and g.tk_s == "ELSE":
        g.ns_el[g.ct_i] = 1
        g.ns_top[g.ct_i] = g.cb_n
        uxc_lex.lx_next()
        return
    while True:
        uxc_expr.ex_expr()
        g.ct_i = g.ns_d
        g.ex_i = g.ex_vn - 1
        if g.ex_vk[g.ex_i] != K_EK_CONST:
            er_stop("CASE NEEDS A CONSTANT")
        g.cs_v = g.ex_vv[g.ex_i]
        g.ex_vn = g.ex_vn - 1
        if g.cs_v > 255:
            er_stop("CASE VALUE OVER 255")
        g.cs_at = (g.ct_i - 1) * K_CS_SIZE + g.cs_v * 2
        cs_get()
        if g.cs_w != 0:
            er_stop("CASE VALUE TWICE")
        g.cs_w = g.cb_n
        cs_put()
        if g.cs_v < g.ns_va[g.ct_i]:
            g.ns_va[g.ct_i] = g.cs_v
        if g.cs_v > g.ns_lv[g.ct_i]:
            g.ns_lv[g.ct_i] = g.cs_v
        if not (g.tk_t == K_TT_OP and g.tk_k == 44):
            return
        uxc_lex.lx_next()


def cs_body_end():
    """CS.BODY.END. The body before this point, if any, jumps out. g.cs_jo is that jump."""
    g.cs_wait = 0
    if g.ns_p[g.ct_i] == 0:
        return
    g.cs_jo = g.cb_n
    g.jp_k = K_JP_LIST
    g.jp_h = g.ns_ex[g.ct_i]
    g.jp_b = T.T_BRA
    uxc_cond.jp_br()
    g.ns_ex[g.ct_i] = g.jp_h


def cs_end():
    """CS.END. END CASE, or ENDCASE: the token is CASE or ENDCASE."""
    g.ct_w = "END CASE WITHOUT ON CASE"
    g.ns_kn = K_NS_CASE
    uxc_flow.ns_topk()
    cs_body_end()
    g.cs_default = g.cs_jo
    if g.ns_el[g.ct_i] != 0:
        g.cs_default = g.ns_top[g.ct_i]
    g.cs_base = (g.ct_i - 1) * K_CS_SIZE
    g.cs_min = g.ns_va[g.ct_i]
    g.cs_max = g.ns_lv[g.ct_i]
    if g.cs_max < 0:
        g.jp_l = g.ns_fl[g.ct_i]
        uxc_cond.jp_here()
        if g.ns_el[g.ct_i] != 0:
            g.jp_v = g.cs_default
            g.jp_b = T.T_BRA
            uxc_cond.jp_back()
    else:
        g.cs_low = g.cb_n
        g.cs_byte = 0
        cs_table()
        g.cs_high = g.cb_n
        g.cs_byte = 1
        cs_table()
        g.jp_l = g.ns_fl[g.ct_i]
        uxc_cond.jp_here()
        if g.cs_min > 0:
            g.sl_s[0] = K_SEC_CONST
            g.sl_v[0] = g.cs_min
            emit(T.T_SUBB_C)
        g.cs_count = g.cs_max - g.cs_min + 1
        if g.cs_count < 256:
            g.sl_s[0] = K_SEC_CONST
            g.sl_v[0] = g.cs_count
            emit(T.T_CMPB_C)
            g.jp_v = g.cs_default
            g.jp_b = T.T_BCS
            uxc_cond.jp_back()
        g.sl_s[0] = K_SEC_CODE
        g.sl_v[0] = g.cs_low
        g.sl_s[1] = K_SEC_CODE
        g.sl_v[1] = g.cs_high
        emit(T.T_CASE_JMP)
    g.jp_l = g.ns_ex[g.ct_i]
    uxc_cond.jp_here()
    g.ns_d = g.ns_d - 1
    uxc_lex.lx_next()


def cs_table():
    """CS.TABLE. The low bytes (g.cs_byte = 0) or the high bytes (1) of the addresses of the
    targets of the values from g.cs_min to g.cs_max."""
    for g.cs_v in range(g.cs_min, g.cs_max + 1):
        g.cs_at = g.cs_base + g.cs_v * 2
        cs_get()
        if g.cs_w == 0:
            g.cs_w = g.cs_default
        g.cs_w = g.lk_org + g.cs_w
        g.cs_wh = g.cs_w // 256
        g.cb_b = g.cs_w - g.cs_wh * 256
        if g.cs_byte != 0:
            g.cb_b = g.cs_wh
        cb_add()
