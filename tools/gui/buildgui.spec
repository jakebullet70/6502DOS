# PyInstaller spec for BUILDGUI.EXE: one file, no console. MKGUI.BAT runs it and puts the exe
# in the repo root, where the exe takes its folder as ROOT.

analysis = Analysis([os.path.join(SPECPATH, "buildgui.py")])
archive = PYZ(analysis.pure)
exe = EXE(archive, analysis.scripts, analysis.binaries, analysis.datas, [],
          name="BUILDGUI", console=False, upx=False)
