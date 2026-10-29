"""Schedule repeated mouse clicks on Windows or a Linux X11 desktop."""

import ctypes
from datetime import datetime, timedelta
import math
import os
from pathlib import Path
import sys
import time
import tkinter as tk
from tkinter import messagebox, ttk

from schedule import ClickPlan, ClickRun, read_datetime, read_seconds


class Mouse:
    def __init__(self):
        if sys.platform not in ("win32", "linux"):
            raise RuntimeError("This app supports Windows and Linux X11 desktops.")
        if sys.platform == "linux":
            if os.environ.get("WAYLAND_DISPLAY") or os.environ.get("XDG_SESSION_TYPE") == "wayland":
                raise RuntimeError(
                    "Mouse automation requires an X11 session on Linux.\n"
                    "Log out and choose an X11/Xorg session at the login screen."
                )
            if not os.environ.get("DISPLAY"):
                raise RuntimeError("Run this app from your Linux desktop with an X11 display.")
        try:
            from pynput.mouse import Button, Controller
        except ImportError as error:
            raise RuntimeError(
                "Mouse control is unavailable. Install the dependencies with:\n"
                "python -m pip install -r requirements.txt\n\n" + str(error)
            ) from error
        self.controller = Controller()
        self.left = Button.left

    def position(self):
        return self.controller.position

    def click(self, point):
        self.controller.position = point
        if tuple(self.controller.position) != tuple(point):
            raise RuntimeError("Could not reach that screen position. Pick a new position.")
        self.controller.click(self.left)

    def keep_awake(self, enabled):
        if sys.platform == "win32":
            flags = 0x80000003 if enabled else 0x80000000
            if not ctypes.windll.kernel32.SetThreadExecutionState(flags):
                raise RuntimeError("Could not update sleep prevention. Check your power settings.")


class ClickerApp:
    def __init__(self, root, mouse):
        self.root, self.mouse = root, mouse
        self.run = None
        self.point = None
        self.job = None
        self.overlay = None
        self.editors = []
        root.title('Simple Autoclicker')
        assets = Path(__file__).resolve().parent / 'assets'
        self.icon = tk.PhotoImage(master=root, file=str(assets / 'icon.png'))
        root.iconphoto(True, self.icon)
        if sys.platform == 'win32':
            root.iconbitmap(str(assets / 'icon.ico'))
        root.configure(background='#F3F6FA')
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.bind('<Escape>', lambda event: self.cancel())
        font = 'Segoe UI' if sys.platform == 'win32' else 'DejaVu Sans'
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('TFrame', background='#F3F6FA')
        style.configure('TLabel', background='#F3F6FA', foreground='#20334D', font=(font, 10))
        style.configure('Title.TLabel', font=(font, 19, 'bold'))
        style.configure('TLabelframe', background='#F3F6FA')
        style.configure('TLabelframe.Label', background='#F3F6FA', foreground='#20334D', font=(font, 10, 'bold'))
        style.configure('TRadiobutton', background='#F3F6FA', font=(font, 10))
        style.configure('TButton', font=(font, 10), padding=(10, 6))
        style.configure('Primary.TButton', background='#245DB5', foreground='white')
        style.map('Primary.TButton', background=[('disabled', '#CED7E4'), ('active', '#194A96')])
        style.configure('TEntry', padding=5)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        frame = ttk.Frame(root, padding=14)
        frame.grid(sticky='nsew')
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text='Clicks, on your schedule.', style='Title.TLabel').grid(
            row=0, column=0, columnspan=2, sticky='w')
        ttk.Label(frame, text='Choose a point, set a pace, and decide when to stop.').grid(
            row=1, column=0, columnspan=2, sticky='w', pady=(6, 12))

        target = self.section(frame, 'Click point', 2)
        x, y = mouse.position()
        self.x, self.y = tk.StringVar(value=str(x)), tk.StringVar(value=str(y))
        ttk.Label(target, text='X').grid(row=0, column=0, padx=(0, 5))
        self.x_entry = self.entry(target, self.x, 0, 1, 10)
        ttk.Label(target, text='Y').grid(row=0, column=2, padx=(12, 5))
        self.y_entry = self.entry(target, self.y, 0, 3, 10)
        self.pick_button = ttk.Button(target, text='Pick point', command=self.pick)
        self.pick_button.grid(row=0, column=4, padx=(12, 0), sticky='ew')
        self.editors.append(self.pick_button)
        target.columnconfigure(4, weight=1)
        ttk.Label(target, text='Pick point, then click the spot on your screen. Esc cancels.').grid(
            row=1, column=0, columnspan=5, sticky='w', pady=(8, 0))

        pace = self.section(frame, 'Repeat', 3)
        ttk.Label(pace, text='Delay between clicks').grid(row=0, column=0, sticky='w', padx=(0, 12))
        self.interval = tk.StringVar(value='1')
        self.interval_entry = self.entry(pace, self.interval, 0, 1, 10)
        self.unit = tk.StringVar(value='seconds')
        self.unit_box = ttk.Combobox(pace, textvariable=self.unit, values=('seconds', 'minutes', 'milliseconds'),
                                    state='readonly', width=13)
        self.unit_box.grid(row=0, column=2, padx=(8, 0))
        self.editors.append(self.unit_box)

        now = datetime.now()
        start = self.section(frame, 'Start', 4)
        self.start_mode = tk.StringVar(value='delay')
        self.delay = tk.StringVar(value='3')
        self.start_date = tk.StringVar(value=now.strftime('%Y-%m-%d'))
        self.clock = tk.StringVar(value=(now + timedelta(minutes=1)).strftime('%H:%M:%S'))
        self.radio(start, 'After a delay', self.start_mode, 'delay', 0)
        self.delay_entry = self.entry(start, self.delay, 0, 1, 10)
        ttk.Label(start, text='seconds').grid(row=0, column=2, sticky='w', padx=8)
        self.radio(start, 'On date / time', self.start_mode, 'date', 1)
        self.date_entry = self.entry(start, self.start_date, 1, 1, 13)
        self.time_entry = self.entry(start, self.clock, 1, 2, 10)

        stop = self.section(frame, 'Stop', 5)
        self.stop_mode = tk.StringVar(value='count')
        self.count = tk.StringVar(value='1')
        end = now + timedelta(hours=1)
        self.end_date = tk.StringVar(value=end.strftime('%Y-%m-%d'))
        self.end_clock = tk.StringVar(value=end.strftime('%H:%M:%S'))
        self.radio(stop, 'After this many clicks', self.stop_mode, 'count', 0)
        self.count_entry = self.entry(stop, self.count, 0, 1, 10)
        self.radio(stop, 'On date / time', self.stop_mode, 'date', 1)
        self.end_date_entry = self.entry(stop, self.end_date, 1, 1, 13)
        self.end_time_entry = self.entry(stop, self.end_clock, 1, 2, 10)
        ttk.Label(stop, text='Dates: YYYY-MM-DD   Time: HH:MM:SS (24-hour, local)').grid(
            row=2, column=0, columnspan=3, sticky='w', pady=(5, 0))

        self.status = tk.StringVar(value='Ready. One click, or as many as you need.\n\n')
        ttk.Label(frame, textvariable=self.status, wraplength=490, width=56, anchor='w').grid(
            row=6, column=0, columnspan=2, sticky='ew', pady=(8, 12))
        self.start_button = ttk.Button(frame, text='Start clicking', style='Primary.TButton', command=self.schedule)
        self.start_button.grid(row=7, column=0, sticky='ew', padx=(0, 12))
        self.cancel_button = ttk.Button(frame, text='Stop / Cancel (Esc)', command=self.cancel, state='disabled')
        self.cancel_button.grid(row=7, column=1, sticky='ew')
        hint = 'Keep the app open and your session unlocked.'
        if sys.platform == 'linux':
            hint += ' Disable automatic sleep.'
        ttk.Label(frame, text=hint, wraplength=490).grid(
            row=8, column=0, columnspan=2, sticky='w', pady=(8, 0))
        self.start_mode.trace_add('write', lambda *args: self.set_busy(False))
        self.stop_mode.trace_add('write', lambda *args: self.set_busy(False))
        self.set_busy(False)
        root.update_idletasks()
        root.minsize(root.winfo_reqwidth(), root.winfo_reqheight())

    def section(self, parent, title, row):
        section = ttk.LabelFrame(parent, text=title, padding=8)
        section.grid(row=row, column=0, columnspan=2, sticky='ew', pady=(0, 6))
        return section

    def entry(self, parent, variable, row, column, width):
        widget = ttk.Entry(parent, textvariable=variable, width=width)
        widget.grid(row=row, column=column, sticky='ew', pady=1, padx=(0, 6))
        self.editors.append(widget)
        return widget

    def radio(self, parent, text, variable, value, row):
        widget = ttk.Radiobutton(parent, text=text, variable=variable, value=value)
        widget.grid(row=row, column=0, sticky='w', padx=(0, 12), pady=2)
        self.editors.append(widget)

    def set_busy(self, busy):
        for widget in self.editors:
            widget.configure(state='disabled' if busy else 'normal')
        if not busy:
            self.unit_box.configure(state='readonly')
            self.delay_entry.configure(state='normal' if self.start_mode.get() == 'delay' else 'disabled')
            for widget in (self.date_entry, self.time_entry):
                widget.configure(state='normal' if self.start_mode.get() == 'date' else 'disabled')
            self.count_entry.configure(state='normal' if self.stop_mode.get() == 'count' else 'disabled')
            for widget in (self.end_date_entry, self.end_time_entry):
                widget.configure(state='normal' if self.stop_mode.get() == 'date' else 'disabled')
        self.start_button.configure(state='disabled' if busy else 'normal')
        self.cancel_button.configure(state='normal' if busy else 'disabled')

    def screen_bounds(self):
        if sys.platform == 'win32':
            metrics = ctypes.windll.user32.GetSystemMetrics
            return tuple(metrics(i) for i in (76, 77, 78, 79))
        return (self.root.winfo_vrootx(), self.root.winfo_vrooty(),
                self.root.winfo_vrootwidth(), self.root.winfo_vrootheight())

    def valid_point(self, x, y):
        if not (-100000 <= x <= 100000 and -100000 <= y <= 100000):
            return False
        if sys.platform == 'win32':
            from ctypes import wintypes
            return bool(ctypes.windll.user32.MonitorFromPoint(wintypes.POINT(x, y), 0))
        left, top, width, height = self.screen_bounds()
        return left <= x < left + width and top <= y < top + height

    def build_plan(self, now):
        units = {'seconds': 1, 'minutes': 60, 'milliseconds': 0.001}
        interval = read_seconds(self.interval.get(), 'Delay between clicks', units[self.unit.get()], 0.05)
        if self.start_mode.get() == 'delay':
            start = now + timedelta(seconds=read_seconds(self.delay.get(), 'Start delay'))
        else:
            start = read_datetime(self.start_date.get(), self.clock.get(), 'Start')
            if start < now:
                raise ValueError('Start date and time must be in the future.')
        limit, end = None, None
        if self.stop_mode.get() == 'count':
            try:
                limit = int(self.count.get())
            except ValueError:
                raise ValueError('Click count must be a whole number of at least 1.') from None
        else:
            end = read_datetime(self.end_date.get(), self.end_clock.get(), 'End')
        return ClickPlan(start, interval, limit, end)

    def schedule(self):
        if self.run is not None or self.overlay is not None:
            return
        try:
            plan = self.build_plan(datetime.now())
            try:
                point = (int(self.x.get()), int(self.y.get()))
            except ValueError:
                raise ValueError('Enter whole numbers for X and Y, or use Pick point.') from None
            if not self.valid_point(*point):
                raise ValueError('That position is outside your screens. Pick a point again.')
            self.mouse.keep_awake(True)
        except (ValueError, RuntimeError, OSError) as error:
            self.status.set(str(error))
            return
        self.run, self.point = ClickRun(plan), point
        self.set_busy(True)
        self.tick()

    def pick(self):
        if self.run is not None or self.overlay is not None:
            return
        try:
            self.set_busy(True)
            self.status.set('Click the target on your screen. Esc cancels point selection.')
            left, top, width, height = self.screen_bounds()
            overlay = self.overlay = tk.Toplevel(self.root)
            overlay.overrideredirect(True)
            overlay.configure(background='#245DB5', cursor='crosshair')
            overlay.attributes('-topmost', True)
            try:
                overlay.attributes('-alpha', 0.22)
            except tk.TclError:
                pass
            overlay.geometry(f'{width}x{height}{left:+d}{top:+d}')
            overlay.update_idletasks()
            if sys.platform == 'win32':
                from ctypes import wintypes
                user32 = ctypes.windll.user32
                user32.GetParent.restype = wintypes.HWND
                handle = user32.GetParent(wintypes.HWND(overlay.winfo_id())) or overlay.winfo_id()
                user32.SetWindowPos(wintypes.HWND(handle), None, left, top, width, height, 0x14)
            overlay.bind('<ButtonRelease-1>', self.capture_point)
            overlay.bind('<Escape>', lambda event: self.cancel())
            overlay.grab_set()
            overlay.focus_force()
        except (tk.TclError, OSError) as error:
            self.finish(f'Could not open point selection: {error}')

    def capture_point(self, event):
        if self.overlay is None:
            return
        if not self.valid_point(event.x_root, event.y_root):
            return
        self.x.set(str(event.x_root))
        self.y.set(str(event.y_root))
        self.finish(f'Point selected: X={event.x_root}, Y={event.y_root}.')
        return 'break'

    def tick(self):
        self.job = None
        if self.run is None:
            return
        try:
            run = self.run
            now, monotonic = datetime.now(), time.monotonic()
            if run.ready(now, monotonic):
                self.mouse.click(self.point)
                run.record_click(time.monotonic())
            if not run.active:
                self.finish(f'Completed {run.completed} click(s).')
                return
            remaining = math.ceil(run.remaining(datetime.now(), time.monotonic()))
            hours, rest = divmod(remaining, 3600)
            minutes, seconds = divmod(rest, 60)
            total = f' / {run.plan.limit}' if run.plan.limit is not None else ''
            timing = (f'Starts {run.plan.start_at:%Y-%m-%d %H:%M:%S}' if run.completed == 0 else
                      f'Ends {run.plan.end_at:%Y-%m-%d %H:%M:%S}' if run.plan.end_at else
                      f'Clicking at X={self.point[0]}, Y={self.point[1]}')
            self.status.set(f'{run.completed}{total} clicks completed\n'
                            f'Next click in {hours:02}:{minutes:02}:{seconds:02}\n{timing}')
        except Exception as error:
            self.finish(f'Stopped after {self.run.completed} click(s): {error}')
            return
        self.job = self.root.after(50, self.tick)

    def finish(self, message):
        if self.job is not None:
            self.root.after_cancel(self.job)
            self.job = None
        if self.overlay is not None:
            self.overlay.grab_release()
            self.overlay.destroy()
            self.overlay = None
        self.run = None
        self.set_busy(False)
        try:
            self.mouse.keep_awake(False)
        except (RuntimeError, OSError) as error:
            message += f'\n{error}'
        self.status.set(message)

    def cancel(self):
        count = self.run.completed if self.run is not None else 0
        self.finish(f'Cancelled. {count} click(s) completed.')

    def close(self):
        self.cancel()
        self.root.destroy()


def main():
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("SimpleAutoclicker.Desktop")
        # Keep captured and injected coordinates consistent on scaled displays.
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            ctypes.windll.user32.SetProcessDPIAware()
    root = tk.Tk()
    root.withdraw()
    try:
        app = ClickerApp(root, Mouse())
    except Exception as error:
        messagebox.showerror("Simple Autoclicker - setup needed", str(error), parent=root)
        root.destroy()
        return 1
    root.deiconify()
    try:
        root.mainloop()
    finally:
        app.mouse.keep_awake(False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
