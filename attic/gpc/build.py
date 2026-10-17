"""Build the UXCBASIC programs with GPC.

    python build.py [NAME ...]    NAME defaults to UXC
    python build.py UXC.HELP      the help viewer
    python build.py UXCEDIT       the editor
    python build.py ALL           all three, staged once

NAME's source is src/NAME.BASL, or src/NAME/NAME.BASL for a program in its own folder.

build/ is the emulator's drive. Each build empties it, then copies in the pinned GPC tools
(tools/gpc), every file in src/, the template table (rebuilt by tpl/MKTPL.PY into
UXC.TPL.BIN), the help content (rebuilt by help/MKHELP.PY into HELP-TXT/) and examples/ as
EXAMPLES/. BASLOAD cannot follow ../ in an #INCLUDE, so the source and the GPC-BASIC library
must sit side by side on one drive. The PRG, OVL, MAP and DEAD of a program not being built,
and the editor's SETTINGS.KVB, are kept.

src/UXCEDIT/ is copied flat into build/: its UXCEDIT* sources and its key table. Its bench/,
its scripts and its GPC-BASIC copy are left out; the editor uses tools/gpc/GPC-BASIC.

The tokenise and compile scripts come from the GPC repo (GPC_REPO). They boot that repo's
emulator. The #GPC OBJECT line in the source must name NAME.PRG.

disk/ is the user's drive. After the builds, the PRG and OVL of each program built are copied
there with its RUN_FILES. The RUNTIME files go to disk/GPC/. A .UXB sample in examples/ or
samples/ is copied only when disk/ has no file of that name. Nothing in disk/ is deleted.
"""

import os
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
GPC_REPO = os.environ.get("GPC_REPO", r"C:\dev\CmdrX16\dos_tools\x16-blitz-compiler")
GPC_SCRIPTS = os.path.join(GPC_REPO, "source", "gpc")
TOOLS = os.path.join(HERE, "tools", "gpc")
SRC = os.path.join(HERE, "src")
HELP = os.path.join(HERE, "help")
TPL = os.path.join(HERE, "tpl")
EXAMPLES = os.path.join(HERE, "examples")
SAMPLES = os.path.join(HERE, "samples")
DRIVE = os.path.join(HERE, "build")
USER_DISK = os.path.join(HERE, "disk")
PROGRAMS = ["UXC", "UXC.HELP", "UXCEDIT"]
OUTPUTS = [".PRG", ".OVL", ".MAP", ".DEAD"]
KEPT = ["SETTINGS.KVB"]
EDITOR = "UXCEDIT"
# The files and folders each program reads at run time, beside its PRG and OVL.
RUN_FILES = {"UXC": ["UXC.TPL.BIN"], "UXC.HELP": ["HELP-TXT", "EXAMPLES"], "UXCEDIT": ["UXCEDIT.KEYS.BIN"]}
RUNTIME = ["GPC.RT.133.BIN", "GPB.RT.133.BIN", "GP1.RT.133.BIN"]

# WARNING: past this many bytes of VARIABLES names in NAME.SRC.SYM, the compiler's GP.ASM
# {VAR} cache (application/source/compiler/symfile.asm in the GPC repo) overflows. It then
# reads the whole .SYM from disk for every {VAR}, and a compile takes minutes.
SYM_CACHE_BYTES = 32768


def source_path(name):
    """The source of program NAME, or None."""
    for path in (os.path.join(SRC, name + ".BASL"), os.path.join(SRC, name, name + ".BASL")):
        if os.path.exists(path):
            return path
    return None


def kept_files(names):
    """The bytes of each file in build/ that a build of NAMES keeps, by file name."""
    if not os.path.isdir(DRIVE):
        return {}
    keep = list(KEPT)
    for program in PROGRAMS:
        if program not in names:
            keep += [program + ext for ext in OUTPUTS]
    kept = {}
    for name in keep:
        path = os.path.join(DRIVE, name)
        if os.path.isfile(path):
            kept[name] = open(path, "rb").read()
    return kept


def stage(names):
    """Empty build/, then copy in the GPC tools, the sources, the templates, the help and the
    examples, and put back the files kept_files() keeps."""
    kept = kept_files(names)
    # Empty build/ but keep the folder: an emulator window open on it locks the folder itself.
    os.makedirs(DRIVE, exist_ok=True)
    for name in os.listdir(DRIVE):
        path = os.path.join(DRIVE, name)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    shutil.copytree(TOOLS, DRIVE, dirs_exist_ok=True)
    for name in os.listdir(SRC):
        path = os.path.join(SRC, name)
        if name == EDITOR:
            for part in os.listdir(path):
                if part.startswith(EDITOR) and os.path.isfile(os.path.join(path, part)):
                    shutil.copy2(os.path.join(path, part), DRIVE)
        elif os.path.isdir(path):
            shutil.copytree(path, os.path.join(DRIVE, name))
        else:
            shutil.copy2(path, DRIVE)
    # UXC reads UXC.TPL.BIN beside itself, and #INCLUDEs the record ids from UXC.TPL.BL.
    if subprocess.run([sys.executable, os.path.join(TPL, "MKTPL.PY")], stdout=subprocess.DEVNULL).returncode != 0:
        sys.exit("build: tpl/MKTPL.PY failed")
    shutil.copy2(os.path.join(TPL, "UXC.TPL.BIN"), DRIVE)
    shutil.copy2(os.path.join(TPL, "UXC.TPL.BL"), DRIVE)
    # UXC.HELP reads //HELP-TXT/: and //EXAMPLES/: beside itself.
    if subprocess.run([sys.executable, os.path.join(HELP, "MKHELP.PY")]).returncode != 0:
        sys.exit("build: help/MKHELP.PY failed")
    shutil.copytree(os.path.join(HELP, "HELP-TXT"), os.path.join(DRIVE, "HELP-TXT"))
    shutil.copytree(EXAMPLES, os.path.join(DRIVE, "EXAMPLES"))
    for name, data in kept.items():
        with open(os.path.join(DRIVE, name), "wb") as out:
            out.write(data)


def step(script, *args):
    """Run one GPC build script on build/, print how long it took, and stop on its failure."""
    started = time.time()
    result = subprocess.run([sys.executable, os.path.join(GPC_SCRIPTS, script), "--drive", DRIVE] + list(args))
    print("build: %s took %d s" % (script, time.time() - started))
    if result.returncode != 0:
        sys.exit("build: %s failed" % script)


def symbol_cache_bytes(name):
    """Bytes the {VAR} cache needs for NAME.SRC.SYM: each VARIABLES name and three."""
    with open(os.path.join(DRIVE, name + ".SRC.SYM"), "rb") as symbols:
        lines = symbols.read().replace(b"\r\n", b"\n").replace(b"\r", b"\n").split(b"\n")
    in_variables = False
    needed = 0
    for line in lines:
        if not line.startswith(b" "):
            in_variables = in_variables or line.startswith(b"VARIABLES")
            continue
        fields = line[1:].split(b" ", 1)
        if in_variables and len(fields) == 2:
            needed += len(fields[1].split(b" ")[0]) + 3
    return needed


def build(name):
    started = time.time()
    step("build_basl.py", name + ".BASL", name + ".SRC.PRG")
    needed = symbol_cache_bytes(name)
    if needed > SYM_CACHE_BYTES:
        print("build: WARNING %s needs %d of %d {VAR} cache bytes, so this compile will be slow"
              % (name, needed, SYM_CACHE_BYTES))
    step("compile_shared.py", name + ".SRC.PRG", name + ".PRG")
    print("build: %s.PRG %d bytes, %d s" % (
        name, os.path.getsize(os.path.join(DRIVE, name + ".PRG")), time.time() - started))


def copy_onto(path, folder):
    """Copy the file or folder PATH into FOLDER. A file of the same name is overwritten. A folder
    is merged: its files overwrite their namesakes, and other files in the target are kept."""
    target = os.path.join(folder, os.path.basename(path))
    if os.path.isdir(path):
        shutil.copytree(path, target, dirs_exist_ok=True)
    else:
        shutil.copy2(path, target)


def publish(names):
    """Copy onto disk/ the PRG and OVL of each program in NAMES with its RUN_FILES, the RUNTIME
    files into disk/GPC/, and each .UXB sample that disk/ lacks."""
    os.makedirs(os.path.join(USER_DISK, "GPC"), exist_ok=True)
    for runtime in RUNTIME:
        copy_onto(os.path.join(TOOLS, runtime), os.path.join(USER_DISK, "GPC"))
    for name in names:
        for part in [name + ".PRG", name + ".OVL"] + RUN_FILES[name]:
            if os.path.exists(os.path.join(DRIVE, part)):
                copy_onto(os.path.join(DRIVE, part), USER_DISK)
    for folder in (EXAMPLES, SAMPLES):
        for sample in sorted(os.listdir(folder)):
            if sample.upper().endswith(".UXB") and not os.path.exists(os.path.join(USER_DISK, sample)):
                copy_onto(os.path.join(folder, sample), USER_DISK)
    print("build: copied %s to disk/" % ", ".join(names))


def main():
    names = [a.upper() for a in sys.argv[1:]] or ["UXC"]
    if names == ["ALL"]:
        names = list(PROGRAMS)
    for name in names:
        if source_path(name) is None:
            sys.exit("build: no src/%s.BASL or src/%s/%s.BASL" % (name, name, name))
    started = time.time()
    stage(names)
    for name in names:
        build(name)
    publish(names)
    print("build: total %d s" % (time.time() - started))


main()
