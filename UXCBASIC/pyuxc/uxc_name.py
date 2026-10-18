"""UXC-NAME.BL: scopes: finding a name, NAMESPACE, BIND, and the reserved words.

    nm_reserved()   in  g.sm_n      stop when the name is a word of the language, or qualified
    nm_word()       in  g.sm_n      out g.nm_word_found, 1 when the name is a word of the language
    nm_scan()                       the first pass: NAMESPACE and END NAMESPACE, with the token
                                    at the line's first word
    nm_find()       in  g.sm_n      out g.sy_*, the record the name means; stops when there is none
    nm_end()                        END NAMESPACE, with the token at NAMESPACE, or ENDNAMESPACE
    nm_body()       in  g.sm_w      stop when a statement may not stand in a namespace body
    nm_declaration() in g.sm_w      CONST, NAMESPACE, ENDNAMESPACE, BIND, ENUM or TYPE, with the
                                    token at it; out g.nm_declared, 0 when g.sm_w is none of them
    nm_at()         in  g.sm_n g.sm_ty g.sm_cnt    DIM name AT address, with the token after the type
    nm_as_type()    in  g.sm_ty     AS type, with the token at AS; out g.sm_ty, and the token
                                    after the type
    nm_type_name()  in  g.tk_s      out g.nm_type_code, the type a word names, 0 for none;
                                    g.nm_type_signed, 1 for a signed type; g.nm_type_enum, the
                                    ENUM's record for ENUM.name, else 0

    nm_bind()                       BIND name [=] target
    nm_bind_scan()                  the first pass: BIND name [=] word, with the token at BIND
    nm_enum_scan()                  the first pass: ENUM name, with the token at ENUM
    nm_enum()       in  g.sm_w      ENUM name, with the token at ENUM, or a stray ENDENUM
    nm_enum_members()               one line inside an ENUM

UXC-NAME.BL has the rules of the scopes.
"""

from uxc_defs import K_ALIASES, K_CN_SIZE, K_EK_CONST, K_SK_BIND, K_SK_CONST, K_SK_ENUM, \
    K_SK_LABEL, K_SK_SPACE, K_SK_SUB, K_SK_VAR, K_SY_ENUM_PARAMETER, K_SY_FIXED, K_SY_MEMBER, K_SY_SCANNED, \
    K_SY_SIGNED, K_TT_EOL, K_TT_NAME, K_TT_NUM, K_TT_OP, K_TT_STR, K_TY_BYTE, K_TY_LONG, K_TY_RECORD, K_TY_STR, K_TY_WORD
import uxc_expr
import uxc_fold
import uxc_lex
import uxc_record
import uxc_sym
from uxc_state import er_missing_as, er_stop, er_syntax, g


def nm_reserved():
    if uxc_lex.instr(g.sm_n, ".") > 0:
        nm_error_qualified()
    nm_word()
    if g.nm_word_found != 0:
        nm_error_reserved()


def nm_word():
    """NM.WORD. PRINT$ is a word as PRINT is. MID$ is in the list as it is spelled."""
    g.nm_word_found = 0
    g.nm_r = "|PRINT|END|DIM|VAR|AS|BYTE|WORD|STRING|IF|THEN|ELSE|ELSEIF|ENDIF|DO|LOOP|WHILE"
    g.nm_r = g.nm_r + "|UBYTE|UWORD|INT|UINT|LONG|ULONG"
    g.nm_r = g.nm_r + "|UNTIL|FOR|TO|STEP|NEXT|REPEAT|ENDREPEAT|EXIT|CONTINUE|ERRORS|UXC"
    g.nm_r = g.nm_r + "|NAMESPACE|ENDNAMESPACE|BIND|CONST|ENUM|ENDENUM|TYPE|ENDTYPE|"
    g.nm_q = "|GOTO|SUB|ENDSUB|FUNCTION|ENDFUNCTION|CALL|RETURN|INPUT|LINPUT|GETKEY|OPEN|CLOSE|READ|WRITE|EOF"
    g.nm_q = g.nm_q + "|DIR|PEEK|POKE|SYS|ASM|AND|OR|XOR|NOT|MOD|LEN|MID$|LEFT$|RIGHT$|CHR$|ASC|STR$|VAL|LVAL|NOFILE|"
    g.nm_q = g.nm_q + "INSTR|POS|ON|CASE|ENDCASE|SELECT|ENDSELECT|"
    g.nm_q = g.nm_q + "ADDROF|CONTENTSAT|CONTENTSATW|"
    g.nm_b = "|" + g.sm_n + "|"
    if uxc_lex.instr(g.nm_r, g.nm_b) > 0:
        g.nm_word_found = 1
    if uxc_lex.instr(g.nm_q, g.nm_b) > 0:
        g.nm_word_found = 1
    g.nm_b = g.sm_n[-1:]
    if g.nm_b != "$":
        return
    g.nm_b = "|" + g.sm_n[:len(g.sm_n) - 1] + "|"
    if uxc_lex.instr(g.nm_r, g.nm_b) > 0:
        g.nm_word_found = 1
    if uxc_lex.instr(g.nm_q, g.nm_b) > 0:
        g.nm_word_found = 1


def nm_scan():
    """NM.SCAN. The first pass makes each namespace's record, so that the SUBs in it are
    declared in it. A NAMESPACE that names an open namespace again reopens it.
    g.nm_scan_path is the qualified name of g.nm_current with a dot after it, "" outside."""
    if g.tk_s == "NAMESPACE":
        nm_scan_open()
        return
    if g.tk_s == "ENDNAMESPACE":
        nm_scan_close()
        return
    if g.tk_s != "END":
        return
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NAME:
        return
    if g.tk_s == "NAMESPACE":
        nm_scan_close()


def nm_scan_open():
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NAME or g.tk_m != 0:
        er_syntax()
    g.sm_n = g.tk_s
    nm_reserved()
    g.sy_name = g.sm_n
    g.sy_ow = g.nm_current
    uxc_sym.sy_find()
    g.nm_scan_path = g.nm_scan_path + g.sm_n + "."
    if g.sy_r == 0:
        # NM.SCAN.NEW
        g.sy_kind = K_SK_SPACE
        g.sy_type = 0
        g.sy_val = 0
        g.sy_flags = 0
        g.sy_cnt = 0
        uxc_sym.sy_add()
        g.nm_current = g.sy_r
        return
    uxc_sym.sy_get()
    if g.sy_kind != K_SK_SPACE:
        nm_error_duplicate()
    g.nm_current = g.sy_r


def nm_scan_close():
    if g.nm_current == 0:
        return
    g.sy_r = g.nm_current
    uxc_sym.sy_get()
    g.nm_current = g.sy_owner
    g.nm_scan_path = g.nm_scan_path[:len(g.nm_scan_path) - 1]
    while True:
        if g.nm_scan_path == "":
            return
        if g.nm_scan_path[-1:] == ".":
            return
        g.nm_scan_path = g.nm_scan_path[:len(g.nm_scan_path) - 1]


def nm_namespace():
    if g.sb_current != 0:
        er_stop("NAMESPACE IN A SUB")
    if g.ns_d != 0:
        er_stop("NAMESPACE IN A BLOCK")
    uxc_lex.lx_next()
    g.sy_name = g.tk_s
    g.sy_ow = g.nm_current
    uxc_sym.sy_find()
    if g.sy_r == 0:
        er_syntax()
    if g.nm_current == 0:
        g.nm_line = g.lx_no
    if g.nm_current == 0:
        g.nm_text = g.lx_l
    g.nm_current = g.sy_r
    g.nm_scope = g.sy_r
    uxc_lex.lx_next()


def nm_end():
    """NM.END. END NAMESPACE, with the token at NAMESPACE, or ENDNAMESPACE."""
    if g.sb_current != 0:
        er_stop("END NAMESPACE IN A SUB")
    if g.nm_current == 0:
        er_stop("END NAMESPACE WITHOUT NAMESPACE")
    g.sy_r = g.nm_current
    uxc_sym.sy_get()
    g.nm_current = g.sy_owner
    g.nm_scope = g.nm_current
    uxc_lex.lx_next()


def nm_body():
    """NM.BODY. A namespace body holds declarations and SUBs, and nothing that runs. END is
    allowed only as END NAMESPACE; the token after it is read, and g.lx_p put back."""
    if uxc_lex.instr("|DIM|VAR|CONST|ENUM|TYPE|ENDTYPE|SUB|FUNCTION|NAMESPACE|ENDNAMESPACE|BIND"
                     "|ERRORS|", "|" + g.sm_w + "|") > 0:
        return
    if g.sm_w != "END":
        nm_error_body()
    g.nm_saved_position = g.lx_p
    uxc_lex.lx_next()
    g.lx_p = g.nm_saved_position
    if g.tk_t != K_TT_NAME:
        nm_error_body()
    if g.tk_s != "NAMESPACE":
        nm_error_body()


def nm_declaration():
    """NM.DECLARATION. Out: g.nm_declared, 0 when g.sm_w is none of the declarations."""
    g.nm_declared = 1
    if g.sm_w == "CONST":
        nm_const()
        return
    if g.sm_w == "NAMESPACE":
        nm_namespace()
        return
    if g.sm_w == "ENDNAMESPACE":
        nm_end()
        return
    if g.sm_w == "BIND":
        nm_bind()
        return
    if g.sm_w == "ENUM" or g.sm_w == "ENDENUM":
        nm_enum()
        return
    if g.sm_w == "TYPE" or g.sm_w == "ENDTYPE":
        uxc_record.rd_type()
        return
    g.nm_declared = 0


# Finding a name

def nm_find():
    """NM.FIND. The first part of the name is looked for in g.nm_scope, then in each scope
    around it, out to the main program. Each further part is looked for in the scope the part
    before it names. A BIND is followed to its target. A name in a SUB is found only from
    inside that SUB. With g.nm_find_quiet set, a name not found gives g.sy_r = 0, not an
    error. The part after a record variable is a field, which RD.MEMBER gives."""
    g.nm_rest = g.sm_n
    nm_split()
    g.nm_owner = g.nm_scope
    # NM.FIND.OUTWARD
    while True:
        g.sy_name = g.nm_part
        g.sy_ow = g.nm_owner
        uxc_sym.sy_find()
        if g.sy_r != 0:
            break
        if g.nm_owner == 0:
            nm_find_missing()
            return
        g.sy_r = g.nm_owner
        uxc_sym.sy_get()
        g.nm_owner = g.sy_owner
    while True:
        # NM.FIND.FOUND
        uxc_sym.sy_get()
        if g.sy_kind == K_SK_BIND:
            g.sy_r = g.sy_val
            uxc_sym.sy_get()
        # NM.FIND.TARGET
        if g.nm_rest == "":
            return
        if g.sy_kind == K_SK_VAR and g.sy_type >= K_TY_RECORD:
            uxc_record.rd_member()
            return
        if g.sy_kind != K_SK_SPACE and g.sy_kind != K_SK_SUB and g.sy_kind != K_SK_ENUM:
            er_stop("NOT A NAMESPACE: " + g.nm_part)
        if g.sy_kind == K_SK_SUB and g.sy_r != g.sb_current:
            er_stop("LOCAL TO A SUB: " + g.sm_n)
        nm_split()
        g.sy_name = g.nm_part
        g.sy_ow = g.sy_r
        uxc_sym.sy_find()
        if g.sy_r == 0:
            nm_find_missing()
            return


def nm_find_missing():
    if g.nm_find_quiet != 0:
        return
    er_stop("UNDECLARED NAME " + g.sm_n)


def nm_split():
    """NM.SPLIT. The first part of g.nm_rest into g.nm_part, and the rest after its dot back
    into g.nm_rest, "" when there is none."""
    g.nm_dot = uxc_lex.instr(g.nm_rest, ".")
    if g.nm_dot == 0:
        g.nm_part = g.nm_rest
        g.nm_rest = ""
        return
    g.nm_part = g.nm_rest[:g.nm_dot - 1]
    g.nm_rest = g.nm_rest[g.nm_dot:]


# Fixed addresses

def nm_at():
    """NM.AT. AT address after the name g.sm_n, of type g.sm_ty, in a DIM. The address is a
    constant. The variable takes no space: its record holds the address, flagged
    K_SY_FIXED."""
    if g.tk_s != "AT":
        er_syntax()
    if g.sm_cnt != 0 or g.sm_ty == K_TY_STR:
        er_stop("NOT YET: AN ARRAY OR A STRING AT AN ADDRESS")
    g.nm_at_name = g.sm_n
    g.nm_at_type = g.sm_ty
    g.nm_at_signed = g.nm_type_signed
    uxc_lex.lx_next()
    uxc_expr.ex_expr()
    g.ex_i = g.ex_vn - 1
    if g.ex_vk[g.ex_i] != K_EK_CONST:
        er_stop("ADDRESS NOT A CONSTANT")
    uxc_fold.ex_const_word()
    g.nm_at_address = g.ex_vv[g.ex_i]
    g.ex_vn = g.ex_vn - 1
    g.sm_n = g.nm_at_name
    g.sm_ty = g.nm_at_type
    g.sy_name = g.sm_n
    g.sy_ow = g.nm_scope
    uxc_sym.sy_find()
    if g.sy_r != 0:
        nm_error_duplicate()
    g.sy_kind = K_SK_VAR
    g.sy_type = g.nm_at_type
    g.sy_val = g.nm_at_address
    g.sy_flags = K_SY_FIXED + g.nm_at_signed * K_SY_SIGNED
    g.sy_cnt = 0
    uxc_sym.sy_add()


# Constants

def nm_as_type():
    """NM.AS.TYPE. AS type, with the token at AS, after a name of mark g.sm_ty. Out: g.sm_ty,
    and the token after the type."""
    if g.sm_ty != 0:
        er_stop("A MARK AND AS")
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NAME:
        er_syntax()
    nm_type_name()
    g.sm_ty = g.nm_type_code
    if g.sm_ty == 0:
        uxc_record.rd_as_type()
    uxc_lex.lx_next()


def nm_type_name():
    """NM.TYPE.NAME. UBYTE and BYTE, UWORD or UINT and WORD or INT, ULONG and LONG, and
    STRING. BYTE, WORD, INT and LONG are signed. ENUM.name is the type of that ENUM's
    members, unsigned. An ENUM's name without ENUM. stops the compile."""
    g.nm_type_code = 0
    g.nm_type_signed = 0
    g.nm_type_enum = 0
    if g.tk_s[:5] == "ENUM.":
        nm_type_enum()
        return
    if g.tk_s == "BYTE" or g.tk_s == "WORD" or g.tk_s == "INT" or g.tk_s == "LONG":
        g.nm_type_signed = 1
    if g.tk_s == "UBYTE" or g.tk_s == "BYTE":
        g.nm_type_code = K_TY_BYTE
    if g.tk_s == "UWORD" or g.tk_s == "UINT":
        g.nm_type_code = K_TY_WORD
    if g.tk_s == "WORD" or g.tk_s == "INT":
        g.nm_type_code = K_TY_WORD
    if g.tk_s == "STRING":
        g.nm_type_code = K_TY_STR
    if g.tk_s == "LONG" or g.tk_s == "ULONG":
        g.nm_type_code = K_TY_LONG
    if g.nm_type_code == 0:
        nm_type_bare_enum()


def nm_type_enum():
    """NM.TYPE.ENUM. ENUM.name, with the token at it."""
    g.nm_type_saved_name = g.sm_n
    g.sm_n = g.tk_s[5:]
    g.nm_find_quiet = 1
    nm_find()
    g.nm_find_quiet = 0
    if g.sy_r == 0 or g.sy_kind != K_SK_ENUM:
        er_stop("NOT AN ENUM: " + g.sm_n)
    g.sm_n = g.nm_type_saved_name
    g.nm_type_code = g.sy_type
    g.nm_type_enum = g.sy_r


def nm_type_bare_enum():
    """NM.TYPE.BARE.ENUM. A word that names an ENUM stops the compile."""
    g.nm_type_saved_name = g.sm_n
    g.sm_n = g.tk_s
    g.nm_find_quiet = 1
    nm_find()
    g.nm_find_quiet = 0
    g.sm_n = g.nm_type_saved_name
    if g.sy_r != 0 and g.sy_kind == K_SK_ENUM:
        er_stop("USE AS ENUM." + g.tk_s)


def nm_const():
    """NM.CONST. CONST N AS UBYTE = 10, several to a line. The AS is required. The value is a
    constant expression, and the type sets its range. A CONST takes no space. A string CONST
    is nm_const_string's."""
    while True:
        uxc_lex.lx_next()
        if g.tk_t != K_TT_NAME:
            er_syntax()
        g.sm_n = g.tk_s
        g.sm_ty = g.tk_m
        nm_reserved()
        uxc_lex.lx_next()
        if g.tk_t == K_TT_NAME and g.tk_s == "AS":
            nm_as_type()
        if g.sm_ty == 0:
            er_missing_as()
        if g.sm_ty >= K_TY_RECORD:
            er_stop("A CONST IS A NUMBER OR A STRING")
        if g.tk_t != K_TT_OP or g.tk_k != 61:
            er_syntax()
        if g.sm_ty == K_TY_STR:
            nm_const_string()
            if g.tk_t != K_TT_OP or g.tk_k != 44:
                return
            continue
        g.nm_const_name = g.sm_n
        g.nm_const_type = g.sm_ty
        g.nm_const_signed = g.nm_type_signed
        uxc_lex.lx_next()
        uxc_expr.ex_expr()
        g.sm_n = g.nm_const_name
        g.ex_i = g.ex_vn - 1
        if g.ex_vk[g.ex_i] != K_EK_CONST:
            er_stop("VALUE NOT A CONSTANT")
        g.nm_const_value = g.ex_vv[g.ex_i]
        g.nm_const_negative = g.ex_vg[g.ex_i]
        uxc_fold.ex_whole()
        g.nm_const_whole = g.ex_whole_value
        g.ex_vn = g.ex_vn - 1
        nm_const_range()
        g.sy_name = g.sm_n
        g.sy_ow = g.nm_scope
        uxc_sym.sy_find()
        if g.sy_r != 0:
            nm_error_duplicate()
        g.sy_kind = K_SK_CONST
        g.sy_type = g.nm_const_type
        g.sy_cnt = g.nm_const_value // 65536
        g.sy_val = g.nm_const_value - g.sy_cnt * 65536
        g.sy_flags = g.nm_const_negative * K_SY_SIGNED
        uxc_sym.sy_add()
        if g.tk_t != K_TT_OP or g.tk_k != 44:
            return


def nm_const_string():
    """NM.CONST.STRING. CONST E$ = CHR$(27) + "[7m", with the token at the =. The value is
    string literals, CHR$ of a constant expression and string CONSTs, joined by +, folded to
    one text. The text goes into g.cn_bank; the record keeps its offset in g.sy_val and its
    length in g.sy_cnt. A use is a literal of the text, which ex_operand pushes."""
    g.nm_const_name = g.sm_n
    g.nm_const_text = ""
    while True:
        uxc_lex.lx_next()
        nm_const_part()
        if len(g.nm_const_text) > 255:
            er_stop("TOO BIG FOR A STRING: " + g.nm_const_name)
        if g.tk_t != K_TT_OP or g.tk_k != 43:
            break
    g.sm_n = g.nm_const_name
    g.sy_name = g.sm_n
    g.sy_ow = g.nm_scope
    uxc_sym.sy_find()
    if g.sy_r != 0:
        nm_error_duplicate()
    g.nm_const_length = len(g.nm_const_text)
    if g.cn_n + g.nm_const_length > K_CN_SIZE:
        er_stop("TOO MANY CONST STRINGS")
    g.ram = g.cn_bank
    for g.nm_const_i in range(g.nm_const_length):
        g.ram[g.cn_n + g.nm_const_i] = ord(g.nm_const_text[g.nm_const_i])
    g.sy_kind = K_SK_CONST
    g.sy_type = K_TY_STR
    g.sy_val = g.cn_n
    g.sy_cnt = g.nm_const_length
    g.sy_flags = 0
    uxc_sym.sy_add()
    g.cn_n = g.cn_n + g.nm_const_length


def nm_const_part():
    """NM.CONST.PART. One part of a string CONST's value, appended to g.nm_const_text, with
    the token at the part. Out: the token after it."""
    if g.tk_t == K_TT_STR:
        g.nm_const_text = g.nm_const_text + g.tk_s
        uxc_lex.lx_next()
        return
    if g.tk_t == K_TT_NUM:
        er_stop("TYPE MISMATCH")
    if g.tk_t != K_TT_NAME:
        er_stop("VALUE NOT A CONSTANT")
    if g.tk_s == "CHR$":
        nm_const_chr()
        return
    g.sm_n = g.tk_s
    nm_word()
    if g.nm_word_found == 1:
        er_stop("VALUE NOT A CONSTANT")
    nm_find()
    if g.sy_kind != K_SK_CONST:
        er_stop("VALUE NOT A CONSTANT")
    if g.sy_type != K_TY_STR:
        er_stop("TYPE MISMATCH")
    nm_const_get()
    g.nm_const_text = g.nm_const_text + g.nm_const_got
    uxc_lex.lx_next()


def nm_const_chr():
    """NM.CONST.CHR. CHR$(n) in a string CONST's value, n a constant expression. The low byte
    of n is the character, as for CHR$ in an expression."""
    uxc_lex.lx_next()
    if g.tk_t != K_TT_OP or g.tk_k != 40:
        er_stop("MISSING ( AFTER CHR$")
    uxc_lex.lx_next()
    uxc_expr.ex_expr()
    g.ex_i = g.ex_vn - 1
    if g.ex_vk[g.ex_i] != K_EK_CONST:
        er_stop("VALUE NOT A CONSTANT")
    g.nm_const_value = g.ex_vv[g.ex_i]
    g.ex_vn = g.ex_vn - 1
    if g.tk_t != K_TT_OP or g.tk_k != 41:
        er_stop("MISSING )")
    g.nm_const_text = g.nm_const_text + chr(g.nm_const_value - (g.nm_const_value // 256) * 256)
    uxc_lex.lx_next()


def nm_const_get():
    """NM.CONST.GET. In: the record of a string CONST loaded by sy_get. Out: g.nm_const_got,
    its text."""
    g.nm_const_got = ""
    g.ram = g.cn_bank
    for g.nm_const_i in range(g.sy_cnt):
        g.nm_const_got = g.nm_const_got + chr(g.ram[g.sy_val + g.nm_const_i])


def nm_const_range():
    """NM.CONST.RANGE. The value g.nm_const_whole fits the CONST's type."""
    g.nm_const_low = 0
    g.nm_const_high = 255
    if g.nm_const_type == K_TY_WORD:
        g.nm_const_high = 65535
    if g.nm_const_type == K_TY_LONG:
        g.nm_const_high = 4294967295
    if g.nm_const_signed == 1:
        g.nm_const_high = g.nm_const_high // 2
        g.nm_const_low = 0 - g.nm_const_high - 1
    if g.nm_const_whole > g.nm_const_high:
        if g.nm_const_type == K_TY_BYTE:
            g.er_m = "TOO BIG FOR A BYTE: " + g.sm_n
        if g.nm_const_type == K_TY_WORD:
            g.er_m = "TOO BIG FOR A WORD: " + g.sm_n
        if g.nm_const_type == K_TY_LONG:
            g.er_m = "TOO BIG FOR A LONG: " + g.sm_n
        er_stop(g.er_m)
    if g.nm_const_whole < g.nm_const_low:
        er_stop("TOO SMALL: " + g.sm_n)


# BIND

def nm_bind():
    """NM.BIND. BIND name [=] target. The target is a variable, an array, a SUB, a namespace
    or a word of the language, and the new name has the same mark as the target. The record
    keeps the target's record, so a BIND of a BIND names the first target. A BIND to a word
    was made by nm_bind_scan, and is passed over here."""
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NAME:
        er_syntax()
    g.nm_bind_name = g.tk_s
    g.nm_bind_mark = g.tk_m
    nm_bind_target()
    g.sm_n = g.tk_s
    nm_word()
    if g.nm_word_found != 0:
        uxc_lex.lx_next()
        return
    g.sm_n = g.nm_bind_name
    nm_reserved()
    g.sm_n = g.tk_s
    nm_find()
    if g.sy_kind == K_SK_LABEL:
        er_stop("BIND OF A LABEL")
    if (g.sy_flags & K_SY_MEMBER) != 0:
        er_stop("BIND OF A FIELD")
    g.nm_target = g.sy_r
    g.nm_target_type = g.sy_type
    g.sy_name = g.nm_bind_name
    g.sy_ow = g.nm_scope
    uxc_sym.sy_find()
    g.sm_n = g.nm_bind_name
    if g.sy_r != 0:
        nm_bind_scanned()
        return
    g.nm_bind_flags = 0
    nm_bind_add()
    uxc_lex.lx_next()


def nm_bind_scanned():
    """NM.BIND.SCANNED. The second pass meets a BIND of nm_bind_scan once and clears its
    flag, so that a second BIND of the name is a duplicate."""
    uxc_sym.sy_get()
    if g.sy_kind != K_SK_BIND:
        nm_error_duplicate()
    if (g.sy_flags & K_SY_SCANNED) == 0:
        nm_error_duplicate()
    g.sy_flags = g.sy_flags - K_SY_SCANNED
    uxc_sym.sy_set()
    uxc_lex.lx_next()


def nm_bind_add():
    """NM.BIND.ADD. The record of BIND g.nm_bind_name in g.sy_ow, to g.nm_target of type
    g.nm_target_type, with flags g.nm_bind_flags."""
    g.sy_name = g.nm_bind_name
    g.sy_kind = K_SK_BIND
    g.sy_type = g.nm_target_type
    g.sy_val = g.nm_target
    g.sy_flags = g.nm_bind_flags
    g.sy_cnt = 0
    uxc_sym.sy_add()


def nm_bind_target():
    """NM.BIND.TARGET. The optional = and the target name, with the token left at the
    target."""
    uxc_lex.lx_next()
    if g.tk_t == K_TT_OP and g.tk_k == 61:
        uxc_lex.lx_next()
    if g.tk_t != K_TT_NAME:
        er_syntax()
    if g.tk_m != g.nm_bind_mark:
        er_stop("BIND NEEDS THE SAME MARK")


def nm_bind_scan():
    """NM.BIND.SCAN. A BIND to a word of the language adds g.nm_scan_path + name to the
    aliases, and lx_next reads that name as the word. In a namespace the name may be a word
    itself: BIND INSTR INSTR in NAMESPACE STR makes STR.INSTR. A BIND to a SUB declared
    above it, outside a SUB body, is made by nm_bind_scan_sub. Any other BIND waits for
    nm_bind."""
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NAME:
        return
    g.nm_bind_name = g.tk_s
    g.nm_bind_mark = g.tk_m
    nm_bind_target()
    g.sm_n = g.tk_s
    nm_word()
    if g.nm_word_found == 0:
        nm_bind_scan_sub()
        return
    g.nm_alias_word = g.tk_s
    g.sm_n = g.nm_bind_name
    if uxc_lex.instr(g.sm_n, ".") > 0:
        nm_error_qualified()
    if g.nm_current == 0:
        nm_reserved()
    g.sm_n = g.nm_scan_path + g.nm_bind_name
    g.nm_alias_index = 0
    while g.nm_alias_index < g.nm_alias_count:
        if g.nm_alias_name[g.nm_alias_index] == g.sm_n:
            nm_error_duplicate()
        g.nm_alias_index = g.nm_alias_index + 1
    if g.nm_alias_count >= K_ALIASES:
        er_stop("TOO MANY BINDS TO WORDS")
    g.nm_alias_name[g.nm_alias_count] = g.sm_n
    g.nm_alias_target[g.nm_alias_count] = g.nm_alias_word
    g.nm_alias_count = g.nm_alias_count + 1


def nm_bind_scan_sub():
    """NM.BIND.SCAN.SUB. A target that is not found, or is not a SUB, or a name already in
    the namespace, is left for nm_bind, which gives the error."""
    if g.sb_scan_in_sub != 0:
        return
    g.nm_scope = g.nm_current
    g.nm_find_quiet = 1
    nm_find()
    g.nm_find_quiet = 0
    g.nm_scope = 0
    if g.sy_r == 0:
        return
    if g.sy_kind != K_SK_SUB:
        return
    g.nm_target = g.sy_r
    g.nm_target_type = g.sy_type
    g.sm_n = g.nm_bind_name
    nm_reserved()
    g.sy_name = g.nm_bind_name
    g.sy_ow = g.nm_current
    uxc_sym.sy_find()
    if g.sy_r != 0:
        return
    g.nm_bind_flags = K_SY_SCANNED
    nm_bind_add()


# Enums

def nm_enum_scan():
    """NM.ENUM.SCAN. The first pass makes the record of an ENUM outside a SUB body, so that a
    parameter can be of its type. Its members are the second pass's. A bad or duplicate name
    is left for nm_enum, which gives the error."""
    if g.sb_scan_in_sub != 0:
        return
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NAME or g.tk_m != 0:
        return
    g.sm_n = g.tk_s
    nm_word()
    if g.nm_word_found != 0:
        return
    g.sy_name = g.tk_s
    g.sy_ow = g.nm_current
    uxc_sym.sy_find()
    if g.sy_r != 0:
        return
    g.sy_kind = K_SK_ENUM
    g.sy_type = K_TY_BYTE
    g.sy_val = 0
    g.sy_flags = K_SY_SCANNED
    g.sy_cnt = 0
    uxc_sym.sy_add()


def nm_enum():
    """NM.ENUM. g.nm_enum_record is the ENUM's record from here to its END ENUM, and sm_line
    sends each line to nm_enum_members. g.nm_scope is the ENUM meanwhile, so that a value can
    use the members before it bare."""
    if g.sm_w == "ENDENUM":
        nm_error_end_enum()
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NAME or g.tk_m != 0:
        er_syntax()
    g.sm_n = g.tk_s
    nm_reserved()
    g.sy_name = g.sm_n
    g.sy_ow = g.nm_scope
    uxc_sym.sy_find()
    if g.sy_r != 0:
        nm_enum_scanned()
    else:
        g.sy_kind = K_SK_ENUM
        g.sy_type = K_TY_BYTE
        g.sy_val = 0
        g.sy_flags = 0
        g.sy_cnt = 0
        uxc_sym.sy_add()
    g.nm_enum_record = g.sy_r
    g.nm_enum_name = g.sm_n
    g.nm_enum_first = g.sy_n + 1
    g.nm_enum_outer_scope = g.nm_scope
    g.nm_scope = g.sy_r
    g.nm_enum_next = 0
    g.nm_enum_type = K_TY_BYTE
    g.nm_enum_start_line = g.lx_no
    g.nm_enum_start_text = g.lx_l
    uxc_lex.lx_next()


def nm_enum_scanned():
    """NM.ENUM.SCANNED. Record g.sy_r has the ENUM's name: the first pass's record of this
    ENUM, which the second pass now meets, or a duplicate."""
    uxc_sym.sy_get()
    if g.sy_kind != K_SK_ENUM or (g.sy_flags & K_SY_SCANNED) == 0:
        nm_error_duplicate()
    g.sy_flags = g.sy_flags - K_SY_SCANNED
    uxc_sym.sy_set()


def nm_enum_members():
    """NM.ENUM.MEMBERS. Members with a comma between them, or END ENUM. A member is NAME or
    NAME = value, and each member after it counts on by 1."""
    g.ex_vn = 0
    g.ex_sd = 0
    g.ex_op_base = 0
    g.sg_n = 0
    g.sg_pointers = 0
    if g.tk_t == K_TT_EOL:
        return
    if g.tk_t != K_TT_NAME:
        er_syntax()
    if g.tk_s == "ENDENUM":
        nm_enum_end()
        return
    if g.tk_s == "END":
        uxc_lex.lx_next()
        if g.tk_t != K_TT_NAME or g.tk_s != "ENUM":
            er_syntax()
        nm_enum_end()
        return
    while True:
        if g.tk_t != K_TT_NAME or g.tk_m != 0:
            er_syntax()
        g.sm_n = g.tk_s
        nm_reserved()
        g.sy_name = g.sm_n
        g.sy_ow = g.nm_enum_record
        uxc_sym.sy_find()
        if g.sy_r != 0:
            nm_error_duplicate()
        g.nm_enum_member_name = g.sm_n
        uxc_lex.lx_next()
        if g.tk_t == K_TT_OP and g.tk_k == 61:
            nm_enum_value()
        if g.nm_enum_next > 65535:
            er_stop("TOO BIG FOR A WORD: " + g.nm_enum_member_name)
        if g.nm_enum_next > 255:
            g.nm_enum_type = K_TY_WORD
        g.sy_name = g.nm_enum_member_name
        g.sy_ow = g.nm_enum_record
        g.sy_kind = K_SK_CONST
        g.sy_type = K_TY_BYTE
        g.sy_val = g.nm_enum_next
        g.sy_flags = 0
        g.sy_cnt = 0
        uxc_sym.sy_add()
        g.nm_enum_next = g.nm_enum_next + 1
        if g.tk_t != K_TT_OP or g.tk_k != 44:
            return
        uxc_lex.lx_next()


def nm_enum_value():
    uxc_lex.lx_next()
    uxc_expr.ex_expr()
    g.ex_i = g.ex_vn - 1
    if g.ex_vk[g.ex_i] != K_EK_CONST:
        er_stop("VALUE NOT A CONSTANT")
    uxc_fold.ex_const_word()
    g.nm_enum_next = g.ex_vv[g.ex_i]
    g.ex_vn = g.ex_vn - 1


def nm_enum_end():
    """NM.ENUM.END. The members are the records from g.nm_enum_first up to g.sy_n. When one
    passes 255, the ENUM and every member become WORD. The first pass gave the parameters
    of its type a BYTE, so then such a parameter stops the compile."""
    g.nm_scope = g.nm_enum_outer_scope
    uxc_lex.lx_next()
    if g.nm_enum_type != K_TY_BYTE:
        g.sy_r = g.nm_enum_record
        uxc_sym.sy_get()
        if (g.sy_flags & K_SY_ENUM_PARAMETER) != 0:
            er_stop("TOO BIG FOR A PARAMETER: " + g.nm_enum_name)
        g.sy_type = K_TY_WORD
        uxc_sym.sy_set()
        for g.nm_enum_member_record in range(g.nm_enum_first, g.sy_n + 1):
            g.sy_r = g.nm_enum_member_record
            uxc_sym.sy_get()
            g.sy_type = K_TY_WORD
            uxc_sym.sy_set()
    g.nm_enum_record = 0


# Errors

def nm_error_qualified():
    er_stop("NOT A SIMPLE NAME: " + g.sm_n)


def nm_error_reserved():
    er_stop("RESERVED NAME " + g.sm_n)


def nm_error_duplicate():
    er_stop("DUPLICATE NAME " + g.sm_n)


def nm_error_end_enum():
    er_stop("END ENUM WITHOUT ENUM")


def nm_error_body():
    er_stop("NOT ALLOWED IN A NAMESPACE")


def nm_open():
    """NM.OPEN. At the end of the source, the error is at the line of the open ENUM, else of
    the outermost NAMESPACE."""
    if g.nm_enum_record != 0:
        g.lx_no = g.nm_enum_start_line
        g.lx_l = g.nm_enum_start_text
        er_stop("ENUM WITHOUT END ENUM")
    if g.nm_current == 0:
        return
    g.lx_no = g.nm_line
    g.lx_l = g.nm_text
    er_stop("NAMESPACE WITHOUT END NAMESPACE")
