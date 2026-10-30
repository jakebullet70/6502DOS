"""#ROMBANKS: one program in two or three ROM banks.

    #ROMBANKS first, second [, third] [, name]
                               with #ORG and #DATA. The program runs from ROM bank first at the
                               #ORG address, and the SUBs at its tail from ROM bank second, then
                               third, at the same address. dd_place_scan reads it: g.rb_on is 1,
                               g.rb_count 2 or 3, and g.rb_bank holds the banks. name, a SUB or
                               FUNCTION, is g.rb_name: it and every SUB after it in code order go
                               to the later banks, and more before it when the first bank needs.

    rb_ranges()   at the start of the link step, after UXC-DEAD.BL: the code range of each SUB,
                  before SB.POOLS writes over K_SY_END
    rb_split()    after the startup work: move the SUBs at the tail, in code order, to the
                  later banks, as many as the first bank needs, and add the first bank's veneers
    rb_end()      after the strings: fill the file with $FF up to K_FAR, then T_FAR
    rb_others()   after the first bank's file: link each later bank and write its file

The first bank holds the main code, the SUBs not moved, the startup work, the veneers, the
runtime records its code names, and the strings that the startup copies to #DATA. The second
holds the SUBs moved, as many as fit, its veneers, and its own copies of the runtime records
they name; the third the rest the same way. g.rb_k is the first SUB moved, g.rb_k2 the first in
the third bank, g.rb_n with two banks. The data records are RAM, placed once for all banks. Each
file runs from the #ORG address to $FFA0 and ends with T_FAR at K_FAR. The second file is
NAME.PR2, the third NAME.PR3.

A call to a SUB in another bank goes to a veneer in the caller's bank, a T_FARCALL, one a SUB
and calling bank. It loads the SUB's address and jumps to T_FAR's entry for the SUB's bank,
which selects that bank, calls the SUB there, and selects the caller's bank again. A moved
SUB's JMP around it is dropped. A GOTO, or a jump of any kind but a SUB call, from one bank into
another stops the link. A pointer holds an address in the first bank: @ of a SUB in a later
bank is the address of its veneer in the first. A pointer call in a later bank, T_ICALL, calls
T_FAR's entry for the first bank instead of R_ICALL, so it runs in the first bank.

The cut out of the first bank uses UXC-DEAD.BL's g.dd_from, g.dd_to, g.dd_sum and dd_shift,
with the ranges of the SUBs moved.
"""

from uxc_code import cb_add, cb_get, emit, fx_put, fx_read, rt_get, rt_place, rt_use
from uxc_defs import K_F_ABS, K_F_REC, K_F_REC_HI, K_FAR, K_FAR_END, K_FAR_ENTRY, K_SEC_CODE, \
    K_SEC_CONST, K_SEC_LABEL, K_SEC_REC, K_SK_LABEL, K_SK_SUB
import uxc_dead
import uxc_link
import uxc_sym
import uxc_tpl as T
from uxc_state import er_stop, g


def rb_ranges():
    """RB.RANGES. g.rb_record, g.rb_from and g.rb_to: each SUB left in, in code order, from its
    JMP around to its end. g.rb_start: the first SUB that must move, g.rb_n when none must."""
    if g.lk_raw == 0 or g.lk_apart == 0:
        er_stop("#ROMBANKS NEEDS #ORG AND #DATA")
    if g.lk_org >= K_FAR:
        er_stop("#ORG PAST THE ROM BANK")
    ranges = []
    for g.rb_r in range(1, g.sy_n + 1):
        g.sy_r = g.rb_r
        uxc_sym.sy_get()
        if g.sy_kind == K_SK_SUB and (g.sy_flags & 1) != 0:
            uxc_sym.sy_end_get()
            ranges.append((g.sy_val - 3, g.sy_end, g.rb_r))
    ranges.sort()
    g.rb_from = [r[0] for r in ranges]
    g.rb_to = [r[1] for r in ranges]
    g.rb_record = [r[2] for r in ranges]
    for i in range(1, len(ranges)):
        if g.rb_from[i] < g.rb_to[i - 1]:
            er_stop("SUBS OVERLAP")
    g.rb_n = len(g.rb_record)
    g.rb_start = g.rb_n
    if g.rb_name != "":
        g.sy_name = g.rb_name
        g.sy_ow = 0
        uxc_sym.sy_find()
        if g.sy_r not in g.rb_record:
            er_stop("#ROMBANKS SUB NOT FOUND")
        g.rb_start = g.rb_record.index(g.sy_r)
    # T_FAR's data record must be known before the startup places the data records.
    g.rt_id = T.R_FARVEC
    rt_use()


def rb_find(at):
    """RB.FIND. The last SUB whose range starts at or before code offset at, or -1."""
    low = 0
    high = g.rb_n
    while low < high:
        mid = (low + high) // 2
        if g.rb_from[mid] <= at:
            low = mid + 1
        else:
            high = mid
    return low - 1


def rb_bank_index(t):
    """RB.BANK.INDEX. The bank, 0 to 2, of SUB t once g.rb_k and g.rb_k2 are chosen; -1, the
    main code, is in bank 0."""
    if t < g.rb_k:
        return 0
    if t < g.rb_k2:
        return 1
    return 2


def rb_bank_of(at):
    """RB.BANK.OF. The bank of code offset at once g.rb_k is chosen: (bank, its offset in that
    bank) inside the body of a SUB moved, else (0, its offset in the first bank after the cut).
    The JMP around a SUB moved is not in its body: the code after the cut lands there."""
    j = rb_find(at)
    if j >= g.rb_k and at >= g.rb_from[j] + 3 and at < g.rb_to[j]:
        return rb_bank_index(j), at - g.rb_from[j] - 3 + g.rb_at[j]
    g.dd_at = at
    uxc_dead.dd_shift()
    return 0, g.dd_at


def rb_tables():
    """RB.TABLES. For each runtime record on K_RT_LIST: g.rb_size, its bytes of code, 0 for a
    data record, and g.rb_refs, the records it names."""
    g.rb_size = [0] * (T.TPL_COUNT + 1)
    g.rb_refs = [[] for _ in range(T.TPL_COUNT + 1)]
    for g.lk_i in range(g.rt_n):
        rt_get()
        if g.rt_dn != 0:
            continue
        g.rb_size[g.rt_id] = g.ram[g.rt_a]
        g.rt_fa = g.rt_a + 2 + g.ram[g.rt_a]
        for g.rt_j in range(g.ram[g.rt_a + 1]):
            g.rt_k = g.ram[g.rt_fa + g.rt_j * 3 + 1]
            g.rt_g = g.ram[g.rt_fa + g.rt_j * 3 + 2]
            if g.rt_k == K_F_REC_HI:
                g.rt_k = K_F_REC
                g.rt_g = g.rt_g + 256
            if g.rt_k == K_F_REC:
                g.rb_refs[g.rt_id].append(g.rt_g)


def rb_close():
    """RB.CLOSE. g.rb_need, 1 for each record a record marked in it names, in turn. Out: the
    bytes of code of the records marked."""
    work = [i for i in range(T.TPL_COUNT + 1) if g.rb_need[i] != 0]
    while work:
        rid = work.pop()
        for ref in g.rb_refs[rid]:
            if g.rb_need[ref] == 0:
                g.rb_need[ref] = 1
                work.append(ref)
    return sum(g.rb_size[i] for i in range(T.TPL_COUNT + 1) if g.rb_need[i] != 0)


def rb_runtime(bank):
    """RB.RUNTIME. The bytes of runtime code bank needs with the SUBs split at g.rb_k and
    g.rb_k2."""
    g.rb_need = [0] * (T.TPL_COUNT + 1)
    for rid in range(T.TPL_COUNT + 1):
        for j in g.rb_users[rid]:
            if rb_bank_index(j) == bank:
                g.rb_need[rid] = 1
                break
    return rb_close()


def rb_need_mark():
    """RB.NEED.MARK. g.rb_need for the bank in the code buffer: the records its fixups name."""
    g.rb_need = [0] * (T.TPL_COUNT + 1)
    for g.fx_i in range(g.fx_n):
        fx_read()
        if g.fx_s == K_SEC_REC:
            g.rb_need[g.fx_v] = 1
    rb_close()


def rb_split():
    """RB.SPLIT. Choose g.rb_k and g.rb_k2, cut the SUBs from g.rb_k on out of the code into
    g.rb_code and their fixups into g.rb_fix, one of each a later bank, then add the first
    bank's veneers. g.rb_need marks the runtime records the first bank places."""
    rb_tables()
    rb_uses()
    rb_choose()
    g.rb_at = [0] * g.rb_n
    g.rb_code = [bytearray(), bytearray(), bytearray()]
    g.dd_n = 0
    cut = 0
    for i in range(g.rb_k, g.rb_n):
        code = g.rb_code[rb_bank_index(i)]
        g.rb_at[i] = len(code)
        for g.cb_at in range(g.rb_from[i] + 3, g.rb_to[i]):
            cb_get()
            code.append(g.cb_b)
        cut = cut + g.rb_to[i] - g.rb_from[i]
        g.dd_from[g.dd_n] = g.rb_from[i]
        g.dd_to[g.dd_n] = g.rb_to[i]
        g.dd_sum[g.dd_n] = cut
        g.dd_n = g.dd_n + 1
    # The veneers follow each bank's code: the first bank's after the startup work.
    g.rb_veneer_at = [[-1] * g.rb_n for _ in range(3)]
    g.rb_veneers = [[], [], []]
    g.rb_veneer_base = [g.cb_n - cut, len(g.rb_code[1]), len(g.rb_code[2])]
    rb_fixups()
    rb_records()
    uxc_dead.dd_code()
    if g.cb_n != g.rb_veneer_base[0]:
        er_stop("ROMBANKS CUT LOST BYTES")
    for t in g.rb_veneers[0]:
        rb_veneer(g.lk_org + g.rb_at[t], rb_bank_index(t))
    rb_need_mark()


def rb_uses():
    """RB.USES. For each fixup, g.rb_in, the SUB whose range holds it, or -1. For each SUB,
    g.rb_callers, the ranges that call it, -1 for the main code; @ of the SUB counts as a call
    from the main code. For each runtime record, g.rb_users, the ranges whose code names it.
    g.rb_index maps a SUB's record to its place in g.rb_record, else -1."""
    g.rb_index = [-1] * (g.sy_n + 1)
    for t in range(g.rb_n):
        g.rb_index[g.rb_record[t]] = t
    g.rb_in = [-1] * g.fx_n
    g.rb_callers = [[] for _ in range(g.rb_n)]
    g.rb_users = [[] for _ in range(T.TPL_COUNT + 1)]
    for g.fx_i in range(g.fx_n):
        fx_read()
        j = rb_find(g.fx_at)
        if j >= 0 and g.fx_at >= g.rb_to[j]:
            j = -1
        g.rb_in[g.fx_i] = j
        if g.fx_s == K_SEC_REC:
            g.rb_users[g.fx_v].append(j)
        if g.fx_s == K_SEC_LABEL and g.rb_index[g.fx_v] >= 0:
            # @ of the SUB: from the first bank's view, wherever the @ is.
            if g.fx_k != K_F_ABS:
                j = -1
            g.rb_callers[g.rb_index[g.fx_v]].append(j)


def rb_bank_size(bank):
    """RB.BANK.SIZE. The bytes bank holds with the SUBs split at g.rb_k and g.rb_k2: its code,
    its veneers, its runtime and T_FAR; the first bank adds the strings."""
    veneers = 0
    body = 0
    for t in range(g.rb_n):
        if rb_bank_index(t) == bank:
            body = body + g.rb_to[t] - g.rb_from[t] - 3
        else:
            for j in g.rb_callers[t]:
                if rb_bank_index(j) == bank:
                    veneers = veneers + 1
                    break
    if bank == 0:
        # The main code, and each SUB kept with its JMP around.
        body = g.cb_n + g.sp_n
        for t in range(g.rb_k, g.rb_n):
            body = body - (g.rb_to[t] - g.rb_from[t])
    return body + veneers * g.rb_veneer_length + rb_runtime(bank) + g.rb_far_length


def rb_choose():
    """RB.CHOOSE. g.rb_k, the first SUB moved: the most SUBs before g.rb_start that the first
    bank can keep. g.rb_k2, the first SUB in the third bank: the most SUBs from g.rb_k that the
    second can keep; g.rb_n with two banks."""
    g.rb_far_length = rb_length(T.T_FAR)
    g.rb_veneer_length = rb_length(T.T_FARCALL)
    room = K_FAR_END - g.lk_org
    g.rb_k = g.rb_start
    g.rb_k2 = g.rb_n
    while rb_bank_size(0) > room:
        if g.rb_k == 0:
            rb_too_big()
        g.rb_k = g.rb_k - 1
    while rb_bank_size(1) > room:
        if g.rb_count == 2 or g.rb_k2 == g.rb_k:
            rb_too_big()
        g.rb_k2 = g.rb_k2 - 1
    if g.rb_count == 3 and rb_bank_size(2) > room:
        rb_too_big()


def rb_too_big():
    """RB.TOO.BIG. Stop: the program does not fit its banks."""
    if g.rb_count == 2:
        er_stop("PROGRAM TOO BIG FOR TWO ROM BANKS")
    er_stop("PROGRAM TOO BIG FOR THREE ROM BANKS")


def rb_length(record_id):
    """RB.LENGTH. The bytes of code of template record_id."""
    g.ram = g.tp_bank
    g.rb_a = g.ram[g.tp_ix + record_id * 2] + 256 * g.ram[g.tp_ix + record_id * 2 + 1]
    return g.ram[g.rb_a]


def rb_fixups():
    """RB.FIXUPS. Each fixup goes with its code: kept in place for the first bank, into
    g.rb_fix for a later bank, or dropped with the JMP around a SUB moved. A call into another
    bank goes to the SUB's veneer in the caller's bank."""
    g.rb_fix = [[], [], []]
    kept = 0
    for i in range(g.fx_n):
        g.fx_i = i
        fx_read()
        j = g.rb_in[i]
        if j >= g.rb_k and g.fx_at < g.rb_from[j] + 3:
            continue
        at = g.fx_at
        bank, g.fx_at = rb_bank_of(at)
        if g.fx_s == K_SEC_CODE:
            target_bank, g.fx_v = rb_bank_of(g.fx_v)
            if target_bank != bank:
                er_stop("JUMP ACROSS ROM BANKS")
        if g.fx_s == K_SEC_LABEL:
            rb_label(bank, at)
        if g.fx_s == K_SEC_REC and g.fx_v == T.R_ICALL and bank != 0:
            # T_FAR's first entry calls into the first bank.
            g.rb_code[bank][g.fx_at] = K_FAR % 256
            g.rb_code[bank][g.fx_at + 1] = K_FAR // 256
            continue
        if bank != 0:
            g.rb_fix[bank].append((g.fx_at, g.fx_k, g.fx_s, g.fx_v, g.fx_ow))
            continue
        g.fx_i = kept
        fx_put()
        kept = kept + 1
    g.fx_n = kept


def rb_label(bank, at):
    """RB.LABEL. A K_SEC_LABEL fixup read, at code offset at before the cut, in bank. A JSR
    to a SUB in another bank goes to its veneer, a K_SEC_CODE fixup in this bank. @ of a SUB
    in a later bank, a LO or HI fixup in any bank, goes to its veneer in the first; all banks
    run at one address."""
    g.sy_r = g.fx_v
    uxc_sym.sy_get()
    if (g.sy_flags & 1) == 0:
        return
    target_bank = rb_bank_of(g.sy_val)[0]
    if g.sy_kind == K_SK_SUB and g.fx_k != K_F_ABS:
        if target_bank != 0:
            rb_veneer_to(0)
        return
    if target_bank == bank:
        return
    g.cb_at = at - 1
    cb_get()
    if g.sy_kind != K_SK_SUB or g.fx_k != K_F_ABS or g.cb_b != 0x20:
        er_stop("GOTO ACROSS ROM BANKS")
    rb_veneer_to(bank)


def rb_veneer_to(bank):
    """RB.VENEER.TO. The fixup read names the veneer in bank of the SUB of record g.fx_v, a
    K_SEC_CODE fixup. The veneer is added when the SUB has none there yet; a SUB has one in
    each other bank that calls it."""
    t = g.rb_index[g.fx_v]
    if g.rb_veneer_at[bank][t] < 0:
        g.rb_veneer_at[bank][t] = g.rb_veneer_base[bank] + \
            len(g.rb_veneers[bank]) * g.rb_veneer_length
        g.rb_veneers[bank].append(t)
    g.fx_s = K_SEC_CODE
    g.fx_v = g.rb_veneer_at[bank][t]


def rb_records():
    """RB.RECORDS. Move the value of each placed LABEL and SUB to its bank's offset."""
    for g.rb_r in range(1, g.sy_n + 1):
        g.sy_r = g.rb_r
        uxc_sym.sy_get()
        if (g.sy_kind == K_SK_LABEL or g.sy_kind == K_SK_SUB) and (g.sy_flags & 1) != 0:
            g.sy_val = rb_bank_of(g.sy_val)[1]
            uxc_sym.sy_set()
    g.dd_at = g.lk_init_at
    uxc_dead.dd_shift()
    g.lk_init_at = g.dd_at


def rb_veneer(address, bank):
    """RB.VENEER. A T_FARCALL to the SUB at address in bank, 0 to 2."""
    g.sl_s[0] = K_SEC_CONST
    g.sl_v[0] = address
    g.sl_s[1] = K_SEC_CONST
    g.sl_v[1] = K_FAR + bank * K_FAR_ENTRY
    emit(T.T_FARCALL)


def rb_end():
    """RB.END. The bank's file ends: $FF up to K_FAR, then T_FAR with the program's banks.
    g.rb_used is the bytes before the $FF."""
    if g.lk_org + g.cb_n > K_FAR:
        er_stop("ROM BANK FULL")
    g.rb_used = g.cb_n
    while g.lk_org + g.cb_n < K_FAR:
        g.cb_b = 0xFF
        cb_add()
    for slot in range(3):
        g.sl_s[slot] = K_SEC_CONST
        g.sl_v[slot] = g.rb_bank[slot]
    emit(T.T_FAR)
    if g.lk_org + g.cb_n != K_FAR_END:
        er_stop("T_FAR DOES NOT END AT $FFA0")


def rb_others():
    """RB.OTHERS. Each later bank: its SUBs moved, its veneers, its runtime records, T_FAR. The
    data records keep the addresses the first bank's link gave them. g.rb_used_banks, g.rb_objs
    and g.rb_sizes hold each bank's bytes in use, file and file size."""
    g.rb_used_banks = [g.rb_used, 0, 0]
    g.rb_objs = [g.ui_obj, "", ""]
    g.rb_sizes = [g.lk_size, 0, 0]
    for bank in range(1, g.rb_count):
        g.cb_n = 0
        for g.cb_b in g.rb_code[bank]:
            cb_add()
        g.fx_n = 0
        for g.fx_at, g.fx_k, g.fx_s, g.fx_v, g.fx_ow in g.rb_fix[bank]:
            g.fx_i = g.fx_n
            fx_put()
            g.fx_n = g.fx_n + 1
        for t in g.rb_veneers[bank]:
            g.sy_r = g.rb_record[t]
            uxc_sym.sy_get()
            rb_veneer(g.lk_org + g.sy_val, rb_bank_index(t))
        rb_need_mark()
        for g.lk_i in range(g.rt_n):
            rt_place()
            if g.rt_dn == 0 and g.rb_need[g.rt_id] != 0:
                emit(g.rt_id)
        rb_end()
        for g.fx_i in range(g.fx_n):
            uxc_link.lk_fix()
        g.rb_objs[bank] = g.rb_objs[0][:-4] + ".PR" + str(bank + 1)
        g.ui_obj = g.rb_objs[bank]
        uxc_link.lk_write()
        g.ui_obj = g.rb_objs[0]
        g.rb_used_banks[bank] = g.rb_used
        g.rb_sizes[bank] = g.lk_size
    g.lk_size = g.rb_sizes[0]
