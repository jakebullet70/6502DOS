"""pyuxc -- the UXCBASIC compiler in Python, a port of the GPC UXC in attic/gpc/src/.

    python pyuxc/pyuxc.py FILE.UXB [-I FOLDER]... [-o FOLDER] [--result FILE] [--keep-subs]
                          [--keep-vars]

FILE.UXB compiles to NAME.PRG, NAME the source's name in capitals, in the -o folder (default:
the source's folder). #INCLUDE looks in the source's folder, then in each -I folder in order.
The program calls the UXDOS16 API, with the template table tpl/UXDOS/UXC.TPL.BIN.
The compiler's screen output is printed, then the result line:

    OK,<prg>,<bytes>[,REMOVED <n> SUBS <m> BYTES][,REMOVED <n> VARS <m> BYTES]
                    [,REMOVED <n> STRINGS <m> BYTES]
    ERROR,<line>,<message>

The SUBs and FUNCTIONs that the main program never reaches are left out of the PRG; the result
line then counts them and the bytes saved. --keep-subs keeps them all, as #KEEP ALL does.
The global variables and arrays that no code left in names get no room; the result line then
counts them and the bytes of the variables and the array space saved. The string literals
that no code left in names are left out too; the result line counts them and their bytes.
--keep-vars keeps the variables and the literals.

--result writes the result line to FILE as well. Exit status 0 when the compile succeeded,
1 on a compile error, 2 when the compile reached a part not ported yet.
"""

import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import uxc_lex  # noqa: E402
import uxc_once  # noqa: E402
import uxc_stmt  # noqa: E402
import uxc_tpl  # noqa: E402
from uxc_state import NotPorted, Stop, g, new  # noqa: E402


def object_name(source):
    """UI.OBJ$: the PRG is named after the source. HELLO.UXB writes HELLO.PRG."""
    name = os.path.basename(source).upper()
    dot = name.rfind(".")
    if dot > 0:
        name = name[:dot]
    return name + ".PRG"


# The template table folder of each target. The stock ROM is not supported: only
# attic/gpc/pyuxc/compare.py compiles for stock, to match the GPC UXC's output byte for byte.
TARGETS = {"uxdos16": os.path.join(uxc_tpl.DIR, "UXDOS"), "stock": uxc_tpl.DIR}


def compile_file(source, include_folders=(), out_folder=None, target="uxdos16",
                 keep_subs=False, keep_vars=False):
    """Compile source for target, a key of TARGETS. keep_subs keeps the SUBs nothing calls,
    keep_vars the variables nothing names. Return (result line, screen lines). NotPorted
    passes through."""
    new()
    g.target = target
    g.dd_keep_subs = 1 if keep_subs else 0
    g.dv_keep_vars = 1 if keep_vars else 0
    g.ui_src = os.path.basename(source).upper()
    g.ui_obj = object_name(source)
    g.source_folder = os.path.dirname(os.path.abspath(source))
    g.include_folders = list(include_folders)
    g.out_folder = out_folder or g.source_folder
    try:
        uxc_once.start(TARGETS[target])
        while True:
            uxc_lex.lx_read()
            if g.lx_got == 0:
                break
            uxc_stmt.sm_line()
        uxc_once.finish()
    except Stop:
        uxc_once.er_report()
    return g.ui_line, g.screen


def main():
    args = sys.argv[1:]
    includes, out_folder, result_file, sources = [], None, None, []
    keep_subs = False
    keep_vars = False
    while args:
        arg = args.pop(0)
        if arg in ("-I", "-o", "--result") and args:
            value = args.pop(0)
            if arg == "-I":
                includes.append(value)
            elif arg == "-o":
                out_folder = value
            else:
                result_file = value
        elif arg == "--keep-subs":
            keep_subs = True
        elif arg == "--keep-vars":
            keep_vars = True
        elif arg.startswith("-"):
            sys.exit(__doc__)
        else:
            sources.append(arg)
    if len(sources) != 1:
        sys.exit(__doc__)
    try:
        result, screen = compile_file(sources[0], includes, out_folder, keep_subs=keep_subs,
                                      keep_vars=keep_vars)
    except NotPorted as missing:
        print("\n".join(g.screen))
        print("pyuxc: %s is not ported yet" % missing)
        sys.exit(2)
    print("\n".join(screen))
    print(result)
    if result_file:
        with open(result_file, "w", encoding="latin-1", newline="\n") as out:
            out.write(result + "\n")
    sys.exit(0 if result.startswith("OK,") else 1)


if __name__ == "__main__":
    main()
