"""UXC-CODE.BL: the template table, the code buffer, the string literals, the fixups, and EMIT.

    tp_load(folder)     load UXC.TPL.BIN from folder into g.tp_bank
    cb_put()   in  g.cb_at g.cb_b      the byte at offset g.cb_at of the code
    cb_get()   in  g.cb_at             out g.cb_b
    cb_add()   in  g.cb_b              append a byte; g.cb_n is the length of the code
    sp_add()   in  g.sp_s              out g.sp_v, the string's offset among the strings, and
                                       g.sp_new, 0 when an equal string was there already
    fx_add()   in  g.fx_at g.fx_k g.fx_s g.fx_v    a fixup, owned by g.sb_current
    fx_read()  in  g.fx_i              out g.fx_at g.fx_k g.fx_s g.fx_v g.fx_ow
    fx_put()   in  g.fx_i g.fx_at g.fx_k g.fx_s g.fx_v g.fx_ow    overwrite fixup g.fx_i
    emit(id)                           copy record id into the code, with slots g.sl_s g.sl_v
    rt_use()   in  g.rt_id             the runtime routine is needed at the end of the program
    rt_clear()                         no runtime routine is needed yet
    rt_close()                         every record the used ones name is used, and the bytes
                                       of the data records
    rt_data_zero()                     the startup's 0 in the data records that ask for it
    rt_place() rt_data_place() rt_address()    the record addresses, for the link step
    cs_clear() cs_put() cs_get()       the ON CASE targets in g.cs_bank, for UXC-CASE.BL
    sp_copy()                          append the strings to the code

uxc_defs.py has the layout of a fixup. UXC-CODE.BL has the layout of the code buffer. Offset n of the code is index
n MOD 8192 of g.cb_bank[n // 8192]. cb_put, fx_add and fx_put take a bank when the offset is past the
last one. A K_RT_ address is index K_RT_x - $A000 of g.rt_bank.
"""

import os

from uxc_defs import K_CS_SIZE, K_F_ABS, K_F_HI, K_F_LO, K_F_REC, K_F_REC_HI, K_F_SELF, K_FX_BANK, \
    K_RT_ADDR, K_RT_LIST, K_RT_USED, K_SEC_CODE, K_SEC_CONST, K_SEC_REC, K_TP_DATA
import uxc_tpl as T
from uxc_state import er_stop, g, uxc_bank


def tp_load(folder):
    uxc_bank()
    g.tp_bank = g.uxc_b
    path = os.path.join(folder, "UXC.TPL.BIN")
    if not os.path.exists(path):
        er_stop("FILE NOT FOUND: UXC.TPL.BIN")
    with open(path, "rb") as table:
        data = table.read()
    g.tp_bank[:len(data)] = data
    g.ram = g.tp_bank
    if g.ram[0:4] != b"UXT\x01":
        er_stop("UXC.TPL.BIN IS NOT A TEMPLATE TABLE")
    # uxc_tpl gave this program the record ids. A table from another build has others.
    if g.ram[4] + 256 * g.ram[5] != T.TPL_COUNT:
        er_stop("UXC.TPL.BIN DOES NOT MATCH UXC")
    g.tp_ix = g.ram[6] + 256 * g.ram[7]


def cb_put():
    g.cb_bi = g.cb_at // 8192
    while g.cb_bi >= len(g.cb_bank):
        uxc_bank()
        g.cb_bank.append(g.uxc_b)
    g.ram = g.cb_bank[g.cb_bi]
    g.ram[g.cb_at - g.cb_bi * 8192] = g.cb_b


def cb_get():
    g.cb_bi = g.cb_at // 8192
    g.ram = g.cb_bank[g.cb_bi]
    g.cb_b = g.ram[g.cb_at - g.cb_bi * 8192]


def cb_add():
    g.cb_at = g.cb_n
    cb_put()
    g.cb_n = g.cb_n + 1


def sp_add():
    """SP.ADD. A string literal, kept as [max][len][data] with max = len. A literal equal to
    one kept already is that one."""
    g.sp_l = len(g.sp_s)
    g.sp_v = 0
    g.sp_new = 0
    g.ram = g.sp_bank
    while g.sp_v < g.sp_n:
        if g.ram[1 + g.sp_v] == g.sp_l:
            g.sp_i = 1
            while g.sp_i <= g.sp_l and g.ram[1 + g.sp_v + g.sp_i] == ord(g.sp_s[g.sp_i - 1]):
                g.sp_i = g.sp_i + 1
            if g.sp_i > g.sp_l:
                return
        g.sp_v = g.sp_v + g.ram[g.sp_v] + 2
    if g.sp_n + g.sp_l + 2 > 8192:
        er_stop("TOO MANY STRINGS")
    g.sp_new = 1
    g.ram[g.sp_n] = g.sp_l
    g.ram[1 + g.sp_n] = g.sp_l
    for g.sp_i in range(1, g.sp_l + 1):
        g.ram[1 + g.sp_n + g.sp_i] = ord(g.sp_s[g.sp_i - 1])
    g.sp_v = g.sp_n
    g.sp_n = g.sp_n + g.sp_l + 2


def fx_add():
    g.fx_bi = g.fx_n // K_FX_BANK
    while g.fx_bi >= len(g.fx_bank):
        uxc_bank()
        g.fx_bank.append(g.uxc_b)
    g.ram = g.fx_bank[g.fx_bi]
    g.fx_ad = (g.fx_n - g.fx_bi * K_FX_BANK) * 10
    g.ram[g.fx_ad] = g.fx_at & 255
    g.ram[g.fx_ad + 1] = (g.fx_at >> 8) & 255
    g.ram[g.fx_ad + 2] = g.fx_at >> 16
    g.ram[g.fx_ad + 3] = g.fx_k
    g.ram[g.fx_ad + 4] = g.fx_s
    g.ram[g.fx_ad + 5] = g.fx_v & 255
    g.ram[g.fx_ad + 6] = (g.fx_v >> 8) & 255
    g.ram[g.fx_ad + 7] = g.fx_v >> 16
    g.ram[g.fx_ad + 8] = g.sb_current & 255
    g.ram[g.fx_ad + 9] = g.sb_current >> 8
    g.fx_n = g.fx_n + 1


def fx_put():
    """FX.PUT. Write fixup g.fx_i from g.fx_at g.fx_k g.fx_s g.fx_v g.fx_ow."""
    g.fx_bi = g.fx_i // K_FX_BANK
    while g.fx_bi >= len(g.fx_bank):
        uxc_bank()
        g.fx_bank.append(g.uxc_b)
    g.ram = g.fx_bank[g.fx_bi]
    g.fx_ad = (g.fx_i - g.fx_bi * K_FX_BANK) * 10
    g.ram[g.fx_ad] = g.fx_at & 255
    g.ram[g.fx_ad + 1] = (g.fx_at >> 8) & 255
    g.ram[g.fx_ad + 2] = g.fx_at >> 16
    g.ram[g.fx_ad + 3] = g.fx_k
    g.ram[g.fx_ad + 4] = g.fx_s
    g.ram[g.fx_ad + 5] = g.fx_v & 255
    g.ram[g.fx_ad + 6] = (g.fx_v >> 8) & 255
    g.ram[g.fx_ad + 7] = g.fx_v >> 16
    g.ram[g.fx_ad + 8] = g.fx_ow & 255
    g.ram[g.fx_ad + 9] = g.fx_ow >> 8


def fx_read():
    g.fx_bi = g.fx_i // K_FX_BANK
    g.ram = g.fx_bank[g.fx_bi]
    g.fx_ad = (g.fx_i - g.fx_bi * K_FX_BANK) * 10
    g.fx_at = g.ram[g.fx_ad] + 256 * g.ram[g.fx_ad + 1] + 65536 * g.ram[g.fx_ad + 2]
    g.fx_k = g.ram[g.fx_ad + 3]
    g.fx_s = g.ram[g.fx_ad + 4]
    g.fx_v = g.ram[g.fx_ad + 5] + 256 * g.ram[g.fx_ad + 6] + 65536 * g.ram[g.fx_ad + 7]
    g.fx_ow = g.ram[g.fx_ad + 8] + 256 * g.ram[g.fx_ad + 9]


def emit(record_id):
    """EM.EMIT. The record's code is read out of the table first, into g.em_b, because the
    code buffer is in another bank. em_fix reads each fixup from the table at g.em_fa."""
    g.em_id = record_id
    g.ram = g.tp_bank
    g.em_a = g.ram[g.tp_ix + g.em_id * 2] + 256 * g.ram[g.tp_ix + g.em_id * 2 + 1]
    g.em_len = g.ram[g.em_a]
    g.em_nf = g.ram[g.em_a + 1]
    for g.em_i in range(g.em_len):
        g.em_b[g.em_i] = g.ram[g.em_a + 2 + g.em_i]
    g.em_fa = g.em_a + 2 + g.em_len
    g.em_start = g.cb_n
    for g.em_j in range(g.em_nf):
        em_fix()
    for g.em_i in range(g.em_len):
        g.cb_b = g.em_b[g.em_i]
        cb_add()


def em_fix():
    """EM.FIX. Fixup g.em_j of the record being emitted. rt_use and fx_add leave other banks
    selected, so g.tp_bank is selected again for each fixup."""
    g.ram = g.tp_bank
    g.em_fp = g.em_fa + g.em_j * 3
    g.em_o = g.ram[g.em_fp]
    g.em_k = g.ram[g.em_fp + 1]
    g.em_g = g.ram[g.em_fp + 2]
    g.fx_at = g.em_start + g.em_o
    # SELF: the record's own address, which is its code offset from the program's start.
    if g.em_k == K_F_SELF:
        g.fx_k = K_F_ABS
        g.fx_s = K_SEC_CODE
        g.fx_v = g.em_start
        fx_add()
        return
    # REC: another record, which the link step places once. REC_HI is record <arg> + 256.
    if g.em_k == K_F_REC_HI:
        g.em_k = K_F_REC
        g.em_g = g.em_g + 256
    if g.em_k == K_F_REC:
        g.rt_id = g.em_g
        rt_use()
        g.fx_k = K_F_ABS
        g.fx_s = K_SEC_REC
        g.fx_v = g.em_g
        fx_add()
        return
    g.em_s = g.sl_s[g.em_g]
    g.em_v = g.sl_v[g.em_g]
    if g.em_s != K_SEC_CONST:
        g.fx_k = g.em_k
        g.fx_s = g.em_s
        g.fx_v = g.em_v
        fx_add()
        return
    # A constant goes into the code now.
    g.em_hi = g.em_v // 256
    g.em_lo = g.em_v - g.em_hi * 256
    if g.em_k == K_F_LO:
        g.em_b[g.em_o] = g.em_lo
        return
    if g.em_k == K_F_HI:
        g.em_b[g.em_o] = g.em_hi
        return
    g.em_w = g.em_b[g.em_o] + 256 * g.em_b[g.em_o + 1] + g.em_v
    if g.em_w > 65535:
        g.em_w = g.em_w - 65536
    g.em_hi = g.em_w // 256
    g.em_b[g.em_o] = g.em_w - g.em_hi * 256
    g.em_b[g.em_o + 1] = g.em_hi


def rt_use():
    """RT.USE. K_RT_LIST lists the records needed, in the order they were first needed. It
    leaves g.rt_bank selected."""
    g.ram = g.rt_bank
    if g.ram[K_RT_USED - 0xA000 + g.rt_id] != 0:
        return
    g.ram[K_RT_USED - 0xA000 + g.rt_id] = 1
    g.ram[K_RT_LIST - 0xA000 + g.rt_n * 2] = g.rt_id & 255
    g.ram[K_RT_LIST - 0xA000 + g.rt_n * 2 + 1] = g.rt_id // 256
    g.rt_n = g.rt_n + 1


def rt_clear():
    g.ram = g.rt_bank
    for g.cb_i in range(T.TPL_COUNT + 1):
        g.ram[K_RT_USED - 0xA000 + g.cb_i] = 0


def rt_get():
    """RT.GET. In g.lk_i, out g.rt_id, record g.lk_i of K_RT_LIST, and g.rt_dn, its size when
    it is a data record, else 0, and g.rt_dz, 1 when the startup sets its first byte to 0.
    Out: g.rt_a, its place in the table, with g.tp_bank selected."""
    g.ram = g.rt_bank
    g.rt_id = g.ram[K_RT_LIST - 0xA000 + g.lk_i * 2] + \
        256 * g.ram[K_RT_LIST - 0xA000 + g.lk_i * 2 + 1]
    g.ram = g.tp_bank
    g.rt_a = g.ram[g.tp_ix + g.rt_id * 2] + 256 * g.ram[g.tp_ix + g.rt_id * 2 + 1]
    g.rt_dn = 0
    g.rt_dz = 0
    if g.ram[g.rt_a + 1] >= K_TP_DATA:
        g.rt_dn = g.ram[g.rt_a]
        g.rt_dz = g.ram[g.rt_a + 1] - K_TP_DATA


def rt_close():
    """RT.CLOSE. Add to K_RT_LIST every record that a record on it names, so that the data
    records are known before the startup sets them. Out: g.rt_dn_all, the bytes of the data
    records."""
    g.rt_dn_all = 0
    g.lk_i = 0
    while g.lk_i < g.rt_n:
        rt_get()
        g.rt_dn_all = g.rt_dn_all + g.rt_dn
        if g.rt_dn == 0:
            g.rt_nf = g.ram[g.rt_a + 1]
            g.rt_fa = g.rt_a + 2 + g.ram[g.rt_a]
            for g.rt_j in range(g.rt_nf):
                g.ram = g.tp_bank
                g.rt_k = g.ram[g.rt_fa + g.rt_j * 3 + 1]
                g.rt_g = g.ram[g.rt_fa + g.rt_j * 3 + 2]
                if g.rt_k == K_F_REC_HI:
                    g.rt_k = K_F_REC
                    g.rt_g = g.rt_g + 256
                if g.rt_k == K_F_REC:
                    g.rt_id = g.rt_g
                    rt_use()
        g.lk_i = g.lk_i + 1


def rt_data_place():
    """RT.DATA.PLACE. In g.rt_data_at: each data record's address, in turn from there. A data
    record that rt_close did not count stops the link: the startup did not see it."""
    g.rt_at = g.rt_data_at
    g.rt_dn_all_placed = 0
    for g.lk_i in range(g.rt_n):
        rt_get()
        if g.rt_dn > 0:
            rt_address_set()
            g.rt_at = g.rt_at + g.rt_dn
            g.rt_dn_all_placed = g.rt_dn_all_placed + g.rt_dn
    if g.rt_dn_all_placed != g.rt_dn_all:
        er_stop("DATA RECORD LINKED LATE")


def rt_data_zero():
    """RT.DATA.ZERO. At startup, the first byte of each data record that asks for it = 0."""
    for g.lk_i in range(g.rt_n):
        rt_get()
        if g.rt_dz != 0:
            g.sl_s[0] = K_SEC_REC
            g.sl_v[0] = g.rt_id
            emit(T.T_STZ)


def rt_place():
    """RT.PLACE. In g.lk_i, out g.rt_id and g.rt_dn as rt_get: record g.lk_i of K_RT_LIST,
    whose address is set to the end of the code. A data record is left to rt_data_place."""
    rt_get()
    if g.rt_dn > 0:
        return
    g.rt_at = g.lk_org + g.cb_n
    rt_address_set()


def rt_address_set():
    """RT.ADDRESS.SET. In g.rt_id g.rt_at: the record's address."""
    g.ram = g.rt_bank
    g.rt_hi = g.rt_at // 256
    g.ram[K_RT_ADDR - 0xA000 + g.rt_id * 2] = g.rt_at - g.rt_hi * 256
    g.ram[K_RT_ADDR - 0xA000 + g.rt_id * 2 + 1] = g.rt_hi


def rt_address():
    """RT.ADDRESS. In g.fx_v, out g.lk_v: the address rt_place gave record g.fx_v."""
    g.ram = g.rt_bank
    g.lk_v = g.ram[K_RT_ADDR - 0xA000 + g.fx_v * 2] + \
        256 * g.ram[K_RT_ADDR - 0xA000 + g.fx_v * 2 + 1]


def cs_clear():
    """CS.CLEAR. In g.cs_at: the K_CS_SIZE bytes of ON CASE targets at g.cs_at are 0."""
    g.ram = g.cs_bank
    for g.cs_i in range(K_CS_SIZE):
        g.ram[g.cs_at + g.cs_i] = 0


def cs_put():
    """CS.PUT. In g.cs_at g.cs_w: the word at g.cs_at in g.cs_bank."""
    g.ram = g.cs_bank
    g.cs_hi = g.cs_w // 256
    g.ram[g.cs_at] = g.cs_w - g.cs_hi * 256
    g.ram[1 + g.cs_at] = g.cs_hi


def cs_get():
    """CS.GET. In g.cs_at, out g.cs_w: the word at g.cs_at in g.cs_bank."""
    g.ram = g.cs_bank
    g.cs_w = g.ram[g.cs_at] + 256 * g.ram[1 + g.cs_at]


def sp_copy():
    for g.sp_i in range(g.sp_n):
        g.ram = g.sp_bank
        g.cb_b = g.ram[g.sp_i]
        cb_add()
