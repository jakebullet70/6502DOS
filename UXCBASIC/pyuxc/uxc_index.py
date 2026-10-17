"""UXC-INDEX.BL: PEEK and array elements in expressions, for ex_close in uxc_expr.

    ex_peek()     PEEK(a) or ContentsAt(a), the BYTE at the top entry; ContentsAtW(a), the
                  WORD. The operator is g.ex_op[g.ex_on].
    ex_index()    array g.ex_oa[g.ex_on], element of the top entry
"""

from uxc_code import emit
from uxc_defs import K_EK_ADDR, K_EK_CONST, K_EK_MEM, K_EK_REG, K_EO_WORDPEEK, K_SEC_BSS, \
    K_SEC_CONST, K_SY_SIGNED, K_TY_BYTE, K_TY_LONG, K_TY_RECORD, K_TY_STR, K_TY_WORD
import uxc_expr
import uxc_fold
import uxc_record
import uxc_sym
import uxc_tpl as T
from uxc_state import er_mismatch, er_stop, g


def ex_peek():
    """EX.PEEK. A constant or @name is a load from that address."""
    g.ex_peek_type = K_TY_BYTE
    if g.ex_op[g.ex_on] == K_EO_WORDPEEK:
        g.ex_peek_type = K_TY_WORD
    g.ex_i = g.ex_vn - 1
    g.ex_lk = g.ex_vk[g.ex_i]
    if g.ex_vt[g.ex_i] == K_TY_STR:
        er_mismatch()
    g.ex_vg[g.ex_i] = 0
    if g.ex_lk == K_EK_CONST:
        uxc_fold.ex_const_word()
    if g.ex_lk == K_EK_CONST or g.ex_lk == K_EK_ADDR:
        g.ex_vk[g.ex_i] = K_EK_MEM
        g.ex_vt[g.ex_i] = g.ex_peek_type
        return
    g.ex_fb = g.ex_i
    uxc_expr.ex_flush()
    g.ex_i = g.ex_vn - 1
    g.ex_wd = 1
    uxc_expr.ex_load()
    if g.ex_peek_type == K_TY_BYTE:
        emit(T.T_PEEK)
    if g.ex_peek_type == K_TY_WORD:
        emit(T.T_PEEKW)
    g.ex_vk[g.ex_i] = K_EK_REG
    g.ex_vt[g.ex_i] = g.ex_peek_type


def ex_index():
    """EX.INDEX. A constant index is checked here, and the element becomes a K_EK_MEM entry. A
    BYTE array with a BYTE index is read with the index in Y. Any other index is a WORD, made
    the element's address."""
    g.sy_r = g.ex_oa[g.ex_on]
    uxc_sym.sy_get()
    if g.sy_type >= K_TY_RECORD:
        uxc_record.rd_index()
        return
    g.ex_i = g.ex_vn - 1
    if g.ex_vt[g.ex_i] == K_TY_STR:
        er_mismatch()
    g.ex_index_signed = 0
    if (g.sy_flags & K_SY_SIGNED) != 0:
        g.ex_index_signed = 1
    if g.ex_vk[g.ex_i] == K_EK_CONST:
        if g.ex_vv[g.ex_i] >= g.sy_cnt:
            er_stop("BAD SUBSCRIPT")
        g.ex_vk[g.ex_i] = K_EK_MEM
        g.ex_vs[g.ex_i] = K_SEC_BSS
        g.ty_code = g.sy_type
        uxc_sym.ty_size()
        g.ex_vv[g.ex_i] = g.sy_val + g.ex_vv[g.ex_i] * g.ty_bytes
        g.ex_vt[g.ex_i] = g.sy_type
        g.ex_vg[g.ex_i] = g.ex_index_signed
        return
    g.ex_fb = g.ex_i
    uxc_expr.ex_flush()
    g.ex_i = g.ex_vn - 1
    if g.sy_type == K_TY_BYTE and g.ex_vt[g.ex_i] == K_TY_BYTE:
        g.ex_wd = 0
        uxc_expr.ex_load()
        if g.sm_errors_on == 1 and g.sy_cnt < 256:
            g.sl_s[0] = K_SEC_CONST
            g.sl_v[0] = g.sy_cnt
            emit(T.T_CHKB)
        g.sl_s[0] = K_SEC_BSS
        g.sl_v[0] = g.sy_val
        emit(T.T_LDB_AY)
    else:
        g.ex_wd = 1
        uxc_expr.ex_load()
        if g.sm_errors_on == 1:
            g.sl_s[0] = K_SEC_CONST
            g.sl_v[0] = g.sy_cnt
            emit(T.T_CHKW)
        g.sl_s[0] = K_SEC_BSS
        g.sl_v[0] = g.sy_val
        if g.sy_type == K_TY_BYTE:
            emit(T.T_IDXB)
            emit(T.T_PEEK)
        if g.sy_type == K_TY_WORD:
            emit(T.T_IDXW)
            emit(T.T_PEEKW)
        if g.sy_type == K_TY_LONG:
            emit(T.T_IDXL)
            emit(T.T_PEEKL)
    g.ex_vk[g.ex_i] = K_EK_REG
    g.ex_vt[g.ex_i] = g.sy_type
    g.ex_vg[g.ex_i] = g.ex_index_signed
