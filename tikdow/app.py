import os
from pathlib import Path
import queue
import re
import signal
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .core import build_command, check_ffmpeg, load_settings, save_settings


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('TikDow • TikTok Downloader')
        self.geometry('780x640')
        self.minsize(680, 580)
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
        self.status = tk.StringVar(value='Sẵn sàng. Dán link TikTok để bắt đầu.')
        self.controls = []
        body = ttk.Frame(self, padding=24)
        body.pack(fill='both', expand=True)
        body.columnconfigure(0, weight=1)
        body.rowconfigure(10, weight=1)
        ttk.Label(body, text='TikDow', style='Title.TLabel').grid(row=0, column=0, sticky='w')
        ttk.Label(body, text='Video hoặc âm thanh — chọn cách bạn muốn lưu.').grid(row=1, column=0, sticky='w', pady=(0, 20))
        ttk.Label(body, text='LINK VIDEO TIKTOK').grid(row=2, column=0, sticky='w')
        link = ttk.Frame(body)
        link.grid(row=3, column=0, sticky='ew', pady=(6, 16))
        entry = ttk.Entry(link, textvariable=self.url, font=('Segoe UI', 11))
        entry.pack(side='left', fill='x', expand=True, ipady=6)
        paste = ttk.Button(link, text='Dán link', command=self.paste)
        paste.pack(side='left', padx=(8, 0))
        self.controls += [entry, paste]
        options = ttk.Frame(body)
        options.grid(row=4, column=0, sticky='ew', pady=(0, 16))
        for kind, label in [('mp4', 'MP4 • Video'), ('mp3', 'MP3 • Âm thanh')]:
            button = ttk.Radiobutton(options, text=label, value=kind, variable=self.values['format'], command=self.persist)
            button.pack(side='left', padx=(0, 18))
            self.controls.append(button)
        ttk.Label(options, text='MP3 kbps:').pack(side='left')
        bitrate = ttk.Combobox(options, textvariable=self.values['mp3_bitrate'], values=('128', '192', '256', '320'), width=5, state='readonly')
        bitrate.pack(side='left', padx=8)
        bitrate.bind('<<ComboboxSelected>>', lambda _: self.persist())
        self.controls.append(bitrate)
        self.folder_row(body, 5, 'Thư mục lưu', 'output_dir')
        self.folder_row(body, 6, 'FFmpeg bin (để trống nếu đã có PATH)', 'ffmpeg_dir')
        actions = ttk.Frame(body)
        actions.grid(row=7, column=0, sticky='ew', pady=16)
        self.download_button = ttk.Button(actions, text='↓  Tải xuống', command=self.start)
        self.download_button.pack(side='left')
        self.controls.append(self.download_button)
        self.cancel_button = ttk.Button(actions, text='Hủy tải', command=self.cancel, state='disabled')
        self.cancel_button.pack(side='left', padx=8)
        ttk.Button(actions, text='Mở thư mục', command=self.open_folder).pack(side='right')
        self.progress = ttk.Progressbar(body, maximum=100)
        self.progress.grid(row=8, column=0, sticky='ew')
        ttk.Label(body, textvariable=self.status, wraplength=690).grid(row=9, column=0, sticky='w', pady=8)
        self.log = tk.Text(body, height=9, bg='#080f1b', fg='#bfd0e7', relief='flat', font=('Consolas', 9), state='disabled', wrap='word')
        self.log.grid(row=10, column=0, sticky='nsew')
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.after(100, self.poll)
        entry.focus_set()

    def folder_row(self, parent, row, label, key):
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, sticky='ew', pady=5)
        ttk.Label(frame, text=label).pack(anchor='w')
        entry = ttk.Entry(frame, textvariable=self.values[key])
        entry.pack(side='left', fill='x', expand=True, ipady=4)
        entry.bind('<FocusOut>', lambda _: self.persist())
        button = ttk.Button(frame, text='Chọn…', command=lambda: self.choose(key))
        button.pack(side='right', padx=(8, 0))
        self.controls += [entry, button]

    def snapshot(self):
        return {key: value.get().strip() for key, value in self.values.items()}

    def persist(self):
        try:
            save_settings(self.snapshot())
            return True
        except OSError as error:
            self.status.set(f'Không lưu được settings: {error}')
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
            self.status.set('Clipboard chưa có văn bản.')

    def start(self):
        if self.busy:
            return
        try:
            settings = self.snapshot()
            if not settings['output_dir']:
                raise ValueError('Hãy chọn thư mục lưu.')
            command = build_command(self.url.get(), settings)
            check_ffmpeg(settings['ffmpeg_dir'])
            Path(settings['output_dir']).mkdir(parents=True, exist_ok=True)
            if not self.persist():
                raise ValueError('Không ghi được settings/settings.json. Kiểm tra quyền ghi thư mục ứng dụng.')
        except (ValueError, OSError) as error:
            messagebox.showerror('Chưa thể tải', str(error), parent=self)
            return
        self.busy = True
        self.cancelled.clear()
        self.progress['value'] = 0
        self.status.set('Đang đọc video…')
        self.log.configure(state='normal')
        self.log.delete('1.0', 'end')
        self.log.configure(state='disabled')
        for control in self.controls:
            control.configure(state='disabled')
        self.cancel_button.configure(state='normal')
        threading.Thread(target=self.worker, args=(command,), daemon=True).start()

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

    def worker(self, command):
        code = 1
        try:
            kwargs = {'creationflags': subprocess.CREATE_NO_WINDOW} if sys.platform == 'win32' else {'start_new_session': True}
            env = dict(os.environ, PYTHONIOENCODING='utf-8')
            with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, encoding='utf-8', errors='replace', env=env, **kwargs) as process:
                self.process = process
                if self.cancelled.is_set():
                    self.terminate(process)
                for line in process.stdout:
                    self.events.put(('log', line.rstrip()))
                code = process.wait()
        except Exception as error:
            self.events.put(('log', str(error)))
        finally:
            self.process = None
            self.events.put(('done', code))

    def cancel(self):
        self.cancelled.set()
        self.cancel_button.configure(state='disabled')
        self.status.set('Đang hủy…')
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
                    self.status.set('Đã hủy. File tải dở có thể được tiếp tục khi tải lại.')
                elif value == 0:
                    self.progress['value'] = 100
                    self.status.set('Đã hoàn tất! Bấm Mở thư mục để xem file.')
                else:
                    self.status.set('Tải thất bại. Xem chi tiết bên dưới; video có thể bị giới hạn hoặc TikTok chặn yêu cầu.')
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
            messagebox.showerror('Không mở được thư mục', str(error), parent=self)

    def close(self):
        if self.busy:
            messagebox.showinfo('Đang tải', 'Hãy hủy tải và chờ dừng trước khi đóng TikDow.', parent=self)
            return
        self.persist()
        self.destroy()
