"""UXC-COND.BL: jumps and conditions, for UXC-FLOW.BL and UXC-EXPR.BL.

Jumps (jp_*). A target is g.jp_k with g.jp_v or g.jp_h:
    K_JP_CODE    g.jp_v, a code offset already reached: a backward jump
    K_JP_LIST    g.jp_h, the head of a list of forward jumps waiting for their target
    K_JP_LABEL   g.jp_v, the symbol record of a label

    jp_br()      in g.jp_b, a branch template (T_BRA for always): a jump to the target
    jp_send()    in g.jp_l: every jump on list g.jp_l goes to the target
    jp_here()    in g.jp_l: every jump on list g.jp_l comes here
    jp_fwd()     in g.jp_b: a short branch forward, out g.jp_at; jp_land then makes it land here

Conditions (cn_*):
    cn_expr()    compile the condition that starts at the token; it is the top entry
    cn_jt()      then jump to the target g.jp_* when it is true, and fall through when false
    cn_jf()      then jump when it is false

UXC-COND.BL has the layout of a list of jumps, and the rules of AND and OR as jumps.
"""

from uxc_code import cb_get, cb_put, emit, fx_add
from uxc_defs import K_EK_ADDR, K_EK_CMP, K_EK_CONST, K_EK_JMP, K_EO_LAND, K_F_ABS, K_JP_CODE, \
    K_JP_LABEL, K_JP_LIST, K_OP_GE, K_OP_NE, K_SEC_CODE, K_SEC_CONST, K_SEC_LABEL, K_TT_EOL, \
    K_TT_NAME, K_TT_OP, K_TY_BYTE
import uxc_expr
import uxc_lex
import uxc_tpl as T
from uxc_state import er_stop, g


# Jumps

def jp_br():
    if g.jp_k == K_JP_CODE:
        g.jp_d = g.jp_v - g.cb_n - 2
        if g.jp_d >= -128 and g.jp_d <= 127:
            if g.jp_d < 0:
                g.jp_d = g.jp_d + 256
            g.sl_s[0] = K_SEC_CONST
            g.sl_v[0] = g.jp_d
            emit(g.jp_b)
            return
    if g.jp_b != T.T_BRA:
        jp_inv()
        g.sl_s[0] = K_SEC_CONST
        g.sl_v[0] = 3
        emit(g.jp_ib)
    if g.jp_k == K_JP_CODE:
        g.sl_s[0] = K_SEC_CODE
        g.sl_v[0] = g.jp_v
    if g.jp_k == K_JP_LABEL:
        g.sl_s[0] = K_SEC_LABEL
        g.sl_v[0] = g.jp_v
    if g.jp_k == K_JP_LIST:
        g.jp_e = g.jp_h
        jp_encode()
        g.sl_s[0] = K_SEC_CONST
        g.sl_v[0] = g.jp_e
        g.jp_h = g.cb_n + 1
    emit(T.T_JMP)


def jp_inv():
    """JP.INV. g.jp_ib, the branch on the opposite flag to g.jp_b."""
    if g.jp_b == T.T_BEQ:
        g.jp_ib = T.T_BNE
    if g.jp_b == T.T_BNE:
        g.jp_ib = T.T_BEQ
    if g.jp_b == T.T_BCC:
        g.jp_ib = T.T_BCS
    if g.jp_b == T.T_BCS:
        g.jp_ib = T.T_BCC


def jp_send():
    if g.jp_l == 0:
        return
    if g.jp_k == K_JP_LIST:
        g.jp_m = g.jp_h
        jp_merge()
        g.jp_h = g.jp_m
        return
    g.jp_fs = K_SEC_CODE
    if g.jp_k == K_JP_LABEL:
        g.jp_fs = K_SEC_LABEL
    g.jp_fv = g.jp_v
    jp_fix()


def jp_here():
    g.jp_fs = K_SEC_CODE
    g.jp_fv = g.cb_n
    jp_fix()


def jp_fix():
    """JP.FIX. Every jump on list g.jp_l goes to g.jp_fv in section g.jp_fs."""
    while g.jp_l != 0:
        g.cb_at = g.jp_l
        cb_get()
        g.jp_n = g.cb_b
        g.cb_b = 0
        cb_put()
        g.cb_at = g.jp_l + 1
        cb_get()
        g.jp_n = g.jp_n + 256 * g.cb_b
        g.cb_b = 0
        cb_put()
        if g.jp_n != 0:
            g.jp_n = g.jp_n + g.jp_base - 1
        g.fx_at = g.jp_l
        g.fx_k = K_F_ABS
        g.fx_s = g.jp_fs
        g.fx_v = g.jp_fv
        fx_add()
        g.jp_l = g.jp_n


def jp_encode():
    """JP.ENCODE. g.jp_e, the head of a list as a jump in the list keeps it: 0 for none, else
    its code offset less g.jp_base, + 1. g.jp_base is where the code of this SUB, or of the
    main program since the last SUB, starts, and a list lies in one of them."""
    if g.jp_e == 0:
        return
    g.jp_e = g.jp_e - g.jp_base + 1
    if g.jp_e > 65535:
        er_stop("PROGRAM TOO BIG")


def jp_merge():
    """JP.MERGE. g.jp_m becomes list g.jp_l joined to list g.jp_m."""
    if g.jp_l == 0:
        return
    if g.jp_m == 0:
        g.jp_m = g.jp_l
        return
    g.jp_a = g.jp_l
    while True:
        g.cb_at = g.jp_a
        cb_get()
        g.jp_n = g.cb_b
        g.cb_at = g.jp_a + 1
        cb_get()
        g.jp_n = g.jp_n + 256 * g.cb_b
        if g.jp_n == 0:
            break
        g.jp_a = g.jp_n + g.jp_base - 1
    g.jp_e = g.jp_m
    jp_encode()
    g.jp_hi = g.jp_e // 256
    g.cb_at = g.jp_a
    g.cb_b = g.jp_e - g.jp_hi * 256
    cb_put()
    g.cb_at = g.jp_a + 1
    g.cb_b = g.jp_hi
    cb_put()
    g.jp_m = g.jp_l


def jp_fwd():
    g.sl_s[0] = K_SEC_CONST
    g.sl_v[0] = 0
    emit(g.jp_b)
    g.jp_at = g.cb_n - 1


def jp_land():
    g.cb_at = g.jp_at
    g.cb_b = g.cb_n - g.jp_at - 1
    if g.cb_b > 127:
        er_stop("BRANCH TOO FAR")
    cb_put()


def jp_back():
    """JP.BACK. A jump of kind g.jp_b back to code offset g.jp_v."""
    g.jp_k = K_JP_CODE
    jp_br()


# Conditions

def cn_expr():
    cn_scan()
    g.ex_cm = g.cn_lg
    uxc_expr.ex_expr()
    g.ex_cm = 0


def cn_scan():
    """CN.SCAN. g.cn_lg = 1 when AND and OR may be jumps in the condition ahead. The
    condition ends at the end of the line, or at THEN or GOTO outside brackets. The token and
    g.lx_p are put back after."""
    g.cn_sp = g.lx_p
    g.cn_st = g.tk_t
    g.cn_sk = g.tk_k
    g.cn_sv = g.tk_v
    g.cn_sm = g.tk_m
    g.cn_ss = g.tk_s
    g.cn_lg = 1
    g.cn_d = 0
    cn_seg_new()
    while g.tk_t != K_TT_EOL:
        if g.cn_d == 0 and g.tk_t == K_TT_NAME:
            if g.tk_s == "THEN" or g.tk_s == "GOTO":
                break
            if g.tk_s == "AND" or g.tk_s == "OR":
                cn_seg()
                uxc_lex.lx_next()
                continue
            if g.tk_s == "XOR":
                g.cn_lg = 0
            if g.tk_s == "NOT" and g.cn_f == 0:
                g.cn_nx = 1
            if g.tk_s == "NOT" and g.cn_f == 1:
                g.cn_nf = 1
        if g.tk_t == K_TT_OP:
            if g.tk_k == 40:
                g.cn_d = g.cn_d + 1
            if g.tk_k == 41:
                g.cn_d = g.cn_d - 1
            if g.cn_d == 0:
                if g.tk_k == 60 or g.tk_k == 61 or g.tk_k == 62:
                    g.cn_c = 1
                if g.tk_k >= K_OP_NE and g.tk_k <= K_OP_GE:
                    g.cn_c = 1
        g.cn_f = 0
        uxc_lex.lx_next()
    cn_seg()
    g.lx_p = g.cn_sp
    g.tk_t = g.cn_st
    g.tk_k = g.cn_sk
    g.tk_v = g.cn_sv
    g.tk_m = g.cn_sm
    g.tk_s = g.cn_ss


def cn_seg():
    """CN.SEG. The end of one part between AND and OR. It gives 0 or 1 when it starts with
    NOT, or when its lowest operator is a compare: one outside brackets, and no NOT after
    the start that could take it."""
    if g.cn_nf == 0 and (g.cn_c == 0 or g.cn_nx == 1):
        g.cn_lg = 0
    cn_seg_new()


def cn_seg_new():
    g.cn_c = 0
    g.cn_nf = 0
    g.cn_nx = 0
    g.cn_f = 1


def cn_jf():
    g.cn_sn = 0
    cn_jump()


def cn_jt():
    g.cn_sn = 1
    cn_jump()


def cn_jump():
    """CN.JUMP. Jump when the top entry is g.cn_sn (1 true, 0 false). The entry is dropped.
    g.cn_ck is 1 or 0 for a condition known now, else -1, and g.cn_bt is the branch taken
    when the condition is true."""
    g.ex_i = g.ex_vn - 1
    g.cn_lt = g.ex_jt[g.ex_i]
    g.cn_lf = g.ex_jf[g.ex_i]
    g.cn_k = g.ex_vk[g.ex_i]
    g.cn_ck = -1
    if g.cn_k == K_EK_ADDR:
        g.cn_ck = 1
    if g.cn_k == K_EK_CONST:
        g.cn_ck = 0
        if g.ex_vv[g.ex_i] != 0:
            g.cn_ck = 1
    if g.cn_k == K_EK_CMP:
        g.ex_tl = g.ex_vv[g.ex_i]
        if g.ex_tl == T.T_ZTRUE:
            g.cn_bt = T.T_BEQ
        if g.ex_tl == T.T_ZFALSE:
            g.cn_bt = T.T_BNE
        if g.ex_tl == T.T_CTRUE:
            g.cn_bt = T.T_BCS
        if g.ex_tl == T.T_CFALSE:
            g.cn_bt = T.T_BCC
    if g.cn_ck < 0 and g.cn_k != K_EK_CMP:
        uxc_expr.ex_test()
        g.cn_bt = T.T_BNE
    g.ex_vn = g.ex_vn - 1
    if g.cn_ck < 0:
        g.jp_b = g.cn_bt
        if g.cn_sn == 0:
            jp_inv()
            g.jp_b = g.jp_ib
        jp_br()
    if g.cn_ck == g.cn_sn:
        g.jp_b = T.T_BRA
        jp_br()
    if g.cn_sn == 0:
        g.jp_l = g.cn_lf
        jp_send()
        g.jp_l = g.cn_lt
        jp_here()
    else:
        g.jp_l = g.cn_lt
        jp_send()
        g.jp_l = g.cn_lf
        jp_here()


def cn_left():
    """CN.LEFT. The left side of a logical AND or OR (g.ex_new), now complete on top of the
    value stack: for AND, jump when it is false, for OR when it is true. It becomes a
    K_EK_JMP entry that keeps those jumps."""
    g.jp_k = K_JP_LIST
    g.jp_h = 0
    if g.ex_new == K_EO_LAND:
        cn_jf()
        g.cn_ljt = 0
        g.cn_ljf = g.jp_h
    else:
        cn_jt()
        g.cn_ljt = g.jp_h
        g.cn_ljf = 0
    g.ex_k = K_EK_JMP
    g.ex_s = K_SEC_CONST
    g.ex_v = 0
    g.ex_ty = K_TY_BYTE
    uxc_expr.ex_pushv()
    g.ex_jt[g.ex_vn - 1] = g.cn_ljt
    g.ex_jf[g.ex_vn - 1] = g.cn_ljf


def cn_logic():
    """CN.LOGIC. Reduce a logical AND or OR. The right side's flag is still to be tested, so
    the result is the right side, with the left side's jumps added to its lists."""
    g.ex_il = g.ex_vn - 2
    g.ex_ir = g.ex_vn - 1
    if g.ex_o == K_EO_LAND:
        g.jp_l = g.ex_jf[g.ex_il]
        g.jp_m = g.ex_jf[g.ex_ir]
        jp_merge()
        g.ex_jf[g.ex_ir] = g.jp_m
    else:
        g.jp_l = g.ex_jt[g.ex_il]
        g.jp_m = g.ex_jt[g.ex_ir]
        jp_merge()
        g.ex_jt[g.ex_ir] = g.jp_m
    g.ex_i = g.ex_il
    g.ex_j = g.ex_ir
    uxc_expr.ex_swap()
    g.ex_jt[g.ex_il] = g.ex_jt[g.ex_ir]
    g.ex_jf[g.ex_il] = g.ex_jf[g.ex_ir]
    g.ex_vn = g.ex_vn - 1
