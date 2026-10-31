"""Short branches: a long conditional jump becomes one branch where the target is in reach.

    br_long()     in jp_br, before the long form: log the jump at g.cb_n
    br_short()    in jp_br and jp_fwd, after a short branch: log its offset byte, at g.cb_n - 1
    br_rewind()   after the code buffer goes back: drop what the log holds past g.cb_n
    br_moved()    in dd_strip, after the cut's tables are set: drop what was cut, move the rest
    br_relax()    in the link step, after ds_strip. Out: g.br_bytes, the bytes saved

jp_br's long form is 5 bytes: a branch over the jump on the opposite flag, then a JMP. The short
form is 2: that branch with its flag turned, to the target. It saves 3 bytes, 2 cycles when the
branch is taken at run time and 1 when it is not. Bit 5 of the opcode is the flag: BEQ $F0 and BNE
$D0, BCS $B0 and BCC $90.

The cut uses UXC-DEAD.BL's g.dd_from, g.dd_to, g.dd_sum and dd_shift, so the fixups, the values
of the LABEL and SUB records and K_SY_END move as they do for a SUB left out. The JMP's fixup goes
with the JMP. A cut shrinks a distance and never grows one, so a short branch stays in reach.

A short branch that spans a cut gets a new offset; each one the compiler makes is logged. An
offset in an ASM block or a template needs none: it stays inside the block or the template, and
neither holds a logged jump.

A SUB can move to another ROM bank, so the target must be in the same SUB as the jump, or in the
main code with no SUB between them. Trap: g.rg_pins holds offsets into a SUB, so a program with
#REGION_SLOT keeps its long jumps. A full log keeps them too.
"""

from uxc_code import cb_get, cb_put, fx_read
from uxc_defs import K_BR_MAX, K_F_ABS, K_SEC_CODE, K_SEC_LABEL, K_SK_LABEL, K_SK_SUB
import uxc_dead
import uxc_sym
from uxc_state import g


def br_long():
    if g.br_n == K_BR_MAX:
        g.br_full = 1
        return
    g.br_at[g.br_n] = g.cb_n
    g.br_n = g.br_n + 1


def br_short():
    if g.br_byte_n == K_BR_MAX:
        g.br_full = 1
        return
    g.br_byte[g.br_byte_n] = g.cb_n - 1
    g.br_byte_n = g.br_byte_n + 1


def br_rewind():
    g.em_end = -1
    while g.br_n > 0 and g.br_at[g.br_n - 1] >= g.cb_n:
        g.br_n = g.br_n - 1
    while g.br_byte_n > 0 and g.br_byte[g.br_byte_n - 1] >= g.cb_n:
        g.br_byte_n = g.br_byte_n - 1


def br_moved():
    g.br_kept = 0
    for g.br_i in range(g.br_n):
        g.dd_at = g.br_at[g.br_i]
        uxc_dead.dd_shift()
        if g.dd_inside == 0:
            g.br_at[g.br_kept] = g.dd_at
            g.br_kept = g.br_kept + 1
    g.br_n = g.br_kept
    g.br_kept = 0
    for g.br_i in range(g.br_byte_n):
        g.dd_at = g.br_byte[g.br_i]
        uxc_dead.dd_shift()
        if g.dd_inside == 0:
            g.br_byte[g.br_kept] = g.dd_at
            g.br_kept = g.br_kept + 1
    g.br_byte_n = g.br_kept


def br_relax():
    g.br_bytes = 0
    if g.br_full != 0 or len(g.rg_subs) != 0:
        return
    br_subs()
    br_targets()
    g.dd_n = 0
    g.br_changed = 1
    while g.br_changed != 0:
        g.br_changed = 0
        for g.br_i in range(g.br_n):
            if g.br_to[g.br_i] >= 0 and g.br_go[g.br_i] == 0:
                br_try()
        br_cuts()
    if g.dd_n == 0:
        return
    br_write()
    br_offsets()
    uxc_dead.dd_fixups()
    uxc_dead.dd_records()
    uxc_dead.dd_code()
    g.br_bytes = g.dd_n * 3


def br_subs():
    """BR.SUBS. g.br_from and g.br_end: each SUB left in, in code order, from its JMP around to
    its end."""
    ranges = []
    for g.br_r in range(1, g.sy_n + 1):
        g.sy_r = g.br_r
        uxc_sym.sy_get()
        if g.sy_kind == K_SK_SUB and (g.sy_flags & 1) != 0:
            uxc_sym.sy_end_get()
            ranges.append((g.sy_val - 3, g.sy_end))
    ranges.sort()
    g.br_from = [r[0] for r in ranges]
    g.br_end = [r[1] for r in ranges]


def br_part(at):
    """BR.PART. The part of the code that code offset at is in: an odd number for a SUB, an even
    number for the main code between two SUBs. A binary search finds the last SUB that starts at
    or before it."""
    low = 0
    high = len(g.br_from)
    while low < high:
        mid = (low + high) // 2
        if g.br_from[mid] <= at:
            low = mid + 1
        else:
            high = mid
    if low > 0 and at < g.br_end[low - 1]:
        return low * 2 - 1
    return low * 2


def br_targets():
    """BR.TARGETS. g.br_to, the code offset each logged jump goes to, or -1 for one that must stay
    long: a jump out of its part of the code, or to a label not found, which the link reports.
    g.br_go is 0, long for now."""
    for g.br_i in range(g.br_n):
        g.br_to[g.br_i] = -1
        g.br_go[g.br_i] = 0
    for g.fx_i in range(g.fx_n):
        fx_read()
        if g.fx_k == K_F_ABS and (g.fx_s == K_SEC_CODE or g.fx_s == K_SEC_LABEL):
            br_find()
            if g.br_k >= 0:
                br_target()


def br_find():
    """BR.FIND. g.br_k, the logged jump whose JMP has the fixup read as its address, or -1."""
    g.br_k = -1
    low = 0
    high = g.br_n
    while low < high:
        mid = (low + high) // 2
        if g.br_at[mid] < g.fx_at - 3:
            low = mid + 1
        else:
            high = mid
    if low < g.br_n and g.br_at[low] == g.fx_at - 3:
        g.br_k = low


def br_target():
    """BR.TARGET. With fixup g.fx_* the address of logged jump g.br_k."""
    g.br_v = g.fx_v
    if g.fx_s == K_SEC_LABEL:
        g.sy_r = g.fx_v
        uxc_sym.sy_get()
        if g.sy_kind != K_SK_LABEL or (g.sy_flags & 1) == 0:
            return
        g.br_v = g.sy_val
    if br_part(g.br_v) == br_part(g.br_at[g.br_k]):
        g.br_to[g.br_k] = g.br_v


def br_try():
    """BR.TRY. Logged jump g.br_i goes short when its target is in reach with the cuts so far and
    its own. A forward target is past its own cut, which is not in the tables yet."""
    g.br_v = g.br_to[g.br_i]
    g.dd_at = g.br_v
    uxc_dead.dd_shift()
    g.br_d = g.dd_at
    g.dd_at = g.br_at[g.br_i]
    uxc_dead.dd_shift()
    g.br_d = g.br_d - g.dd_at - 2
    if g.br_v > g.br_at[g.br_i]:
        g.br_d = g.br_d - 3
    if g.br_d >= -128 and g.br_d <= 127:
        g.br_go[g.br_i] = 1
        g.br_changed = 1


def br_cuts():
    """BR.CUTS. The cut's tables: the JMP of each logged jump gone short."""
    g.dd_n = 0
    g.br_cut = 0
    for g.br_i in range(g.br_n):
        if g.br_go[g.br_i] != 0:
            g.br_cut = g.br_cut + 3
            g.dd_from[g.dd_n] = g.br_at[g.br_i] + 2
            g.dd_to[g.dd_n] = g.br_at[g.br_i] + 5
            g.dd_sum[g.dd_n] = g.br_cut
            g.dd_n = g.dd_n + 1


def br_write():
    """BR.WRITE. Each logged jump gone short: turn the flag and set the offset."""
    for g.br_i in range(g.br_n):
        if g.br_go[g.br_i] != 0:
            g.dd_at = g.br_to[g.br_i]
            uxc_dead.dd_shift()
            g.br_d = g.dd_at
            g.dd_at = g.br_at[g.br_i]
            uxc_dead.dd_shift()
            g.br_d = g.br_d - g.dd_at - 2
            g.cb_at = g.br_at[g.br_i]
            cb_get()
            g.cb_b = g.cb_b ^ 0x20
            cb_put()
            g.cb_at = g.br_at[g.br_i] + 1
            g.cb_b = g.br_d & 255
            cb_put()


def br_offsets():
    """BR.OFFSETS. A new offset for each logged short branch."""
    for g.br_i in range(g.br_byte_n):
        g.cb_at = g.br_byte[g.br_i]
        cb_get()
        g.br_d = g.cb_b
        if g.br_d > 127:
            g.br_d = g.br_d - 256
        g.dd_at = g.cb_at + 1 + g.br_d
        uxc_dead.dd_shift()
        g.br_d = g.dd_at
        g.dd_at = g.cb_at + 1
        uxc_dead.dd_shift()
        g.cb_b = (g.br_d - g.dd_at) & 255
        cb_put()
