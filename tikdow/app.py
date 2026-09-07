import os
import json
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .audio import AudioProcessor, Cancelled, terminate
from .i18n import tr
from .core import build_command, check_ffmpeg, load_settings, save_settings


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('TikDow • TikTok Downloader')
        self.geometry('840x760')
        self.minsize(780, 700)
        self.configure(bg='#101827')
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TFrame', background='#101827')
        style.configure('TLabel', background='#101827', foreground='#e5edf9', font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 28, 'bold'), foreground='#38ddd0')
        style.configure('TButton', font=('Segoe UI', 10), padding=8)
        style.configure('TRadiobutton', background='#101827', foreground='#e5edf9')
        self.events = queue.Queue()
        self.cancelled = threading.Event()
        self.busy = False
        self.process = None
        self.saved = load_settings()
        self.url = tk.StringVar()
        self.values = {key: tk.StringVar(value=value) for key, value in self.saved.items()}
        self.status = tk.StringVar(value=self.t('ready'))
        self.translated = []
        self.controls = []
        body = ttk.Frame(self, padding=24)
        body.pack(fill='both', expand=True)
        body.columnconfigure(0, weight=1)
        body.rowconfigure(11, weight=1)
        ttk.Label(body, text='TikDow', style='Title.TLabel').grid(row=0, column=0, sticky='w')
        self.widget(ttk.Label, body, 'subtitle').grid(row=1, column=0, sticky='w', pady=(0, 20))
        self.widget(ttk.Label, body, 'link').grid(row=2, column=0, sticky='w')
        link = ttk.Frame(body)
        link.grid(row=3, column=0, sticky='ew', pady=(6, 16))
        entry = ttk.Entry(link, textvariable=self.url, font=('Segoe UI', 11))
        entry.pack(side='left', fill='x', expand=True, ipady=6)
        paste = self.widget(ttk.Button, link, 'paste', command=self.paste)
        paste.pack(side='left', padx=(8, 0))
        self.controls += [entry, paste]
        options = ttk.Frame(body)
        options.grid(row=4, column=0, sticky='ew', pady=(0, 16))
        for kind, label in [('mp4', 'mp4'), ('mp3', 'mp3')]:
            button = self.widget(ttk.Radiobutton, options, label, value=kind, variable=self.values['format'], command=self.persist)
            button.pack(side='left', padx=(0, 18))
            self.controls.append(button)
        ttk.Label(options, text='MP3 kbps:').pack(side='left')
        bitrate = ttk.Combobox(options, textvariable=self.values['mp3_bitrate'], values=('128', '192', '256', '320'), width=5, state='readonly')
        bitrate.pack(side='left', padx=8)
        bitrate.bind('<<ComboboxSelected>>', lambda _: self.persist())
        self.controls.append(bitrate)
        self.folder_row(body, 5, 'folder', 'output_dir')
        self.folder_row(body, 6, 'ffmpeg', 'ffmpeg_dir')
        language = ttk.Combobox(body, values=('Tiếng Việt', 'English'), width=13, state='readonly')
        language.current(1 if self.values['language'].get() == 'en' else 0)
        language.grid(row=0, column=0, sticky='e')
        language.bind('<<ComboboxSelected>>', lambda _: self.change_language(language.current()))
        self.controls.append(language)
        audio = ttk.Frame(body)
        audio.grid(row=7, column=0, sticky='ew', pady=(10, 0))
        self.widget(ttk.Label, audio, 'audio').grid(row=0, column=0, sticky='w')
        modes = ttk.Frame(audio)
        modes.grid(row=1, column=0, sticky='w', pady=6)
        for mode in ('original', 'analyze', 'enhance'):
            button = self.widget(ttk.Radiobutton, modes, mode, value=mode,
                                variable=self.values['audio_mode'], command=self.persist)
            button.pack(side='left', padx=(0, 12))
            self.controls.append(button)
        self.widget(ttk.Label, modes, 'target').pack(side='left')
        target = ttk.Combobox(modes, textvariable=self.values['target_lufs'],
                              values=('-16', '-14', '-12'), width=5, state='readonly')
        target.pack(side='left', padx=8)
        target.bind('<<ComboboxSelected>>', lambda _: self.persist())
        self.controls.append(target)
        self.widget(ttk.Label, audio, 'hint', wraplength=750).grid(row=2, column=0, sticky='w')
        local = self.widget(ttk.Button, audio, 'local', command=self.start_local)
        local.grid(row=3, column=0, sticky='w', pady=(8, 0))
        self.controls.append(local)
        actions = ttk.Frame(body)
        actions.grid(row=8, column=0, sticky='ew', pady=16)
        self.download_button = self.widget(ttk.Button, actions, 'download', command=self.start)
        self.download_button.pack(side='left')
        self.controls.append(self.download_button)
        self.cancel_button = self.widget(ttk.Button, actions, 'cancel', command=self.cancel, state='disabled')
        self.cancel_button.pack(side='left', padx=8)
        self.widget(ttk.Button, actions, 'open', command=self.open_folder).pack(side='right')
        self.progress = ttk.Progressbar(body, maximum=100)
        self.progress.grid(row=9, column=0, sticky='ew')
        ttk.Label(body, textvariable=self.status, wraplength=690).grid(row=10, column=0, sticky='w', pady=8)
        self.log = tk.Text(body, height=9, bg='#080f1b', fg='#bfd0e7', relief='flat', font=('Consolas', 9), state='disabled', wrap='word')
        self.log.grid(row=11, column=0, sticky='nsew')
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.after(100, self.poll)
        entry.focus_set()

    def t(self, key, **values):
        return tr(self.values['language'].get(), key, **values)

    def widget(self, factory, parent, key, **kwargs):
        widget = factory(parent, text=self.t(key), **kwargs)
        self.translated.append((widget, key))
        return widget

    def change_language(self, index):
        self.values['language'].set('en' if index == 1 else 'vi')
        for widget, key in self.translated:
            widget.configure(text=self.t(key))
        self.status.set(self.t('ready'))
        self.persist()

    def start_local(self):
        if self.busy:
            return
        source = filedialog.askopenfilename(parent=self, title=self.t('local_title'),
                                           filetypes=[(self.t('media'), '*.mp3 *.mp4')])
        if not source:
            return
        try:
            settings = self.snapshot()
            check_ffmpeg(settings['ffmpeg_dir'], settings['language'])
            if not self.persist():
                return
            # Local "Original" means inspect only; there is no download to perform.
            if settings['audio_mode'] == 'original':
                settings['audio_mode'] = 'analyze'
            self.begin_work(None, settings, source)
        except (ValueError, OSError) as error:
            messagebox.showerror(self.t('cannot_start'), str(error), parent=self)

    def folder_row(self, parent, row, label, key):
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, sticky='ew', pady=5)
        self.widget(ttk.Label, frame, label).pack(anchor='w')
        entry = ttk.Entry(frame, textvariable=self.values[key])
        entry.pack(side='left', fill='x', expand=True, ipady=4)
        entry.bind('<FocusOut>', lambda _: self.persist())
        button = self.widget(ttk.Button, frame, 'browse', command=lambda: self.choose(key))
        button.pack(side='right', padx=(8, 0))
        self.controls += [entry, button]

    def snapshot(self):
        return {key: value.get().strip() for key, value in self.values.items()}

    def persist(self):
        try:
            save_settings(self.snapshot())
            return True
        except OSError as error:
            self.status.set(self.t('save_error', error=error))
            return False

    def choose(self, key):
        folder = filedialog.askdirectory(parent=self)
        if folder:
            self.values[key].set(folder)
            self.persist()

    def paste(self):
        try:
            self.url.set(self.clipboard_get().strip())
        except tk.TclError:
            self.status.set(self.t('clipboard'))

    def start(self):
        if self.busy:
            return
        try:
            settings = self.snapshot()
            if not settings['output_dir']:
                raise ValueError(self.t('choose_folder'))
            command = build_command(self.url.get(), settings)
            check_ffmpeg(settings['ffmpeg_dir'], settings['language'])
            Path(settings['output_dir']).mkdir(parents=True, exist_ok=True)
            if not self.persist():
                raise ValueError(self.t('settings_error'))
        except (ValueError, OSError) as error:
            messagebox.showerror(self.t('cannot_start'), str(error), parent=self)
            return
        self.begin_work(command, settings)

    def begin_work(self, command, settings, source=None):
        self.busy = True
        self.cancelled.clear()
        self.progress['value'] = 0
        self.status.set(self.t('measuring' if source else 'reading'))
        self.last_folder = Path(source).resolve().parent if source else Path(settings['output_dir']).expanduser().resolve()
        self.log.configure(state='normal')
        self.log.delete('1.0', 'end')
        self.log.configure(state='disabled')
        for control in self.controls:
            control.configure(state='disabled')
        self.cancel_button.configure(state='normal')
        threading.Thread(target=self.worker, args=(command, settings, source), daemon=True).start()

    terminate = staticmethod(terminate)

    def set_process(self, process):
        self.process = process

    def worker(self, command, settings, source=None):
        code = 1
        paths = [str(source)] if source else []
        try:
            if command:
                kwargs = {'creationflags': subprocess.CREATE_NO_WINDOW} if sys.platform == 'win32' else {'start_new_session': True}
                env = dict(os.environ, PYTHONIOENCODING='utf-8')
                with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                      text=True, encoding='utf-8', errors='replace', env=env, **kwargs) as process:
                    self.process = process
                    if self.cancelled.is_set():
                        self.terminate(process)
                    for line in process.stdout:
                        if line.startswith('TIKDOW_FILE:'):
                            paths.append(json.loads(line[len('TIKDOW_FILE:'):]))
                        else:
                            self.events.put(('log', line.rstrip()))
                    code = process.wait()
                self.process = None
            else:
                code = 0
            if code == 0 and not self.cancelled.is_set() and settings['audio_mode'] != 'original':
                if not paths:
                    raise ValueError(tr(settings['language'], 'file_missing'))
                processor = AudioProcessor(settings, self.cancelled,
                    lambda text: self.events.put(('log', text)), self.set_process)
                for path in dict.fromkeys(paths):
                    processor.process(path)
        except Cancelled:
            code = 1
        except Exception as error:
            code = 1
            self.events.put(('log', str(error)))
        finally:
            self.process = None
            self.events.put(('done', code))

    def cancel(self):
        self.cancelled.set()
        self.cancel_button.configure(state='disabled')
        self.status.set(self.t('cancelling'))
        process = self.process
        if process is not None:
            threading.Thread(target=self.terminate, args=(process,), daemon=True).start()

    def poll(self):
        for _ in range(150):
            try:
                kind, value = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == 'log':
                self.log.configure(state='normal')
                self.log.insert('end', value + '\n')
                if int(self.log.index('end-1c').split('.')[0]) > 500:
                    self.log.delete('1.0', '100.0')
                self.log.see('end')
                self.log.configure(state='disabled')
                match = re.search(r'\[download\]\s+([\d.]+)%', value)
                if match:
                    self.progress['value'] = float(match.group(1))
                if not self.cancelled.is_set():
                    self.status.set(value[:160])
            else:
                self.busy = False
                for control in self.controls:
                    control.configure(state='readonly' if isinstance(control, ttk.Combobox) else 'normal')
                self.cancel_button.configure(state='disabled')
                if self.cancelled.is_set():
                    self.status.set(self.t('cancelled'))
                elif value == 0:
                    self.progress['value'] = 100
                    self.status.set(self.t('done'))
                else:
                    self.status.set(self.t('failed'))
        self.after(100, self.poll)

    def open_folder(self):
        try:
            folder = getattr(self, 'last_folder', Path(self.values['output_dir'].get()).expanduser().resolve())
            folder.mkdir(parents=True, exist_ok=True)
            if sys.platform == 'win32':
                os.startfile(str(folder))
            else:
                subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open', str(folder)])
        except OSError as error:
            messagebox.showerror(self.t('open_error'), str(error), parent=self)

    def close(self):
        if self.busy:
            messagebox.showinfo(self.t('busy'), self.t('close_busy'), parent=self)
            return
        self.persist()
        self.destroy()
