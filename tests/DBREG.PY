"""DBREG's card: DBDOT's."""
import os
import runpy

card = runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "DBDOT.PY"))["card"]
