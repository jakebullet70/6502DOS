"""UXC-LINK.BL: the link step, and the PRG writer.

    lk_init_call()   at the start of the program, the call to the startup work
    lk_link()        append the startup work, the runtime routines, the strings and the
                     variables to the code, then resolve every fixup
    lk_write()       in  g.ui_obj    write the PRG: the load address, then the code buffer.
                     With #ORG, the code buffer only. Out: g.lk_size, the file's bytes

UXC-LINK.BL has the order of the routines and why a forward call needs nothing special.
"""

import os

import uxc_code
import uxc_dead
import uxc_ramreg
import uxc_rombank
from uxc_code import cb_add, cb_get, cb_put, emit
from uxc_defs import K_F_HI, K_F_LO, K_FRAME_BASE, K_SEC_BSS, K_SEC_CODE, K_SEC_CONST, \
    K_SEC_LABEL, K_SEC_REC, K_SEC_RGDATA, K_SEC_RGSIZE, K_SEC_STR, K_SEC_TEMP, K_SEC_VAR, K_SK_LABEL, K_TOP
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
    cleared. With #DATA the strings, the variables and the array space lie outside the file in
    that order: the startup copies the strings there and one clear covers the rest. The data records follow the pools; the startup sets the first byte
    of those that ask for it to 0. For 6502DOS it also stores the page of the program's end in
    PSP_TOP. The SUBs nothing calls are left out first, then the global variables nothing
    names, then the string literals nothing names."""
    uxc_dead.dd_strip()
    uxc_dead.dv_strip()
    uxc_dead.ds_strip()
    uxc_ramreg.rg_ranges()
    if g.rg_on != 0:
        uxc_ramreg.rg_data()
        uxc_ramreg.rg_split()
    if g.rb_on != 0:
        uxc_rombank.rb_ranges()
    g.sy_r = g.lk_init_record
    uxc_sym.sy_get()
    g.sy_val = g.cb_n
    g.sy_flags = 1
    uxc_sym.sy_set()
    g.lk_start = g.cb_n
    uxc_code.rt_close()
    if g.rg_on != 0:
        uxc_ramreg.rg_load()
    if g.lk_apart != 0 and g.vr_n + g.bs_n > 0:
        g.sl_s[0] = K_SEC_VAR
        g.sl_v[0] = 0
        g.sl_s[1] = K_SEC_CONST
        g.sl_v[1] = g.vr_n + g.bs_n
        emit(T.T_ZERO)
    elif g.bs_n > 0:
        g.sl_s[0] = K_SEC_BSS
        g.sl_v[0] = 0
        g.sl_s[1] = K_SEC_CONST
        g.sl_v[1] = g.bs_n
        emit(T.T_ZERO)
    if g.lk_apart != 0 and g.sp_n > 0:
        lk_strs_copy()
    uxc_str.sg_maxes()
    uxc_sub.sb_pools()
    # The data records follow the pools.
    g.rt_data_at = g.bs_n
    g.bs_n = g.bs_n + g.rt_dn_all
    uxc_code.rt_data_zero()
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
    if g.rb_on != 0:
        uxc_rombank.rb_split()
    if g.rg_on != 0:
        uxc_ramreg.rg_runtime()
    g.lk_i = 0
    while g.lk_i < g.rt_n:
        uxc_code.rt_place()
        if g.rt_dn == 0 and (g.rb_on == 0 or g.rb_need[g.rt_id] != 0) and \
                (g.rg_on == 0 or (g.rt_id != T.R_ERROR and g.rg_runtime_k[g.rt_id] == 0)):
            emit(g.rt_id)
        g.lk_i = g.lk_i + 1
    # The strings, out of their own bank. With #DATA the startup copies them to its address.
    g.lk_str = g.lk_org + g.cb_n
    if g.lk_apart != 0 and g.sp_n > 0:
        if g.sp_n != g.lk_strs_n:
            er_stop("STRINGS ADDED LATE")
        g.sy_r = g.lk_strs_record
        uxc_sym.sy_get()
        g.sy_val = g.cb_n
        g.sy_flags = 1
        uxc_sym.sy_set()
    uxc_code.sp_copy()
    if g.rb_on != 0:
        uxc_rombank.rb_end()
    # The variables, all 0, in the file or after the strings at #DATA's address.
    g.lk_var = g.lk_org + g.cb_n
    if g.lk_apart != 0:
        g.lk_str = g.lk_data
        g.lk_var = g.lk_data + g.sp_n
    else:
        for g.lk_i in range(1, g.vr_n + 1):
            g.cb_b = 0
            cb_add()
    # The region's image follows, where the array space starts.
    g.lk_low_n = g.cb_n
    if g.rg_on != 0:
        uxc_ramreg.rg_place()
    # The array space follows, outside the file.
    g.lk_bss = g.lk_var + g.vr_n
    if g.lk_bss + g.bs_n > K_TOP or g.lk_org + g.lk_low_n > 65536:
        er_stop("PROGRAM TOO BIG")
    if g.lk_apart != 0 and g.lk_data < g.lk_org + g.cb_n and g.lk_org < g.lk_bss + g.bs_n:
        er_stop("#DATA OVERLAPS THE CODE")
    g.rt_data_at = g.lk_bss + g.rt_data_at
    uxc_code.rt_data_place()
    for g.fx_i in range(g.fx_n):
        lk_fix()


def lk_strs_copy():
    """LK.STRS.COPY. At startup, with #DATA: copy the g.sp_n bytes of strings from the file,
    at the label %STRS, which lk_link places, to the data area."""
    g.sy_name = "%STRS"
    g.sy_ow = 0
    g.sy_kind = K_SK_LABEL
    g.sy_type = 0
    g.sy_val = 0
    g.sy_flags = 0
    g.sy_cnt = 0
    uxc_sym.sy_add()
    g.lk_strs_record = g.sy_r
    g.lk_strs_n = g.sp_n
    g.sl_s[0] = K_SEC_LABEL
    g.sl_v[0] = g.lk_strs_record
    g.sl_s[1] = K_SEC_STR
    g.sl_v[1] = 0
    g.sl_s[2] = K_SEC_CONST
    g.sl_v[2] = g.sp_n
    emit(T.T_LITCOPY)


def lk_fix():
    """LK.FIX. Resolve fixup g.fx_i. g.lk_v is the address of the value."""
    uxc_code.fx_read()
    if g.fx_s == K_SEC_CODE:
        g.lk_v = g.fx_v
        uxc_ramreg.rg_code_address()
    if g.fx_s == K_SEC_REC:
        if g.rg_on != 0 and g.fx_v == T.R_ERROR:
            g.fx_v = T.R_ERRORB
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
    if g.fx_s == K_SEC_RGDATA:
        uxc_ramreg.rg_data_address()
    if g.fx_s == K_SEC_RGSIZE:
        uxc_ramreg.rg_bytes()
    if g.fx_s == K_SEC_LABEL:
        g.sy_r = g.fx_v
        uxc_sym.sy_get()
        if (g.sy_flags & 1) == 0:
            er_stop("LABEL NOT FOUND")
        g.lk_v = g.sy_val
        uxc_ramreg.rg_code_address()
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
    g.lk_size = g.cb_n
    with open(os.path.join(g.out_folder, g.ui_obj), "wb") as prg:
        if g.lk_raw == 0:
            prg.write(bytes((g.lk_org - g.lk_hi * 256, g.lk_hi)))
            g.lk_size = g.cb_n + 2
        for g.cb_at in range(g.cb_n):
            cb_get()
            prg.write(bytes((g.cb_b,)))
