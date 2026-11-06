"""A window that runs tools/build.py and tools/tests.py.

The build tab lists the programs of `build.py --list` in a tree, one branch a group. Full build
runs build.py with the --release, --card and --force switches ticked. Build selected runs
`build.py --only` on the selected programs, and a selected group stands for each of its
programs; ROM programs are left out, since only a full build makes them. The tree is read again
after each run.

The tests tab lists the tests of `tests.py --list`, one branch a group, stopped tests grey. Run
test runs tests.py on the one test selected, with --host when ticked; an msbasic test runs with
--msbasic.

Each run's output goes to the log pane under the tabs, with the exit code and the time. Stop
kills the run's process tree by its PID; Clear log empties the pane.

Each run's time is its baseline, kept in BASELINES under the script and its switches, or "test"
for a test. A run past SLOW_FACTOR times its baseline plus SLOW_MARGIN seconds logs one warning.
A full build without Force takes the larger of its own baseline and the Force build's with the
same switches, as it compiles at most what Force compiles. A stopped run keeps the old baseline.

The window runs the repo's Python on build.py and tests.py as subprocesses. Run from the
source, ROOT is two folders up and the Python is the one running this file. Frozen, ROOT is the
folder of the exe and the Python is PYTHON.
"""

import json
import os
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk

if getattr(sys, "frozen", False):
    ROOT = os.path.dirname(sys.executable)
    PYTHON = r"C:\Users\Admin\AppData\Local\Programs\Python\Python313\python.exe"
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    PYTHON = sys.executable
BUILD = os.path.join(ROOT, "tools", "build.py")
TESTS = os.path.join(ROOT, "tools", "tests.py")
BASELINES = os.path.join(ROOT, "build", "gui-baselines.json")
SLOW_FACTOR = 2
SLOW_MARGIN = 5
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class BuildWindow:
    def __init__(self, root):
        self.root = root
        self.lines = queue.Queue()
        self.running = False
        self.baselines = self.load_baselines()
        self.limit = None
        root.title("6502DOS build")
        root.geometry("900x640")

        panes = ttk.PanedWindow(root, orient="vertical")
        panes.pack(fill="both", expand=True, padx=6, pady=(6, 0))
        tabs = ttk.Notebook(panes)
        panes.add(tabs, weight=3)

        build_tab = ttk.Frame(tabs, padding=6)
        tabs.add(build_tab, text="Build")
        buttons = ttk.Frame(build_tab)
        buttons.pack(fill="x")
        self.full_button = ttk.Button(buttons, text="Full build", command=self.full_build)
        self.full_button.pack(side="left")
        self.release = tk.BooleanVar()
        self.card = tk.BooleanVar()
        ttk.Checkbutton(buttons, text="--release", variable=self.release).pack(side="left", padx=4)
        ttk.Checkbutton(buttons, text="--card", variable=self.card).pack(side="left", padx=4)
        self.force = tk.BooleanVar()
        ttk.Checkbutton(buttons, text="--force", variable=self.force).pack(side="left", padx=4)
        self.only_button = ttk.Button(buttons, text="Build selected", command=self.build_selected)
        self.only_button.pack(side="left", padx=12)
        self.refresh_button = ttk.Button(buttons, text="Refresh", command=self.refresh)
        self.refresh_button.pack(side="left")
        tree_frame = ttk.Frame(build_tab)
        tree_frame.pack(fill="both", expand=True, pady=(6, 0))
        self.tree = ttk.Treeview(tree_frame, columns=("state", "source"), selectmode="extended")
        self.tree.heading("#0", text="Program")
        self.tree.heading("state", text="State")
        self.tree.heading("source", text="Source")
        self.tree.column("#0", width=180)
        self.tree.column("state", width=70, anchor="center")
        self.tree.column("source", width=560)
        self.tree.tag_configure("stale", foreground="#b05000")
        self.tree.tag_configure("rom", foreground="#808080")
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        tests_tab = ttk.Frame(tabs, padding=6)
        tabs.add(tests_tab, text="Tests")
        test_buttons = ttk.Frame(tests_tab)
        test_buttons.pack(fill="x")
        self.test_button = ttk.Button(test_buttons, text="Run test", command=self.run_test)
        self.test_button.pack(side="left")
        self.host = tk.BooleanVar()
        ttk.Checkbutton(test_buttons, text="--host", variable=self.host).pack(side="left", padx=4)
        tests_frame = ttk.Frame(tests_tab)
        tests_frame.pack(fill="both", expand=True, pady=(6, 0))
        self.tests = ttk.Treeview(tests_frame, columns=("state",), selectmode="browse")
        self.tests.heading("#0", text="Test")
        self.tests.heading("state", text="State")
        self.tests.column("#0", width=180)
        self.tests.column("state", width=70, anchor="center")
        self.tests.tag_configure("stopped", foreground="#808080")
        tests_scroll = ttk.Scrollbar(tests_frame, orient="vertical", command=self.tests.yview)
        self.tests.configure(yscrollcommand=tests_scroll.set)
        self.tests.pack(side="left", fill="both", expand=True)
        tests_scroll.pack(side="right", fill="y")

        log_pane = ttk.Frame(panes)
        log_buttons = ttk.Frame(log_pane)
        log_buttons.pack(fill="x", pady=(4, 2))
        self.stop_button = ttk.Button(log_buttons, text="Stop", command=self.stop, state="disabled")
        self.stop_button.pack(side="left")
        ttk.Button(log_buttons, text="Clear log", command=self.clear).pack(side="left", padx=4)
        log_frame = ttk.Frame(log_pane)
        log_frame.pack(fill="both", expand=True)
        self.log = tk.Text(log_frame, height=12, wrap="none", font=("Consolas", 9), state="disabled")
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=log_scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")
        panes.add(log_pane, weight=2)

        self.status = ttk.Label(root, text="", anchor="w", padding=(6, 2))
        self.status.pack(fill="x")

        self.buttons = (self.full_button, self.only_button, self.refresh_button, self.test_button)
        self.refresh()
        self.list_tests()
        root.after(50, self.drain)

    def write(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.configure(state="disabled")

    def clear(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def drain(self):
        """Move queued output to the log pane; a None ends a run. Warn once on a run past its limit."""
        try:
            while True:
                item = self.lines.get_nowait()
                if item is None:
                    self.finish()
                else:
                    self.write(item)
        except queue.Empty:
            pass
        if self.running and self.limit and not self.warned and time.time() - self.started > self.limit:
            self.warned = True
            self.write("past baseline %.2f s; Stop kills it\n" % self.baseline)
            self.status.configure(text="past baseline")
        self.root.after(50, self.drain)

    def refresh(self):
        """Fill the tree from `build.py --list`, keeping the open groups and the selection."""
        opened = {item for item in self.tree.get_children() if self.tree.item(item, "open")}
        selected = set(self.tree.selection())
        result = subprocess.run([PYTHON, BUILD, "--list"], cwd=ROOT, capture_output=True,
                                text=True, creationflags=NO_WINDOW)
        if result.returncode != 0:
            self.write(result.stdout + result.stderr)
            return
        self.tree.delete(*self.tree.get_children())
        stale = 0
        for line in result.stdout.splitlines():
            group, name, state, source, program = line.split("\t")
            if not self.tree.exists(group):
                self.tree.insert("", "end", iid=group, text=group, open=group in opened)
            self.tree.insert(group, "end", iid=name, text=name, values=(state, source), tags=(state,))
            stale += state == "stale"
        for item in selected:
            if self.tree.exists(item):
                self.tree.selection_add(item)
        self.status.configure(text="%d stale" % stale)

    def list_tests(self):
        """Fill the tests tree from `tests.py --list`. An item's id is group/name."""
        result = subprocess.run([PYTHON, TESTS, "--list"], cwd=ROOT, capture_output=True,
                                text=True, creationflags=NO_WINDOW)
        if result.returncode != 0:
            self.write(result.stdout + result.stderr)
            return
        for line in result.stdout.splitlines():
            group, name, state = line.split("\t")
            if not self.tests.exists(group):
                self.tests.insert("", "end", iid=group, text=group)
            self.tests.insert(group, "end", iid=group + "/" + name, text=name, values=(state,),
                              tags=(state,))

    def selected_names(self):
        """The programs selected, a group standing for each of its programs, ROM programs left out."""
        names = []
        for item in self.tree.selection():
            children = self.tree.get_children(item) or (item,)
            for child in children:
                if self.tree.item(child, "values")[0] != "rom" and child not in names:
                    names.append(child)
        return names

    def full_build(self):
        arguments = []
        if self.release.get():
            arguments.append("--release")
        if self.card.get():
            arguments.append("--card")
        if self.force.get():
            arguments.append("--force")
        self.start(BUILD, arguments)

    def build_selected(self):
        names = self.selected_names()
        if not names:
            self.write("nothing selected to build; ROM programs need a full build\n")
            return
        self.start(BUILD, ["--only"] + names)

    def run_test(self):
        selected = self.tests.selection()
        if not selected or "/" not in selected[0]:
            self.write("select one test\n")
            return
        group, name = selected[0].split("/")
        if group == "msbasic":
            arguments = ["--msbasic", name]
        else:
            arguments = [name] + (["--host"] if self.host.get() else [])
        self.start(TESTS, arguments, "test")

    def start(self, script, arguments, key=None):
        """Run the Python script with arguments in a thread, its output to the log pane.

        key names the run's baseline in BASELINES; it defaults to the script and its switches.
        """
        if self.running:
            return
        self.running = True
        for button in self.buttons:
            button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        if key is None:
            switches = [argument for argument in arguments if argument.startswith("--")]
            key = " ".join([os.path.basename(script)] + sorted(switches))
        self.key = key
        baseline = self.baselines.get(key)
        if script == BUILD and "--force" not in arguments and "--only" not in arguments:
            forced = " ".join(sorted(key.split()[1:] + ["--force"]))
            forced = os.path.basename(script) + " " + forced
            baseline = max(baseline or 0, self.baselines.get(forced) or 0) or None
        self.baseline = baseline
        self.limit = baseline * SLOW_FACTOR + SLOW_MARGIN if baseline else None
        self.warned = False
        self.stopped = False
        command = [PYTHON, "-u", script] + arguments
        self.write("> %s %s\n" % (os.path.basename(script), " ".join(arguments)))
        self.started = time.time()
        self.process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, text=True,
                                        creationflags=NO_WINDOW)
        threading.Thread(target=self.run, args=(self.process,), daemon=True).start()

    def run(self, process):
        for line in process.stdout:
            self.lines.put(line)
        self.code = process.wait()
        self.lines.put(None)

    def stop(self):
        """Kill the run's process tree by its PID, the emulator a test started with it."""
        if not self.running or self.stopped:
            return
        self.stopped = True
        subprocess.run(["taskkill", "/PID", str(self.process.pid), "/T", "/F"],
                       capture_output=True, creationflags=NO_WINDOW)

    def finish(self):
        took = time.time() - self.started
        if self.stopped:
            self.write("stopped, %.2f s\n\n" % took)
        else:
            self.write("exit %d, %.2f s\n\n" % (self.code, took))
            self.baselines[self.key] = round(took, 2)
            self.save_baselines()
        self.running = False
        for button in self.buttons:
            button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.refresh()

    def load_baselines(self):
        try:
            with open(BASELINES, encoding="utf-8") as file:
                return json.load(file)
        except (OSError, ValueError):
            return {}

    def save_baselines(self):
        os.makedirs(os.path.dirname(BASELINES), exist_ok=True)
        with open(BASELINES, "w", encoding="utf-8") as file:
            json.dump(self.baselines, file, indent=1, sort_keys=True)


def main():
    root = tk.Tk()
    BuildWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
