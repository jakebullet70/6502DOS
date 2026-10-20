"""UXC-LINK.BL: the link step, and the PRG writer.

    lk_init_call()   at the start of the program, the call to the startup work
    lk_link()        append the startup work, the runtime routines, the strings and the
                     variables to the code, then resolve every fixup
    lk_write()       in  g.ui_obj    write the PRG: the load address, then the code buffer

UXC-LINK.BL has the order of the routines and why a forward call needs nothing special.
"""

import os

import uxc_code
import uxc_dead
from uxc_code import cb_add, cb_get, cb_put, emit
from uxc_defs import K_F_HI, K_F_LO, K_FRAME_BASE, K_SEC_BSS, K_SEC_CODE, K_SEC_CONST, \
    K_SEC_LABEL, K_SEC_REC, K_SEC_STR, K_SEC_TEMP, K_SEC_VAR, K_SK_LABEL, K_TOP
import uxc_str
import uxc_sub
import uxc_sym
import uxc_tpl as T
from uxc_state import er_stop, g


def lk_init_call():
    """LK.INIT.CALL. A JSR to the label %INIT, which no source name can spell. lk_link places
    the label on the startup work, or turns the JSR into a BIT when there is none."""
    g.sy_name = "%INIT"
    g.sy_ow = 0
    g.sy_kind = K_SK_LABEL
    g.sy_type = 0
    g.sy_val = 0
    g.sy_flags = 0
    g.sy_cnt = 0
    uxc_sym.sy_add()
    g.lk_init_record = g.sy_r
    g.lk_init_at = g.cb_n
    g.sl_s[0] = K_SEC_LABEL
    g.sl_v[0] = g.lk_init_record
    emit(T.T_JSR)


def lk_link():
    """LK.LINK. The startup work: clear the array space, set the max of each string block,
    then lay out the pools of temps after it and set the max of each temp. The temps are not
    cleared. For 6502DOS it also stores the page of the program's end in PSP_TOP. The SUBs
    nothing calls are left out first, then the global variables nothing names, then the string
    literals nothing names."""
    uxc_dead.dd_strip()
    uxc_dead.dv_strip()
    uxc_dead.ds_strip()
    g.sy_r = g.lk_init_record
    uxc_sym.sy_get()
    g.sy_val = g.cb_n
    g.sy_flags = 1
    uxc_sym.sy_set()
    g.lk_start = g.cb_n
    if g.bs_n > 0:
        g.sl_s[0] = K_SEC_BSS
        g.sl_v[0] = 0
        g.sl_s[1] = K_SEC_CONST
        g.sl_v[1] = g.bs_n
        emit(T.T_ZERO)
    uxc_str.sg_maxes()
    uxc_sub.sb_pools()
    if g.target == "6502dos":
        g.sl_s[0] = K_SEC_BSS
        g.sl_v[0] = g.bs_n
        emit(T.T_TOP)
    if g.cb_n > g.lk_start:
        emit(T.T_RTS)
    else:
        g.cb_at = g.lk_init_at
        g.cb_b = 0x2C
        cb_put()
    g.lk_i = 0
    while g.lk_i < g.rt_n:
        uxc_code.rt_place()
        emit(g.rt_id)
        g.lk_i = g.lk_i + 1
    # The strings, out of their own bank.
    g.lk_str = g.lk_org + g.cb_n
    uxc_code.sp_copy()
    # The variables, all 0.
    g.lk_var = g.lk_org + g.cb_n
    for g.lk_i in range(1, g.vr_n + 1):
        g.cb_b = 0
        cb_add()
    # The array space follows, outside the file.
    g.lk_bss = g.lk_org + g.cb_n
    if g.lk_bss + g.bs_n > K_TOP:
        er_stop("PROGRAM TOO BIG")
    for g.fx_i in range(g.fx_n):
        lk_fix()


def lk_fix():
    """LK.FIX. Resolve fixup g.fx_i. g.lk_v is the address of the value."""
    uxc_code.fx_read()
    if g.fx_s == K_SEC_CODE:
        g.lk_v = g.lk_org + g.fx_v
    if g.fx_s == K_SEC_REC:
        uxc_code.rt_address()
    if g.fx_s == K_SEC_STR:
        g.lk_v = g.lk_str + g.fx_v
    if g.fx_s == K_SEC_VAR:
        g.lk_v = g.lk_var + g.fx_v
    if g.fx_s == K_SEC_BSS:
        g.lk_v = g.lk_bss + g.fx_v
    if g.fx_s == K_SEC_VAR and g.fx_v >= K_FRAME_BASE:
        uxc_sub.sb_pool_of()
        g.lk_v = g.lk_bss + g.sb_pool + g.fx_v - 65536
    if g.fx_s == K_SEC_BSS and g.fx_v >= K_FRAME_BASE:
        uxc_sub.sb_pool_of()
        g.lk_v = g.lk_bss + g.sb_pool + g.fx_v - 65536
    if g.fx_s == K_SEC_TEMP:
        uxc_sub.sb_pool_of()
        g.lk_v = g.lk_bss + g.sb_pool + g.fx_v
    if g.fx_s == K_SEC_LABEL:
        g.sy_r = g.fx_v
        uxc_sym.sy_get()
        if (g.sy_flags & 1) == 0:
            er_stop("LABEL NOT FOUND")
        g.lk_v = g.lk_org + g.sy_val
    g.lk_hi = g.lk_v // 256
    g.lk_lo = g.lk_v - g.lk_hi * 256
    if g.fx_k == K_F_LO:
        g.cb_at = g.fx_at
        g.cb_b = g.lk_lo
        cb_put()
        return
    if g.fx_k == K_F_HI:
        g.cb_at = g.fx_at
        g.cb_b = g.lk_hi
        cb_put()
        return
    # ABS: add to the addend in the code.
    g.cb_at = g.fx_at
    cb_get()
    g.lk_w = g.cb_b
    g.cb_at = g.fx_at + 1
    cb_get()
    g.lk_w = g.lk_w + 256 * g.cb_b + g.lk_v
    if g.lk_w > 65535:
        g.lk_w = g.lk_w - 65536
    g.lk_hi = g.lk_w // 256
    g.cb_at = g.fx_at
    g.cb_b = g.lk_w - g.lk_hi * 256
    cb_put()
    g.cb_at = g.fx_at + 1
    g.cb_b = g.lk_hi
    cb_put()


def lk_write():
    """LK.WRITE. The PRG goes into g.out_folder."""
    g.lk_hi = g.lk_org // 256
    with open(os.path.join(g.out_folder, g.ui_obj), "wb") as prg:
        prg.write(bytes((g.lk_org - g.lk_hi * 256, g.lk_hi)))
        for g.cb_at in range(g.cb_n):
            cb_get()
            prg.write(bytes((g.cb_b,)))
