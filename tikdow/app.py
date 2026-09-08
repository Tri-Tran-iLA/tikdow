import json
import os
from pathlib import Path
import queue
import re
import signal
import subprocess
import sys
import threading
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .display import DisplayController, enable_dpi_awareness
from .i18n import STRINGS, translate

from .core import is_photo_url, is_short_url, build_command, check_ffmpeg, load_settings, save_settings


class App(tk.Tk):
    def __init__(self):
        enable_dpi_awareness()
        super().__init__()
        self.withdraw()
        self.tk.call('tk', 'scaling', 96 / 72)
        self.title('TikDow • TikTok Downloader')
        self.configure(bg='#101827')
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TFrame', background='#101827')
        style.configure('TLabel', background='#101827', foreground='#e5edf9', font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 28, 'bold'), foreground='#38ddd0')
        style.configure('TButton', font=('Segoe UI', 10), padding=8)
        style.configure('TCheckbutton', background='#101827', foreground='#e5edf9')
        style.configure('TRadiobutton', background='#101827', foreground='#e5edf9')
        self.events = queue.Queue()
        self.cancelled = threading.Event()
        self.busy = False
        self.process = None
        self.saved = load_settings()
        self.url = tk.StringVar()
        self.photo_mode = False
        self.previous_format = self.saved['format']
        self.values = {key: tk.StringVar(value=value) for key, value in self.saved.items()}
        self.status = tk.StringVar(value=self.t('Sẵn sàng. Dán link TikTok để bắt đầu.'))
        self.controls = []
        body = ttk.Frame(self, padding=24)
        body.pack(fill='both', expand=True)
        body.columnconfigure(0, weight=1)
        body.rowconfigure(12, weight=1)
        ttk.Label(body, text='TikDow', style='Title.TLabel').grid(row=0, column=0, sticky='w')
        ttk.Label(body, text=self.t('Video hoặc âm thanh — chọn cách bạn muốn lưu.')).grid(row=1, column=0, sticky='w', pady=(0, 20))
        ttk.Label(body, text=self.t('LINK VIDEO TIKTOK')).grid(row=2, column=0, sticky='w')
        link = ttk.Frame(body)
        link.grid(row=3, column=0, sticky='ew', pady=(6, 16))
        entry = ttk.Entry(link, textvariable=self.url, font=('Segoe UI', 11))
        entry.pack(side='left', fill='x', expand=True, ipady=6)
        paste = ttk.Button(link, text=self.t('Dán link'), command=self.paste)
        paste.pack(side='left', padx=(8, 0))
        self.controls += [entry, paste]
        options = ttk.Frame(body)
        options.grid(row=4, column=0, sticky='ew', pady=(0, 16))
        for kind, label in [('mp4', 'MP4 • Video'), ('mp3', self.t('MP3 • Âm thanh'))]:
            button = ttk.Radiobutton(options, text=label, value=kind, variable=self.values['format'], command=self.persist)
            button.pack(side='left', padx=(0, 18))
            self.controls.append(button)
            if kind == 'mp4':
                self.mp4_button = button
        ttk.Label(options, text='MP3 kbps:').pack(side='left')
        bitrate = ttk.Combobox(options, textvariable=self.values['mp3_bitrate'], values=('128', '192', '256', '320'), width=5, state='readonly')
        bitrate.pack(side='left', padx=8)
        bitrate.bind('<<ComboboxSelected>>', lambda _: self.persist())
        self.controls.append(bitrate)
        self.folder_row(body, 5, self.t('Thư mục lưu'), 'output_dir')
        self.folder_row(body, 6, self.t('FFmpeg bin (để trống nếu đã có PATH)'), 'ffmpeg_dir')
        self.language_name = tk.StringVar(value='English' if self.values['language'].get() == 'en' else 'Tiếng Việt')
        language = ttk.Combobox(body, textvariable=self.language_name, values=('Tiếng Việt', 'English'), width=12, state='readonly')
        language.grid(row=0, column=0, sticky='e')
        language.bind('<<ComboboxSelected>>', self.change_language)
        self.controls.append(language)
        loud = ttk.Frame(body)
        loud.grid(row=7, column=0, sticky='ew', pady=8)
        toggle = ttk.Checkbutton(loud, text=self.t('Nâng loudness (lưu thêm bản riêng)'), variable=self.values['loudness'], onvalue='on', offvalue='off', command=self.persist)
        toggle.pack(side='left')
        ttk.Label(loud, text=self.t('Mục tiêu LUFS:')).pack(side='left', padx=(18, 6))
        target = ttk.Combobox(loud, textvariable=self.values['target_lufs'], values=('-16', '-14', '-12'), width=5, state='readonly')
        target.pack(side='left')
        target.bind('<<ComboboxSelected>>', lambda _: self.persist())
        self.controls += [toggle, target]
        ttk.Label(body, text=self.t('Đo trước/sau • True peak mục tiêu −1.5 dBTP • Giữ bản gốc')).grid(row=8, column=0, sticky='w')
        actions = ttk.Frame(body)
        actions.grid(row=9, column=0, sticky='ew', pady=16)
        self.download_button = ttk.Button(actions, text=self.t('↓  Tải xuống'), command=self.start)
        self.download_button.pack(side='left')
        self.controls.append(self.download_button)
        self.cancel_button = ttk.Button(actions, text=self.t('Hủy tải'), command=self.cancel, state='disabled')
        self.cancel_button.pack(side='left', padx=8)
        ttk.Button(actions, text=self.t('Mở thư mục'), command=self.open_folder).pack(side='right')
        self.progress = ttk.Progressbar(body, maximum=100)
        self.progress.grid(row=10, column=0, sticky='ew')
        ttk.Label(body, textvariable=self.status, wraplength=690).grid(row=11, column=0, sticky='w', pady=8)
        self.log = tk.Text(body, height=9, bg='#080f1b', fg='#bfd0e7', relief='flat', font=('Consolas', 9), state='disabled', wrap='word')
        self.log.grid(row=12, column=0, sticky='nsew')
        footer = ttk.Frame(body)
        footer.grid(row=13, column=0, sticky='ew', pady=(12, 0))
        for label, url, side in (
            ('Tri-Tran-iLA', 'https://github.com/Tri-Tran-iLA', 'left'),
            ('GitHub Repo ↗', 'https://github.com/Tri-Tran-iLA/tikdow', 'right'),
        ):
            link_label = ttk.Label(footer, text=label, foreground='#38ddd0',
                                   cursor='hand2', takefocus=True)
            link_label.pack(side=side)
            def open_link(_event=None, target=url):
                webbrowser.open_new_tab(target)
            link_label.bind('<Button-1>', open_link)
            link_label.bind('<Return>', open_link)
            link_label.bind('<space>', open_link)
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.after(100, self.poll)
        self.update_idletasks()
        self.display = DisplayController(self)
        self.deiconify()
        self.url.trace_add('write', self.update_photo_mode)
        entry.focus_set()

    def update_photo_mode(self, *_args, resolved_photo=False):
        photo = resolved_photo or is_photo_url(self.url.get())
        if photo == self.photo_mode:
            return
        if photo and not self.photo_mode:
            self.previous_format = self.values['format'].get()
            self.values['format'].set('mp3')
            self.mp4_button.pack_forget()
            self.status.set(self.t('Bài ảnh: chỉ tải nhạc MP3.'))
        elif not photo and self.photo_mode:
            others = self.mp4_button.master.pack_slaves()
            self.mp4_button.pack(side='left', padx=(0, 18), before=others[0])
            self.values['format'].set(self.previous_format)
            self.status.set(self.t('Sẵn sàng. Dán link TikTok để bắt đầu.'))
        self.photo_mode = photo
        self.persist()

    def t(self, text):
        return translate(text, self.values['language'].get())

    def change_language(self, _event=None):
        self.values['language'].set('en' if self.language_name.get() == 'English' else 'vi')
        reverse = {v: k for k, v in STRINGS.items()}
        def visit(widget):
            if 'text' in widget.keys():
                text = str(widget.cget('text'))
                widget.configure(text=self.t(reverse.get(text, text)))
            for child in widget.winfo_children():
                visit(child)
        visit(self)
        self.status.set(self.t('Sẵn sàng. Dán link TikTok để bắt đầu.'))
        self.persist()

    def folder_row(self, parent, row, label, key):
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, sticky='ew', pady=5)
        ttk.Label(frame, text=label).pack(anchor='w')
        entry = ttk.Entry(frame, textvariable=self.values[key])
        entry.pack(side='left', fill='x', expand=True, ipady=4)
        entry.bind('<FocusOut>', lambda _: self.persist())
        button = ttk.Button(frame, text=self.t('Chọn…'), command=lambda: self.choose(key))
        button.pack(side='right', padx=(8, 0))
        self.controls += [entry, button]

    def snapshot(self):
        return {key: value.get().strip() for key, value in self.values.items()}

    def persist(self):
        try:
            save_settings(self.snapshot())
            return True
        except OSError as error:
            self.status.set(self.t('Không lưu được settings:') + ' ' + str(error))
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
            self.status.set(self.t('Clipboard chưa có văn bản.'))

    def start(self):
        if self.busy:
            return
        try:
            settings = self.snapshot()
            if not settings['output_dir']:
                raise ValueError(self.t('Hãy chọn thư mục lưu.'))
            command = build_command(self.url.get(), settings)
            check_ffmpeg(settings['ffmpeg_dir'])
            Path(settings['output_dir']).mkdir(parents=True, exist_ok=True)
            if not self.persist():
                raise ValueError(self.t('Không ghi được settings/settings.json. Kiểm tra quyền ghi thư mục ứng dụng.'))
        except (ValueError, OSError) as error:
            messagebox.showerror(self.t('Chưa thể tải'), self.t(str(error)), parent=self)
            return
        self.busy = True
        self.cancelled.clear()
        self.progress['value'] = 0
        self.status.set(self.t('Đang đọc video…'))
        self.log.configure(state='normal')
        self.log.delete('1.0', 'end')
        self.log.configure(state='disabled')
        for control in self.controls:
            control.configure(state='disabled')
        self.cancel_button.configure(state='normal')
        threading.Thread(target=self.worker, args=(self.url.get().strip(), settings), daemon=True).start()

    @staticmethod
    def terminate(process):
        if process.poll() is not None:
            return
        try:
            if sys.platform == 'win32':
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                               capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                os.killpg(process.pid, signal.SIGTERM)
        except (OSError, ProcessLookupError):
            pass

    def run_process(self, command, result_prefix='TIKDOW_FILE:'):
        code = 1
        paths = []
        try:
            kwargs = {'creationflags': subprocess.CREATE_NO_WINDOW} if sys.platform == 'win32' else {'start_new_session': True}
            env = dict(os.environ, PYTHONIOENCODING='utf-8')
            with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, encoding='utf-8', errors='replace', env=env, **kwargs) as process:
                self.process = process
                if self.cancelled.is_set():
                    self.terminate(process)
                for line in process.stdout:
                    if line.startswith(result_prefix):
                        paths.append(json.loads(line[len(result_prefix):]))
                    else:
                        self.events.put(('log', line.rstrip()))
                code = process.wait()
        except Exception as error:
            self.events.put(('log', str(error)))
        finally:
            self.process = None
        return code, paths

    def worker(self, url, settings):
        code = 1
        try:
            if is_short_url(url):
                code, resolved = self.run_process([sys.executable, '-m', 'tikdow.resolve', url], 'TIKDOW_URL:')
                if code or not resolved or self.cancelled.is_set():
                    code = code or 1
                    return
                url = resolved[-1]
            if is_photo_url(url):
                settings = dict(settings, format='mp3')
                self.events.put(('photo', None))
            command = build_command(url, settings)
            code, paths = self.run_process(command)
            if code == 0 and settings['loudness'] == 'on' and not self.cancelled.is_set():
                if not paths:
                    raise RuntimeError('No downloaded file path returned / Không nhận được đường dẫn file tải.')
                self.events.put(('processing', None))
                for path in dict.fromkeys(paths):
                    if self.cancelled.is_set():
                        break
                    code, _ = self.run_process([sys.executable, '-m', 'tikdow.loudness', path, json.dumps(settings)])
                    if code:
                        break
        except Exception as error:
            self.events.put(('log', str(error)))
            code = 1
        finally:
            self.events.put(('done', code))

    def cancel(self):
        self.cancelled.set()
        self.cancel_button.configure(state='disabled')
        self.status.set(self.t('Đang hủy…'))
        process = self.process
        if process is not None:
            threading.Thread(target=self.terminate, args=(process,), daemon=True).start()

    def poll(self):
        for _ in range(150):
            try:
                kind, value = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == 'photo':
                self.update_photo_mode(resolved_photo=True)
            elif kind == 'processing':
                self.progress.configure(mode='indeterminate')
                self.progress.start(15)
            elif kind == 'log':
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
                self.progress.stop()
                self.progress.configure(mode='determinate')
                self.busy = False
                for control in self.controls:
                    control.configure(state='readonly' if isinstance(control, ttk.Combobox) else 'normal')
                self.cancel_button.configure(state='disabled')
                if self.cancelled.is_set():
                    self.status.set(self.t('Đã hủy. File tải dở có thể được tiếp tục khi tải lại.'))
                elif value == 0:
                    self.progress['value'] = 100
                    self.status.set(self.t('Đã hoàn tất! Bấm Mở thư mục để xem file.'))
                else:
                    self.status.set(self.t('Tải thất bại. Xem chi tiết bên dưới; video có thể bị giới hạn hoặc TikTok chặn yêu cầu.'))
        self.after(100, self.poll)

    def open_folder(self):
        try:
            folder = Path(self.values['output_dir'].get()).expanduser().resolve()
            folder.mkdir(parents=True, exist_ok=True)
            if sys.platform == 'win32':
                os.startfile(str(folder))
            else:
                subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open', str(folder)])
        except OSError as error:
            messagebox.showerror(self.t('Không mở được thư mục'), self.t(str(error)), parent=self)

    def close(self):
        if self.busy:
            messagebox.showinfo(self.t('Đang tải'), self.t('Hãy hủy tải và chờ dừng trước khi đóng TikDow.'), parent=self)
            return
        self.persist()
        self.destroy()
