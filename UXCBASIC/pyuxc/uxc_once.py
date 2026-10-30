"""UXC-ONCE.BL: the code that runs once, at the start and at the end.

    start(tpl_folder)   claim the banks, load the templates, run the first pass, open the
                        source for the second, and emit the program's start
    finish()            the link step, the PRG and the result line
    cb_init()           claim the banks of the strings, the records and the ON CASE targets;
                        the code buffer and the fixups take theirs as they grow
    er_report()         the error message on the screen and in g.ui_line

GPC UXC reads the source name and the result file from UXC.INPUT (UI.READ). pyuxc has them
from its command line, and pyuxc.compile_file sets g.ui_src, g.ui_obj and the folders before
start. GPC UXC claims its own code banks, K.BANK.EXPR to K.BANK.ONCE; pyuxc has none. The PRG
is not chained to (UI.CHAIN).
"""

import uxc_asm
import uxc_code
from uxc_code import emit
import uxc_dead
from uxc_defs import K_ORG
import uxc_flow
import uxc_lex
import uxc_link
import uxc_name
import uxc_ramreg
import uxc_record
import uxc_rombank
import uxc_sub
import uxc_sym
import uxc_tpl as T
from uxc_state import g, put, uxc_bank


def start(tpl_folder):
    put("UXCBASIC 0.1")
    g.lx_no = 0
    g.lx_including = 0
    g.lx_l = ""
    uxc_code.tp_load(tpl_folder)
    uxc_sym.sy_init()
    cb_init()
    g.lx_name = g.ui_src
    uxc_lex.lx_open()
    put("COMPILING " + g.ui_src)
    g.lk_org = K_ORG
    g.lk_raw = 0
    g.lk_apart = 0
    g.lk_data = 0
    g.lk_strs_n = 0
    g.lk_strs_record = 0
    g.rb_on = 0
    g.rb_bank = [0, 0, 0]
    g.rb_count = 0
    g.rb_name = ""
    g.rg_slot = 0
    g.rg_slot_outer = 0
    g.rg_subs = []
    g.rg_sub_slots = []
    g.rg_pins = []
    g.rg_forwards = []
    g.rg_sub_start = 0
    g.rg_pin_from = 0
    g.rg_image = 0
    g.rg_on = 0
    g.rg_base = [0]
    g.vr_n = 0
    g.rt_n = 0
    g.bs_n = 0
    g.sm_errors_on = 1
    g.as_block = 0
    g.nm_enum_record = 0
    g.rd_type_record = 0
    g.rd_type_count = 0
    uxc_sub.sb_scan()
    uxc_lex.close_2()
    uxc_lex.lx_open()
    if g.lk_raw == 0:
        emit(T.T_STUB)
    emit(T.T_START)
    uxc_link.lk_init_call()


def finish():
    """UXC.FINISH. The result line goes into g.ui_line."""
    uxc_lex.close_2()
    uxc_flow.ct_open()
    uxc_sub.sb_open()
    uxc_record.rd_open()
    uxc_name.nm_open()
    uxc_asm.as_open()
    uxc_dead.dd_open()
    emit(T.T_END)
    g.lx_no = 0
    uxc_link.lk_link()
    uxc_link.lk_write()
    if g.rb_on != 0:
        uxc_rombank.rb_others()
    # The emulator's echo shows the file's bytes too, so start a fresh line.
    put("")
    put(g.ui_obj + " " + str(g.lk_size) + " BYTES")
    g.ui_line = "OK," + g.ui_obj + "," + str(g.lk_size)
    if g.rb_on != 0:
        put(", ".join("ROM BANK " + str(g.rb_bank[b]) + " " + str(g.rb_used_banks[b]) + " BYTES"
                      for b in range(g.rb_count)))
        g.ui_line = g.ui_line + ",SECOND " + g.rb_objs[1] + " " + str(g.rb_sizes[1])
        if g.rb_count == 3:
            g.ui_line = g.ui_line + ",THIRD " + g.rb_objs[2] + " " + str(g.rb_sizes[2])
    if g.rg_on != 0:
        for k in range(1, g.rg_count + 1):
            slot = str(g.rg_slots[k - 1])
            put("REGION " + slot + ": " + str(g.rg_size[k]) + " BYTES, " +
                str(len(g.rg_data[k])) + " OF DATA, " + str(g.rg_runtime_size[k]) +
                " OF RUNTIME, " +
                str(uxc_ramreg.K_RG_ROOM - g.rg_size[k]) + " FREE")
            g.ui_line = g.ui_line + ",REGION " + slot + " " + str(g.rg_size[k]) + " BYTES"
    if g.dd_subs > 0:
        g.ui_line = g.ui_line + ",REMOVED " + str(g.dd_subs) + " SUBS " + str(g.dd_bytes) + \
            " BYTES"
    if g.dv_bytes > 0:
        g.ui_line = g.ui_line + ",REMOVED " + str(g.dv_vars) + " VARS " + str(g.dv_bytes) + \
            " BYTES"
    if g.ds_bytes > 0:
        g.ui_line = g.ui_line + ",REMOVED " + str(g.ds_strings) + " STRINGS " + \
            str(g.ds_bytes) + " BYTES"


def cb_init():
    uxc_bank()
    g.sp_bank = g.uxc_b
    uxc_bank()
    g.rt_bank = g.uxc_b
    uxc_bank()
    g.cs_bank = g.uxc_b
    uxc_bank()
    g.cn_bank = g.uxc_b
    g.cn_n = 0
    uxc_code.rt_clear()
    g.cb_n = 0
    g.jp_base = 0
    g.fx_n = 0
    g.sp_n = 0


def er_report():
    """ER.REPORT. The result line goes into g.ui_line."""
    if g.lx_including != 0:
        g.er_m = g.er_m + " (" + g.lx_name + " " + str(g.lx_no) + ")"
        g.lx_no = g.lx_source_no
    if g.lx_no > 0:
        put("?" + g.er_m + " IN " + str(g.lx_no))
        put(g.lx_l)
    else:
        put("?" + g.er_m)
    g.ui_line = "ERROR," + str(g.lx_no) + "," + g.er_m
