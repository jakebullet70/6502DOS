# The GPC UXC

This folder holds the UXCBASIC compiler written in GPC BASIC, and its tools. It is frozen.
pyuxc in `UXCBASIC/pyuxc` replaces it. Nothing in the build or the tests uses this folder.

The files keep the layout of the old UXCBASIC folder, so their paths name that layout. They do
not run from here as they are.

| Path | What it is |
|---|---|
| `src/` | The GPC UXC (`UXC.BASL`, `UXC-*.BL`), the help viewer (`UXC.HELP.BASL`) and the editor (`UXCEDIT/`) |
| `tools/gpc/` | A pinned copy of GPC build 133, with its manual in `GPC-BASIC/` |
| `tools/prof/` | A sampling profiler of the GPC runtime |
| `build.py`, `BUILD.BAT` | The GPC build of UXC, UXC.HELP and UXCEDIT |
| `uxc.py`, `run.py`, `RUN*.BAT` | Compile and run on the stock ROM in the emulator |
| `pyuxc/golden.py`, `pyuxc/golden/` | The GPC UXC's output for the corpus, the reference pyuxc was ported against |
| `pyuxc/compare.py`, `pyuxc/cases/` | Compares pyuxc with `golden/` for the stock table; the hand-made cases |
| `pyuxc/README.md` | The port plan, its steps and the corpus |
| `disk/` | The user drive of the stock-ROM programs |
| `tpl/MKTPL.PY` | MKTPL with `--test`, which links and runs a test program from the stock table |
| `basl-author.md` | GPC semantics, the SHARED memory layout and the GPC build |
| `NOTES.md` | The working rules of the old UXCBASIC folder |

The GPC build scripts and the emulator came from `C:\dev\CmdrX16\dos_tools\x16-blitz-compiler`.
