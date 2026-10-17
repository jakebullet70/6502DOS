"""UXC-RECORD.BL: record types, TYPE ... END TYPE, and LEN of a TYPE name.

    rd_type()            TYPE name, with g.sm_w at TYPE, or a stray ENDTYPE
    rd_fields()          one line inside a TYPE
    rd_as_type()         the TYPE named by the token, after AS. Out: g.sm_ty, g.rd_as_record
                         and g.rd_as_size
    rd_dim()             DIM name[(n)] AS type [AT address], in g.sm_n g.sm_ty g.sm_cnt, with
                         the token after the type
    rd_member()          g.sy_* becomes the field g.nm_rest of the record variable in g.sy_*
    rd_index()           from ex_index: the field after an element, as the top entry
    rd_at_element()      from ex_at_name: @array, @array(i) or @array(i).field
    rd_let_element()     array(i).field = value or array(i) = record, with the token at the (
    rd_maxes()           at startup, the max of each string field of the record in g.sy_*, or
                         of every element of the array of records in g.sy_*
    rd_section()         out g.rd_sec, the section of the variable in g.sy_*
    rd_section_value()   the same, and stop when the variable is a record
    rd_section_counter() the same, and stop when the variable is no FOR counter
    rd_let()             record = record, with the token at the =
    rd_len()             LEN of a TYPE or a record, with the token at the (. Out: g.rd_len_found
    rd_open()            at the end of the source, an open TYPE is an error

A TYPE is a K_SK_TYPE record. Its type is K_TY_RECORD plus its number, and its value is its
size. Each field is a K_SK_FIELD record owned by its TYPE: its type is the field's type, its
value the field's offset, and its count a string field's max.

A record variable is a K_SK_VAR record of its TYPE's type, in the block space (K_SY_BLOCK)
or at a fixed address (K_SY_FIXED). Its TYPE's record is at K_SY_RECORD_TYPE. An array of
records is a K_SK_ARRAY record of its TYPE's type, with its TYPE's record at
K_SY_RECORD_TYPE.
"""

from uxc_code import emit
from uxc_defs import K_EK_ADDR, K_EK_CONST, K_EK_MEM, K_EK_REG, K_EO_PAR, K_FRAME_BASE, \
    K_RD_TYPES, K_SEC_BSS, K_SEC_CONST, K_SEC_VAR, K_SK_ARRAY, K_SK_FIELD, K_SK_TYPE, \
    K_SK_VAR, K_SY_BLOCK, K_SY_FIXED, K_SY_MEMBER, K_SY_RECORD_TYPE, K_SY_SIGNED, K_TOP, \
    K_TT_EOL, K_TT_NAME, K_TT_NUM, K_TT_OP, K_TY_BYTE, K_TY_LONG, K_TY_RECORD, K_TY_STR, \
    K_TY_WORD
import uxc_expr
import uxc_lex
import uxc_name
import uxc_stmt
import uxc_str
import uxc_sub
import uxc_sym
import uxc_tpl as T
from uxc_state import er_mismatch, er_stop, er_syntax, g


# TYPE ... END TYPE

def rd_type():
    """RD.TYPE. g.rd_type_record is the TYPE's record from here to its END TYPE, and sm_line
    sends each line to rd_fields."""
    if g.sm_w == "ENDTYPE":
        rd_error_end()
    if g.sb_current != 0:
        er_stop("TYPE IN A SUB")
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NAME or g.tk_m != 0:
        er_syntax()
    g.sm_n = g.tk_s
    uxc_name.nm_reserved()
    g.sy_name = g.sm_n
    g.sy_ow = g.nm_scope
    uxc_sym.sy_find()
    if g.sy_r != 0:
        rd_error_duplicate()
    if g.rd_type_count >= K_RD_TYPES:
        er_stop("TOO MANY TYPES")
    g.sy_kind = K_SK_TYPE
    g.sy_type = K_TY_RECORD + g.rd_type_count
    g.sy_val = 0
    g.sy_flags = 0
    g.sy_cnt = 0
    uxc_sym.sy_add()
    g.rd_type_count = g.rd_type_count + 1
    g.rd_type_record = g.sy_r
    g.rd_type_size = 0
    g.rd_type_start_line = g.lx_no
    g.rd_type_start_text = g.lx_l
    uxc_lex.lx_next()


def rd_fields():
    """RD.FIELDS. One field, name AS BYTE, name AS WORD or name AS STRING * n, or END TYPE."""
    if g.tk_t == K_TT_EOL:
        return
    if g.tk_t != K_TT_NAME:
        er_syntax()
    if g.tk_s == "ENDTYPE":
        rd_type_end()
        return
    if g.tk_s == "END":
        uxc_lex.lx_next()
        if g.tk_t != K_TT_NAME or g.tk_s != "TYPE":
            er_syntax()
        rd_type_end()
        return
    g.sm_n = g.tk_s
    if g.tk_m != 0:
        er_stop("A FIELD HAS NO MARK: " + g.sm_n)
    uxc_name.nm_reserved()
    g.sy_name = g.sm_n
    g.sy_ow = g.rd_type_record
    uxc_sym.sy_find()
    if g.sy_r != 0:
        rd_error_duplicate()
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NAME or g.tk_s != "AS":
        er_syntax()
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NAME:
        er_syntax()
    g.rd_field_type = 0
    g.rd_field_max = 0
    uxc_name.nm_type_name()
    if g.nm_type_code != K_TY_STR:
        g.rd_field_type = g.nm_type_code
    if g.nm_type_code == K_TY_STR:
        rd_string_size()
    if g.rd_field_type == 0:
        er_stop("NOT A FIELD TYPE: " + g.tk_s)
    g.ty_code = g.rd_field_type
    uxc_sym.ty_size()
    g.rd_field_size = g.ty_bytes
    if g.rd_field_type == K_TY_STR:
        g.rd_field_size = g.rd_field_max + 2
    if g.rd_type_size + g.rd_field_size > 255:
        er_stop("TYPE OVER 255 BYTES")
    g.sy_name = g.sm_n
    g.sy_ow = g.rd_type_record
    g.sy_kind = K_SK_FIELD
    g.sy_type = g.rd_field_type
    g.sy_val = g.rd_type_size
    g.sy_flags = g.nm_type_signed * K_SY_SIGNED
    g.sy_cnt = g.rd_field_max
    uxc_sym.sy_add()
    g.rd_type_size = g.rd_type_size + g.rd_field_size
    uxc_lex.lx_next()


def rd_string_size():
    """RD.STRING.SIZE. * n, with the token at STRING. It leaves the token at n."""
    uxc_lex.lx_next()
    if g.tk_t != K_TT_OP or g.tk_k != 42:
        er_stop("NO SIZE FOR " + g.sm_n)
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NUM:
        rd_error_size()
    if g.tk_v < 1 or g.tk_v > 255:
        rd_error_size()
    g.rd_field_type = K_TY_STR
    g.rd_field_max = g.tk_v


def rd_type_end():
    """RD.TYPE.END. The TYPE's value becomes its size."""
    if g.rd_type_size == 0:
        er_stop("TYPE WITH NO FIELDS")
    g.sy_r = g.rd_type_record
    uxc_sym.sy_get()
    g.sy_val = g.rd_type_size
    uxc_sym.sy_set()
    g.rd_type_record = 0
    uxc_lex.lx_next()


# Record variables

def rd_as_type():
    """RD.AS.TYPE. A name that is no TYPE is a syntax error."""
    g.rd_as_name = g.sm_n
    g.sm_n = g.tk_s
    g.nm_find_quiet = 1
    uxc_name.nm_find()
    g.nm_find_quiet = 0
    g.sm_n = g.rd_as_name
    if g.sy_r == 0:
        er_syntax()
    if g.sy_kind != K_SK_TYPE:
        er_syntax()
    g.sm_ty = g.sy_type
    g.rd_as_record = g.sy_r
    g.rd_as_size = g.sy_val


def rd_dim():
    """RD.DIM."""
    g.rd_dim_record = g.rd_as_record
    if g.tk_t == K_TT_NAME:
        uxc_name.nm_at()
    elif g.sm_cnt != 0:
        rd_dim_array()
    else:
        g.sy_name = g.sm_n
        g.sy_ow = g.nm_scope
        uxc_sym.sy_find()
        if g.sy_r != 0:
            rd_error_duplicate()
        g.sb_place_size = g.rd_as_size
        uxc_sub.sb_place_block()
        if g.bs_n > K_TOP:
            rd_error_too_big_space()
        g.sy_name = g.sm_n
        g.sy_ow = g.nm_scope
        g.sy_kind = K_SK_VAR
        g.sy_type = g.sm_ty
        g.sy_val = g.sb_place
        g.sy_flags = K_SY_BLOCK
        g.sy_cnt = 0
        uxc_sym.sy_add()
    g.sb_field = K_SY_RECORD_TYPE
    g.sb_word = g.rd_dim_record
    uxc_sub.sb_field_set()
    if g.sb_current == 0 or (g.sy_flags & K_SY_FIXED) != 0:
        return
    g.rd_maxes_local = 1
    rd_string_maxes()


def rd_dim_array():
    """RD.DIM.ARRAY. g.sm_cnt records in the block space, or in the frame of the SUB being
    compiled."""
    g.sy_name = g.sm_n
    g.sy_ow = g.nm_scope
    uxc_sym.sy_find()
    if g.sy_r != 0:
        rd_error_duplicate()
    g.sb_place_size = g.sm_cnt * g.rd_as_size
    uxc_sub.sb_place_block()
    if g.bs_n > K_TOP:
        rd_error_too_big_space()
    g.sy_name = g.sm_n
    g.sy_ow = g.nm_scope
    g.sy_kind = K_SK_ARRAY
    g.sy_type = g.sm_ty
    g.sy_val = g.sb_place
    g.sy_flags = 0
    g.sy_cnt = g.sm_cnt
    uxc_sym.sy_add()


def rd_member():
    """RD.MEMBER. With g.nm_find_quiet set, a name that is no field gives g.sy_r = 0."""
    g.rd_member_value = g.sy_val
    g.rd_member_flags = g.sy_flags + K_SY_MEMBER
    g.sb_field = K_SY_RECORD_TYPE
    uxc_sub.sb_field_get()
    g.sy_name = g.nm_rest
    g.sy_ow = g.sb_word
    uxc_sym.sy_find()
    if g.sy_r == 0 and g.nm_find_quiet != 0:
        return
    if g.sy_r == 0:
        rd_error_not_field()
    uxc_sym.sy_get()
    g.sy_kind = K_SK_VAR
    g.sy_val = g.rd_member_value + g.sy_val
    if g.sy_val > 65535:
        g.sy_val = g.sy_val - 65536
    g.sy_flags = g.rd_member_flags + (g.sy_flags & K_SY_SIGNED)


def rd_maxes():
    """RD.MAXES. A record of a SUB gets its maxes in rd_dim. Clobbers g.sy_*."""
    if (g.sy_flags & K_SY_FIXED) != 0:
        return
    if g.sy_val >= K_FRAME_BASE:
        return
    g.rd_maxes_local = 0
    rd_string_maxes()


def rd_string_maxes():
    """RD.STRING.MAXES. A field is after its TYPE in the table, with the TYPE as its owner.
    In a local record the length byte is set to 0 with the max; the array space is cleared at
    startup."""
    g.rd_maxes_value = g.sy_val
    g.rd_maxes_count = 0
    if g.sy_kind == K_SK_ARRAY:
        g.rd_maxes_count = g.sy_cnt
    rd_section()
    g.rd_maxes_section = g.rd_sec
    if g.rd_maxes_count > 0:
        g.rd_maxes_section = K_SEC_BSS
    g.sb_field = K_SY_RECORD_TYPE
    uxc_sub.sb_field_get()
    g.rd_maxes_type = g.sb_word
    g.rd_maxes_field = g.sb_word + 1
    g.sy_r = g.sb_word
    uxc_sym.sy_get()
    g.rd_maxes_size = g.sy_val
    # RD.STRING.MAXES.NEXT
    while g.rd_maxes_field <= g.sy_n:
        g.sy_r = g.rd_maxes_field
        uxc_sym.sy_get()
        if g.sy_kind != K_SK_FIELD or g.sy_owner != g.rd_maxes_type:
            return
        if g.sy_type == K_TY_STR:
            rd_string_max()
        g.rd_maxes_field = g.rd_maxes_field + 1


def rd_string_max():
    """RD.STRING.MAX. The max of the string field in g.sy_*. In an array, T_RMAX sets it in
    every element, with a 0 length."""
    g.rd_maxes_at = g.rd_maxes_value + g.sy_val
    if g.rd_maxes_at > 65535:
        g.rd_maxes_at = g.rd_maxes_at - 65536
    if g.rd_maxes_count > 0:
        g.sl_s[0] = g.rd_maxes_section
        g.sl_v[0] = g.rd_maxes_at
        g.sl_s[1] = K_SEC_CONST
        g.sl_v[1] = g.rd_maxes_size
        g.sl_s[2] = K_SEC_CONST
        g.sl_v[2] = g.rd_maxes_count
        g.sl_s[3] = K_SEC_CONST
        g.sl_v[3] = g.sy_cnt
        emit(T.T_RMAX)
        g.sg_loaded = 0
        return
    g.sl_s[0] = K_SEC_CONST
    g.sl_v[0] = g.sy_cnt
    if g.rd_maxes_local == 1:
        emit(T.T_LDW_C)
        g.sl_s[0] = g.rd_maxes_section
        g.sl_v[0] = g.rd_maxes_at
        emit(T.T_STW_V)
        return
    if g.sy_cnt != g.sg_loaded:
        emit(T.T_LDB_C)
    g.sg_loaded = g.sy_cnt
    g.sl_s[0] = g.rd_maxes_section
    g.sl_v[0] = g.rd_maxes_at
    emit(T.T_STB_V)


def rd_section():
    """RD.SECTION. K_SEC_VAR, K_SEC_BSS for a string block, K_SEC_CONST for a fixed address,
    K_SEC_BSS for a record in the block space."""
    g.rd_sec = K_SEC_VAR
    if g.sy_type == K_TY_STR and g.sy_cnt > 0:
        g.rd_sec = K_SEC_BSS
    if (g.sy_flags & K_SY_FIXED) != 0:
        g.rd_sec = K_SEC_CONST
    if (g.sy_flags & K_SY_BLOCK) != 0:
        g.rd_sec = K_SEC_BSS


def rd_section_value():
    if g.sy_type >= K_TY_RECORD:
        rd_error_not_value_record()
    rd_section()


def rd_section_counter():
    if g.sy_type == K_TY_STR:
        er_mismatch()
    if (g.sy_flags & K_SY_MEMBER) != 0:
        er_stop("A FIELD IS NO FOR COUNTER: " + g.sm_n)
    rd_section_value()


def rd_let():
    """RD.LET. record = record, with the record variable on the left in g.sy_*."""
    g.rd_let_type = g.sy_type
    rd_section()
    g.ex_k = K_EK_ADDR
    g.ex_s = g.rd_sec
    g.ex_v = g.sy_val
    g.ex_ty = K_TY_WORD
    uxc_expr.ex_pushv()
    g.sb_field = K_SY_RECORD_TYPE
    uxc_sub.sb_field_get()
    g.sy_r = g.sb_word
    uxc_sym.sy_get()
    g.rd_let_size = g.sy_val
    rd_let_source()


def rd_let_source():
    """RD.LET.SOURCE. The record after the =, of type g.rd_let_type and g.rd_let_size bytes.
    The destination's address is the top entry. A copy between two fixed addresses is
    T_RCOPY; any other is T_RCOPY_P."""
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NAME:
        er_mismatch()
    g.sm_n = g.tk_s
    uxc_name.nm_find()
    if g.sy_type != g.rd_let_type:
        er_mismatch()
    if g.sy_kind == K_SK_VAR:
        rd_section()
        g.ex_k = K_EK_ADDR
        g.ex_s = g.rd_sec
        g.ex_v = g.sy_val
        g.ex_ty = K_TY_WORD
        uxc_expr.ex_pushv()
        uxc_lex.lx_next()
    elif g.sy_kind == K_SK_ARRAY:
        g.rd_let_array = g.sy_r
        uxc_lex.lx_next()
        if g.tk_t != K_TT_OP or g.tk_k != 40:
            er_mismatch()
        uxc_lex.lx_next()
        uxc_expr.ex_expr()
        if g.tk_t != K_TT_OP or g.tk_k != 41:
            rd_error_missing_close()
        uxc_lex.lx_next()
        if g.tk_t == K_TT_OP and g.tk_k == 46:
            er_mismatch()
        g.sy_r = g.rd_let_array
        uxc_sym.sy_get()
        rd_array()
        g.rd_element_offset = 0
        rd_element()
    else:
        er_mismatch()
    g.rd_let_target = g.ex_vn - 2
    g.rd_let_from = g.ex_vn - 1
    if g.ex_vk[g.rd_let_target] == K_EK_ADDR and g.ex_vk[g.rd_let_from] == K_EK_ADDR:
        g.sl_s[0] = g.ex_vs[g.rd_let_target]
        g.sl_v[0] = g.ex_vv[g.rd_let_target]
        g.sl_s[1] = g.ex_vs[g.rd_let_from]
        g.sl_v[1] = g.ex_vv[g.rd_let_from]
        g.sl_s[2] = K_SEC_CONST
        g.sl_v[2] = g.rd_let_size
        emit(T.T_RCOPY)
    else:
        g.ex_fb = g.rd_let_from
        uxc_expr.ex_flush()
        g.ex_i = g.rd_let_from
        g.ex_wd = 1
        uxc_expr.ex_load()
        g.sl_s[0] = K_SEC_CONST
        g.sl_v[0] = g.rd_let_size
        emit(T.T_RCOPY_P)
        g.ex_sd = g.ex_sd - 1
    g.ex_vn = g.ex_vn - 2


# Arrays of records

def rd_array():
    """RD.ARRAY. The array of records in g.sy_*: g.rd_array_base, g.rd_array_count,
    g.rd_array_record (its TYPE's record) and g.rd_array_size. Clobbers g.sy_*."""
    g.rd_array_base = g.sy_val
    g.rd_array_count = g.sy_cnt
    g.sb_field = K_SY_RECORD_TYPE
    uxc_sub.sb_field_get()
    g.rd_array_record = g.sb_word
    g.sy_r = g.sb_word
    uxc_sym.sy_get()
    g.rd_array_size = g.sy_val


def rd_field_after():
    """RD.FIELD.AFTER. With the token after the ) of an element: g.rd_field_found = 1 when a
    .name follows, with the field of g.rd_array_record in g.sy_* and the token after the
    name."""
    g.rd_field_found = 0
    if g.tk_t != K_TT_OP or g.tk_k != 46:
        return
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NAME:
        er_syntax()
    g.sy_name = g.tk_s
    g.sy_ow = g.rd_array_record
    uxc_sym.sy_find()
    if g.sy_r == 0:
        g.sm_n = g.tk_s
        rd_error_not_field()
    uxc_sym.sy_get()
    g.rd_field_found = 1
    uxc_lex.lx_next()


def rd_element():
    """RD.ELEMENT. The address of the element of g.rd_array_* at the index in the top entry,
    plus g.rd_element_offset, becomes the top entry: K_EK_ADDR for a constant index, else
    K_EK_REG in A/Y."""
    g.ex_i = g.ex_vn - 1
    if g.ex_vt[g.ex_i] == K_TY_STR:
        er_mismatch()
    if g.ex_vk[g.ex_i] == K_EK_CONST:
        if g.ex_vv[g.ex_i] >= g.rd_array_count:
            er_stop("BAD SUBSCRIPT")
        g.ex_vk[g.ex_i] = K_EK_ADDR
        g.ex_vs[g.ex_i] = K_SEC_BSS
        g.ex_vv[g.ex_i] = g.rd_array_base + g.ex_vv[g.ex_i] * g.rd_array_size + \
            g.rd_element_offset
        g.ex_vt[g.ex_i] = K_TY_WORD
        g.ex_vg[g.ex_i] = 0
        return
    g.ex_fb = g.ex_i
    uxc_expr.ex_flush()
    g.ex_i = g.ex_vn - 1
    g.ex_wd = 1
    uxc_expr.ex_load()
    g.sl_s[0] = K_SEC_CONST
    g.sl_v[0] = 0
    if g.sm_errors_on == 1:
        g.sl_v[0] = g.rd_array_count
    g.sl_s[1] = K_SEC_CONST
    g.sl_v[1] = g.rd_array_size
    g.sl_s[2] = K_SEC_BSS
    g.sl_v[2] = g.rd_array_base + g.rd_element_offset
    emit(T.T_RELEM)
    g.ex_i = g.ex_vn - 1
    g.ex_vk[g.ex_i] = K_EK_REG
    g.ex_vt[g.ex_i] = K_TY_WORD
    g.ex_vg[g.ex_i] = 0


def rd_pointer():
    """RD.POINTER. A/Y is stored in the statement's next %E word. Out: g.sg_pointer.
    Clobbers g.sy_*."""
    g.sg_pointers = g.sg_pointers + 1
    g.sy_name = "%E" + uxc_str.basic_str(g.sg_pointers)
    uxc_str.sg_pointer_word()


def rd_index():
    """RD.INDEX."""
    rd_array()
    rd_field_after()
    if g.rd_field_found == 0:
        er_stop("A RECORD IS NOT A VALUE")
    g.rd_element_offset = g.sy_val
    g.rd_field_type = g.sy_type
    g.rd_field_signed = 0
    if (g.sy_flags & K_SY_SIGNED) != 0:
        g.rd_field_signed = 1
    rd_element()
    g.ex_i = g.ex_vn - 1
    if g.rd_field_type == K_TY_STR:
        rd_index_string()
        return
    if g.ex_vk[g.ex_i] == K_EK_ADDR:
        g.ex_vk[g.ex_i] = K_EK_MEM
    else:
        if g.rd_field_type == K_TY_BYTE:
            emit(T.T_PEEK)
        if g.rd_field_type == K_TY_WORD:
            emit(T.T_PEEKW)
        if g.rd_field_type == K_TY_LONG:
            emit(T.T_PEEKL)
    g.ex_vt[g.ex_i] = g.rd_field_type
    g.ex_vg[g.ex_i] = g.rd_field_signed


def rd_index_string():
    g.ex_vt[g.ex_i] = K_TY_STR
    if g.ex_vk[g.ex_i] == K_EK_ADDR:
        return
    rd_pointer()
    g.ex_i = g.ex_vn - 1
    g.ex_vk[g.ex_i] = K_EK_MEM
    g.ex_vs[g.ex_i] = K_SEC_VAR
    g.ex_vv[g.ex_i] = g.sg_pointer


def rd_at_element():
    """RD.AT.ELEMENT. The index is parsed nested, as a function's argument is. The array's
    record waits in g.ex_oa under a ( of its own, so an element inside the index cannot
    overwrite it."""
    uxc_lex.lx_next()
    if g.tk_t != K_TT_OP or g.tk_k != 40:
        g.ex_k = K_EK_ADDR
        g.ex_s = K_SEC_BSS
        g.ex_v = g.sy_val
        g.ex_ty = K_TY_WORD
        uxc_expr.ex_pushv()
        return
    uxc_sub.sb_nest()
    g.ex_o = K_EO_PAR
    uxc_expr.ex_pusho()
    g.ex_oa[g.ex_on - 1] = g.sy_r
    uxc_lex.lx_next()
    g.ex_op_base = g.ex_on
    g.ex_cm = 0
    uxc_expr.ex_expr()
    if g.tk_t != K_TT_OP or g.tk_k != 41:
        rd_error_missing_close()
    uxc_sub.sb_unnest()
    g.sy_r = g.ex_oa[g.ex_on]
    uxc_sym.sy_get()
    rd_array()
    uxc_lex.lx_next()
    g.rd_element_offset = 0
    rd_field_after()
    if g.rd_field_found == 1:
        g.rd_element_offset = g.sy_val
    rd_element()


def rd_let_element():
    """RD.LET.ELEMENT."""
    g.rd_let_array = g.sy_r
    g.rd_let_name = g.sm_n
    uxc_lex.lx_next()
    uxc_expr.ex_expr()
    if g.tk_t != K_TT_OP or g.tk_k != 41:
        rd_error_missing_close()
    uxc_lex.lx_next()
    g.sy_r = g.rd_let_array
    uxc_sym.sy_get()
    g.rd_let_type = g.sy_type
    rd_array()
    g.rd_let_size = g.rd_array_size
    g.rd_element_offset = 0
    rd_field_after()
    if g.tk_t != K_TT_OP or g.tk_k != 61:
        er_syntax()
    if g.rd_field_found == 0:
        rd_element()
        rd_let_source()
        return
    g.rd_element_offset = g.sy_val
    g.rd_field_type = g.sy_type
    g.rd_field_max = g.sy_cnt
    rd_element()
    g.ex_i = g.ex_vn - 1
    if g.rd_field_type == K_TY_STR:
        rd_let_string()
        return
    g.sm_ty = g.rd_field_type
    if g.ex_vk[g.ex_i] == K_EK_ADDR:
        g.sm_ad = g.ex_vv[g.ex_i]
        g.sm_sec = K_SEC_BSS
        g.ex_vn = g.ex_vn - 1
        uxc_lex.lx_next()
        uxc_expr.ex_expr()
        uxc_stmt.sm_store()
        return
    g.ex_vn = g.ex_vn - 1
    uxc_stmt.sm_store_through()


def rd_let_string():
    """RD.LET.STRING. g.sy_* becomes a string variable at the field, and sg_let stores into
    it: a block at a constant index, else a block through a %E word, as a STRING parameter's."""
    if g.ex_vk[g.ex_i] == K_EK_ADDR:
        g.sy_val = g.ex_vv[g.ex_i]
        g.sy_cnt = g.rd_field_max
    else:
        rd_pointer()
        g.sy_val = g.sg_pointer
        g.sy_cnt = 0
    g.ex_vn = g.ex_vn - 1
    g.sy_kind = K_SK_VAR
    g.sy_type = K_TY_STR
    g.sy_flags = 0
    g.sm_n = g.rd_let_name
    uxc_str.sg_let()


# LEN

def rd_len():
    """RD.LEN. LEN of a TYPE name or of a record variable is the TYPE's size, a constant. On
    g.rd_len_found = 1 the token is after the ). On 0 the argument is something else, and the
    token is back at the (."""
    g.rd_len_found = 0
    g.rd_len_position = g.lx_p
    uxc_lex.lx_next()
    if g.tk_t != K_TT_NAME:
        rd_len_other()
        return
    g.sm_n = g.tk_s
    g.nm_find_quiet = 1
    uxc_name.nm_find()
    g.nm_find_quiet = 0
    if g.sy_r == 0:
        rd_len_other()
        return
    g.rd_len_kind = g.sy_kind
    if g.sy_kind == K_SK_ARRAY and g.sy_type >= K_TY_RECORD:
        rd_skip_index()
        if g.rd_skipped == 0:
            rd_len_other()
            return
        g.rd_len_kind = K_SK_VAR
    if g.rd_len_kind == K_SK_VAR and g.sy_type >= K_TY_RECORD:
        g.sb_field = K_SY_RECORD_TYPE
        uxc_sub.sb_field_get()
        g.sy_r = g.sb_word
        uxc_sym.sy_get()
    if g.sy_kind != K_SK_TYPE:
        rd_len_other()
        return
    uxc_lex.lx_next()
    if g.tk_t != K_TT_OP or g.tk_k != 41:
        # RD.LEN.NOT.VALUE
        if g.rd_len_kind == K_SK_VAR:
            rd_error_not_value_record()
        er_stop("A TYPE IS NOT A VALUE: " + g.sm_n)
    g.ex_k = K_EK_CONST
    g.ex_s = K_SEC_CONST
    g.ex_v = g.sy_val
    g.ex_ty = 0
    uxc_expr.ex_pushv()
    uxc_lex.lx_next()
    g.rd_len_found = 1


def rd_len_other():
    g.lx_p = g.rd_len_position
    g.tk_t = K_TT_OP
    g.tk_k = 40


def rd_skip_index():
    """RD.SKIP.INDEX. With the token at the name of an array of records: the (index) after it
    is passed over, and no code is made for it. g.rd_skipped = 1 when a .field does not
    follow, with the token at the ) that closes the index."""
    g.rd_skipped = 0
    uxc_lex.lx_next()
    if g.tk_t != K_TT_OP or g.tk_k != 40:
        return
    g.rd_skip_depth = 1
    while g.rd_skip_depth > 0:
        # RD.SKIP.INDEX.NEXT
        uxc_lex.lx_next()
        if g.tk_t == K_TT_EOL:
            return
        if g.tk_t == K_TT_OP and g.tk_k == 40:
            g.rd_skip_depth = g.rd_skip_depth + 1
        if g.tk_t == K_TT_OP and g.tk_k == 41:
            g.rd_skip_depth = g.rd_skip_depth - 1
    g.rd_skip_position = g.lx_p
    uxc_lex.lx_next()
    if g.tk_t == K_TT_OP and g.tk_k == 46:
        return
    g.lx_p = g.rd_skip_position
    g.tk_t = K_TT_OP
    g.tk_k = 41
    g.rd_skipped = 1


def rd_open():
    """RD.OPEN. The error is at the line of the open TYPE."""
    if g.rd_type_record == 0:
        return
    g.lx_no = g.rd_type_start_line
    g.lx_l = g.rd_type_start_text
    er_stop("TYPE WITHOUT END TYPE")


# Errors

def rd_error_end():
    er_stop("END TYPE WITHOUT TYPE")


def rd_error_duplicate():
    er_stop("DUPLICATE NAME " + g.sm_n)


def rd_error_size():
    er_stop("BAD STRING SIZE")


def rd_error_not_value_record():
    er_stop("A RECORD IS NOT A VALUE: " + g.sm_n)


def rd_error_missing_close():
    er_stop("MISSING )")


def rd_error_too_big_space():
    er_stop("ARRAYS TOO BIG")


def rd_error_not_field():
    er_stop("NOT A FIELD: " + g.sm_n)
