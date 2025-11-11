import os
import sys
import glob
import threading
import subprocess
import time
import queue
import tkinter as tk
from tkinter import ttk

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LSG_DIR = os.path.join(ROOT, "lsg")

pyexe = sys.executable


class RunLsgGui:
    def __init__(self, master):
        self.master = master
        master.title("run_lsg_tests GUI")
        master.geometry("900x600")

        self.files = sorted(glob.glob(os.path.join(LSG_DIR, "lsg*.py")))
        if not self.files:
            tk.messagebox.showerror("Fehler", "Keine lsg/*.py Dateien gefunden.")
            master.destroy()
            return

        self.selected = {}
        self.check_vars = {}

        # Top frame: file list and controls
        top = ttk.Frame(master)
        top.pack(side=tk.TOP, fill=tk.BOTH, expand=False, padx=6, pady=6)

        left = ttk.Frame(top)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollable checkbox list
        canvas = tk.Canvas(left)
        scrollbar = ttk.Scrollbar(left, orient="vertical", command=canvas.yview)
        self.list_frame = ttk.Frame(canvas)

        self.list_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.list_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Populate checkboxes
        for path in self.files:
            name = os.path.basename(path)
            var = tk.BooleanVar(value=True)
            cb = ttk.Checkbutton(self.list_frame, text=name, variable=var)
            cb.pack(anchor='w', padx=4, pady=2)
            self.check_vars[name] = var

        # Right controls
        right = ttk.Frame(top)
        right.pack(side=tk.RIGHT, fill=tk.Y, expand=False, padx=6)

        ttk.Label(right, text="Delay (ms, -1 to keep scripts'):").pack(anchor='w', pady=(4,2))
        self.delay_var = tk.StringVar(value=os.getenv("RUN_LSG_DELAY_MS", "0"))
        self.delay_entry = ttk.Entry(right, textvariable=self.delay_var, width=12)
        self.delay_entry.pack(anchor='w')

        btn_frame = ttk.Frame(right)
        btn_frame.pack(anchor='w', pady=8)

        self.all_btn = ttk.Button(btn_frame, text="Alle", command=self.select_all)
        self.all_btn.pack(side=tk.LEFT, padx=2)
        self.none_btn = ttk.Button(btn_frame, text="Keine", command=self.select_none)
        self.none_btn.pack(side=tk.LEFT, padx=2)

        self.run_btn = ttk.Button(right, text="Run", command=self.start_run)
        self.run_btn.pack(fill=tk.X, pady=(10,2))

        self.stop_btn = ttk.Button(right, text="Stop", command=self.stop_run, state=tk.DISABLED)
        self.stop_btn.pack(fill=tk.X, pady=2)

        # Text output
        out_frame = ttk.Frame(master)
        out_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=6, pady=(0,6))
        self.text = tk.Text(out_frame, wrap='none')
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        out_scroll = ttk.Scrollbar(out_frame, orient='vertical', command=self.text.yview)
        out_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.configure(yscrollcommand=out_scroll.set)

        # Queue and threading
        self.queue = queue.Queue()
        self.worker_thread = None
        self._stop_event = threading.Event()

        # Poll queue periodically
        self.master.after(100, self._poll_queue)

    def select_all(self):
        for v in self.check_vars.values():
            v.set(True)

    def select_none(self):
        for v in self.check_vars.values():
            v.set(False)

    def start_run(self):
        selected_files = [os.path.join(LSG_DIR, n) for n, v in self.check_vars.items() if v.get()]
        if not selected_files:
            self._append_text("Keine Dateien ausgewählt.\n")
            return

        # parse delay
        try:
            delay = int(self.delay_var.get())
        except Exception:
            self._append_text("Ungültiger Delay-Wert, bitte Ganzzahl eingeben.\n")
            return

        # disable UI controls while running
        self.run_btn.config(state=tk.DISABLED)
        self.all_btn.config(state=tk.DISABLED)
        self.none_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        for cb in self.list_frame.winfo_children():
            cb.config(state=tk.DISABLED)
        self._stop_event.clear()

        # start background thread
        self.worker_thread = threading.Thread(target=self._run_worker, args=(selected_files, delay), daemon=True)
        self.worker_thread.start()

    def stop_run(self):
        # signal worker to stop; it will attempt to terminate current subprocess
        self._stop_event.set()
        self._append_text("Stop requested. Trying to terminate running tests...\n")

    def _run_worker(self, files, delay_ms):
        results = []
        for path in files:
            if self._stop_event.is_set():
                break
            name = os.path.basename(path)
            self.queue.put(f"\n=== Running {name} ===\n")
            env = os.environ.copy()
            env["OOP_TEST"] = "1"
            env["PYTHONPATH"] = ROOT
            env["RUN_LSG_DELAY_MS"] = str(delay_ms)

            proc = subprocess.Popen(
                [pyexe, path], cwd=ROOT,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                env=env, text=True, bufsize=1
            )

            # store proc so stop can kill it
            self._current_proc = proc

            try:
                with proc.stdout:
                    for line in proc.stdout:
                        # forward line to main thread
                        self.queue.put(line)
                        if self._stop_event.is_set():
                            try:
                                proc.kill()
                            except Exception:
                                pass
                            break
                proc.wait()
            except Exception as e:
                self.queue.put(f"[runner] Exception: {e}\n")
                try:
                    proc.kill()
                except Exception:
                    pass

            rc = proc.returncode if proc else -1
            ok = (rc == 0)
            results.append((name, ok, rc))
            self.queue.put(f"=> {'OK' if ok else f'FAIL (code {rc})'}\n")

        # summary
        self.queue.put("\n--- summary ---\n")
        for name, ok, code in results:
            status = "OK" if ok else f"FAIL ({code})"
            self.queue.put(f"{name}: {status}\n")

        self.queue.put("\n[run finished]\n")
        # re-enable UI by posting a special token
        self.queue.put("__RUN_FINISHED__")

    def _append_text(self, txt):
        self.text.insert(tk.END, txt)
        self.text.see(tk.END)

    def _poll_queue(self):
        try:
            while True:
                item = self.queue.get_nowait()
                if item == "__RUN_FINISHED__":
                    self._on_run_finished()
                    continue
                self._append_text(item)
        except queue.Empty:
            pass
        # keep polling
        self.master.after(100, self._poll_queue)

    def _on_run_finished(self):
        self.run_btn.config(state=tk.NORMAL)
        self.all_btn.config(state=tk.NORMAL)
        self.none_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        for cb in self.list_frame.winfo_children():
            cb.config(state=tk.NORMAL)
        self._current_proc = None


if __name__ == '__main__':
    root = tk.Tk()
    app = RunLsgGui(root)
    root.mainloop()
