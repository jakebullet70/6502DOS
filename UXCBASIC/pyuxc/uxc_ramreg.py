"""#REGION_SLOT: SUBs whose code runs from a RAM bank at $A000.

    #REGION_SLOT n   n is 0 to 63. Each SUB or FUNCTION after #REGION_SLOT n, n 1 or more,
                     goes to region n, a RAM bank of its own that the program takes at startup.
                     After #REGION_SLOT 0 they stay in low RAM. An included file starts in its
                     includer's slot, and the includer's slot holds again after it. The main
                     code stays in low RAM. A string literal or a global variable that only one
                     region's code names moves into that region; the others, the locals and the
                     temps stay in low RAM.

    rg_line()     dd_keep_line's #REGION_SLOT, with the token at REGION_SLOT
    rg_sub()      in sb_sub, with the SUB's record in g.sb_current: the SUB joins the region of
                  the slot, when the slot is 1 or more
    rg_pin_from(), rg_pin_to()  around the load of a STRING FUNCTION's result, or of a STRING
                  argument: what the code between names stays in low RAM
    rg_forward()  in sb_call_argument, before sg_pass: a STRING parameter passed on as an
                  address is noted
    rg_store()    sm_store to the constant address 0: stops the compile in a SUB of a region
    rg_asm()      in as_instruction, after as_choose: a write to $00 stops the compile in a SUB
                  of a region
    rg_ranges()   at the start of the link step, after UXC-DEAD.BL: the code range of each SUB
                  of a region, before SB.POOLS writes over K_SY_END. g.rg_on is 1 when one is
                  left in
    rg_data()     then: move the literals and the variables that only one region names into its
                  g.rg_data
    rg_split()    then: cut the regions' SUBs out of the code into g.rg_code and their fixups
                  into g.rg_fix, then add the gates and the veneers in low RAM
    rg_image_of(), rg_max()  in sg_maxes: a moved variable's string maxes go into g.rg_data
    rg_load()     first in the startup work: T_RGFROM, then a T_RGLOAD a region
    rg_runtime()  after the startup work: move into a region the runtime records that only its
                  code names
    rg_place()    after the variables: append each region's code, its veneers, its data and
                  its runtime records
    rg_code_address()  in lk_fix: the address of code offset g.lk_v
    rg_data_address()  in lk_fix: the address of the K_SEC_RGDATA fixup read

The regions are numbered 1 up, k, in the order of their slots. $00 selects the RAM bank at
$A000. The file holds the regions' images after the variables, where the array space starts,
one after the other. T_RGLOAD, first in the startup work, takes a free RAM bank for each, copies
its image to $A000 there, and writes the bank into the region's gate. The array space, the temps
and the data records then cover the images. A code offset from g.rg_base[k] on is in region k,
at $A000 + the offset - g.rg_base[k]. A K_SEC_RGDATA value is at $A000 + g.rg_data_at[k] + the
value, where k is the region of the fixup's own code.

A STRING argument passes the address of the caller's string. In a call from a region to a SUB
outside it, what the argument's code names stays in low RAM. So does what it names in a call
to a SUB of the same region that passes the parameter on, as an address, to a SUB outside the
region, or to another such SUB.
Trap: a WORD that holds the address of a variable moved into a region, passed out of the
region, points into the wrong bank.

A call across an edge goes to a veneer on the caller's side, a T_FARCALL, one a SUB and side.
It loads the SUB's address and jumps to a T_RGGATE in low RAM: the gate of the SUB's region, or
for a SUB in low RAM, the gate of the caller's region. The gate calls the SUB through bank_call
with the region's bank selected and then selects the caller's bank again. A call within a side
is a JSR, and so is a call from a region to a runtime record. A runtime record that only one
region's code, or records in that region, name moves into it. A data record, a record that
writes $00, the records that low code names, and R_RGLOAD, R_EMEM and R_ERRORB stay in low
RAM. A region's records follow its data in its image; rg_runtime writes the larger size into
the region's T_RGLOAD. A GOTO, or a jump of any kind but a SUB call, across an edge stops the link.
R_ERRORB takes R_ERROR's place, so that an error in a region prints its bank.

The cut out of the low code uses UXC-DEAD.BL's g.dd_from, g.dd_to, g.dd_sum and dd_shift, with
the ranges of the SUBs moved.
"""

from uxc_code import cb_add, cb_get, cb_put, emit, fx_put, fx_read, rt_address_set, rt_get, \
    rt_use
from uxc_defs import K_DV_MAX, K_EK_MEM, K_F_ABS, K_FX_MAX, K_SEC_BSS, K_SEC_CODE, K_SEC_CONST, \
    K_SEC_LABEL, K_SEC_REC, K_SEC_RGDATA, K_SEC_STR, K_SEC_VAR, K_SK_LABEL, K_SK_SUB, \
    K_SY_END, K_SY_READ_ONLY, K_TOP, K_TT_EOL, K_TT_NUM, K_TY_STR
import uxc_dead
import uxc_lex
import uxc_rombank
import uxc_sym
import uxc_tpl as T
from uxc_state import er_stop, er_syntax, g

K_RG_ORG = 0xA000
K_RG_ROOM = 8192
K_RG_SLOTS = 63
K_RG_GATE_BANK = 5
# The bytes of T_RGLOAD that hold the image's size, lda #<size and ldy #>size.
K_RG_LOAD_SIZE_LO = 1
K_RG_LOAD_SIZE_HI = 3
# The 65C02 stores to a zero-page address, then those to an absolute one.
K_RG_STORES_ZP = (0x64, 0x84, 0x85, 0x86)
K_RG_STORES_ABS = (0x8C, 0x8D, 0x8E, 0x9C)


def rg_line():
    """RG.LINE. #REGION_SLOT n, with the token at REGION_SLOT. The token is left at the end of
    the line."""
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NUM:
        er_syntax()
    if g.tk_v > K_RG_SLOTS:
        er_stop("#REGION_SLOT IS 0 TO 63")
    g.rg_slot = g.tk_v
    uxc_lex.lx_next()
    if g.tk_t != K_TT_EOL:
        er_syntax()


def rg_sub():
    g.rg_sub_start = g.sy_val
    if g.rg_slot != 0:
        g.rg_subs.append(g.sb_current)
        g.rg_sub_slots.append(g.rg_slot)


def rg_pin_from():
    g.rg_pin_from = g.cb_n


def rg_pin_to(callee):
    """RG.PIN.TO. In a SUB of a region, the code since rg_pin_from loads the address that a
    STRING FUNCTION returns, callee 0, or a STRING argument to SUB callee. A caller in low RAM,
    or a callee outside the region, reads it with another bank selected, so what a fixup there
    names stays in low RAM. rg_data drops the pin of an argument to a SUB of the same region,
    unless that SUB is in rg_leaky."""
    if rg_in_region() != 0:
        g.rg_pins.append((g.sb_current, g.rg_pin_from - g.rg_sub_start,
                          g.cb_n - g.rg_sub_start, callee))


def rg_forward(callee):
    """RG.FORWARD. In a SUB of a region, with a STRING argument to SUB callee on top of the
    value stack and g.sg_read_only set for an AS CONST parameter: when the argument is a STRING
    parameter of the SUB that sg_pass passes on as an address, not as a copy, the pair goes into
    g.rg_forwards. Clobbers g.sy_*."""
    if rg_in_region() == 0:
        return
    i = g.ex_vn - 1
    if g.ex_vk[i] != K_EK_MEM or g.ex_vs[i] != K_SEC_VAR:
        return
    g.sy_r = g.sb_current
    uxc_sym.sy_get()
    for n in range(g.sy_np, 0, -1):
        g.sy_r = g.sb_current + n
        uxc_sym.sy_get()
        if g.sy_type == K_TY_STR and g.sy_val == g.ex_vv[i]:
            # An AS CONST parameter passed to one that is not AS CONST is copied.
            if (g.sy_flags & K_SY_READ_ONLY) == 0 or g.sg_read_only != 0:
                g.rg_forwards.append((g.sb_current, callee))
            return


def rg_leaky():
    """RG.LEAKY. The set of the SUBs of the regions that pass a STRING parameter on, as an
    address, to a SUB outside their region, or to another SUB of the set."""
    leaky = set()
    grew = True
    while grew:
        grew = False
        for caller, callee in g.rg_forwards:
            if caller not in leaky:
                if callee in leaky or rg_slot_of(callee) != rg_slot_of(caller):
                    leaky.add(caller)
                    grew = True
    return leaky


def rg_slot_of(record):
    """RG.SLOT.OF. The slot of SUB record, 0 for one in low RAM."""
    if record in g.rg_subs:
        return g.rg_sub_slots[g.rg_subs.index(record)]
    return 0


def rg_in_region():
    """RG.IN.REGION. 1 when the code being compiled is a SUB of a region."""
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
    """RG.RANGES. g.rg_from, g.rg_to, g.rg_record and g.rg_range_k: each SUB of a region left
    in, in code order, from its JMP around to its end, and its region. g.rg_slots: the slot of
    each region, region k at k - 1."""
    g.rg_on = 0
    ranges = []
    g.rg_slots = []
    for g.rg_r in range(1, g.sy_n + 1):
        g.sy_r = g.rg_r
        uxc_sym.sy_get()
        if g.sy_kind == K_SK_SUB and (g.sy_flags & 1) != 0 and g.rg_r in g.rg_subs:
            slot = g.rg_sub_slots[g.rg_subs.index(g.rg_r)]
            ranges.append((g.sy_val - 3, g.ram[g.sy_ad + K_SY_END] +
                           256 * g.ram[g.sy_ad + K_SY_END + 1], g.rg_r, slot))
            if slot not in g.rg_slots:
                g.rg_slots.append(slot)
    if len(ranges) == 0:
        return
    if g.lk_raw != 0 or g.lk_apart != 0 or g.rb_on != 0:
        er_stop("#REGION_SLOT WITH #ORG, #DATA OR #ROMBANKS")
    if g.target != "6502dos":
        er_stop("#REGION_SLOT NEEDS 6502DOS")
    g.rg_on = 1
    ranges.sort()
    g.rg_slots.sort()
    g.rg_count = len(g.rg_slots)
    g.rg_from = [r[0] for r in ranges]
    g.rg_to = [r[1] for r in ranges]
    g.rg_record = [r[2] for r in ranges]
    g.rg_range_k = [g.rg_slots.index(r[3]) + 1 for r in ranges]
    g.rg_n = len(ranges)
    # The records the startup and the veneers name must be known before rt_close.
    for g.rt_id in (T.R_RGLOAD, T.R_EMEM, T.R_ERRORB):
        rt_use()


def rg_find(at):
    """RG.FIND. The last SUB of a region whose range starts at or before code offset at, or
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
    """RG.SIDE.OF. (k, the offset in region k) for code offset at inside the body of a SUB of
    region k, else (0, its offset in the low code after the cut). The JMP around a SUB moved is
    not in its body: the code after the cut lands there."""
    j = rg_find(at)
    if j >= 0 and at >= g.rg_from[j] + 3 and at < g.rg_to[j]:
        return g.rg_range_k[j], at - g.rg_from[j] - 3 + g.rg_at[j]
    g.dd_at = at
    uxc_dead.dd_shift()
    return 0, g.dd_at


def rg_namer(at):
    """RG.NAMER. The region k whose code names what a fixup at code offset at names, or 0 when
    it keeps it in low RAM: it is outside the body of every SUB of a region, or in a pin."""
    j = rg_find(at)
    if j < 0 or at < g.rg_from[j] + 3 or at >= g.rg_to[j]:
        return 0
    for pin_from, pin_to in g.rg_pin_at:
        if pin_from <= at < pin_to:
            return 0
    return g.rg_range_k[j]


def rg_data():
    """RG.DATA. Move into a region each string literal and each global variable that only the
    region's code names. Out: g.rg_data[k], region k's data, the literals then the variables,
    and g.rg_banked, the region of each variable's record moved, else 0. A fixup to one becomes
    K_SEC_RGDATA. A variable's bytes are 0 but for the string maxes, which sg_maxes writes in
    through rg_max. Without a full log of the variables, only the literals move."""
    g.rg_data = [bytearray() for k in range(g.rg_count + 1)]
    g.rg_banked = [0] * (g.sy_n + 1)
    g.rg_pin_at = []
    leaky = rg_leaky()
    for g.sy_r, pin_from, pin_to, callee in g.rg_pins:
        if rg_slot_of(callee) == rg_slot_of(g.sy_r) and callee not in leaky:
            continue
        uxc_sym.sy_get()
        if g.sy_kind == K_SK_SUB and (g.sy_flags & 1) != 0:
            g.rg_pin_at.append((g.sy_val + pin_from, g.sy_val + pin_to))
    rg_strings()
    if g.dv_full == 0:
        rg_vars()


def rg_strings():
    """RG.STRINGS. g.rg_mark of each literal: 0 named by no fixup, -1 named in low RAM or by
    two regions, k named by region k alone, which moves there."""
    uxc_dead.ds_index()
    g.rg_mark = [0] * g.ds_count
    for g.fx_i in range(g.fx_n):
        fx_read()
        if g.fx_s == K_SEC_STR:
            g.ds_off = g.fx_v
            uxc_dead.ds_find()
            rg_mark_by(g.ds_k)
    g.rg_moved_at = [0] * g.ds_count
    g.ram = g.sp_bank
    for g.ds_i in range(g.ds_count):
        g.ds_used[g.ds_i] = 1
        k = g.rg_mark[g.ds_i]
        if k > 0:
            g.ds_used[g.ds_i] = 0
            g.rg_moved_at[g.ds_i] = len(g.rg_data[k])
            g.ds_from = g.ds_at[g.ds_i]
            g.rg_data[k].extend(g.ram[g.ds_from:g.ds_from + g.ram[g.ds_from] + 2])
    for g.fx_i in range(g.fx_n):
        fx_read()
        if g.fx_s == K_SEC_STR:
            g.ds_off = g.fx_v
            uxc_dead.ds_find()
            if g.rg_mark[g.ds_k] > 0:
                g.fx_s = K_SEC_RGDATA
                g.fx_v = g.fx_v - g.ds_at[g.ds_k] + g.rg_moved_at[g.ds_k]
                fx_put()
    # The pool closes up over the literals moved, as over those UXC-DEAD.BL leaves out.
    saved_bytes = g.ds_bytes
    saved_strings = g.ds_strings
    g.ds_bytes = 0
    g.ds_strings = 0
    uxc_dead.ds_cuts()
    if g.ds_bytes > 0:
        uxc_dead.ds_fixups()
        uxc_dead.ds_pool()
    g.ds_bytes = saved_bytes
    g.ds_strings = saved_strings


def rg_mark_by(i):
    """RG.MARK.BY. Mark entry i of g.rg_mark for the fixup read."""
    k = rg_namer(g.fx_at)
    if k == 0:
        g.rg_mark[i] = -1
    elif g.rg_mark[i] == 0:
        g.rg_mark[i] = k
    elif g.rg_mark[i] != k:
        g.rg_mark[i] = -1


def rg_vars():
    """RG.VARS. The same for the global variables, through UXC-DEAD.BL's log, which dv_strip
    left in the new offsets: g.rg_mark of each log entry, then the variables, then the array
    space close up over those moved."""
    g.rg_mark = [0] * (2 * K_DV_MAX)
    for g.fx_i in range(g.fx_n):
        fx_read()
        uxc_dead.dv_section()
        if g.dv_s >= 0:
            g.dv_off = g.fx_v
            uxc_dead.dv_find()
            if g.dv_k >= 0:
                rg_mark_by(g.dv_k)
    g.rg_moved_at = [0] * (2 * K_DV_MAX)
    for g.dv_s in range(2):
        g.dv_end = g.vr_n
        if g.dv_s == 1:
            g.dv_end = g.bs_n
        g.dv_base = g.dv_s * K_DV_MAX
        for g.dv_i in range(g.dv_count[g.dv_s]):
            g.dv_k = g.dv_base + g.dv_i
            g.dv_used[g.dv_k] = 1
            k = g.rg_mark[g.dv_k]
            if k > 0:
                g.dv_used[g.dv_k] = 0
                g.rg_moved_at[g.dv_k] = len(g.rg_data[k])
                g.dv_next = g.dv_end
                if g.dv_i + 1 < g.dv_count[g.dv_s]:
                    g.dv_next = g.dv_at[g.dv_k + 1]
                g.rg_data[k].extend(bytes(g.dv_next - g.dv_at[g.dv_k]))
        uxc_dead.dv_cuts()
    for g.fx_i in range(g.fx_n):
        fx_read()
        uxc_dead.dv_section()
        if g.dv_s >= 0:
            g.dv_off = g.fx_v
            uxc_dead.dv_find()
            if g.dv_k >= 0 and g.rg_mark[g.dv_k] > 0:
                g.fx_s = K_SEC_RGDATA
                g.fx_v = g.fx_v - g.dv_at[g.dv_k] + g.rg_moved_at[g.dv_k]
                fx_put()
    uxc_dead.dv_fixups()
    for g.rg_r in range(1, g.sy_n + 1):
        g.sy_r = g.rg_r
        uxc_sym.sy_get()
        uxc_dead.dv_kind()
        if g.dv_s >= 0:
            g.dv_off = g.sy_val
            uxc_dead.dv_find()
            if g.dv_k >= 0 and g.rg_mark[g.dv_k] > 0:
                g.sy_val = g.sy_val - g.dv_at[g.dv_k] + g.rg_moved_at[g.dv_k]
                g.rg_banked[g.rg_r] = g.rg_mark[g.dv_k]
                uxc_sym.sy_set()
            elif g.dv_k >= 0:
                g.sy_val = g.sy_val - g.dv_cut[g.dv_k]
                uxc_sym.sy_set()
    g.vr_n = g.vr_n - g.dv_total[0]
    g.bs_n = g.bs_n - g.dv_total[1]


def rg_image_of():
    """RG.IMAGE.OF. In sg_maxes, with a record in g.sy_*: g.rg_image is the region of a
    variable moved into one, whose maxes go into its image, else 0."""
    g.rg_image = 0
    if g.rg_on != 0 and g.sy_r < len(g.rg_banked):
        g.rg_image = g.rg_banked[g.sy_r]


def rg_max(at, value, size, count):
    """RG.MAX. Put max value at offset at of region g.rg_image's data, or with count, in each of
    count records of size bytes from there."""
    if count == 0:
        g.rg_data[g.rg_image][at] = value
        return
    for i in range(count):
        g.rg_data[g.rg_image][at + i * size] = value


def rg_split():
    """RG.SPLIT. Cut the regions' SUBs out of the code into g.rg_code[k] and their fixups into
    g.rg_fix[k], then add the gates and the veneers in low RAM. Out: g.rg_size[k], the bytes of
    region k, and g.rg_data_at[k], the offset of its data in it."""
    m = g.rg_count
    g.rg_at = [0] * g.rg_n
    g.rg_code = [bytearray() for k in range(m + 1)]
    g.dd_n = 0
    cut = 0
    for i in range(g.rg_n):
        code = g.rg_code[g.rg_range_k[i]]
        g.rg_at[i] = len(code)
        for g.cb_at in range(g.rg_from[i] + 3, g.rg_to[i]):
            cb_get()
            code.append(g.cb_b)
        cut = cut + g.rg_to[i] - g.rg_from[i]
        g.dd_from[g.dd_n] = g.rg_from[i]
        g.dd_to[g.dd_n] = g.rg_to[i]
        g.dd_sum[g.dd_n] = cut
        g.dd_n = g.dd_n + 1
    low_end = g.cb_n - cut
    gate_length = uxc_rombank.rb_length(T.T_RGGATE)
    g.rg_gate_at = [0] * (m + 1)
    for k in range(1, m + 1):
        g.rg_gate_at[k] = low_end + (k - 1) * gate_length
    g.rg_veneer_length = uxc_rombank.rb_length(T.T_FARCALL)
    g.rg_veneers = [[] for k in range(m + 1)]
    g.rg_veneer_base = [len(g.rg_code[k]) for k in range(m + 1)]
    g.rg_veneer_base[0] = low_end + m * gate_length
    rg_fixups()
    rg_records()
    uxc_dead.dd_code()
    if g.cb_n != low_end:
        er_stop("REGION CUT LOST BYTES")
    for k in range(1, m + 1):
        emit(T.T_RGGATE)
    for g.rg_r, g.rg_gate in g.rg_veneers[0]:
        rg_veneer()
    g.rg_data_at = [0] * (m + 1)
    g.rg_size = [0] * (m + 1)
    for k in range(1, m + 1):
        g.rg_data_at[k] = len(g.rg_code[k]) + len(g.rg_veneers[k]) * g.rg_veneer_length
        g.rg_size[k] = g.rg_data_at[k] + len(g.rg_data[k])
        if g.rg_size[k] > K_RG_ROOM:
            er_stop("REGION " + str(g.rg_slots[k - 1]) + " FULL")


def rg_fixups():
    """RG.FIXUPS. Each fixup goes with its code: kept in place for the low code, into
    g.rg_fix[k] for region k, or dropped with the JMP around a SUB moved. A call across an edge
    goes to the SUB's veneer on the caller's side."""
    g.rg_fix = [[] for k in range(g.rg_count + 1)]
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
        if g.fx_s == K_SEC_RGDATA and side == 0:
            er_stop("REGION DATA NAMED OUTSIDE")
        if side != 0:
            g.rg_fix[side].append((g.fx_at, g.fx_k, g.fx_s, g.fx_v, g.fx_ow))
            continue
        g.fx_i = kept
        fx_put()
        kept = kept + 1
    g.fx_n = kept


def rg_label(side, at):
    """RG.LABEL. A K_SEC_LABEL fixup read, at code offset at before the cut, on side. A JSR to
    a SUB on another side goes to its veneer, a K_SEC_CODE fixup on this side. The veneer goes
    through the gate of the SUB's region, or of the caller's when the SUB is in low RAM."""
    g.sy_r = g.fx_v
    uxc_sym.sy_get()
    if (g.sy_flags & 1) == 0:
        return
    target_side = rg_side_of(g.sy_val)[0]
    if target_side == side:
        return
    g.cb_at = at - 1
    cb_get()
    if g.sy_kind != K_SK_SUB or g.fx_k != K_F_ABS or g.cb_b != 0x20:
        er_stop("GOTO ACROSS THE REGION")
    gate = target_side
    if gate == 0:
        gate = side
    veneers = g.rg_veneers[side]
    i = 0
    while i < len(veneers) and veneers[i][0] != g.fx_v:
        i = i + 1
    if i == len(veneers):
        veneers.append((g.fx_v, gate))
    g.fx_s = K_SEC_CODE
    g.fx_v = g.rg_veneer_base[side] + i * g.rg_veneer_length


def rg_records():
    """RG.RECORDS. Move the value of each placed LABEL and SUB to its side's offset.
    g.rg_moved[k] lists those in region k, which rg_place moves again to g.rg_base[k]."""
    g.rg_moved = [[] for k in range(g.rg_count + 1)]
    for g.rg_r in range(1, g.sy_n + 1):
        g.sy_r = g.rg_r
        uxc_sym.sy_get()
        if (g.sy_kind == K_SK_LABEL or g.sy_kind == K_SK_SUB) and (g.sy_flags & 1) != 0:
            side, g.sy_val = rg_side_of(g.sy_val)
            uxc_sym.sy_set()
            if side != 0:
                g.rg_moved[side].append(g.rg_r)
    g.dd_at = g.lk_init_at
    uxc_dead.dd_shift()
    g.lk_init_at = g.dd_at


def rg_veneer():
    """RG.VENEER. A T_FARCALL to the SUB of record g.rg_r, on another side, through the
    T_RGGATE of region g.rg_gate."""
    g.sl_s[0] = K_SEC_LABEL
    g.sl_v[0] = g.rg_r
    g.sl_s[1] = K_SEC_CODE
    g.sl_v[1] = g.rg_gate_at[g.rg_gate]
    emit(T.T_FARCALL)


def rg_load():
    """RG.LOAD. T_RGFROM points at the start of the array space, where rg_place puts the
    images; then each region's T_RGLOAD copies its g.rg_size[k] bytes and writes its bank into
    its gate."""
    g.sl_s[0] = K_SEC_BSS
    g.sl_v[0] = 0
    emit(T.T_RGFROM)
    g.rg_load_at = [0] * (g.rg_count + 1)
    for k in range(1, g.rg_count + 1):
        g.rg_load_at[k] = g.cb_n
        g.sl_s[0] = K_SEC_CONST
        g.sl_v[0] = g.rg_size[k]
        g.sl_s[1] = K_SEC_CODE
        g.sl_v[1] = g.rg_gate_at[k] + K_RG_GATE_BANK
        emit(T.T_RGLOAD)


def rg_runtime():
    """RG.RUNTIME. After the startup work: each runtime record that only region k's code, or
    records of region k, name moves into region k. Out: g.rg_runtime_ids[k], those records in
    list order; g.rg_runtime_k, the region of each record, else 0; g.rg_runtime_size[k], their
    bytes. g.rg_size[k] and the size in region k's T_RGLOAD grow by them."""
    uxc_rombank.rb_tables()
    # g.rg_named: 0 named by nothing yet, -1 kept in low RAM, else the one region naming it.
    g.rg_named = [0] * (T.TPL_COUNT + 1)
    g.rg_work = []
    for g.fx_i in range(g.fx_n):
        fx_read()
        if g.fx_s == K_SEC_REC:
            rg_name(g.fx_v, -1)
    for k in range(1, g.rg_count + 1):
        for fixup in g.rg_fix[k]:
            if fixup[2] == K_SEC_REC:
                rg_name(fixup[3], k)
    for record_id in (T.R_RGLOAD, T.R_EMEM, T.R_ERRORB):
        rg_name(record_id, -1)
    for g.lk_i in range(g.rt_n):
        rt_get()
        if g.rt_dn != 0 or rg_writes_bank() != 0:
            rg_name(g.rt_id, -1)
    while len(g.rg_work) > 0:
        record_id = g.rg_work.pop()
        for named in g.rb_refs[record_id]:
            rg_name(named, g.rg_named[record_id])
    g.rg_runtime_k = [0] * (T.TPL_COUNT + 1)
    g.rg_runtime_ids = [[] for k in range(g.rg_count + 1)]
    g.rg_runtime_size = [0] * (g.rg_count + 1)
    for g.lk_i in range(g.rt_n):
        rt_get()
        k = g.rg_named[g.rt_id]
        if k > 0:
            g.rg_runtime_k[g.rt_id] = k
            g.rg_runtime_ids[k].append(g.rt_id)
            g.rg_runtime_size[k] = g.rg_runtime_size[k] + g.rb_size[g.rt_id]
    for k in range(1, g.rg_count + 1):
        g.rg_size[k] = g.rg_size[k] + g.rg_runtime_size[k]
        if g.rg_size[k] > K_RG_ROOM:
            er_stop("REGION " + str(g.rg_slots[k - 1]) + " FULL")
        g.cb_at = g.rg_load_at[k] + K_RG_LOAD_SIZE_LO
        g.cb_b = g.rg_size[k] % 256
        cb_put()
        g.cb_at = g.rg_load_at[k] + K_RG_LOAD_SIZE_HI
        g.cb_b = g.rg_size[k] // 256
        cb_put()


def rg_name(record_id, k):
    """RG.NAME. Code of region k, or of low RAM when k is -1, names runtime record record_id.
    A record whose g.rg_named changes goes on g.rg_work, so that the records it names follow.
    R_ERRORB stands for R_ERROR, which lk_fix resolves to it."""
    if record_id == T.R_ERROR:
        record_id = T.R_ERRORB
    if g.rg_named[record_id] == k or g.rg_named[record_id] == -1:
        return
    if g.rg_named[record_id] == 0:
        g.rg_named[record_id] = k
    else:
        g.rg_named[record_id] = -1
    g.rg_work.append(record_id)


def rg_writes_bank():
    """RG.WRITES.BANK. 1 when the code of the record rt_get read holds a store to $00, else 0.
    A byte pair that only looks like one counts too; a fixup's operand does not."""
    length = g.ram[g.rt_a]
    code = g.rt_a + 2
    fixups = g.rt_a + 2 + length
    operands = [g.ram[fixups + j * 3] for j in range(g.ram[g.rt_a + 1])]
    for i in range(length - 1):
        if i + 1 in operands or g.ram[code + i + 1] != 0:
            continue
        if g.ram[code + i] in K_RG_STORES_ZP:
            return 1
        if g.ram[code + i] in K_RG_STORES_ABS and i + 2 < length and g.ram[code + i + 2] == 0:
            return 1
    return 0


def rg_place():
    """RG.PLACE. After the variables, for each region k: its code, its fixups, its records, its
    veneers, its data and its runtime records, from g.rg_base[k] on."""
    g.rg_base = [0] * (g.rg_count + 1)
    for k in range(1, g.rg_count + 1):
        g.rg_base[k] = g.cb_n
        for g.cb_b in g.rg_code[k]:
            cb_add()
        for g.fx_at, g.fx_k, g.fx_s, g.fx_v, g.fx_ow in g.rg_fix[k]:
            if g.fx_n >= K_FX_MAX:
                er_stop("TOO MANY FIXUPS")
            g.fx_at = g.fx_at + g.rg_base[k]
            if g.fx_s == K_SEC_CODE:
                g.fx_v = g.fx_v + g.rg_base[k]
            g.fx_i = g.fx_n
            fx_put()
            g.fx_n = g.fx_n + 1
        for g.sy_r in g.rg_moved[k]:
            uxc_sym.sy_get()
            g.sy_val = g.sy_val + g.rg_base[k]
            uxc_sym.sy_set()
        for g.rg_r, g.rg_gate in g.rg_veneers[k]:
            rg_veneer()
        for g.cb_b in g.rg_data[k]:
            cb_add()
        for record_id in g.rg_runtime_ids[k]:
            g.rt_id = record_id
            g.rt_at = K_RG_ORG + g.cb_n - g.rg_base[k]
            rt_address_set()
            emit(record_id)
        if g.cb_n - g.rg_base[k] != g.rg_size[k]:
            er_stop("REGION SIZE CHANGED")
    if g.lk_org + g.cb_n > K_TOP:
        er_stop("PROGRAM TOO BIG")


def rg_region_of(at):
    """RG.REGION.OF. The region k whose image holds code offset at, or 0 for the low code."""
    k = g.rg_count
    while k > 0 and at < g.rg_base[k]:
        k = k - 1
    return k


def rg_code_address():
    """RG.CODE.ADDRESS. In g.lk_v, a code offset; out g.lk_v, its address."""
    if g.rg_on != 0:
        k = rg_region_of(g.lk_v)
        if k != 0:
            g.lk_v = K_RG_ORG + g.lk_v - g.rg_base[k]
            return
    g.lk_v = g.lk_org + g.lk_v


def rg_data_address():
    """RG.DATA.ADDRESS. In lk_fix, with a K_SEC_RGDATA fixup read: g.lk_v, its address in the
    region of its own code."""
    k = rg_region_of(g.fx_at)
    g.lk_v = K_RG_ORG + g.rg_data_at[k] + g.fx_v
