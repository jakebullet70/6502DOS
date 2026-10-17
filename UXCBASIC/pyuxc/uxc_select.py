"""SELECT CASE: a chain of compares on one value.

    SELECT CASE v              v is a number or a string
    CASE 1, 3 TO 5, IS > 9     tests; the body runs when any test is true
    CASE ELSE                  last; the body runs when no CASE before it ran
    END SELECT                 or ENDSELECT

A test is a value (v = value), a range (low TO high, both ends in), or IS with a compare
operator and a value. A value is any expression of the selector's kind. Only the first CASE
that matches runs.

The selector: a variable, or an address such as a string literal, is read again at each test. Any other number is
stored once in a hidden variable of its type. Any other string is an error.
Trap: a function in a test that changes a variable selector changes the tests after it.

The code of a CASE, with fail the next CASE and match its body:

    [JMP out]                  the body before, if any and if it does not end in a jump
    the fails of the CASE before land here
    a test but the last:       value compare, true to match
                               a range: low > v to next, high >= v to match, next:
    the last test:             value compare, false to fail
                               a range: low > v to fail, high >= v false to fail
    match:
    body

A test compares the value, on the left, with the selector, so its operator is turned round:
v < 5 is 5 > v.

The entry on the nesting stack: g.ns_fl[] the fails, g.ns_ex[] the jumps out, g.ns_p[] the
count of CASEs, g.ns_el[] 1 after CASE ELSE. The selector's expression entry is g.ns_sk[]
kind, g.ns_vs[] section, g.ns_va[] value, g.ns_vt[] type and g.ns_sg[] sign.

    sl_select() sl_case() sl_end()    the statements
"""

from uxc_defs import K_EK_ADDR, K_EK_MEM, K_EO_EQ, K_EO_GE, K_EO_GT, K_EO_LE, K_EO_LT, \
    K_EO_NE, K_JP_LIST, K_NS_SEL, K_OP_GE, K_OP_LE, K_OP_NE, K_SEC_TEMP, K_SEC_VAR, K_TT_EOL, \
    K_TT_NAME, K_TT_OP, K_TY_BYTE, K_TY_LONG, K_TY_STR, K_TY_WORD
import uxc_cond
import uxc_expr
import uxc_flow
import uxc_lex
import uxc_stmt
import uxc_sub
import uxc_tpl as T
from uxc_state import er_stop, er_syntax, g


def sl_select():
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NAME or g.tk_s != "CASE":
        er_syntax()
    uxc_lex.lx_next()
    uxc_expr.ex_expr()
    g.ex_i = g.ex_vn - 1
    g.sc_k = g.ex_vk[g.ex_i]
    g.sc_s = g.ex_vs[g.ex_i]
    g.sc_v = g.ex_vv[g.ex_i]
    g.sc_t = g.ex_vt[g.ex_i]
    g.sc_g = g.ex_vg[g.ex_i]
    if (g.sc_k == K_EK_MEM or g.sc_k == K_EK_ADDR) and g.sc_s != K_SEC_TEMP:
        g.ex_vn = g.ex_vn - 1
    else:
        sl_hidden()
    g.ns_kn = K_NS_SEL
    uxc_flow.ns_push()
    g.ns_sk[g.ns_d] = g.sc_k
    g.ns_vs[g.ns_d] = g.sc_s
    g.ns_va[g.ns_d] = g.sc_v
    g.ns_vt[g.ns_d] = g.sc_t
    g.ns_sg[g.ns_d] = g.sc_g
    g.cs_wait = 1


def sl_hidden():
    """The selector, a number on top of the expression stack, into a new hidden
    variable of its type; g.sc_* then name that variable."""
    if g.sc_t == K_TY_STR:
        er_stop("SELECT CASE NEEDS A STRING VARIABLE")
    if g.sc_t != K_TY_BYTE and g.sc_t != K_TY_LONG:
        g.sc_t = K_TY_WORD
    g.sb_place_size = 2
    if g.sc_t == K_TY_BYTE:
        g.sb_place_size = 1
    if g.sc_t == K_TY_LONG:
        g.sb_place_size = 4
    uxc_sub.sb_place_variable()
    g.sm_ty = g.sc_t
    g.sm_sec = K_SEC_VAR
    g.sm_ad = g.sb_place
    uxc_stmt.sm_store()
    g.sc_k = K_EK_MEM
    g.sc_s = K_SEC_VAR
    g.sc_v = g.sb_place


def sl_case():
    """CASE in a SELECT CASE: cs_case sends it here."""
    g.sc_d = g.ns_d
    if g.ns_el[g.sc_d] != 0:
        er_stop("CASE AFTER CASE ELSE")
    g.cs_wait = 0
    g.ct_i = g.sc_d
    uxc_stmt.sm_unreached()
    if g.ns_p[g.sc_d] != 0 and g.sm_skip == 0:
        g.jp_k = K_JP_LIST
        g.jp_h = g.ns_ex[g.sc_d]
        g.jp_b = T.T_BRA
        uxc_cond.jp_br()
        g.ns_ex[g.sc_d] = g.jp_h
    g.ns_p[g.sc_d] = g.ns_p[g.sc_d] + 1
    g.jp_l = g.ns_fl[g.sc_d]
    uxc_cond.jp_here()
    g.ns_fl[g.sc_d] = 0
    uxc_lex.lx_next()
    if g.tk_t == K_TT_NAME and g.tk_s == "ELSE":
        g.ns_el[g.sc_d] = 1
        uxc_lex.lx_next()
        return
    g.sc_match = 0
    while True:
        sl_test()
        if not (g.tk_t == K_TT_OP and g.tk_k == 44):
            break
        uxc_lex.lx_next()
    g.jp_l = g.sc_match
    uxc_cond.jp_here()


def sl_test():
    """One test. It jumps to g.sc_match when true; the last test of the CASE jumps to
    the fails when false."""
    g.sc_o = K_EO_EQ
    if g.tk_t == K_TT_NAME and g.tk_s == "IS":
        uxc_lex.lx_next()
        sl_operator()
        uxc_lex.lx_next()
    uxc_expr.ex_expr()
    if g.tk_t == K_TT_NAME and g.tk_s == "TO":
        if g.sc_o != K_EO_EQ:
            er_syntax()
        g.sc_o = K_EO_GT
        sl_compare()
        g.jp_k = K_JP_LIST
        g.jp_h = 0
        uxc_cond.cn_jt()
        g.sc_next = g.jp_h
        uxc_lex.lx_next()
        uxc_expr.ex_expr()
        g.sc_o = K_EO_GE
        sl_compare()
        sl_jump()
        if g.sc_last == 1:
            g.jp_k = K_JP_LIST
            g.jp_h = g.ns_fl[g.sc_d]
            g.jp_l = g.sc_next
            uxc_cond.jp_send()
            g.ns_fl[g.sc_d] = g.jp_h
        else:
            g.jp_l = g.sc_next
            uxc_cond.jp_here()
        return
    sl_turn()
    sl_compare()
    sl_jump()


def sl_operator():
    """The compare operator after IS, in g.sc_o."""
    g.sc_o = 0
    if g.tk_t == K_TT_OP:
        if g.tk_k == 61:
            g.sc_o = K_EO_EQ
        if g.tk_k == 60:
            g.sc_o = K_EO_LT
        if g.tk_k == 62:
            g.sc_o = K_EO_GT
        if g.tk_k == K_OP_NE:
            g.sc_o = K_EO_NE
        if g.tk_k == K_OP_LE:
            g.sc_o = K_EO_LE
        if g.tk_k == K_OP_GE:
            g.sc_o = K_EO_GE
    if g.sc_o == 0:
        er_syntax()


def sl_turn():
    """g.sc_o for the selector on the left becomes the operator for the value on the
    left."""
    if g.sc_o == K_EO_LT:
        g.sc_o = K_EO_GT
    elif g.sc_o == K_EO_GT:
        g.sc_o = K_EO_LT
    elif g.sc_o == K_EO_LE:
        g.sc_o = K_EO_GE
    elif g.sc_o == K_EO_GE:
        g.sc_o = K_EO_LE


def sl_compare():
    """The value on top of the expression stack, operator g.sc_o, the selector. The
    compare is then the top entry. g.sc_last is 1 when the token ends the CASE."""
    g.ex_k = g.ns_sk[g.sc_d]
    g.ex_s = g.ns_vs[g.sc_d]
    g.ex_v = g.ns_va[g.sc_d]
    g.ex_ty = g.ns_vt[g.sc_d]
    g.ex_sg = g.ns_sg[g.sc_d]
    uxc_expr.ex_pushv()
    g.ex_on = g.ex_op_base
    g.ex_o = g.sc_o
    uxc_expr.ex_pusho()
    uxc_expr.ex_reduce()
    g.sc_last = 0
    if g.tk_t == K_TT_EOL:
        g.sc_last = 1


def sl_jump():
    """The compare on top: a test but the last jumps to the body when true, the last
    jumps to the fails when false."""
    g.jp_k = K_JP_LIST
    if g.sc_last == 1:
        g.jp_h = g.ns_fl[g.sc_d]
        uxc_cond.cn_jf()
        g.ns_fl[g.sc_d] = g.jp_h
    else:
        g.jp_h = g.sc_match
        uxc_cond.cn_jt()
        g.sc_match = g.jp_h


def sl_end():
    """END SELECT, or ENDSELECT: the token is SELECT or ENDSELECT."""
    g.ct_w = "END SELECT WITHOUT SELECT"
    g.ns_kn = K_NS_SEL
    uxc_flow.ns_topk()
    g.cs_wait = 0
    g.jp_l = g.ns_fl[g.ct_i]
    uxc_cond.jp_here()
    g.jp_l = g.ns_ex[g.ct_i]
    uxc_cond.jp_here()
    g.ns_d = g.ns_d - 1
    uxc_lex.lx_next()
