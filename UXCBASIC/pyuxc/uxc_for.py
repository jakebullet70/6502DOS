"""UXC-FOR.BL: FOR ... NEXT, ct_for and ct_next, called from sm_stmt. The nesting stack is in
uxc_flow, the jumps in uxc_cond.

FOR v = a TO b [STEP k]. STEP is a constant, 1 when it is left out. The body runs zero times
when the range is empty. The test at the bottom is made before the step, on the value the body
saw, so v never wraps, and after the loop v is the last value the body saw. A limit that is
not a constant is copied once into the hidden word of the depth.

The bottom, with H the limit, or the bound the limit gives for a bigger step:
  STEP 1 or -1       out when v = H, else INC or DEC v
  STEP k, k > 1      out when v >= H, H = the limit - (k - 1), at least 0
  STEP -k, constant  out when v < H, H = the limit + k
  STEP -k, variable  out when v <= H, H = the limit + (k - 1), at most the type's top
When H cannot be reached, there is no jump back: the body runs once.

A signed v is worked in the biased range: fr_bias adds half the range, so -128 to 127 becomes
0 to 255, and the rules above hold. The compares are the signed ones. fr_bias is its own
inverse, and turns each constant the code is given back into v's form. A signed STEP is at
most half the range.
"""

from uxc_code import emit
from uxc_defs import K_EK_CONST, K_JP_LIST, K_NS_FOR, K_SEC_CONST, K_SEC_VAR, K_SY_SIGNED, \
    K_TT_NAME, K_TT_OP, K_TY_BYTE, K_TY_LONG, K_TY_WORD
import uxc_cond
import uxc_expr
import uxc_flow
import uxc_lex
import uxc_record
import uxc_stmt
import uxc_tpl as T
from uxc_state import er_stop, er_syntax, g


def ct_for():
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NAME:
        er_syntax()
    g.sm_n = g.tk_s
    uxc_stmt.sm_var()
    g.fr_sg = 0
    if (g.sy_flags & K_SY_SIGNED) != 0:
        g.fr_sg = 1
    uxc_record.rd_section_counter()
    g.ns_kn = K_NS_FOR
    uxc_flow.ns_push()
    g.ct_i = g.ns_d
    g.fr_va = g.sy_val
    g.fr_vt = g.sy_type
    g.fr_vs = g.rd_sec
    if g.fr_vt == K_TY_LONG:
        er_stop("A FOR COUNTER IS A BYTE OR A WORD")
    g.fr_m = 255
    if g.fr_vt == K_TY_WORD:
        g.fr_m = 65535
    g.fr_half = g.fr_m // 2 + 1
    uxc_lex.lx_next()
    if g.tk_t != K_TT_OP or g.tk_k != 61:
        er_syntax()
    # v = a
    uxc_lex.lx_next()
    uxc_expr.ex_expr()
    g.fr_ac = 0
    if g.ex_vk[g.ex_vn - 1] == K_EK_CONST:
        g.fr_ac = 1
        g.fr_a = g.ex_vv[g.ex_vn - 1]
        if g.fr_vt == K_TY_BYTE:
            g.fr_a = g.fr_a - (g.fr_a // 256) * 256
        if g.fr_vt == K_TY_WORD:
            g.fr_a = g.fr_a - (g.fr_a // 65536) * 65536
        g.fr_x = g.fr_a
        fr_bias()
        g.fr_a = g.fr_x
    if g.fr_vt == K_TY_BYTE:
        uxc_expr.ex_tob()
        g.fr_t = T.T_STB_V
    else:
        uxc_expr.ex_tow()
        g.fr_t = T.T_STW_V
    g.fr_of = 0
    fr_v()
    if g.tk_t != K_TT_NAME or g.tk_s != "TO":
        er_syntax()
    # The limit stays an entry on the value stack until the step is known.
    uxc_lex.lx_next()
    uxc_expr.ex_expr()
    g.fr_up = 1
    g.fr_k = 1
    if g.tk_t == K_TT_NAME and g.tk_s == "STEP":
        uxc_lex.lx_next()
        if g.tk_t == K_TT_OP and g.tk_k == 45:
            g.fr_up = 0
            uxc_lex.lx_next()
        uxc_expr.ex_expr()
        if g.ex_vk[g.ex_vn - 1] != K_EK_CONST:
            er_stop("STEP MUST BE A CONSTANT")
        g.fr_k = g.ex_vv[g.ex_vn - 1]
        g.ex_vn = g.ex_vn - 1
        if g.ex_vt[g.ex_vn] == K_TY_LONG:
            er_stop("STEP TOO BIG")
        if g.ex_vg[g.ex_vn] == 1:
            g.fr_up = 1 - g.fr_up
            g.fr_k = 65536 - g.fr_k
        if g.fr_k == 0:
            er_stop("STEP 0")
        if g.fr_k > g.fr_m:
            er_stop("STEP TOO BIG")
        if g.fr_sg == 1 and g.fr_k > g.fr_half:
            er_stop("STEP TOO BIG")
    g.fr_nb = 0
    g.fr_hv = 0
    if g.ex_vk[g.ex_vn - 1] == K_EK_CONST:
        g.fr_lc = 1
        g.fr_l = g.ex_vv[g.ex_vn - 1]
        g.ex_vn = g.ex_vn - 1
        fr_limit()
        fr_const()
        g.fr_x = g.fr_h
        fr_bias()
        g.fr_h = g.fr_x
    else:
        g.fr_lc = 0
        fr_var()
    g.ns_va[g.ct_i] = g.fr_va
    g.ns_vs[g.ct_i] = g.fr_vs
    g.ns_vt[g.ct_i] = g.fr_vt + 4 * g.fr_sg
    g.ns_lc[g.ct_i] = g.fr_lc
    g.ns_lv[g.ct_i] = g.fr_h
    g.ns_st[g.ct_i] = g.fr_k
    g.ns_sn[g.ct_i] = g.fr_up
    g.ns_nb[g.ct_i] = g.fr_nb
    g.ns_ha[g.ct_i] = g.fr_hv
    g.ns_top[g.ct_i] = g.cb_n


def fr_const():
    """FR.CONST. A constant limit g.fr_l. A/Y still holds v."""
    # The test before the first pass, left out when it cannot fail.
    g.fr_zt = 1
    if g.fr_up == 1 and g.fr_l == g.fr_m:
        g.fr_zt = 0
    if g.fr_up == 0 and g.fr_l == 0:
        g.fr_zt = 0
    if g.fr_ac == 1:
        g.fr_zt = 0
        g.fr_z = 0
        if g.fr_up == 1 and g.fr_a > g.fr_l:
            g.fr_z = 1
        if g.fr_up == 0 and g.fr_a < g.fr_l:
            g.fr_z = 1
        if g.fr_z == 1:
            g.jp_b = T.T_BRA
            fr_out()
    if g.fr_zt == 1:
        if g.fr_up == 1:
            g.fr_c = g.fr_l + 1
            g.jp_b = T.T_BCS
        else:
            g.fr_c = g.fr_l
            g.jp_b = T.T_BCC
        fr_cmpc()
        g.fr_x = g.fr_c
        fr_bias()
        g.fr_c = g.fr_x
        fr_ce()
        fr_out()
    g.fr_h = g.fr_l
    if g.fr_k == 1:
        return
    if g.fr_up == 1:
        g.fr_h = g.fr_l - g.fr_k + 1
        if g.fr_h <= 0:
            g.fr_nb = 1
    else:
        g.fr_h = g.fr_l + g.fr_k
        if g.fr_h > g.fr_m:
            g.fr_nb = 1


def fr_var():
    """FR.VAR. The limit is the top entry: copy it into the hidden word."""
    uxc_flow.ns_hidden()
    g.fr_hv = g.ns_hv
    g.fr_h = 0
    if g.fr_vt == K_TY_BYTE:
        uxc_expr.ex_tob()
        g.fr_t = T.T_STB_V
    else:
        uxc_expr.ex_tow()
        g.fr_t = T.T_STW_V
    g.fr_of = 0
    fr_he()
    # The test before the first pass. A/Y holds the limit.
    if g.fr_up == 1:
        fr_cmpv()
        g.fr_of = 0
        fr_v()
    else:
        fr_load()
        g.fr_of = 0
        fr_v()
        fr_cmpv()
        g.fr_of = 0
        fr_he()
    g.jp_b = T.T_BCC
    fr_out()
    if g.fr_k == 1:
        return
    # The bound, worked out once.
    fr_load()
    g.fr_of = 0
    fr_he()
    g.fr_c = g.fr_k - 1
    if g.fr_up == 1:
        g.fr_t = T.T_SUBB_C
        if g.fr_vt == K_TY_WORD:
            g.fr_t = T.T_SUBW_C
        fr_ce()
        g.jp_b = T.T_BCS
        g.fr_c = 0
    else:
        g.fr_t = T.T_ADDB_C
        if g.fr_vt == K_TY_WORD:
            g.fr_t = T.T_ADDW_C
        fr_ce()
        g.jp_b = T.T_BCC
        g.fr_c = g.fr_m
    if g.fr_sg == 1:
        g.jp_b = T.T_BVC
    g.fr_x = g.fr_c
    fr_bias()
    g.fr_c = g.fr_x
    uxc_cond.jp_fwd()
    g.fr_t = T.T_LDB_C
    if g.fr_vt == K_TY_WORD:
        g.fr_t = T.T_LDW_C
    fr_ce()
    uxc_cond.jp_land()
    g.fr_t = T.T_STB_V
    if g.fr_vt == K_TY_WORD:
        g.fr_t = T.T_STW_V
    g.fr_of = 0
    fr_he()


def fr_out():
    """FR.OUT. A jump of kind g.jp_b to the end of the loop."""
    g.jp_k = K_JP_LIST
    g.jp_h = g.ns_ex[g.ct_i]
    uxc_cond.jp_br()
    g.ns_ex[g.ct_i] = g.jp_h


# Emit g.fr_t with: fr_v the variable + g.fr_of in section g.fr_vs, fr_he the hidden word +
# g.fr_of, fr_ce the constant g.fr_c. fr_load and fr_cmpv set g.fr_t to the load or the compare
# with a variable, of v's width and sign; fr_cmpc to the compare with a constant.

def fr_v():
    g.sl_s[0] = g.fr_vs
    g.sl_v[0] = g.fr_va + g.fr_of
    emit(g.fr_t)


def fr_he():
    g.sl_s[0] = K_SEC_VAR
    g.sl_v[0] = g.fr_hv + g.fr_of
    emit(g.fr_t)


def fr_ce():
    g.sl_s[0] = K_SEC_CONST
    g.sl_v[0] = g.fr_c
    emit(g.fr_t)


def fr_load():
    g.fr_t = T.T_LDB_V
    if g.fr_vt == K_TY_WORD:
        g.fr_t = T.T_LDW_V


def fr_cmpv():
    g.fr_t = T.T_CMPB_V
    if g.fr_vt == K_TY_WORD:
        g.fr_t = T.T_CMPW_V
    if g.fr_sg == 0:
        return
    g.fr_t = T.T_SCMPB_V
    if g.fr_vt == K_TY_WORD:
        g.fr_t = T.T_SCMPW_V


def fr_cmpc():
    g.fr_t = T.T_CMPB_C
    if g.fr_vt == K_TY_WORD:
        g.fr_t = T.T_CMPW_C
    if g.fr_sg == 0:
        return
    g.fr_t = T.T_SCMPB_C
    if g.fr_vt == K_TY_WORD:
        g.fr_t = T.T_SCMPW_C


def ct_next():
    g.ct_w = "NEXT WITHOUT FOR"
    g.ns_kn = K_NS_FOR
    uxc_flow.ns_topk()
    uxc_lex.lx_next()
    if g.tk_t == K_TT_NAME:
        g.sm_n = g.tk_s
        uxc_stmt.sm_var()
        if g.sy_val != g.ns_va[g.ct_i]:
            er_stop("NEXT " + g.sm_n + " IS NOT THE FOR VARIABLE")
        uxc_lex.lx_next()
    g.jp_l = g.ns_ct[g.ct_i]
    uxc_cond.jp_here()
    g.fr_va = g.ns_va[g.ct_i]
    g.fr_vs = g.ns_vs[g.ct_i]
    g.fr_sg = g.ns_vt[g.ct_i] // 4
    g.fr_vt = g.ns_vt[g.ct_i] - 4 * g.fr_sg
    g.fr_lc = g.ns_lc[g.ct_i]
    g.fr_h = g.ns_lv[g.ct_i]
    g.fr_k = g.ns_st[g.ct_i]
    g.fr_up = g.ns_sn[g.ct_i]
    g.fr_hv = g.ns_ha[g.ct_i]
    g.fr_top = g.ns_top[g.ct_i]
    if g.ns_nb[g.ct_i] == 0:
        fr_bottom()
    g.jp_l = g.ns_ex[g.ct_i]
    uxc_cond.jp_here()
    g.ns_d = g.ns_d - 1


def fr_bottom():
    """FR.BOTTOM. The test, the step, and the jump back to the top."""
    g.fr_w = 0
    if g.fr_vt == K_TY_WORD:
        g.fr_w = 1
    if g.fr_k == 1:
        # Out when v = H, a byte at a time.
        g.fr_t = T.T_LDB_V
        g.fr_of = 0
        fr_v()
        g.fr_of = 0
        fr_cmph()
        if g.fr_w == 0:
            g.jp_b = T.T_BEQ
            uxc_cond.jp_fwd()
            g.fr_o = g.jp_at
            g.fr_t = T.T_INCB_V
            if g.fr_up == 0:
                g.fr_t = T.T_DECB_V
            g.fr_of = 0
            fr_v()
        else:
            g.jp_b = T.T_BNE
            uxc_cond.jp_fwd()
            g.fr_n = g.jp_at
            g.fr_t = T.T_LDB_V
            g.fr_of = 1
            fr_v()
            g.fr_of = 1
            fr_cmph()
            g.jp_b = T.T_BEQ
            uxc_cond.jp_fwd()
            g.fr_o = g.jp_at
            g.jp_at = g.fr_n
            uxc_cond.jp_land()
            if g.fr_up == 1:
                g.fr_t = T.T_INCB_V
                g.fr_of = 0
                fr_v()
                g.jp_v = g.fr_top
                g.jp_b = T.T_BNE
                uxc_cond.jp_back()
                g.fr_t = T.T_INCB_V
                g.fr_of = 1
                fr_v()
            else:
                g.fr_t = T.T_DECW_V
                g.fr_of = 0
                fr_v()
        g.jp_v = g.fr_top
        g.jp_b = T.T_BRA
        uxc_cond.jp_back()
        g.jp_at = g.fr_o
        uxc_cond.jp_land()
        return
    # A bigger step: the test.
    g.fr_rl = g.fr_sg
    if g.fr_up == 0 and g.fr_lc == 0:
        # out when H >= v
        fr_load()
        g.fr_of = 0
        fr_he()
        fr_cmpv()
        g.fr_of = 0
        fr_v()
        g.jp_b = T.T_BCS
        g.fr_rl = 1
    else:
        # out when v >= H (up), or v < H (down)
        fr_load()
        g.fr_of = 0
        fr_v()
        if g.fr_lc == 1:
            fr_cmpc()
            g.fr_c = g.fr_h
            fr_ce()
        else:
            fr_cmpv()
            g.fr_of = 0
            fr_he()
        g.jp_b = T.T_BCS
        if g.fr_up == 0:
            g.jp_b = T.T_BCC
    uxc_cond.jp_fwd()
    g.fr_o = g.jp_at
    # The step. An unsigned BYTE v is still in A after a compare with the bound.
    g.fr_c = g.fr_k
    if g.fr_w == 0:
        if g.fr_rl == 1:
            g.fr_t = T.T_LDB_V
            g.fr_of = 0
            fr_v()
        g.fr_t = T.T_ADDB_C
        if g.fr_up == 0:
            g.fr_t = T.T_SUBB_C
        fr_ce()
        g.fr_t = T.T_STB_V
        g.fr_of = 0
        fr_v()
    else:
        if g.fr_k < 256:
            g.fr_t = T.T_LDB_V
            g.fr_of = 0
            fr_v()
            g.fr_t = T.T_ADDB_C
            if g.fr_up == 0:
                g.fr_t = T.T_SUBB_C
            fr_ce()
            g.fr_t = T.T_STB_V
            g.fr_of = 0
            fr_v()
            g.jp_b = T.T_BCC
            if g.fr_up == 0:
                g.jp_b = T.T_BCS
            uxc_cond.jp_fwd()
            g.fr_n = g.jp_at
            g.fr_t = T.T_INCB_V
            if g.fr_up == 0:
                g.fr_t = T.T_DECB_V
            g.fr_of = 1
            fr_v()
            g.jp_at = g.fr_n
            uxc_cond.jp_land()
        else:
            g.fr_t = T.T_LDW_V
            g.fr_of = 0
            fr_v()
            g.fr_t = T.T_ADDW_C
            if g.fr_up == 0:
                g.fr_t = T.T_SUBW_C
            fr_ce()
            g.fr_t = T.T_STW_V
            g.fr_of = 0
            fr_v()
    g.jp_v = g.fr_top
    g.jp_b = T.T_BRA
    uxc_cond.jp_back()
    g.jp_at = g.fr_o
    uxc_cond.jp_land()


def fr_cmph():
    """FR.CMPH. The compare of A with byte g.fr_of of H: the constant, or the hidden word."""
    if g.fr_lc == 1:
        g.fr_c = g.fr_h - (g.fr_h // 256) * 256
        if g.fr_of == 1:
            g.fr_c = g.fr_h // 256
        g.fr_t = T.T_CMPB_C
        fr_ce()
        return
    g.fr_t = T.T_CMPB_V
    fr_he()


def fr_bias():
    """FR.BIAS. g.fr_x moved half v's range up, for a signed v. It is its own inverse."""
    if g.fr_sg == 0:
        return
    g.fr_x = g.fr_x + g.fr_half
    if g.fr_x > g.fr_m:
        g.fr_x = g.fr_x - g.fr_m - 1


def fr_limit():
    """FR.LIMIT. The constant limit g.fr_l checked against v's range, and biased.
    g.ex_vg[g.ex_vn] is the limit's sign."""
    if g.fr_sg == 0:
        if g.fr_l > g.fr_m:
            er_stop("TO VALUE TOO BIG")
        return
    g.fr_bad = 0
    if g.ex_vt[g.ex_vn] == K_TY_LONG:
        g.fr_bad = 1
    if g.ex_vg[g.ex_vn] == 0 and g.fr_l >= g.fr_half:
        g.fr_bad = 1
    if g.ex_vg[g.ex_vn] == 1 and g.fr_l < 65536 - g.fr_half:
        g.fr_bad = 1
    if g.fr_bad == 1:
        er_stop("TO VALUE OUT OF RANGE")
    g.fr_x = g.fr_l - (g.fr_l // (g.fr_m + 1)) * (g.fr_m + 1)
    fr_bias()
    g.fr_l = g.fr_x
