"""The template record ids, read from tpl/UXC.TPL.IDS when pyuxc starts.

GPC UXC has them from UXC.TPL.BL, as T.STUB.ID. Here they are T_STUB, and TPL_COUNT is the
number of records:

    import uxc_tpl as T
    emit(T.T_STUB)

The ids belong to one build of the table: tp_load stops when UXC.TPL.BIN holds another count.
"""

import os

DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tpl")


def _read_ids():
    ids = {}
    with open(os.path.join(DIR, "UXC.TPL.IDS"), encoding="utf-8") as lines:
        for line in lines:
            name, _, rid = line.partition("=")
            ids[name.strip()] = int(rid)
    return ids


_IDS = _read_ids()
globals().update(_IDS)
TPL_COUNT = len(_IDS)
