"""UXC-DEAD.BL: leave out the SUBs and FUNCTIONs that nothing calls, and the global variables
that nothing names.

    dd_strip()   at the start of the link step: cut the code of every SUB that the main
                 program does not reach through a chain of calls, and count the runtime
                 records again. Out: g.dd_subs, the SUBs left out, and g.dd_bytes, the bytes
                 of code and runtime records saved. g.dd_keep_subs set keeps every SUB.
    dd_keep_line() a line that starts with #, with the token at the #: #KEEP or #ENDKEEP.
                   #ORG and #DATA lines are skipped; dd_place_scan read them
    dd_place_scan() in sb_scan's pass, a line that starts with #: #ORG or #DATA
    dd_open()      at the end of the source, a #KEEP without its #ENDKEEP is an error
    dv_log()       in g.dv_s, 0 for the variables or 1 for the array space, and g.sb_place:
                   log where a new global variable starts
    dv_strip()     after dd_strip: give no room to a global variable that no fixup names, and
                   move the others down. Out: g.dv_vars, the named variables left out, and
                   g.dv_bytes, the bytes saved. g.dv_keep_vars set keeps every variable.
    ds_strip()     after dv_strip: leave out each string literal that no fixup names, and move
                   the others down. Out: g.ds_strings, the literals left out, and g.ds_bytes,
                   the bytes saved. g.dv_keep_vars set keeps every literal.

    #KEEP NAME[, NAME]...  keeps each SUB or FUNCTION named, and the SUBs it calls
    #KEEP ALL              keeps every SUB, as g.dd_keep_subs does
    #KEEP ... #ENDKEEP     keeps each SUB whose SUB line is between them
A SUB kept has K_SY_LIVE set before the link step.

    #ORG address    the code starts at the address. The file has no BASIC line and no load
                    address: g.lk_raw is 1.
    #DATA address   the variables, then the array space, start at the address, outside the
                    file, and the startup clears both: g.lk_apart is 1, g.lk_data the address.
Each is allowed once. The first pass reads them, so they hold for the whole source wherever
they stand.

A call is a K_SEC_LABEL fixup to the SUB's record, owned by the caller. A SUB's code runs from
the JMP around it, 3 bytes before its value, to the word at K_SY_END of its record. Every
reference into the code is a fixup, or the value of a LABEL or SUB record, so cutting a range
moves the code after it down and changes only those. A SUB left out becomes a K_SK_DEAD record,
and so do the call records and temps it owned, so SB.POOLS gives them no room.

The global variables lie end to end in the order DV.LOG met them, so each logged start runs to
the next. A variable is used when a fixup's value falls in its range; a variable left out
becomes K_SK_DEAD. A local, a temp, and a DIM ... AT variable are never logged.
Trap: in ASM, @name plus a number past the variable's end names the next variable instead.

The string literals lie end to end in SP.ADD's pool, each [max][len][data]. A literal is used
when a K_SEC_STR fixup names it. A literal of a SUB left out, or of a CONST nothing names, has
none once dd_strip has dropped the fixups in the code cut.
"""

from uxc_code import cb_get, cb_put, fx_put, fx_read, rt_clear, rt_use
from uxc_defs import K_DD_MAX, K_DS_MAX, K_DV_MAX, K_FRAME_BASE, K_RT_LIST, K_SEC_BSS, \
    K_SEC_CODE, K_SEC_LABEL, K_SEC_REC, K_SEC_STR, K_SEC_VAR, K_SK_ARRAY, K_SK_CALL, K_SK_DEAD, K_SK_LABEL, K_SK_SUB, \
    K_SK_VAR, K_SY_BLOCK, K_SY_END, K_SY_FIXED, K_SY_LIVE, K_SY_TEMP, K_TT_EOL, K_TT_NAME, \
    K_TT_NUM, K_TT_OP, K_TY_STR
import uxc_lex
import uxc_name
import uxc_sym
from uxc_state import er_stop, er_syntax, g


def dd_strip():
    g.dd_subs = 0
    g.dd_bytes = 0
    if g.dd_keep_subs != 0:
        return
    dd_live()
    dd_ranges()
    if g.dd_n == 0:
        return
    dd_owned()
    dd_runtime_bytes()
    g.dd_runtime_before = g.dd_runtime
    dd_fixups()
    dd_records()
    dd_code()
    dd_runtime()
    dd_runtime_bytes()
    g.dd_bytes = g.dd_bytes + g.dd_runtime_before - g.dd_runtime


def dd_live():
    """DD.LIVE. Set K_SY_LIVE on every SUB the main program, or a SUB kept, reaches. Each
    pass follows the calls of the SUBs found live so far, until a pass finds none new. A
    GOTO to a label inside a SUB keeps that SUB too."""
    g.dd_changed = 1
    while g.dd_changed != 0:
        g.dd_changed = 0
        for g.fx_i in range(g.fx_n):
            fx_read()
            if g.fx_s == K_SEC_LABEL:
                dd_follow()


def dd_follow():
    """DD.FOLLOW. With a K_SEC_LABEL fixup read: when its owner is live, so is the SUB it
    calls, or the SUB that owns the label it jumps to."""
    if g.fx_ow != 0:
        g.sy_r = g.fx_ow
        uxc_sym.sy_get()
        if (g.sy_flags & K_SY_LIVE) == 0:
            return
    g.sy_r = g.fx_v
    uxc_sym.sy_get()
    if g.sy_kind == K_SK_LABEL:
        if g.sy_owner == 0:
            return
        g.sy_r = g.sy_owner
        uxc_sym.sy_get()
    if g.sy_kind != K_SK_SUB or (g.sy_flags & K_SY_LIVE) != 0:
        return
    g.sy_flags = g.sy_flags + K_SY_LIVE
    uxc_sym.sy_set()
    g.dd_changed = 1


def dd_ranges():
    """DD.RANGES. The code range of each SUB not live, in g.dd_from and g.dd_to, in code
    order, and g.dd_sum(k), the bytes cut up to the end of range k. Each such SUB becomes
    K_SK_DEAD."""
    g.dd_n = 0
    g.dd_last = 0
    for g.dd_record in range(1, g.sy_n + 1):
        g.sy_r = g.dd_record
        uxc_sym.sy_get()
        if g.sy_kind == K_SK_SUB and (g.sy_flags & K_SY_LIVE) == 0:
            dd_range()


def dd_range():
    if g.dd_n >= K_DD_MAX:
        er_stop("TOO MANY SUBS TO LEAVE OUT")
    g.dd_from[g.dd_n] = g.sy_val - 3
    g.ram[g.sy_ad + 2] = K_SK_DEAD
    g.dd_to[g.dd_n] = g.ram[g.sy_ad + K_SY_END] + 256 * g.ram[g.sy_ad + K_SY_END + 1]
    # SB.SCAN adds the SUB records in source order, which is code order.
    if g.dd_from[g.dd_n] < g.dd_last:
        er_stop("SUBS OUT OF ORDER")
    g.dd_last = g.dd_to[g.dd_n]
    g.dd_bytes = g.dd_bytes + g.dd_to[g.dd_n] - g.dd_from[g.dd_n]
    g.dd_sum[g.dd_n] = g.dd_bytes
    g.dd_n = g.dd_n + 1
    g.dd_subs = g.dd_subs + 1


def dd_owned():
    """DD.OWNED. A call record or a temp owned by a SUB left out becomes K_SK_DEAD."""
    for g.dd_record in range(1, g.sy_n + 1):
        g.sy_r = g.dd_record
        uxc_sym.sy_get()
        g.dd_kind = g.sy_kind
        if g.dd_kind == K_SK_VAR and (g.sy_flags & K_SY_TEMP) == 0:
            g.dd_kind = 0
        if (g.dd_kind == K_SK_CALL or g.dd_kind == K_SK_VAR) and g.sy_owner != 0:
            g.sy_r = g.sy_owner
            uxc_sym.sy_get()
            if g.sy_kind == K_SK_DEAD:
                g.sy_r = g.dd_record
                uxc_sym.sy_at()
                g.ram[g.sy_ad + 2] = K_SK_DEAD


def dd_shift():
    """DD.SHIFT. In g.dd_at, a code offset; out g.dd_at, where that code is after the cut,
    and g.dd_inside, 1 when the offset is in a range cut. A binary search finds the ranges
    that end at or before it."""
    g.dd_low = 0
    g.dd_high = g.dd_n
    while g.dd_low < g.dd_high:
        g.dd_mid = (g.dd_low + g.dd_high) // 2
        if g.dd_to[g.dd_mid] <= g.dd_at:
            g.dd_low = g.dd_mid + 1
        else:
            g.dd_high = g.dd_mid
    g.dd_inside = 0
    if g.dd_low < g.dd_n and g.dd_from[g.dd_low] <= g.dd_at:
        g.dd_inside = 1
    if g.dd_low > 0:
        g.dd_at = g.dd_at - g.dd_sum[g.dd_low - 1]


def dd_fixups():
    """DD.FIXUPS. Drop the fixups in the ranges cut, and move the others with the code.
    Trap: the owner does not tell where a fixup is. A call stores its arguments under the
    SUB called as owner, in the caller's code."""
    g.dd_kept = 0
    for g.dd_i in range(g.fx_n):
        g.fx_i = g.dd_i
        fx_read()
        g.dd_at = g.fx_at
        dd_shift()
        if g.dd_inside == 0:
            dd_fixup_keep()
    g.fx_n = g.dd_kept


def dd_fixup_keep():
    """DD.FIXUP.KEEP. With g.dd_at the fixup's place after the cut."""
    g.fx_at = g.dd_at
    if g.fx_s == K_SEC_CODE:
        g.dd_at = g.fx_v
        dd_shift()
        g.fx_v = g.dd_at
    g.fx_i = g.dd_kept
    fx_put()
    g.dd_kept = g.dd_kept + 1


def dd_records():
    """DD.RECORDS. Move the value of each placed LABEL and live SUB with the code."""
    for g.dd_record in range(1, g.sy_n + 1):
        g.sy_r = g.dd_record
        uxc_sym.sy_get()
        if (g.sy_kind == K_SK_LABEL or g.sy_kind == K_SK_SUB) and (g.sy_flags & 1) != 0:
            g.dd_at = g.sy_val
            dd_shift()
            g.sy_val = g.dd_at
            uxc_sym.sy_set()
    g.dd_at = g.lk_init_at
    dd_shift()
    g.lk_init_at = g.dd_at


def dd_code():
    """DD.CODE. Copy the code down over the ranges cut."""
    g.dd_write = 0
    g.dd_read = 0
    for g.dd_k in range(g.dd_n + 1):
        g.dd_stop = g.cb_n
        if g.dd_k < g.dd_n:
            g.dd_stop = g.dd_from[g.dd_k]
        while g.dd_read < g.dd_stop:
            g.cb_at = g.dd_read
            cb_get()
            g.cb_at = g.dd_write
            cb_put()
            g.dd_read = g.dd_read + 1
            g.dd_write = g.dd_write + 1
        if g.dd_k < g.dd_n:
            g.dd_read = g.dd_to[g.dd_k]
    g.cb_n = g.dd_write


def dd_runtime():
    """DD.RUNTIME. The runtime records needed are those the fixups kept name, in the order
    they first name them, the order RT.USE met them in."""
    rt_clear()
    g.rt_n = 0
    for g.fx_i in range(g.fx_n):
        fx_read()
        if g.fx_s == K_SEC_REC:
            g.rt_id = g.fx_v
            rt_use()


def dd_keep_line():
    """DD.KEEP.LINE. #KEEP, #KEEP ALL, #KEEP NAME[, NAME]... or #ENDKEEP, with the token at
    the #. The token is left at the end of the line."""
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NAME:
        er_syntax()
    if g.tk_s == "ENDKEEP":
        if g.dd_region_line == 0:
            er_stop("#ENDKEEP WITHOUT #KEEP")
        g.dd_region_line = 0
        uxc_lex.lx_next()
        return
    if g.tk_s == "ORG" or g.tk_s == "DATA":
        uxc_lex.lx_next()
        uxc_lex.lx_next()
        return
    if g.tk_s != "KEEP":
        er_syntax()
    uxc_lex.lx_next()
    if g.tk_t == K_TT_EOL:
        if g.dd_region_line != 0:
            er_stop("#KEEP INSIDE #KEEP")
        g.dd_region_line = g.lx_no
        g.dd_region_text = g.lx_l
        return
    if g.tk_t == K_TT_NAME and g.tk_s == "ALL":
        g.dd_keep_subs = 1
        uxc_lex.lx_next()
        return
    while True:
        dd_keep_name()
        if g.tk_t != K_TT_OP or g.tk_k != 44:
            return
        uxc_lex.lx_next()


def dd_place_scan():
    """DD.PLACE.SCAN. #ORG address or #DATA address, with the token at the #. Any other #
    line is left to dd_keep_line."""
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NAME or (g.tk_s != "ORG" and g.tk_s != "DATA"):
        return
    g.dd_place = g.tk_s
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NUM or g.tk_v > 65535:
        er_syntax()
    if g.dd_place == "ORG":
        if g.lk_raw != 0:
            er_stop("#ORG TWICE")
        g.lk_raw = 1
        g.lk_org = g.tk_v
    else:
        if g.lk_apart != 0:
            er_stop("#DATA TWICE")
        g.lk_apart = 1
        g.lk_data = g.tk_v
    uxc_lex.lx_next()
    if g.tk_t != K_TT_EOL:
        er_syntax()


def dd_keep_name():
    """DD.KEEP.NAME. One name of #KEEP NAME, found as a CALL finds it."""
    if g.tk_t != K_TT_NAME:
        er_syntax()
    g.sm_n = g.tk_s
    uxc_name.nm_find()
    if g.sy_kind != K_SK_SUB:
        er_stop("NOT A SUB: " + g.sm_n)
    if (g.sy_flags & K_SY_LIVE) == 0:
        g.sy_flags = g.sy_flags + K_SY_LIVE
        uxc_sym.sy_set()
    uxc_lex.lx_next()


def dd_open():
    """DD.OPEN. A #KEEP still open at the end of the source is an error at its line."""
    if g.dd_region_line == 0:
        return
    g.lx_no = g.dd_region_line
    g.lx_l = g.dd_region_text
    er_stop("#KEEP WITHOUT #ENDKEEP")


def dd_runtime_bytes():
    """DD.RUNTIME.BYTES. g.dd_runtime, the bytes of the runtime records needed now."""
    g.dd_runtime = 0
    for g.dd_i in range(g.rt_n):
        g.ram = g.rt_bank
        g.dd_id = g.ram[K_RT_LIST - 0xA000 + g.dd_i * 2] + \
            256 * g.ram[K_RT_LIST - 0xA000 + g.dd_i * 2 + 1]
        g.ram = g.tp_bank
        g.dd_a = g.ram[g.tp_ix + g.dd_id * 2] + 256 * g.ram[g.tp_ix + g.dd_id * 2 + 1]
        g.dd_runtime = g.dd_runtime + g.ram[g.dd_a]


# Unused variables

def dv_log():
    """DV.LOG. A variable of no bytes is not logged, so that no two starts are the same. A
    full log keeps every variable."""
    if g.sb_place_size == 0:
        return
    if g.dv_count[g.dv_s] == K_DV_MAX:
        g.dv_full = 1
        return
    g.dv_at[g.dv_s * K_DV_MAX + g.dv_count[g.dv_s]] = g.sb_place
    g.dv_count[g.dv_s] = g.dv_count[g.dv_s] + 1


def dv_strip():
    g.dv_vars = 0
    g.dv_bytes = 0
    if g.dv_keep_vars != 0 or g.dv_full != 0:
        return
    dv_mark()
    g.dv_s = 0
    g.dv_end = g.vr_n
    dv_cuts()
    g.dv_s = 1
    g.dv_end = g.bs_n
    dv_cuts()
    g.dv_bytes = g.dv_total[0] + g.dv_total[1]
    if g.dv_bytes == 0:
        return
    dv_fixups()
    dv_records()
    g.vr_n = g.vr_n - g.dv_total[0]
    g.bs_n = g.bs_n - g.dv_total[1]


def dv_section():
    """DV.SECTION. g.dv_s for fixup g.fx_s g.fx_v: 0 in the variables, 1 in the array space,
    and -1 for any other section or a local."""
    g.dv_s = -1
    if g.fx_v >= K_FRAME_BASE:
        return
    if g.fx_s == K_SEC_VAR:
        g.dv_s = 0
    if g.fx_s == K_SEC_BSS:
        g.dv_s = 1


def dv_find():
    """DV.FIND. In g.dv_s and g.dv_off, an offset there. Out: g.dv_k, the log entry of the
    variable that holds it, or -1 before the first. A binary search finds the last start at or
    below the offset."""
    g.dv_low = 0
    g.dv_high = g.dv_count[g.dv_s]
    g.dv_base = g.dv_s * K_DV_MAX
    while g.dv_low < g.dv_high:
        g.dv_mid = (g.dv_low + g.dv_high) // 2
        if g.dv_at[g.dv_base + g.dv_mid] <= g.dv_off:
            g.dv_low = g.dv_mid + 1
        else:
            g.dv_high = g.dv_mid
    g.dv_k = -1
    if g.dv_low > 0:
        g.dv_k = g.dv_base + g.dv_low - 1


def dv_mark():
    """DV.MARK. g.dv_used is 1 for each variable a fixup names."""
    for g.dv_i in range(2 * K_DV_MAX):
        g.dv_used[g.dv_i] = 0
    for g.fx_i in range(g.fx_n):
        fx_read()
        dv_section()
        if g.dv_s >= 0:
            g.dv_off = g.fx_v
            dv_find()
            if g.dv_k >= 0:
                g.dv_used[g.dv_k] = 1


def dv_cuts():
    """DV.CUTS. In g.dv_s, and g.dv_end, the end of its variables. g.dv_cut, the bytes left
    out below each variable, and g.dv_total(g.dv_s), the bytes left out in all."""
    g.dv_base = g.dv_s * K_DV_MAX
    g.dv_sum = 0
    for g.dv_i in range(g.dv_count[g.dv_s]):
        g.dv_k = g.dv_base + g.dv_i
        g.dv_cut[g.dv_k] = g.dv_sum
        if g.dv_used[g.dv_k] == 0:
            g.dv_next = g.dv_end
            if g.dv_i + 1 < g.dv_count[g.dv_s]:
                g.dv_next = g.dv_at[g.dv_k + 1]
            g.dv_sum = g.dv_sum + g.dv_next - g.dv_at[g.dv_k]
    g.dv_total[g.dv_s] = g.dv_sum


def dv_fixups():
    """DV.FIXUPS. Move each fixup's value down by the bytes left out below it."""
    for g.fx_i in range(g.fx_n):
        fx_read()
        dv_section()
        if g.dv_s >= 0:
            g.dv_off = g.fx_v
            dv_find()
            if g.dv_k >= 0:
                g.fx_v = g.fx_v - g.dv_cut[g.dv_k]
                fx_put()


def dv_records():
    """DV.RECORDS. A global variable or array left out becomes K_SK_DEAD; the value of each
    other one moves down. A record or string variable lives in the array space."""
    for g.dd_record in range(1, g.sy_n + 1):
        g.sy_r = g.dd_record
        uxc_sym.sy_get()
        g.dv_s = -1
        if g.sy_kind == K_SK_VAR:
            g.dv_s = 0
            if (g.sy_flags & K_SY_BLOCK) != 0 or g.sy_type == K_TY_STR:
                g.dv_s = 1
            if (g.sy_flags & K_SY_TEMP) != 0:
                g.dv_s = -1
        if g.sy_kind == K_SK_ARRAY:
            g.dv_s = 1
        if (g.sy_flags & K_SY_FIXED) != 0 or g.sy_val >= K_FRAME_BASE:
            g.dv_s = -1
        if g.dv_s >= 0:
            dv_record()


def dv_record():
    g.dv_off = g.sy_val
    dv_find()
    if g.dv_k < 0:
        return
    if g.dv_used[g.dv_k] == 0:
        g.ram[g.sy_ad + 2] = K_SK_DEAD
        g.dv_vars = g.dv_vars + 1
        return
    g.sy_val = g.sy_val - g.dv_cut[g.dv_k]
    uxc_sym.sy_set()


# Unused string literals

def ds_strip():
    g.ds_strings = 0
    g.ds_bytes = 0
    if g.dv_keep_vars != 0:
        return
    ds_index()
    ds_mark()
    ds_cuts()
    if g.ds_bytes == 0:
        return
    ds_fixups()
    ds_pool()


def ds_index():
    """DS.INDEX. g.ds_at, the start of each literal in the pool, and g.ds_count."""
    g.ds_count = 0
    g.ds_off = 0
    g.ram = g.sp_bank
    while g.ds_off < g.sp_n:
        if g.ds_count == K_DS_MAX:
            er_stop("TOO MANY STRINGS")
        g.ds_at[g.ds_count] = g.ds_off
        g.ds_used[g.ds_count] = 0
        g.ds_count = g.ds_count + 1
        g.ds_off = g.ds_off + g.ram[g.ds_off] + 2


def ds_find():
    """DS.FIND. In g.ds_off, an offset in the pool. Out: g.ds_k, the literal that holds it. A
    binary search finds the last start at or below the offset."""
    g.ds_low = 0
    g.ds_high = g.ds_count
    while g.ds_low < g.ds_high:
        g.ds_mid = (g.ds_low + g.ds_high) // 2
        if g.ds_at[g.ds_mid] <= g.ds_off:
            g.ds_low = g.ds_mid + 1
        else:
            g.ds_high = g.ds_mid
    g.ds_k = g.ds_low - 1


def ds_mark():
    """DS.MARK. g.ds_used is 1 for each literal a fixup names."""
    for g.fx_i in range(g.fx_n):
        fx_read()
        if g.fx_s == K_SEC_STR:
            g.ds_off = g.fx_v
            ds_find()
            g.ds_used[g.ds_k] = 1


def ds_cuts():
    """DS.CUTS. g.ds_cut, the bytes left out below each literal, and g.ds_bytes in all."""
    g.ram = g.sp_bank
    for g.ds_i in range(g.ds_count):
        g.ds_cut[g.ds_i] = g.ds_bytes
        if g.ds_used[g.ds_i] == 0:
            g.ds_bytes = g.ds_bytes + g.ram[g.ds_at[g.ds_i]] + 2
            g.ds_strings = g.ds_strings + 1


def ds_fixups():
    """DS.FIXUPS. Move each K_SEC_STR fixup's value down by the bytes left out below it."""
    for g.fx_i in range(g.fx_n):
        fx_read()
        if g.fx_s == K_SEC_STR:
            g.ds_off = g.fx_v
            ds_find()
            g.fx_v = g.fx_v - g.ds_cut[g.ds_k]
            fx_put()


def ds_pool():
    """DS.POOL. Copy each literal used down over those left out."""
    g.ram = g.sp_bank
    for g.ds_i in range(g.ds_count):
        if g.ds_used[g.ds_i] != 0:
            g.ds_from = g.ds_at[g.ds_i]
            g.ds_to = g.ds_from - g.ds_cut[g.ds_i]
            g.ds_end = g.ds_from + g.ram[g.ds_from] + 2
            while g.ds_from < g.ds_end:
                g.ram[g.ds_to] = g.ram[g.ds_from]
                g.ds_from = g.ds_from + 1
                g.ds_to = g.ds_to + 1
    g.sp_n = g.sp_n - g.ds_bytes
