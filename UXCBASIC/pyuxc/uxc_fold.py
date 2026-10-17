"""UXC-FOLD.BL: constant folding, for ex_binary and ex_unary, and the whole number of a
constant.

    ex_fold()          two constants: the result is a constant, and no code is emitted
    ex_fold_address()  @name + constant or @name - constant is an address too
    ex_fold_negate()   0 minus the constant entry g.ex_i, as g.ex_r and g.ex_cg for ex_setc
    ex_whole()         in  g.ex_i    out g.ex_whole_value, the whole number of the constant
    ex_text()          in  g.ex_whole_value    out g.ex_text_result, as STR$ shows it
    ex_const_word()    stop the compile when the constant entry g.ex_i is a LONG

UXC-FOLD.BL has the rules of a fold. GPC's numbers are exact only below 4294967296, so the
fold works on the bits 16 at a time. Python's are exact, and pyuxc keeps the same steps.
"""

from uxc_defs import K_EO_ADD, K_EO_AND, K_EO_EQ, K_EO_GE, K_EO_GT, K_EO_LE, K_EO_LT, K_EO_MOD, \
    K_EO_MUL, K_EO_NE, K_EO_OR, K_EO_SHL, K_EO_SHR, K_EO_SUB, K_EO_XOR, K_TY_LONG, K_TY_WORD
import uxc_expr
from uxc_state import er_stop, g


def ex_fold():
    g.ex_i = g.ex_il
    ex_whole()
    g.ex_a = g.ex_whole_value
    g.ex_i = g.ex_ir
    ex_whole()
    g.ex_b = g.ex_whole_value
    g.ex_fold_long = 0
    if g.ex_vt[g.ex_il] == K_TY_LONG or g.ex_vt[g.ex_ir] == K_TY_LONG:
        g.ex_fold_long = 1
    g.ex_r = 0
    g.ex_negative = 0
    if g.ex_o == K_EO_ADD or g.ex_o == K_EO_SUB or g.ex_o == K_EO_MUL:
        ex_fold_arithmetic()
    if g.ex_z == 1:
        ex_fold_divide()
    if g.ex_o == K_EO_EQ and g.ex_a == g.ex_b:
        g.ex_r = 1
    if g.ex_o == K_EO_NE and g.ex_a != g.ex_b:
        g.ex_r = 1
    if g.ex_o == K_EO_LT and g.ex_a < g.ex_b:
        g.ex_r = 1
    if g.ex_o == K_EO_GT and g.ex_a > g.ex_b:
        g.ex_r = 1
    if g.ex_o == K_EO_LE and g.ex_a <= g.ex_b:
        g.ex_r = 1
    if g.ex_o == K_EO_GE and g.ex_a >= g.ex_b:
        g.ex_r = 1
    if g.ex_o == K_EO_SHL or g.ex_o == K_EO_SHR:
        ex_fold_shift()
    if g.ex_o <= K_EO_AND:
        ex_fold_bits()
    g.ex_wrap = g.ex_r
    ex_fold_wrap()
    g.ex_r = g.ex_wrap
    if g.ex_negative == 1 and g.ex_r >= g.ex_fold_half:
        g.ex_cg = 1
    g.ex_vn = g.ex_vn - 1
    g.ex_i = g.ex_il
    uxc_expr.ex_setc()


def ex_fold_arithmetic():
    """EX.FOLD.ARITHMETIC. g.ex_a + g.ex_b, g.ex_a - g.ex_b or g.ex_a * g.ex_b in g.ex_r, as
    bits."""
    if g.ex_o == K_EO_ADD and g.ex_a < 0 - g.ex_b:
        g.ex_negative = 1
    if g.ex_o == K_EO_SUB and g.ex_a < g.ex_b:
        g.ex_negative = 1
    if g.ex_o == K_EO_MUL and (g.ex_a < 0) != (g.ex_b < 0):
        g.ex_negative = 1
    g.ex_wrap = g.ex_a
    ex_fold_wrap()
    g.ex_x = g.ex_wrap
    g.ex_wrap = g.ex_b
    ex_fold_wrap()
    g.ex_y = g.ex_wrap
    if g.ex_o == K_EO_SUB and g.ex_y > 0:
        g.ex_y = g.ex_fold_max - g.ex_y + 1
    g.ex_fold_xh = g.ex_x // 65536
    g.ex_fold_xl = g.ex_x - g.ex_fold_xh * 65536
    g.ex_fold_yh = g.ex_y // 65536
    g.ex_fold_yl = g.ex_y - g.ex_fold_yh * 65536
    if g.ex_o == K_EO_MUL:
        g.ex_fold_low = g.ex_fold_xl * g.ex_fold_yl
        g.ex_fold_part = g.ex_fold_xl * g.ex_fold_yh
        g.ex_fold_high = g.ex_fold_part - g.ex_fold_part // 65536 * 65536
        g.ex_fold_part = g.ex_fold_xh * g.ex_fold_yl
        g.ex_fold_high = g.ex_fold_high + (g.ex_fold_part - g.ex_fold_part // 65536 * 65536)
    else:
        g.ex_fold_low = g.ex_fold_xl + g.ex_fold_yl
        g.ex_fold_high = g.ex_fold_xh + g.ex_fold_yh
    g.ex_fold_high = g.ex_fold_high + g.ex_fold_low // 65536
    g.ex_fold_high = g.ex_fold_high - g.ex_fold_high // 65536 * 65536
    g.ex_fold_low = g.ex_fold_low - g.ex_fold_low // 65536 * 65536
    g.ex_r = g.ex_fold_high * 65536 + g.ex_fold_low


def ex_fold_divide():
    """EX.FOLD.DIVIDE. g.ex_a / g.ex_b or g.ex_a MOD g.ex_b in g.ex_r. The quotient rounds
    toward 0, and the remainder has the sign of g.ex_a."""
    g.ex_aa = g.ex_a
    if g.ex_aa < 0:
        g.ex_aa = 0 - g.ex_aa
    g.ex_bb = g.ex_b
    if g.ex_bb < 0:
        g.ex_bb = 0 - g.ex_bb
    g.ex_q = 0
    g.ex_fold_rest = g.ex_aa
    g.ex_fold_bit = 2147483648
    for g.ex_j in range(1, 33):
        if g.ex_fold_rest // g.ex_fold_bit >= g.ex_bb:
            g.ex_fold_rest = g.ex_fold_rest - g.ex_bb * g.ex_fold_bit
            g.ex_q = g.ex_q + g.ex_fold_bit
        g.ex_fold_bit = g.ex_fold_bit // 2
    g.ex_r = g.ex_q
    if (g.ex_a < 0) != (g.ex_b < 0):
        g.ex_r = 0 - g.ex_q
    if g.ex_o == K_EO_MOD:
        g.ex_r = g.ex_fold_rest
        if g.ex_a < 0:
            g.ex_r = 0 - g.ex_fold_rest
    if g.ex_r < 0:
        g.ex_negative = 1


def ex_fold_address():
    g.ex_r = g.ex_vv[g.ex_il] + g.ex_vv[g.ex_ir]
    if g.ex_o == K_EO_SUB:
        g.ex_r = g.ex_vv[g.ex_il] - g.ex_vv[g.ex_ir] + 65536
    g.ex_r = g.ex_r - g.ex_r // 65536 * 65536
    g.ex_vn = g.ex_vn - 1
    g.ex_i = g.ex_il
    g.ex_vv[g.ex_il] = g.ex_r
    g.ex_vt[g.ex_il] = K_TY_WORD


def ex_fold_shift():
    """EX.FOLD.SHIFT. g.ex_a shifted by the low byte of g.ex_b, at the width of the left side.
    << works on the bits. >> halves the whole number, so a signed g.ex_a keeps its sign."""
    g.ex_fold_long = 0
    if g.ex_vt[g.ex_il] == K_TY_LONG:
        g.ex_fold_long = 1
    ex_fold_size()
    g.ex_r = g.ex_a
    if g.ex_o == K_EO_SHL:
        g.ex_wrap = g.ex_r
        ex_fold_wrap()
        g.ex_r = g.ex_wrap
    g.ex_negative = g.ex_vg[g.ex_il]
    g.ex_n = g.ex_b - g.ex_b // 256 * 256
    if g.ex_n > g.ex_fold_width:
        g.ex_n = g.ex_fold_width
    if g.ex_n == 0:
        return
    for g.ex_j in range(1, g.ex_n + 1):
        if g.ex_o == K_EO_SHL and g.ex_r >= g.ex_fold_half:
            g.ex_r = g.ex_r - g.ex_fold_half
        if g.ex_o == K_EO_SHL:
            g.ex_r = g.ex_r * 2
        if g.ex_o == K_EO_SHR:
            g.ex_r = g.ex_r // 2


def ex_fold_size():
    """EX.FOLD.SIZE. The width g.ex_fold_long gives: g.ex_fold_width bits, g.ex_fold_max the
    top bits and g.ex_fold_half the first bit that reads as negative."""
    g.ex_fold_width = 16
    g.ex_fold_max = 65535
    g.ex_fold_half = 32768
    if g.ex_fold_long == 0:
        return
    g.ex_fold_width = 32
    g.ex_fold_max = 4294967295
    g.ex_fold_half = 2147483648


def ex_fold_wrap():
    """EX.FOLD.WRAP. g.ex_wrap, a whole number from -4294967295 to 4294967295, made bits at
    the width g.ex_fold_long gives."""
    ex_fold_size()
    if g.ex_wrap < 0:
        g.ex_wrap = g.ex_fold_max + g.ex_wrap + 1
    if g.ex_wrap > g.ex_fold_max:
        g.ex_wrap = g.ex_wrap - g.ex_wrap // 65536 * 65536


def ex_fold_bits():
    """EX.FOLD.BITS. AND, OR or XOR, a bit at a time."""
    g.ex_wrap = g.ex_a
    ex_fold_wrap()
    g.ex_x = g.ex_wrap
    g.ex_wrap = g.ex_b
    ex_fold_wrap()
    g.ex_y = g.ex_wrap
    g.ex_r = 0
    g.ex_m = 1
    g.ex_negative = 0
    if g.ex_vg[g.ex_il] == 1 or g.ex_vg[g.ex_ir] == 1:
        g.ex_negative = 1
    for g.ex_j in range(1, g.ex_fold_width + 1):
        g.ex_xb = g.ex_x - g.ex_x // 2 * 2
        g.ex_yb = g.ex_y - g.ex_y // 2 * 2
        if g.ex_o == K_EO_AND:
            g.ex_r = g.ex_r + g.ex_m * g.ex_xb * g.ex_yb
        if g.ex_o == K_EO_OR:
            g.ex_r = g.ex_r + g.ex_m * min(g.ex_xb + g.ex_yb, 1)
        if g.ex_o == K_EO_XOR:
            g.ex_r = g.ex_r + g.ex_m * (g.ex_xb + g.ex_yb - 2 * g.ex_xb * g.ex_yb)
        g.ex_m = g.ex_m * 2
        g.ex_x = g.ex_x // 2
        g.ex_y = g.ex_y // 2


def ex_fold_negate():
    ex_whole()
    g.ex_n = 0 - g.ex_whole_value
    g.ex_r = g.ex_n
    if g.ex_n < 0:
        g.ex_r = 4294967295 + g.ex_n + 1
    if g.ex_n < 0 and g.ex_r >= 2147483648:
        g.ex_cg = 1


def ex_whole():
    g.ex_whole_value = g.ex_vv[g.ex_i]
    if g.ex_vg[g.ex_i] == 0:
        return
    g.ex_whole_value = g.ex_whole_value - 65536
    if g.ex_vt[g.ex_i] == K_TY_LONG:
        g.ex_whole_value = g.ex_whole_value - 4294901760


def ex_text():
    """EX.TEXT. A space or a -, then the digits."""
    g.ex_text_n = g.ex_whole_value
    if g.ex_text_n < 0:
        g.ex_text_n = 0 - g.ex_text_n
    g.ex_text_result = ""
    while True:
        g.ex_text_q = g.ex_text_n // 10
        g.ex_text_result = chr(48 + (g.ex_text_n - g.ex_text_q * 10)) + g.ex_text_result
        g.ex_text_n = g.ex_text_q
        if g.ex_text_n <= 0:
            break
    if g.ex_whole_value < 0:
        g.ex_text_result = "-" + g.ex_text_result
    else:
        g.ex_text_result = " " + g.ex_text_result


def ex_const_word():
    if g.ex_vt[g.ex_i] == K_TY_LONG:
        er_stop("NUMBER TOO BIG")
