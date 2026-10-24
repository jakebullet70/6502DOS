"""The compiler's global variables, and the stop on the first error.

GPC UXC keeps every variable global. pyuxc keeps them as attributes of g, named after the GPC
variable: CB.N there is g.cb_n here. new() empties g before each compile and makes the arrays
of UXC.BASL.

Trap: a GPC variable reads 0 or "" before its first assignment. An attribute of g does not
exist until it is set, so a read before the first set raises AttributeError. Set it where GPC
UXC first reads it.

GPC selects a RAM bank with BANK and then PEEKs $A000 + n. Here g.ram is the selected bank, a
bytearray of 8192 bytes, and that PEEK is g.ram[n].

er_stop is ER.STOP: it raises Stop, and pyuxc.compile_file reports the error. The UXCBASIC
rewrite reports the error and ENDs at the same point.
"""

from uxc_defs import K_ALIASES, K_ASM_LABELS, K_DD_MAX, K_DS_MAX, K_DV_MAX, K_EX_MAX, K_NS_MAX, \
    K_RAM_BANKS, K_SB_DEFAULTS, K_SB_DEPTH, K_SYM_BANKS


class State:
    pass


g = State()


class Stop(Exception):
    """The compile stops with g.er_m, the message."""


class NotPorted(Exception):
    """The compile reached a part of GPC UXC that pyuxc does not have yet. The argument names
    the GPC routine."""


def new():
    g.__dict__.clear()
    g.screen = []
    g.uxc_banks = 0
    dim()


def dim():
    """The DIMs at the top of UXC.BASL."""
    g.sy_bank = [0] * K_SYM_BANKS
    g.cb_bank = []
    g.fx_bank = []
    g.em_b = [0] * 256
    g.sl_s = [0] * 4
    g.sl_v = [0] * 4
    g.ex_poke_at = -1
    g.ex_poke_vb = 0
    for name in ("ex_op", "ex_vk", "ex_vs", "ex_vt", "ex_vv", "ex_jt", "ex_jf", "ex_oa", "ex_vg"):
        setattr(g, name, [0] * (K_EX_MAX + 1))
    for name in ("ns_k", "ns_no", "ns_p", "ns_sn", "ns_top", "ns_ex", "ns_ct", "ns_fl", "ns_el",
                 "ns_va", "ns_vt", "ns_lc", "ns_lv", "ns_st", "ns_vs", "ns_nb", "ns_ha", "hv_ad", "ns_sk",
                 "ns_sg",
                 "sb_saved_hidden"):
        setattr(g, name, [0] * (K_NS_MAX + 1))
    g.ns_l = [""] * (K_NS_MAX + 1)
    for name in ("sb_call_record", "sb_call_parameters", "sb_call_result", "sb_call_argument",
                 "sb_call_stacked", "sb_call_enum", "sb_call_sig", "sb_call_at", "sb_call_pin", "sb_saved_operators", "sb_saved_operator_base",
                 "sb_saved_parentheses", "sb_saved_condition"):
        setattr(g, name, [0] * (K_SB_DEPTH + 1))
    g.sg_called = [""] * (K_SB_DEPTH + 1)
    g.sb_default_text = [""] * (K_SB_DEFAULTS + 1)
    g.as_label_name = [""] * K_ASM_LABELS
    g.as_label_at = [0] * K_ASM_LABELS
    g.nm_alias_name = [""] * K_ALIASES
    g.nm_alias_target = [""] * K_ALIASES
    g.as_reference_name = [""] * K_ASM_LABELS
    g.as_reference_at = [0] * K_ASM_LABELS
    g.as_reference_kind = [0] * K_ASM_LABELS
    g.as_reference_no = [0] * K_ASM_LABELS
    g.hv_ad = [-1] * (K_NS_MAX + 1)
    g.dd_from = [0] * K_DD_MAX
    g.dd_to = [0] * K_DD_MAX
    g.dd_sum = [0] * K_DD_MAX
    g.dv_at = [0] * (2 * K_DV_MAX)
    g.dv_cut = [0] * (2 * K_DV_MAX)
    g.dv_used = [0] * (2 * K_DV_MAX)
    g.dv_count = [0, 0]
    g.dv_total = [0, 0]
    g.ds_at = [0] * K_DS_MAX
    g.ds_cut = [0] * K_DS_MAX
    g.ds_used = [0] * K_DS_MAX
    # The variables GPC UXC reads before it first sets them.
    for name in ("ns_d", "tk_k", "ex_cm", "ex_sg", "ex_cg", "ex_ty", "sm_last_return", "cs_wait",
                 "sb_depth", "sb_frame", "sy_cnt", "ex_on", "ex_pd", "sg_base", "sg_depth",
                 "sg_printing", "nm_find_quiet", "nm_type_signed", "sg_last_offset",
                 "sg_last_new", "sg_empty_offset", "sg_empty_known", "sg_appending",
                 "sg_chr_temp", "sg_chr_start", "sg_chr_fixups", "cs_jo", "sm_last_jump",
                 "dd_keep_subs", "dd_region_line", "dv_keep_vars", "dv_full", "ex_const_record",
                 "nm_type_enum", "sb_enum", "sb_default_count", "sb_filling", "sb_read_only",
                 "sg_read_only", "nm_type_sig", "sb_sig", "sb_pointer_at"):
        setattr(g, name, 0)
    g.sg_last_text = ""
    g.dd_region_text = ""


def put(text):
    """PRINT text: one line of the compiler's screen output, kept in g.screen."""
    g.screen.append(text)


def uxc_bank():
    """UXC.BANK. A free RAM bank in g.uxc_b. The compile stops with OUT OF RAM BANKS after
    K_RAM_BANKS banks."""
    if g.uxc_banks >= K_RAM_BANKS:
        er_stop("OUT OF RAM BANKS")
    g.uxc_banks = g.uxc_banks + 1
    g.uxc_b = bytearray(8192)


def er_stop(message):
    g.er_m = message
    raise Stop(message)


def er_mismatch():
    er_stop("TYPE MISMATCH")


def er_missing_as():
    er_stop("MISSING AS: " + g.sm_n)


def er_syntax():
    er_stop("SYNTAX ERROR")
