"""UXC-FLOW.BL: the statements IF, DO, REPEAT, EXIT, CONTINUE and GOTO. FOR is in uxc_for,
ON CASE in uxc_case. Their jumps and conditions are in uxc_cond.

Blocks (ns_*): the nesting stack holds each open IF and loop, g.ns_d deep, from 1. An entry
keeps its line for errors, its exit list g.ns_ex[] (EXIT, and the end of each IF branch), its
continue list g.ns_ct[], the false list of an IF in g.ns_fl[], and the top of a loop in
g.ns_top[].

    ns_push()     in g.ns_kn: a new entry of that kind, for the line being compiled
    ns_topk()     in g.ns_kn, g.ct_w: the innermost entry must be of kind g.ns_kn, out g.ct_i
    ns_find()     in g.ns_kn: out g.ns_i, the innermost entry of that kind, or of any loop
                  when g.ns_kn is 0; 0 when there is none
    ns_hidden()   out g.ns_hv: the hidden WORD of depth g.ns_d, a FOR limit or a REPEAT count
    ct_open()     at the end of the source, a block still open is an error

The statements: ct_if, ct_elseif, ct_else, ct_endif, ct_goto, ct_exit, ct_cont, ct_do,
ct_loop, ct_repeat, ct_endrep. Each starts at its first token and leaves the token after its
last one.
"""

from uxc_code import emit
from uxc_defs import K_EK_CONST, K_JP_CODE, K_JP_LABEL, K_JP_LIST, K_NS_CASE, K_NS_DO, \
    K_NS_FOR, K_NS_IFB, K_NS_IFL, K_NS_MAX, K_NS_REP, K_NS_SEL, K_SEC_CONST, K_SEC_VAR, K_SK_LABEL, \
    K_TT_EOL, K_TT_NAME, K_TY_BYTE, K_TY_WORD
import uxc_cond
import uxc_expr
import uxc_fold
import uxc_lex
import uxc_name
import uxc_stmt
import uxc_sub
import uxc_sym
import uxc_tpl as T
from uxc_state import er_stop, er_syntax, g


# The nesting stack

def ns_push():
    if g.ns_d >= K_NS_MAX:
        er_stop("NESTED TOO DEEP")
    g.ns_d = g.ns_d + 1
    g.ns_k[g.ns_d] = g.ns_kn
    g.ns_no[g.ns_d] = g.lx_no
    g.ns_l[g.ns_d] = g.lx_l
    g.ns_ex[g.ns_d] = 0
    g.ns_ct[g.ns_d] = 0
    g.ns_fl[g.ns_d] = 0
    g.ns_p[g.ns_d] = 0
    g.ns_el[g.ns_d] = 0


def ns_topk():
    if g.ns_d == 0:
        er_stop(g.ct_w)
    if g.ns_k[g.ns_d] != g.ns_kn:
        er_stop(g.ct_w)
    g.ct_i = g.ns_d


def ns_find():
    g.ns_i = g.ns_d
    while g.ns_i != 0:
        g.ns_ki = g.ns_k[g.ns_i]
        if g.ns_kn == 0 and g.ns_ki >= K_NS_DO:
            return
        if g.ns_ki == g.ns_kn:
            return
        g.ns_i = g.ns_i - 1


def ns_hidden():
    """NS.HIDDEN. Each depth has its own hidden word, made when first needed."""
    if g.hv_ad[g.ns_d] < 0:
        g.sb_place_size = 2
        uxc_sub.sb_place_variable()
        g.hv_ad[g.ns_d] = g.sb_place
    g.ns_hv = g.hv_ad[g.ns_d]


def ct_open():
    """CT.OPEN. The error is at the first line of the block."""
    if g.ns_d == 0:
        return
    g.lx_no = g.ns_no[g.ns_d]
    g.lx_l = g.ns_l[g.ns_d]
    g.ns_ki = g.ns_k[g.ns_d]
    if g.ns_ki == K_NS_IFB:
        g.er_m = "IF WITHOUT ENDIF"
    if g.ns_ki == K_NS_DO:
        g.er_m = "DO WITHOUT LOOP"
    if g.ns_ki == K_NS_FOR:
        g.er_m = "FOR WITHOUT NEXT"
    if g.ns_ki == K_NS_REP:
        g.er_m = "REPEAT WITHOUT END REPEAT"
    if g.ns_ki == K_NS_CASE:
        g.er_m = "ON CASE WITHOUT END CASE"
    if g.ns_ki == K_NS_SEL:
        g.er_m = "SELECT WITHOUT END SELECT"
    er_stop(g.er_m)


# IF

def ct_if():
    """CT.IF.
    IF c [THEN] ... [ELSEIF c [THEN]] ... [ELSE] ... ENDIF    a block
    IF c THEN statement                                       on one line, with no ELSE
    IF c THEN GOTO label, EXIT DO|FOR|REPEAT, or CONTINUE is one branch to the target, and
    IF c GOTO label is the same."""
    uxc_lex.lx_next()
    uxc_cond.cn_expr()
    g.ct_th = 0
    if g.tk_t == K_TT_NAME and g.tk_s == "THEN":
        g.ct_th = 1
        uxc_lex.lx_next()
    if g.tk_t == K_TT_EOL:
        g.jp_k = K_JP_LIST
        g.jp_h = 0
        uxc_cond.cn_jf()
        g.ns_kn = K_NS_IFB
        ns_push()
        g.ns_fl[g.ns_d] = g.jp_h
        return
    if g.tk_t != K_TT_NAME:
        er_syntax()
    if g.tk_s == "GOTO":
        uxc_lex.lx_next()
        ct_label()
        uxc_cond.cn_jt()
        return
    if g.ct_th == 0:
        er_syntax()
    if g.tk_s == "EXIT":
        ct_exit_to()
        uxc_cond.cn_jt()
        g.ns_ex[g.ct_i] = g.jp_h
        return
    if g.tk_s == "CONTINUE":
        ct_cont_to()
        uxc_cond.cn_jt()
        g.ns_ct[g.ct_i] = g.jp_h
        return
    g.jp_k = K_JP_LIST
    g.jp_h = 0
    uxc_cond.cn_jf()
    g.ns_kn = K_NS_IFL
    ns_push()
    g.ns_fl[g.ns_d] = g.jp_h
    uxc_stmt.sm_stmt()
    if g.ns_k[g.ns_d] != K_NS_IFL:
        er_stop("BLOCK STATEMENT AFTER THEN")
    if g.tk_t == K_TT_NAME and g.tk_s == "ELSE":
        er_stop("NO ELSE IN A ONE-LINE IF")
    g.jp_l = g.ns_fl[g.ns_d]
    uxc_cond.jp_here()
    g.ns_d = g.ns_d - 1


def ct_if_next():
    """CT.IF.NEXT. The branch before ELSEIF or ELSE is done: jump to the end, unless the
    branch ends in a jump, and the false jumps of its test come here."""
    g.ns_kn = K_NS_IFB
    ns_topk()
    if g.ns_el[g.ct_i] != 0:
        er_stop(g.sm_w + " AFTER ELSE")
    uxc_stmt.sm_unreached()
    if g.sm_skip == 0:
        g.jp_k = K_JP_LIST
        g.jp_h = g.ns_ex[g.ct_i]
        g.jp_b = T.T_BRA
        uxc_cond.jp_br()
        g.ns_ex[g.ct_i] = g.jp_h
    g.jp_l = g.ns_fl[g.ct_i]
    uxc_cond.jp_here()
    g.ns_fl[g.ct_i] = 0


def ct_elseif():
    g.ct_w = "ELSEIF WITHOUT IF"
    ct_if_next()
    uxc_lex.lx_next()
    uxc_cond.cn_expr()
    if g.tk_t == K_TT_NAME and g.tk_s == "THEN":
        uxc_lex.lx_next()
    if g.tk_t != K_TT_EOL:
        er_syntax()
    g.jp_k = K_JP_LIST
    g.jp_h = 0
    uxc_cond.cn_jf()
    g.ns_fl[g.ct_i] = g.jp_h


def ct_else():
    g.ct_w = "ELSE WITHOUT IF"
    ct_if_next()
    g.ns_el[g.ct_i] = 1
    uxc_lex.lx_next()


def ct_endif():
    """CT.ENDIF. ENDIF, or END IF: the token is ENDIF or IF."""
    g.ct_w = "ENDIF WITHOUT IF"
    g.ns_kn = K_NS_IFB
    ns_topk()
    g.jp_l = g.ns_fl[g.ct_i]
    uxc_cond.jp_here()
    g.jp_l = g.ns_ex[g.ct_i]
    uxc_cond.jp_here()
    g.ns_d = g.ns_d - 1
    uxc_lex.lx_next()


# GOTO, EXIT, CONTINUE

def ct_goto():
    uxc_lex.lx_next()
    ct_label()
    g.jp_b = T.T_BRA
    uxc_cond.jp_br()
    uxc_stmt.sm_jumped()


def ct_label():
    """CT.LABEL. The label named by the token is the target g.jp_*. A label not placed yet is
    added, and placed when its line comes."""
    if g.tk_t != K_TT_NAME or g.tk_m != 0:
        er_syntax()
    g.sm_n = g.tk_s
    uxc_name.nm_reserved()
    g.sy_name = g.sm_n
    g.sy_ow = g.sb_current
    uxc_sym.sy_find()
    if g.sy_r == 0:
        g.sy_kind = K_SK_LABEL
        g.sy_type = 0
        g.sy_val = 0
        g.sy_flags = 0
        uxc_sym.sy_add()
    else:
        uxc_sym.sy_get()
        if g.sy_kind != K_SK_LABEL:
            er_stop("NOT A LABEL: " + g.sm_n)
    g.jp_k = K_JP_LABEL
    g.jp_v = g.sy_r
    if (g.sy_flags & 1) != 0:
        g.jp_k = K_JP_CODE
        g.jp_v = g.sy_val
    uxc_lex.lx_next()


def ct_exit():
    ct_exit_to()
    g.jp_b = T.T_BRA
    uxc_cond.jp_br()
    g.ns_ex[g.ct_i] = g.jp_h
    uxc_stmt.sm_jumped()


def ct_exit_to():
    """CT.EXIT.TO. EXIT DO, EXIT FOR or EXIT REPEAT: the target is the exit list of that
    loop, entry g.ct_i."""
    uxc_lex.lx_next()
    g.ns_kn = -1
    if g.tk_t == K_TT_NAME:
        if g.tk_s == "DO":
            g.ns_kn = K_NS_DO
        if g.tk_s == "FOR":
            g.ns_kn = K_NS_FOR
        if g.tk_s == "REPEAT":
            g.ns_kn = K_NS_REP
    if g.ns_kn < 0:
        er_syntax()
    ns_find()
    if g.ns_i == 0:
        er_stop("EXIT " + g.tk_s + " WITHOUT " + g.tk_s)
    g.ct_i = g.ns_i
    g.jp_k = K_JP_LIST
    g.jp_h = g.ns_ex[g.ct_i]
    uxc_lex.lx_next()


def ct_cont():
    ct_cont_to()
    g.jp_b = T.T_BRA
    uxc_cond.jp_br()
    g.ns_ct[g.ct_i] = g.jp_h
    uxc_stmt.sm_jumped()


def ct_cont_to():
    """CT.CONT.TO. CONTINUE: the target is the continue list of the innermost loop, which
    comes to its test, or its step."""
    g.ns_kn = 0
    ns_find()
    if g.ns_i == 0:
        er_stop("CONTINUE WITHOUT A LOOP")
    g.ct_i = g.ns_i
    g.jp_k = K_JP_LIST
    g.jp_h = g.ns_ct[g.ct_i]
    uxc_lex.lx_next()


# DO ... LOOP
#
#   DO                          DO WHILE|UNTIL a
#   top: body                   JMP test
#   cont: [bottom test]         top: body
#         BRA top               cont: [bottom test, out when it fails]
#   out:                        test: top test, back to top when it holds
#                               out:
#
# A top test is compiled at the bottom. Its text is kept, and LOOP compiles it again from the
# DO line. DO compiles it once too, and throws the code away, so that an error in it is found
# on its own line.

def ct_do():
    g.ns_kn = K_NS_DO
    ns_push()
    g.ct_i = g.ns_d
    uxc_lex.lx_next()
    if g.tk_t == K_TT_NAME and (g.tk_s == "WHILE" or g.tk_s == "UNTIL"):
        g.ns_sn[g.ct_i] = 0
        if g.tk_s == "WHILE":
            g.ns_sn[g.ct_i] = 1
        g.jp_k = K_JP_LIST
        g.jp_h = 0
        g.jp_b = T.T_BRA
        uxc_cond.jp_br()
        g.ns_fl[g.ct_i] = g.jp_h
        g.ns_p[g.ct_i] = g.lx_p
        g.ct_cb = g.cb_n
        g.ct_fx = g.fx_n
        uxc_lex.lx_next()
        uxc_cond.cn_expr()
        g.jp_k = K_JP_LIST
        g.jp_h = 0
        uxc_cond.cn_jt()
        g.cb_n = g.ct_cb
        g.fx_n = g.ct_fx
    g.ns_top[g.ct_i] = g.cb_n


def ct_loop():
    g.ct_w = "LOOP WITHOUT DO"
    g.ns_kn = K_NS_DO
    ns_topk()
    g.jp_l = g.ns_ct[g.ct_i]
    uxc_cond.jp_here()
    uxc_lex.lx_next()
    g.ct_bt = 0
    if g.tk_t == K_TT_NAME and (g.tk_s == "WHILE" or g.tk_s == "UNTIL"):
        g.ct_sn = 0
        if g.tk_s == "WHILE":
            g.ct_sn = 1
        uxc_lex.lx_next()
        uxc_cond.cn_expr()
        if g.ns_p[g.ct_i] == 0:
            g.jp_k = K_JP_CODE
            g.jp_v = g.ns_top[g.ct_i]
            if g.ct_sn == 1:
                uxc_cond.cn_jt()
            if g.ct_sn == 0:
                uxc_cond.cn_jf()
        else:
            g.jp_k = K_JP_LIST
            g.jp_h = g.ns_ex[g.ct_i]
            if g.ct_sn == 1:
                uxc_cond.cn_jf()
            if g.ct_sn == 0:
                uxc_cond.cn_jt()
            g.ns_ex[g.ct_i] = g.jp_h
        g.ct_bt = 1
    if g.tk_t != K_TT_EOL:
        er_syntax()
    if g.ns_p[g.ct_i] > 0:
        g.jp_l = g.ns_fl[g.ct_i]
        uxc_cond.jp_here()
        g.ct_l = g.lx_l
        g.ct_no = g.lx_no
        g.ct_n = g.lx_n
        g.ct_p = g.lx_p
        g.lx_l = g.ns_l[g.ct_i]
        g.lx_no = g.ns_no[g.ct_i]
        g.lx_n = len(g.lx_l)
        g.lx_p = g.ns_p[g.ct_i]
        g.ex_vn = 0
        g.ex_sd = 0
        uxc_lex.lx_next()
        uxc_cond.cn_expr()
        g.jp_k = K_JP_CODE
        g.jp_v = g.ns_top[g.ct_i]
        if g.ns_sn[g.ct_i] == 1:
            uxc_cond.cn_jt()
        if g.ns_sn[g.ct_i] == 0:
            uxc_cond.cn_jf()
        g.lx_l = g.ct_l
        g.lx_no = g.ct_no
        g.lx_n = g.ct_n
        g.lx_p = g.ct_p
        g.tk_t = K_TT_EOL
    else:
        if g.ct_bt == 0:
            g.jp_v = g.ns_top[g.ct_i]
            g.jp_b = T.T_BRA
            uxc_cond.jp_back()
    g.jp_l = g.ns_ex[g.ct_i]
    uxc_cond.jp_here()
    g.ns_d = g.ns_d - 1


# REPEAT [n] ... END REPEAT
#
# The count goes into the hidden word of the depth, and counts down: a BYTE count is
# DEC c / BNE top. A WORD count is set by T_RPTW_SET and counts down a byte at a time. A count
# of 0 skips the body. With no count the loop runs until EXIT REPEAT.

def ct_repeat():
    g.ns_kn = K_NS_REP
    ns_push()
    g.ct_i = g.ns_d
    g.ns_vt[g.ct_i] = 0
    uxc_lex.lx_next()
    if g.tk_t != K_TT_EOL:
        rp_count()
    g.ns_top[g.ct_i] = g.cb_n


def rp_count():
    uxc_expr.ex_expr()
    ns_hidden()
    g.ns_va[g.ct_i] = g.ns_hv
    g.ex_i = g.ex_vn - 1
    if g.ex_vk[g.ex_i] == K_EK_CONST:
        uxc_fold.ex_const_word()
        g.rp_n = g.ex_vv[g.ex_i]
        g.ex_vn = g.ex_vn - 1
        if g.rp_n == 0:
            g.jp_k = K_JP_LIST
            g.jp_h = g.ns_ex[g.ct_i]
            g.jp_b = T.T_BRA
            uxc_cond.jp_br()
            g.ns_ex[g.ct_i] = g.jp_h
            return
        if g.rp_n < 256:
            g.ns_vt[g.ct_i] = K_TY_BYTE
            g.sl_s[0] = K_SEC_CONST
            g.sl_v[0] = g.rp_n
            emit(T.T_LDB_C)
            g.sl_s[0] = K_SEC_VAR
            g.sl_v[0] = g.ns_hv
            emit(T.T_STB_V)
            return
        # What T_RPTW_SET would store: the high byte is one more when the low byte is not 0.
        g.ns_vt[g.ct_i] = K_TY_WORD
        g.rp_hi = g.rp_n // 256
        g.rp_lo = g.rp_n - g.rp_hi * 256
        if g.rp_lo != 0:
            g.rp_hi = g.rp_hi + 1
        if g.rp_hi == 256:
            g.rp_hi = 0
        g.sl_s[0] = K_SEC_CONST
        g.sl_v[0] = g.rp_lo + 256 * g.rp_hi
        emit(T.T_LDW_C)
        g.sl_s[0] = K_SEC_VAR
        g.sl_v[0] = g.ns_hv
        emit(T.T_STW_V)
        return
    if g.ex_vt[g.ex_i] != K_TY_BYTE:
        g.ns_vt[g.ct_i] = K_TY_WORD
        uxc_expr.ex_tow()
        g.sl_s[0] = K_SEC_VAR
        g.sl_v[0] = g.ns_hv
        emit(T.T_RPTW_SET)
    else:
        g.ns_vt[g.ct_i] = K_TY_BYTE
        uxc_expr.ex_tob()
        g.sl_s[0] = K_SEC_VAR
        g.sl_v[0] = g.ns_hv
        emit(T.T_STB_V)
        emit(T.T_TSTB)
    g.jp_k = K_JP_LIST
    g.jp_h = g.ns_ex[g.ct_i]
    g.jp_b = T.T_BEQ
    uxc_cond.jp_br()
    g.ns_ex[g.ct_i] = g.jp_h


def ct_endrep():
    """CT.ENDREP. END REPEAT, or ENDREPEAT: the token is REPEAT or ENDREPEAT."""
    g.ct_w = "END REPEAT WITHOUT REPEAT"
    g.ns_kn = K_NS_REP
    ns_topk()
    g.jp_l = g.ns_ct[g.ct_i]
    uxc_cond.jp_here()
    g.jp_v = g.ns_top[g.ct_i]
    if g.ns_vt[g.ct_i] == 0:
        g.jp_b = T.T_BRA
        uxc_cond.jp_back()
    else:
        g.sl_s[0] = K_SEC_VAR
        g.sl_v[0] = g.ns_va[g.ct_i]
        emit(T.T_DECB_V)
        g.jp_b = T.T_BNE
        uxc_cond.jp_back()
        if g.ns_vt[g.ct_i] == K_TY_WORD:
            g.sl_s[0] = K_SEC_VAR
            g.sl_v[0] = g.ns_va[g.ct_i] + 1
            emit(T.T_DECB_V)
            g.jp_b = T.T_BNE
            uxc_cond.jp_back()
    g.jp_l = g.ns_ex[g.ct_i]
    uxc_cond.jp_here()
    g.ns_d = g.ns_d - 1
    uxc_lex.lx_next()
