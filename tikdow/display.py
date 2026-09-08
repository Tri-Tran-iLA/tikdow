"""Fixed-size, DPI-aware desktop layout. No third-party dependencies."""
import ctypes
from ctypes import wintypes
import sys
import tkinter.font as tkfont
from tkinter import ttk

BASE_WIDTH, BASE_HEIGHT = 860, 800


def enable_dpi_awareness():
    """Must run before the first Tk window is created."""
    if sys.platform != 'win32':
        return
    try:
        api = ctypes.windll.user32.SetProcessDpiAwarenessContext
        api.argtypes = [ctypes.c_void_p]
        api.restype = wintypes.BOOL
        if api(ctypes.c_void_p(-4)):  # PER_MONITOR_AWARE_V2
            return
        if ctypes.windll.kernel32.GetLastError() == 5:
            return  # A host/manifest already established process awareness.
    except AttributeError:
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        ctypes.windll.user32.SetProcessDPIAware()


def layout_for(work_width, work_height, dpi):
    """Fit the whole client area, leaving room for borders and taskbar-free margins."""
    dpi_scale = max(0.5, dpi / 96)
    available_w = max(1, work_width - round(32 * dpi_scale))
    available_h = max(1, work_height - round(80 * dpi_scale))
    scale = min(dpi_scale, available_w / BASE_WIDTH, available_h / BASE_HEIGHT)
    return scale, max(1, round(BASE_WIDTH * scale)), max(1, round(BASE_HEIGHT * scale))


def clamp_position(x, y, width, height, work, dpi):
    left, top, right, bottom = work
    margin = round(16 * dpi / 96)
    title = round(48 * dpi / 96)
    return (max(left, min(x, right - width - margin)),
            max(top, min(y, bottom - height - title)))


class WindowsMonitor:
    def __init__(self, root):
        self.root = root
        self.user = ctypes.windll.user32
        self.user.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
        self.user.GetAncestor.restype = wintypes.HWND
        self.user.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
        self.user.MonitorFromWindow.restype = wintypes.HANDLE
        self.user.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
        self.user.GetMonitorInfoW.restype = wintypes.BOOL
        self.user.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
        self.user.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int,
                                          ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
        if hasattr(self.user, 'GetDpiForWindow'):
            self.user.GetDpiForWindow.argtypes = [wintypes.HWND]
            self.user.GetDpiForWindow.restype = wintypes.UINT

    @property
    def hwnd(self):
        # Tk may recreate the outer HWND when resizable/style flags change.
        # Never retain that handle across event-loop iterations.
        client = self.root.winfo_id()
        return self.user.GetAncestor(client, 2) or client

    def read(self):
        class Info(ctypes.Structure):
            _fields_ = [('size', wintypes.DWORD), ('monitor', wintypes.RECT),
                        ('work', wintypes.RECT), ('flags', wintypes.DWORD)]
        info = Info()
        info.size = ctypes.sizeof(info)
        hwnd = self.hwnd
        monitor = self.user.MonitorFromWindow(hwnd, 2)
        if not self.user.GetMonitorInfoW(monitor, ctypes.byref(info)):
            raise OSError('GetMonitorInfoW failed')
        dpi = self.user.GetDpiForWindow(hwnd) if hasattr(self.user, 'GetDpiForWindow') else 96
        return (info.work.left, info.work.top, info.work.right, info.work.bottom), dpi or 96

    def position(self):
        rect = wintypes.RECT()
        if not self.user.GetWindowRect(self.hwnd, ctypes.byref(rect)):
            raise OSError('GetWindowRect failed')
        return rect.left, rect.top

    def move(self, x, y):
        self.user.SetWindowPos(self.hwnd, None, x, y, 0, 0, 0x0015)  # NOSIZE|NOZORDER|NOACTIVATE


class DisplayController:
    def __init__(self, root):
        self.root = root
        self.native = WindowsMonitor(root) if sys.platform == 'win32' else None
        self.last = None
        self.fonts = []
        self.options = []
        self.spacing = []
        self.style = ttk.Style(root)
        # Capture once at 96 DPI. Never multiply already-scaled measurements.
        for name in tkfont.names(root):
            font = tkfont.nametofont(name, root=root)
            self.fonts.append((font, self.base_font_pixels(font)))
        self.capture(root)
        self.refresh(initial=True)

    @staticmethod
    def base_font_pixels(font):
        size = font.actual('size')
        return abs(size) if size < 0 else size * 96 / 72

    def numbers(self, value):
        # Tk returns scalar ints, Python sequences, strings or Tcl_Obj values.
        if isinstance(value, (int, float)):
            return (float(value),)
        if isinstance(value, (tuple, list)):
            parts = value
        else:
            parts = self.root.tk.splitlist(value if isinstance(value, (str, bytes)) else str(value))
        return tuple(float(str(v)) for v in parts)

    def capture(self, widget):
        keys = widget.keys()
        if 'font' in keys and str(widget.cget('font')):
            font = tkfont.Font(root=self.root, font=widget.cget('font'))
            self.fonts.append((font, self.base_font_pixels(font)))
            widget.configure(font=font)
        for option in ('padding', 'wraplength', 'borderwidth', 'highlightthickness'):
            if option in keys and str(widget.cget(option)):
                try:
                    numbers = self.numbers(widget.cget(option))
                    if numbers:
                        self.options.append((widget, option, numbers))
                except (ValueError, TypeError):
                    pass
        manager = widget.winfo_manager()
        if manager in ('pack', 'grid'):
            info = widget.pack_info() if manager == 'pack' else widget.grid_info()
            for key in ('padx', 'pady', 'ipadx', 'ipady'):
                if key in info:
                    self.spacing.append((widget, manager, key, self.numbers(info[key])))
        for child in widget.winfo_children():
            self.capture(child)

    def refresh(self, initial=False):
        try:
            self.apply_layout(initial)
        except OSError:
            # A transient monitor/window transition must not stop DPI tracking.
            self.last = None
        finally:
            self.timer = self.root.after(500, self.refresh)

    def apply_layout(self, initial=False):
        root = self.root
        if self.native:
            try:
                work, dpi = self.native.read()
            except OSError:
                if not initial:
                    raise
                # Still show a usable initial window if the native wrapper is not ready.
                work = (0, 0, root.winfo_screenwidth(), root.winfo_screenheight())
                dpi = 96
        else:
            work = (0, 0, root.winfo_screenwidth(), root.winfo_screenheight())
            dpi = root.winfo_fpixels('1i')
        key = (work, dpi)
        if key != self.last:
            self.last = key
            scale, width, height = layout_for(work[2] - work[0], work[3] - work[1], dpi)
            for font, pixels in self.fonts:
                font.configure(size=-max(1, round(pixels * scale)))
            for widget, option, values in self.options:
                scaled = tuple(round(v * scale) for v in values)
                widget.configure(**{option: scaled if len(scaled) > 1 else scaled[0]})
            for widget, manager, option, values in self.spacing:
                if widget.winfo_manager() != manager:
                    continue  # Keep conditionally hidden controls hidden during DPI changes.
                scaled = tuple(round(v * scale) for v in values)
                configure = widget.pack_configure if manager == 'pack' else widget.grid_configure
                configure(**{option: scaled if len(scaled) > 1 else scaled[0]})
            for style, points, bold in [('TLabel', 10, False), ('Title.TLabel', 28, True),
                                        ('TButton', 10, False), ('TRadiobutton', 10, False),
                                        ('TCheckbutton', 10, False), ('TCombobox', 10, False)]:
                self.style.configure(style, font=('Segoe UI', -round(points * 96 / 72 * scale), 'bold' if bold else 'normal'))
            self.style.configure('TButton', padding=round(8 * scale))
            self.style.configure('TCombobox', arrowsize=max(8, round(14 * scale)))
            self.style.configure('TRadiobutton', indicatorsize=max(6, round(14 * scale)))
            self.style.configure('TCheckbutton', indicatorsize=max(6, round(14 * scale)))
            self.style.configure('TProgressbar', thickness=max(4, round(14 * scale)))
            root.minsize(width, height)
            root.maxsize(width, height)
            root.geometry(f'{width}x{height}')
            root.resizable(False, False)
            root.update_idletasks()
            if initial:
                x = work[0] + (work[2] - work[0] - width) // 2
                y = work[1] + (work[3] - work[1] - height - round(40 * dpi / 96)) // 2
            else:
                x, y = self.native.position() if self.native else (root.winfo_x(), root.winfo_y())
            x, y = clamp_position(x, y, width, height, work, dpi)
            if self.native:
                self.native.move(x, y)
            else:
                root.geometry(f'{width}x{height}+{x}+{y}')

