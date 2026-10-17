"""UXC-LONG.BL: LONG and ULONG in expressions, for uxc_expr.

    ex_long_load()     emit the code that puts entry g.ex_i in A/Y/ZP_HI
    ex_long_const()    for ex_setc: g.ex_r has bits past 16
    ex_long_stack()    the left side of a LONG operator, made a LONG on the run-time stack
    ex_long_fast()     a LONG + or - with a constant on the right
    ex_long_opcode()   emit the LONG operator g.ex_o
    ex_long_test()     the LONG entry g.ex_i loaded, and Z set when it is 0

UXC-LONG.BL has where a LONG is kept, in the registers and on the run-time stack.
"""

from uxc_code import emit
from uxc_defs import K_EK_CMP, K_EK_CONST, K_EK_MEM, K_EK_REG, K_EO_ADD, K_EO_AND, K_EO_DIV, \
    K_EO_EQ, K_EO_GE, K_EO_GT, K_EO_LE, K_EO_LT, K_EO_MOD, K_EO_MUL, K_EO_NE, K_EO_OR, \
    K_EO_SHL, K_EO_SHR, K_EO_SUB, K_EO_XOR, K_SEC_CONST, K_TY_BYTE, K_TY_LONG
import uxc_expr
import uxc_tpl as T
from uxc_state import g


def ex_long_load():
    """EX.LONG.LOAD. g.ex_wd is 2 after it."""
    g.ex_long_kind = g.ex_vk[g.ex_i]
    if g.ex_long_kind == K_EK_CONST:
        ex_long_bits()
        g.sl_s[0] = K_SEC_CONST
        g.sl_v[0] = g.ex_long_low
        g.sl_s[1] = K_SEC_CONST
        g.sl_v[1] = g.ex_long_high
        if g.ex_long_high == 0:
            emit(T.T_LDW_C)
            emit(T.T_LWIDEN)
        else:
            emit(T.T_LDL_C)
        return
    if g.ex_vt[g.ex_i] == K_TY_LONG:
        if g.ex_long_kind != K_EK_MEM:
            return
        g.sl_s[0] = g.ex_vs[g.ex_i]
        g.sl_v[0] = g.ex_vv[g.ex_i]
        emit(T.T_LDL_V)
        return
    g.ex_wd = 1
    uxc_expr.ex_load()
    g.ex_wd = 2
    if g.ex_vg[g.ex_i] == 0:
        emit(T.T_LWIDEN)
    if g.ex_vg[g.ex_i] == 1:
        emit(T.T_LSWIDEN)


def ex_long_bits():
    """EX.LONG.BITS. The 32 bits of the constant entry g.ex_i, in g.ex_long_low and
    g.ex_long_high. A signed 16-bit constant is widened with its sign."""
    g.ex_long_value = g.ex_vv[g.ex_i]
    if g.ex_vg[g.ex_i] == 1 and g.ex_vt[g.ex_i] != K_TY_LONG:
        g.ex_long_value = g.ex_long_value + 4294901760
    g.ex_long_high = g.ex_long_value // 65536
    g.ex_long_low = g.ex_long_value - g.ex_long_high * 65536


def ex_long_const():
    """EX.LONG.CONST. g.ex_setc_long = 1 for a LONG; a signed value from -32768 up is made 16
    bits instead."""
    g.ex_setc_long = 1
    if g.ex_cg == 0 or g.ex_r < 4294934528:
        return
    g.ex_r = g.ex_r - 4294901760
    g.ex_setc_long = 0


def ex_long_stack():
    if g.ex_vg[g.ex_il] == 0:
        emit(T.T_STKWIDEN)
    if g.ex_vg[g.ex_il] == 1:
        emit(T.T_STKSWIDEN)


def ex_long_fast():
    """EX.LONG.FAST. g.ex_fd = 1 when it was done."""
    g.ex_fd = 0
    if g.ex_o != K_EO_ADD and g.ex_o != K_EO_SUB:
        return
    if g.ex_vk[g.ex_ir] != K_EK_CONST:
        return
    uxc_expr.ex_fast_left()
    g.ex_i = g.ex_ir
    ex_long_bits()
    g.sl_s[0] = K_SEC_CONST
    g.sl_v[0] = g.ex_long_low
    g.sl_s[1] = K_SEC_CONST
    g.sl_v[1] = g.ex_long_high
    if g.ex_o == K_EO_ADD:
        emit(T.T_ADDL_C)
    if g.ex_o == K_EO_SUB:
        emit(T.T_SUBL_C)
    g.ex_vn = g.ex_vn - 1
    g.ex_i = g.ex_il
    g.ex_vk[g.ex_i] = K_EK_REG
    g.ex_vt[g.ex_i] = K_TY_LONG
    g.ex_vs[g.ex_i] = K_SEC_CONST
    g.ex_vv[g.ex_i] = 0
    g.ex_vg[g.ex_i] = g.ex_g
    g.ex_fd = 1


def ex_long_opcode():
    """EX.LONG.OPCODE. The result's g.ex_rt, and for a compare g.ex_rk, g.ex_rg and the tail
    g.ex_rv."""
    g.ex_rt = K_TY_LONG
    if g.ex_o == K_EO_MUL:
        g.ex_tp = T.T_MULL
    if g.ex_o == K_EO_DIV:
        g.ex_tp = T.T_DIVL
        if g.ex_g == 1:
            g.ex_tp = T.T_DIVLS
    if g.ex_o == K_EO_MOD:
        g.ex_tp = T.T_MODL
        if g.ex_g == 1:
            g.ex_tp = T.T_MODLS
    if g.ex_o == K_EO_ADD:
        g.ex_tp = T.T_ADDL
    if g.ex_o == K_EO_SUB:
        g.ex_tp = T.T_SUBL
    if g.ex_o == K_EO_AND:
        g.ex_tp = T.T_ANDL
    if g.ex_o == K_EO_OR:
        g.ex_tp = T.T_ORL
    if g.ex_o == K_EO_XOR:
        g.ex_tp = T.T_XORL
    if g.ex_o == K_EO_SHL:
        g.ex_tp = T.T_SHLL
    if g.ex_o == K_EO_SHR:
        g.ex_tp = T.T_SHRL
        if g.ex_g == 1:
            g.ex_tp = T.T_SARL
    if g.ex_o >= K_EO_EQ and g.ex_o <= K_EO_GE:
        ex_long_compare()
    emit(g.ex_tp)


def ex_long_compare():
    g.ex_rk = K_EK_CMP
    g.ex_rt = K_TY_BYTE
    g.ex_rg = 0
    if g.ex_o == K_EO_EQ:
        g.ex_tp = T.T_CMPL_EQ
        g.ex_rv = T.T_ZTRUE
    if g.ex_o == K_EO_NE:
        g.ex_tp = T.T_CMPL_EQ
        g.ex_rv = T.T_ZFALSE
    if g.ex_o == K_EO_GE:
        g.ex_tp = T.T_CMPL_LR
        g.ex_rv = T.T_CTRUE
    if g.ex_o == K_EO_LT:
        g.ex_tp = T.T_CMPL_LR
        g.ex_rv = T.T_CFALSE
    if g.ex_o == K_EO_LE:
        g.ex_tp = T.T_CMPL_RL
        g.ex_rv = T.T_CTRUE
    if g.ex_o == K_EO_GT:
        g.ex_tp = T.T_CMPL_RL
        g.ex_rv = T.T_CFALSE
    if g.ex_g == 0:
        return
    if g.ex_tp == T.T_CMPL_LR:
        g.ex_tp = T.T_SCMPL_LR
        return
    if g.ex_tp == T.T_CMPL_RL:
        g.ex_tp = T.T_SCMPL_RL


def ex_long_test():
    g.ex_wd = 2
    uxc_expr.ex_load()
    emit(T.T_TSTL)
