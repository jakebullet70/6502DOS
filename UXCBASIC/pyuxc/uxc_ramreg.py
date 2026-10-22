"""#REGION_SLOT: SUBs whose code runs from a RAM bank at $A000.

    #REGION_SLOT n   n is 1 or 0. Each SUB or FUNCTION after #REGION_SLOT 1 goes to region 1,
                     a RAM bank that the program takes at startup. After #REGION_SLOT 0 they
                     stay in low RAM. An included file starts in its includer's slot, and the
                     includer's slot holds again after it. The main code stays in low RAM, and
                     so do the variables and the strings of every SUB.

    rg_line()     dd_keep_line's #REGION_SLOT, with the token at REGION_SLOT
    rg_sub()      in sb_sub, with the SUB's record in g.sb_current: the SUB joins the region
                  when its slot is 1
    rg_store()    sm_store to the constant address 0: stops the compile in a SUB of the region
    rg_asm()      in as_instruction, after as_choose: a write to $00 stops the compile in a SUB
                  of the region
    rg_ranges()   at the start of the link step, after UXC-DEAD.BL: the code range of each SUB
                  of the region, before SB.POOLS writes over K_SY_END. g.rg_on is 1 when one is
                  left in
    rg_split()    then: cut the region's SUBs out of the code into g.rg_code and their fixups
                  into g.rg_fix, then add the veneers in low RAM
    rg_load()     first in the startup work: T_RGLOAD
    rg_place()    after the variables: append the region's code and its veneers
    rg_code_address()  in lk_fix: the address of code offset g.lk_v

$00 selects the RAM bank at $A000. The file holds the region's image after the variables, where
the array space starts. T_RGLOAD, first in the startup work, takes a free RAM bank, copies the
image to $A000 there, and keeps the bank in R_RGBANK. The array space, the temps and the data
records then cover the image. A code offset from g.rg_base on is in the region, at $A000 + the
offset - g.rg_base.

A call across the edge goes to a veneer on the caller's side, a T_FARCALL, one per SUB. It
loads the SUB's address and jumps to T_RGCALL, which calls the SUB through bank_call with the
region's bank selected and then selects the caller's bank again. A call within a side is a JSR,
and so is a call from the region to a runtime routine. A GOTO, or a jump of any kind but a SUB
call, across the edge stops the link. R_ERRORB takes R_ERROR's place, so that an error in the
region prints its bank.

The cut out of the low code uses UXC-DEAD.BL's g.dd_from, g.dd_to, g.dd_sum and dd_shift, with
the ranges of the SUBs moved.
"""

from uxc_code import cb_add, cb_get, emit, fx_put, fx_read, rt_use
from uxc_defs import K_F_ABS, K_FX_MAX, K_SEC_BSS, K_SEC_CODE, K_SEC_CONST, K_SEC_LABEL, \
    K_SEC_REC, K_SK_LABEL, K_SK_SUB, K_SY_END, K_TOP, K_TT_EOL, K_TT_NUM
import uxc_dead
import uxc_lex
import uxc_rombank
import uxc_sym
import uxc_tpl as T
from uxc_state import er_stop, er_syntax, g

K_RG_ORG = 0xA000
K_RG_ROOM = 8192


def rg_line():
    """RG.LINE. #REGION_SLOT n, with the token at REGION_SLOT. The token is left at the end of
    the line."""
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NUM:
        er_syntax()
    if g.tk_v > 1:
        er_stop("#REGION_SLOT IS 0 OR 1")
    g.rg_slot = g.tk_v
    uxc_lex.lx_next()
    if g.tk_t != K_TT_EOL:
        er_syntax()


def rg_sub():
    if g.rg_slot != 0:
        g.rg_subs.append(g.sb_current)


def rg_in_region():
    """RG.IN.REGION. 1 when the code being compiled is a SUB of the region."""
    if g.sb_current == 0 or len(g.rg_subs) == 0:
        return 0
    if g.rg_subs[-1] != g.sb_current:
        return 0
    return 1


def rg_store():
    if rg_in_region() != 0:
        er_stop("RAM BANK WRITE IN A REGION")


def rg_asm():
    """RG.ASM. With the mode chosen: an instruction that writes the address $00 itself."""
    if g.as_form != 3 or g.as_known == 0 or g.as_v != 0:
        return
    if g.as_mnemonic not in ("STA", "STX", "STY", "STZ", "INC", "DEC", "ASL", "LSR", "ROL",
                             "ROR", "TSB", "TRB", "RMB", "SMB"):
        return
    rg_store()


def rg_ranges():
    """RG.RANGES. g.rg_from, g.rg_to and g.rg_record: each SUB of the region left in, in code
    order, from its JMP around to its end."""
    g.rg_on = 0
    ranges = []
    for g.rg_r in range(1, g.sy_n + 1):
        g.sy_r = g.rg_r
        uxc_sym.sy_get()
        if g.sy_kind == K_SK_SUB and (g.sy_flags & 1) != 0 and g.rg_r in g.rg_subs:
            ranges.append((g.sy_val - 3, g.ram[g.sy_ad + K_SY_END] +
                           256 * g.ram[g.sy_ad + K_SY_END + 1], g.rg_r))
    if len(ranges) == 0:
        return
    if g.lk_raw != 0 or g.lk_apart != 0 or g.rb_on != 0:
        er_stop("#REGION_SLOT WITH #ORG, #DATA OR #ROMBANKS")
    if g.target != "6502dos":
        er_stop("#REGION_SLOT NEEDS 6502DOS")
    g.rg_on = 1
    ranges.sort()
    g.rg_from = [r[0] for r in ranges]
    g.rg_to = [r[1] for r in ranges]
    g.rg_record = [r[2] for r in ranges]
    g.rg_n = len(ranges)
    # The records the startup and the veneers name must be known before rt_close.
    for g.rt_id in (T.T_RGCALL, T.R_EMEM, T.R_ERRORB):
        rt_use()


def rg_find(at):
    """RG.FIND. The last SUB of the region whose range starts at or before code offset at, or
    -1."""
    low = 0
    high = g.rg_n
    while low < high:
        mid = (low + high) // 2
        if g.rg_from[mid] <= at:
            low = mid + 1
        else:
            high = mid
    return low - 1


def rg_side_of(at):
    """RG.SIDE.OF. (1, the offset in the region) for code offset at inside the body of a SUB
    of the region, else (0, its offset in the low code after the cut). The JMP around a SUB
    moved is not in its body: the code after the cut lands there."""
    j = rg_find(at)
    if j >= 0 and at >= g.rg_from[j] + 3 and at < g.rg_to[j]:
        return 1, at - g.rg_from[j] - 3 + g.rg_at[j]
    g.dd_at = at
    uxc_dead.dd_shift()
    return 0, g.dd_at


def rg_split():
    """RG.SPLIT. Cut the region's SUBs out of the code into g.rg_code and their fixups into
    g.rg_fix, then add the veneers in low RAM. Out: g.rg_size, the bytes of the region."""
    g.rg_at = [0] * g.rg_n
    g.rg_code = bytearray()
    g.dd_n = 0
    cut = 0
    for i in range(g.rg_n):
        g.rg_at[i] = len(g.rg_code)
        for g.cb_at in range(g.rg_from[i] + 3, g.rg_to[i]):
            cb_get()
            g.rg_code.append(g.cb_b)
        cut = cut + g.rg_to[i] - g.rg_from[i]
        g.dd_from[g.dd_n] = g.rg_from[i]
        g.dd_to[g.dd_n] = g.rg_to[i]
        g.dd_sum[g.dd_n] = cut
        g.dd_n = g.dd_n + 1
    g.rg_veneer_length = uxc_rombank.rb_length(T.T_FARCALL)
    g.rg_veneer_at = [-1] * (g.sy_n + 1)
    g.rg_veneers = [[], []]
    g.rg_veneer_base = [g.cb_n - cut, len(g.rg_code)]
    rg_fixups()
    rg_records()
    uxc_dead.dd_code()
    if g.cb_n != g.rg_veneer_base[0]:
        er_stop("REGION CUT LOST BYTES")
    for g.rg_r in g.rg_veneers[0]:
        rg_veneer()
    g.rg_size = len(g.rg_code) + len(g.rg_veneers[1]) * g.rg_veneer_length
    if g.rg_size > K_RG_ROOM:
        er_stop("REGION 1 FULL")


def rg_fixups():
    """RG.FIXUPS. Each fixup goes with its code: kept in place for the low code, into g.rg_fix
    for the region, or dropped with the JMP around a SUB moved. A call across the edge goes to
    the SUB's veneer on the caller's side."""
    g.rg_fix = []
    kept = 0
    for i in range(g.fx_n):
        g.fx_i = i
        fx_read()
        j = rg_find(g.fx_at)
        if j >= 0 and g.fx_at < g.rg_from[j] + 3:
            continue
        at = g.fx_at
        side, g.fx_at = rg_side_of(at)
        if g.fx_s == K_SEC_CODE:
            target_side, g.fx_v = rg_side_of(g.fx_v)
            if target_side != side:
                er_stop("JUMP ACROSS THE REGION")
        if g.fx_s == K_SEC_LABEL:
            rg_label(side, at)
        if side == 1:
            g.rg_fix.append((g.fx_at, g.fx_k, g.fx_s, g.fx_v, g.fx_ow))
            continue
        g.fx_i = kept
        fx_put()
        kept = kept + 1
    g.fx_n = kept


def rg_label(side, at):
    """RG.LABEL. A K_SEC_LABEL fixup read, at code offset at before the cut, on side. A JSR to
    a SUB on the other side goes to its veneer, a K_SEC_CODE fixup on this side."""
    g.sy_r = g.fx_v
    uxc_sym.sy_get()
    if (g.sy_flags & 1) == 0:
        return
    if rg_side_of(g.sy_val)[0] == side:
        return
    g.cb_at = at - 1
    cb_get()
    if g.sy_kind != K_SK_SUB or g.fx_k != K_F_ABS or g.cb_b != 0x20:
        er_stop("GOTO ACROSS THE REGION")
    if g.rg_veneer_at[g.fx_v] < 0:
        g.rg_veneer_at[g.fx_v] = g.rg_veneer_base[side] + \
            len(g.rg_veneers[side]) * g.rg_veneer_length
        g.rg_veneers[side].append(g.fx_v)
    g.fx_s = K_SEC_CODE
    g.fx_v = g.rg_veneer_at[g.fx_v]


def rg_records():
    """RG.RECORDS. Move the value of each placed LABEL and SUB to its side's offset.
    g.rg_moved lists those in the region, which rg_place moves again to g.rg_base."""
    g.rg_moved = []
    for g.rg_r in range(1, g.sy_n + 1):
        g.sy_r = g.rg_r
        uxc_sym.sy_get()
        if (g.sy_kind == K_SK_LABEL or g.sy_kind == K_SK_SUB) and (g.sy_flags & 1) != 0:
            side, g.sy_val = rg_side_of(g.sy_val)
            uxc_sym.sy_set()
            if side == 1:
                g.rg_moved.append(g.rg_r)
    g.dd_at = g.lk_init_at
    uxc_dead.dd_shift()
    g.lk_init_at = g.dd_at


def rg_veneer():
    """RG.VENEER. A T_FARCALL to the SUB of record g.rg_r, on the other side, through
    T_RGCALL."""
    g.sl_s[0] = K_SEC_LABEL
    g.sl_v[0] = g.rg_r
    g.sl_s[1] = K_SEC_REC
    g.sl_v[1] = T.T_RGCALL
    emit(T.T_FARCALL)


def rg_load():
    """RG.LOAD. T_RGLOAD copies g.rg_size bytes from the start of the array space, where
    rg_place puts the image."""
    g.sl_s[0] = K_SEC_BSS
    g.sl_v[0] = 0
    g.sl_s[1] = K_SEC_CONST
    g.sl_v[1] = g.rg_size
    emit(T.T_RGLOAD)


def rg_place():
    """RG.PLACE. After the variables: the region's code, its fixups, its records and its
    veneers, from g.rg_base on."""
    g.rg_base = g.cb_n
    for g.cb_b in g.rg_code:
        cb_add()
    for g.fx_at, g.fx_k, g.fx_s, g.fx_v, g.fx_ow in g.rg_fix:
        if g.fx_n >= K_FX_MAX:
            er_stop("TOO MANY FIXUPS")
        g.fx_at = g.fx_at + g.rg_base
        if g.fx_s == K_SEC_CODE:
            g.fx_v = g.fx_v + g.rg_base
        g.fx_i = g.fx_n
        fx_put()
        g.fx_n = g.fx_n + 1
    for g.sy_r in g.rg_moved:
        uxc_sym.sy_get()
        g.sy_val = g.sy_val + g.rg_base
        uxc_sym.sy_set()
    for g.rg_r in g.rg_veneers[1]:
        rg_veneer()
    if g.cb_n - g.rg_base != g.rg_size:
        er_stop("REGION SIZE CHANGED")
    if g.lk_org + g.cb_n > K_TOP:
        er_stop("PROGRAM TOO BIG")


def rg_code_address():
    """RG.CODE.ADDRESS. In g.lk_v, a code offset; out g.lk_v, its address."""
    if g.rg_on != 0 and g.lk_v >= g.rg_base:
        g.lk_v = K_RG_ORG + g.lk_v - g.rg_base
        return
    g.lk_v = g.lk_org + g.lk_v
