"""UXC-SYM.BL: the symbol table, in banked RAM.

    sy_init()                               claim the banks, empty the table
    sy_find()  in  g.sy_name g.sy_ow        out g.sy_r, the record, or 0 when the name is not there
    sy_add()   in  g.sy_name g.sy_ow g.sy_kind g.sy_type g.sy_val g.sy_flags g.sy_cnt   out g.sy_r
    sy_get()   in  g.sy_r                   out g.sy_kind g.sy_type g.sy_val g.sy_flags g.sy_np
                                                g.sy_cnt g.sy_owner
    sy_set()   in  g.sy_r g.sy_type g.sy_val g.sy_flags g.sy_np
    sy_end_get()  in  g.sy_r               out g.sy_end, the code offset where SUB g.sy_r ends
    sy_end_set()  in  g.sy_r g.sy_end
    ty_size()  in  g.ty_code                out g.ty_bytes

UXC-SYM.BL has the record layout. After sy_at, sy_get, sy_set or sy_add, g.ram is the bank of
record g.sy_r and g.sy_ad is the record's offset in it. A value and a SUB's end are code
offsets of up to 3 bytes: the third byte of record r's value is index r * 2 of g.sy_xbank,
and of its end index r * 2 + 1.
"""

from uxc_defs import K_SY_END, K_SY_HEADS, K_SY_MAX, K_SYM_BANKS, K_TY_BYTE, K_TY_LONG
from uxc_state import er_stop, g, uxc_bank


def sy_init():
    for g.sy_i in range(K_SYM_BANKS):
        uxc_bank()
        g.sy_bank[g.sy_i] = g.uxc_b
    uxc_bank()
    g.sy_xbank = g.uxc_b
    g.ram = g.sy_bank[0]
    for g.sy_i in range(K_SY_HEADS):
        g.ram[g.sy_i] = 0
    g.sy_n = 0


def sy_hash():
    """SY.HASH. g.sy_h, the bucket of g.sy_name. g.sy_l is its length."""
    g.sy_l = len(g.sy_name)
    g.sy_h = 0
    for g.sy_i in range(1, g.sy_l + 1):
        g.sy_h = g.sy_h * 3 + ord(g.sy_name[g.sy_i - 1])
        g.sy_h = g.sy_h - (g.sy_h // 256) * 256


def sy_at():
    """SY.AT. The offset of record g.sy_r in g.sy_ad, with its bank selected."""
    g.sy_off = K_SY_HEADS + (g.sy_r - 1) * 32
    g.sy_bi = g.sy_off // 8192
    g.ram = g.sy_bank[g.sy_bi]
    g.sy_ad = g.sy_off - g.sy_bi * 8192


def sy_find():
    sy_hash()
    g.ram = g.sy_bank[0]
    g.sy_r = g.ram[g.sy_h * 2] + 256 * g.ram[g.sy_h * 2 + 1]
    while g.sy_r != 0:
        sy_at()
        if g.ram[g.sy_ad + 7] == g.sy_l and \
                g.ram[g.sy_ad + 8:g.sy_ad + 8 + g.sy_l] == g.sy_name.encode("latin-1"):
            if g.ram[g.sy_ad + 25] + 256 * g.ram[g.sy_ad + 26] == g.sy_ow:
                return
        g.sy_r = g.ram[g.sy_ad] + 256 * g.ram[g.sy_ad + 1]


def sy_add():
    """SY.ADD. A new record at the head of its bucket. The caller has found that the name is
    not there."""
    if g.sy_n >= K_SY_MAX:
        er_stop("TOO MANY NAMES")
    sy_hash()
    g.sy_n = g.sy_n + 1
    g.sy_r = g.sy_n
    g.ram = g.sy_bank[0]
    g.sy_hd = g.sy_h * 2
    g.sy_old = g.ram[g.sy_hd] + 256 * g.ram[g.sy_hd + 1]
    g.ram[g.sy_hd] = g.sy_r & 255
    g.ram[g.sy_hd + 1] = g.sy_r >> 8
    sy_at()
    g.ram[g.sy_ad] = g.sy_old & 255
    g.ram[g.sy_ad + 1] = g.sy_old >> 8
    g.ram[g.sy_ad + 2] = g.sy_kind
    g.ram[g.sy_ad + 3] = g.sy_type
    g.ram[g.sy_ad + 7] = g.sy_l
    for g.sy_i in range(1, g.sy_l + 1):
        g.ram[g.sy_ad + 7 + g.sy_i] = ord(g.sy_name[g.sy_i - 1])
    g.ram[g.sy_ad + 25] = g.sy_ow & 255
    g.ram[g.sy_ad + 26] = g.sy_ow >> 8
    g.ram[g.sy_ad + 28] = g.sy_cnt & 255
    g.ram[g.sy_ad + 29] = g.sy_cnt >> 8
    g.sy_np = 0
    sy_set()


def sy_get():
    g.ram = g.sy_xbank
    g.sy_hi = g.ram[g.sy_r * 2]
    sy_at()
    g.sy_kind = g.ram[g.sy_ad + 2]
    g.sy_type = g.ram[g.sy_ad + 3]
    g.sy_val = g.ram[g.sy_ad + 4] + 256 * g.ram[g.sy_ad + 5] + 65536 * g.sy_hi
    g.sy_flags = g.ram[g.sy_ad + 6]
    g.sy_np = g.ram[g.sy_ad + 27]
    g.sy_cnt = g.ram[g.sy_ad + 28] + 256 * g.ram[g.sy_ad + 29]
    g.sy_owner = g.ram[g.sy_ad + 25] + 256 * g.ram[g.sy_ad + 26]


def sy_set():
    g.ram = g.sy_xbank
    g.ram[g.sy_r * 2] = g.sy_val >> 16
    sy_at()
    g.ram[g.sy_ad + 4] = g.sy_val & 255
    g.ram[g.sy_ad + 5] = (g.sy_val >> 8) & 255
    g.ram[g.sy_ad + 3] = g.sy_type
    g.ram[g.sy_ad + 6] = g.sy_flags
    g.ram[g.sy_ad + 27] = g.sy_np


def sy_end_get():
    g.ram = g.sy_xbank
    g.sy_hi = g.ram[g.sy_r * 2 + 1]
    sy_at()
    g.sy_end = g.ram[g.sy_ad + K_SY_END] + 256 * g.ram[g.sy_ad + K_SY_END + 1] + 65536 * g.sy_hi


def sy_end_set():
    g.ram = g.sy_xbank
    g.ram[g.sy_r * 2 + 1] = g.sy_end >> 16
    sy_at()
    g.ram[g.sy_ad + K_SY_END] = g.sy_end & 255
    g.ram[g.sy_ad + K_SY_END + 1] = (g.sy_end >> 8) & 255


def ty_size():
    """TY.SIZE. g.ty_bytes, the bytes one value of type g.ty_code takes in a variable, an
    element or a parameter. A STRING there is the 2-byte address of its block."""
    g.ty_bytes = 2
    if g.ty_code == K_TY_BYTE:
        g.ty_bytes = 1
    if g.ty_code == K_TY_LONG:
        g.ty_bytes = 4
