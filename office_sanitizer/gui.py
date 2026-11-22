"""Offline Tkinter desktop interface. UI never executes Office files or VBA."""
from __future__ import annotations

import json
import queue
import threading
from pathlib import Path

from . import __version__
from .batch import choose_files, process_batch
from .updater import find_update, UpdateError


def main() -> None:
    # Tk imports are lazy so CLI and headless CI run without a display server.
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    class Window:
        def __init__(self):
            self.root = tk.Tk()
            self.root.title(f'Office Sanitizer {__version__} — Offline review')
            self.root.geometry('900x620')
            self.root.minsize(740, 520)
            self.queue: queue.Queue = queue.Queue()
            self.files: list[Path] = []
            self.results = []
            self.worker_running = False
            self.output = tk.StringVar(value=str(Path.home() / 'OfficeSanitizer-Review'))
            self.mode = tk.StringVar(value='audit')
            self.recursive = tk.BooleanVar(value=False)
            self.status = tk.StringVar(value='Ready: select documents or folders')
            main = ttk.Frame(self.root, padding=16)
            main.pack(fill='both', expand=True)
            ttk.Label(main, text='Office Sanitizer — Document Review', font=('TkDefaultFont', 16, 'bold')).pack(anchor='w')
            ttk.Label(main, text='Offline, metadata-only. No result authorizes disclosure of confidential or classified files.',
                      wraplength=810).pack(anchor='w', pady=(4, 14))
            controls = ttk.Frame(main)
            controls.pack(fill='x')
            ttk.Button(controls, text='Add files', command=self.add_files).pack(side='left', padx=(0, 6))
            ttk.Button(controls, text='Add folder', command=self.add_folder).pack(side='left', padx=6)
            ttk.Checkbutton(controls, text='Include subfolders', variable=self.recursive).pack(side='left', padx=8)
            ttk.Button(controls, text='Clear', command=self.clear).pack(side='right')
            ttk.Button(controls, text='Check updates', command=self.check_updates).pack(side='right', padx=7)
            ttk.Label(main, text='Selected files (local names shown only in this window)').pack(anchor='w', pady=(12, 4))
            self.file_list = tk.Listbox(main, height=8, exportselection=False)
            self.file_list.pack(fill='both', expand=True)
            modes = ttk.Frame(main)
            modes.pack(fill='x', pady=(12, 8))
            ttk.Radiobutton(modes, text='Audit only (no file changes)', variable=self.mode, value='audit').pack(side='left')
            ttk.Radiobutton(modes, text='Guarded metadata cleanup', variable=self.mode, value='guarded').pack(side='left', padx=24)
            out = ttk.Frame(main)
            out.pack(fill='x', pady=5)
            ttk.Label(out, text='Output directory:').pack(side='left')
            ttk.Entry(out, textvariable=self.output).pack(side='left', fill='x', expand=True, padx=8)
            ttk.Button(out, text='Browse', command=self.select_output).pack(side='right')
            row = ttk.Frame(main)
            row.pack(fill='x', pady=(12, 6))
            self.run_button = ttk.Button(row, text='Run locally', command=self.run)
            self.run_button.pack(side='left')
            self.save_button = ttk.Button(row, text='Save privacy-safe report', command=self.save_report,
                                          state='disabled')
            self.save_button.pack(side='left', padx=10)
            ttk.Label(row, textvariable=self.status).pack(side='right')
            ttk.Label(main, text='Results — file indexes only; review original documents manually').pack(anchor='w', pady=5)
            self.results_view = tk.Text(main, height=8, state='disabled', wrap='word')
            self.results_view.pack(fill='both', expand=True)
            self.root.after(100, self.poll)

        def add_files(self):
            selected = filedialog.askopenfilenames(title='Choose Office documents')
            self.files = sorted({*self.files, *choose_files(selected)}, key=str)
            self.refresh_files()

        def add_folder(self):
            folder = filedialog.askdirectory(title='Choose folder')
            if folder:
                self.files = sorted({*self.files, *choose_files([folder], recursive=self.recursive.get())}, key=str)
                self.refresh_files()

        def refresh_files(self):
            self.file_list.delete(0, 'end')
            for file in self.files:
                self.file_list.insert('end', file.name)
            self.status.set(f'{len(self.files)} selected')

        def clear(self):
            if self.worker_running:
                return
            self.files = []
            self.results = []
            self.refresh_files()
            self.save_button.configure(state='disabled')
            self.show_results('')

        def select_output(self):
            folder = filedialog.askdirectory(title='Destination for review copies')
            if folder:
                self.output.set(folder)

        def run(self):
            if self.worker_running or not self.files:
                return
            mode = self.mode.get()
            output = self.output.get()
            sources = tuple(self.files)
            self.results = []
            self.run_button.configure(state='disabled')
            self.save_button.configure(state='disabled')
            self.worker_running = True
            self.status.set('Processing offline…')

            def work():
                try:
                    results = process_batch(sources, mode=mode, output_dir=output)
                    self.queue.put(('done', [r.as_dict() for r in results]))
                except Exception:
                    # Do not display exception contents (they may contain sensitive paths).
                    self.queue.put(('error', 'Processing failed; review inputs locally'))
            threading.Thread(target=work, daemon=True).start()

        def poll(self):
            try:
                while True:
                    event, value = self.queue.get_nowait()
                    self.worker_running = False
                    self.run_button.configure(state='normal')
                    if event == 'done':
                        self.results = value
                        self.status.set(f'{len(value)} documents processed — human review required')
                        self.show_results('\n'.join(f"File #{x['index']}: {x['status']}" for x in value))
                        self.save_button.configure(state='normal')
                    elif event == 'update':
                        if value:
                            self.status.set(f"Update available: {value['tag']}")
                            if messagebox.askyesno('Update available',
                               f"A newer version ({value['tag']}) is available.\n\n"
                               'Install via authenticated APT? A terminal confirmation is required.'):
                                import shutil
                                import subprocess
                                if shutil.which('xfce4-terminal'):
                                    subprocess.Popen(['xfce4-terminal', '--hold', '-x',
                                                      'office-sanitizer-update', '--install'])
                                else:
                                    messagebox.showinfo('Install update',
                                        'Run office-sanitizer-update --install in a terminal.')
                        else:
                            self.status.set('No newer verified GitHub Release found')
                    elif event == 'update_error':
                        self.status.set('Unable to contact official GitHub Releases')
                    else:
                        self.status.set(value)
            except queue.Empty:
                pass
            self.root.after(100, self.poll)

        def show_results(self, text):
            self.results_view.configure(state='normal')
            self.results_view.delete('1.0', 'end')
            self.results_view.insert('1.0', text)
            self.results_view.configure(state='disabled')

        def check_updates(self):
            if self.worker_running:
                return
            self.status.set('Checking official GitHub Releases (no document content sent)…')
            def work():
                try:
                    candidate = find_update()
                    self.queue.put(('update', candidate))
                except UpdateError:
                    self.queue.put(('update_error', None))
            threading.Thread(target=work, daemon=True).start()

        def save_report(self):
            if not self.results:
                return
            path = filedialog.asksaveasfilename(defaultextension='.json',
                                                filetypes=[('JSON reports', '*.json')])
            if not path:
                return
            dest = Path(path)
            if dest.exists():
                messagebox.showwarning('Not saved', 'Existing report will not be overwritten')
                return
            try:
                with dest.open('x', encoding='utf-8') as stream:
                    json.dump({'version': __version__, 'disclaimer': 'Human review required',
                               'results': self.results}, stream, indent=2)
            except OSError:
                messagebox.showerror('Not saved', 'Could not save report')

    Window().root.mainloop()


if __name__ == '__main__':
    main()
