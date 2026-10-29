"""Schedule repeated mouse clicks on Windows or a Linux X11 desktop."""

import ctypes
from datetime import datetime, timedelta
import math
import json
import os
from pathlib import Path
import sys
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from schedule import ClickPlan, ClickRun, ClickStep, parse_keys, validate_action, read_datetime, read_seconds


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
            from pynput.keyboard import Key, Controller as KeyboardController
        except ImportError as error:
            raise RuntimeError(
                "Mouse control is unavailable. Install the dependencies with:\n"
                "python -m pip install -r requirements.txt\n\n" + str(error)
            ) from error
        self.controller = Controller()
        self.left = Button.left
        self.buttons = {'left': Button.left, 'right': Button.right, 'middle': Button.middle}
        self.keyboard = KeyboardController()
        self.key_enum = Key

    def position(self):
        return self.controller.position

    def click(self, point):
        self.perform(point)

    def perform(self, point, action='left', key=''):
        validate_action(action, key)
        if action == 'key':
            keys = [getattr(self.key_enum, name) if len(name) > 1 else name for name in parse_keys(key)]
            pressed = []
            try:
                for button in keys:
                    # Track before pressing so failures still attempt a release.
                    pressed.append(button)
                    self.keyboard.press(button)
            finally:
                first_error = None
                for button in reversed(pressed):
                    try:
                        self.keyboard.release(button)
                    except Exception as error:
                        first_error = first_error or error
                if first_error is not None:
                    raise first_error
            return
        self.controller.position = point
        if tuple(self.controller.position) != tuple(point):
            raise RuntimeError("Could not reach that screen position. Pick a new position.")
        self.controller.click(self.buttons[action])

    def keep_awake(self, enabled):
        if sys.platform == "win32":
            flags = 0x80000003 if enabled else 0x80000000
            if not ctypes.windll.kernel32.SetThreadExecutionState(flags):
                raise RuntimeError("Could not update sleep prevention. Check your power settings.")


class ClickerApp:
    def __init__(self, root, mouse):
        self.root, self.mouse = root, mouse
        self.run = None
        self.last_completed = 0
        self.point = None
        self.job = None
        self.overlay = None
        self.pattern = ()
        self.pattern_editor = None
        self.pick_callback = None
        self.editors = []
        self.action = tk.StringVar(master=root, value='left')
        self.key = tk.StringVar(master=root, value='enter')
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
        self.target_mode = tk.StringVar(value='single')
        modes = ttk.Frame(target)
        modes.grid(row=0, column=0, columnspan=5, sticky='ew', pady=(0, 6))
        self.radio(modes, 'Single point', self.target_mode, 'single', 0)
        pattern_radio = ttk.Radiobutton(modes, text='Pattern', variable=self.target_mode, value='pattern')
        pattern_radio.grid(row=0, column=1, padx=(0, 12))
        self.editors.append(pattern_radio)
        self.pattern_button = ttk.Button(modes, text='Edit pattern...', command=self.edit_pattern)
        self.pattern_button.grid(row=0, column=2)
        self.editors.append(self.pattern_button)
        x, y = mouse.position()
        self.x, self.y = tk.StringVar(value=str(x)), tk.StringVar(value=str(y))
        ttk.Label(target, text='X').grid(row=1, column=0, padx=(0, 5))
        self.x_entry = self.entry(target, self.x, 1, 1, 10)
        ttk.Label(target, text='Y').grid(row=1, column=2, padx=(12, 5))
        self.y_entry = self.entry(target, self.y, 1, 3, 10)
        self.pick_button = ttk.Button(target, text='Pick point', command=self.pick)
        self.pick_button.grid(row=1, column=4, padx=(12, 0), sticky='ew')
        self.editors.append(self.pick_button)
        target.columnconfigure(4, weight=1)
        self.target_hint = tk.StringVar(value='Pick point, then click the spot on your screen. Esc cancels.')
        ttk.Label(target, textvariable=self.target_hint).grid(
            row=2, column=0, columnspan=5, sticky='w', pady=(8, 0))
        self.action_box = ttk.Combobox(target, textvariable=self.action, values=('left', 'right', 'middle', 'key'),
                                      state='readonly', width=13)
        self.action_box.grid(row=3, column=0, columnspan=2, sticky='ew', pady=(6, 0))
        self.key_entry = self.entry(target, self.key, 3, 3, 12)
        self.editors.extend((self.action_box,))
        ttk.Label(target, text='Key / shortcut').grid(row=3, column=2, padx=6)

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
        self.count_label = tk.StringVar(value='After this many actions')
        count_radio = ttk.Radiobutton(stop, textvariable=self.count_label, variable=self.stop_mode, value='count')
        count_radio.grid(row=0, column=0, sticky='w', padx=(0, 12), pady=2)
        self.editors.append(count_radio)
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
        self.target_mode.trace_add('write', lambda *args: self.set_busy(False))
        self.action.trace_add('write', lambda *args: self.set_busy(False))
        self.set_busy(False)
        root.update_idletasks()
        root.minsize(root.winfo_reqwidth(), root.winfo_reqheight())

    def section(self, parent, title, row):
        section = ttk.LabelFrame(parent, text=title, padding=(8, 5))
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
            pattern_mode = self.target_mode.get() == 'pattern'
            for widget in (self.x_entry, self.y_entry, self.pick_button, self.interval_entry, self.unit_box):
                widget.configure(state='disabled' if pattern_mode else 'normal')
            if not pattern_mode:
                self.unit_box.configure(state='readonly')
            self.action_box.configure(state='disabled' if pattern_mode else 'readonly')
            self.key_entry.configure(state='normal' if not pattern_mode and self.action.get() == 'key' else 'disabled')
            if self.action.get() == 'key':
                for widget in (self.x_entry, self.y_entry, self.pick_button):
                    widget.configure(state='disabled')
            self.count_label.set('After this many cycles' if pattern_mode else 'After this many actions')
            self.target_hint.set(f'{len(self.pattern)} steps. Edit pattern to add or reorder points.' if pattern_mode else
                                 'Pick point, then click the spot on your screen. Esc cancels.')
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

    def edit_pattern(self):
        if self.run is not None or self.overlay is not None:
            return
        if self.pattern_editor is not None:
            self.pattern_editor.window.lift()
            return
        self.pattern_editor = PatternEditor(self)

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
        pattern = self.pattern if self.target_mode.get() == 'pattern' else ()
        if self.target_mode.get() == 'pattern' and not pattern:
            raise ValueError('Add at least one step with Edit pattern first.')
        interval = pattern[0].delay if pattern else read_seconds(
            self.interval.get(), 'Delay between clicks', units[self.unit.get()], 0.05)
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
            if pattern:
                limit *= len(pattern)
        else:
            end = read_datetime(self.end_date.get(), self.end_clock.get(), 'End')
        return ClickPlan(start, interval, limit, end, pattern,
                         'left' if pattern else self.action.get(), '' if pattern else self.key.get())

    def schedule(self):
        if self.run is not None or self.overlay is not None:
            return
        try:
            plan = self.build_plan(datetime.now())
            if plan.pattern:
                point = plan.pattern[0].point
                for index, step in enumerate(plan.pattern, 1):
                    if step.action != 'key' and not self.valid_point(*step.point):
                        raise ValueError(f'Pattern step {index} is outside your screens. Edit that point.')
            elif plan.action == 'key':
                point = (0, 0)
            else:
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
        self.last_completed = 0
        self.set_busy(True)
        self.tick()

    def pick(self, callback=None):
        if self.run is not None or self.overlay is not None:
            return
        try:
            self.pick_callback = callback
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
        if self.pick_callback is not None:
            self.pick_callback(event.x_root, event.y_root)
        else:
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
                step = run.current_step
                self.point = step.point if step is not None else self.point
                action = step.action if step is not None else run.plan.action
                key = step.key if step is not None else run.plan.key
                self.mouse.perform(self.point, action, key)
                run.record_click(time.monotonic())
                self.last_completed = run.completed
            if not run.active:
                self.finish(f'Completed {run.completed} action(s).')
                return
            remaining = math.ceil(run.remaining(datetime.now(), time.monotonic()))
            hours, rest = divmod(remaining, 3600)
            minutes, seconds = divmod(rest, 60)
            total = f' / {run.plan.limit}' if run.plan.limit is not None else ''
            timing = (f'Starts {run.plan.start_at:%Y-%m-%d %H:%M:%S}' if run.completed == 0 else
                      f'Ends {run.plan.end_at:%Y-%m-%d %H:%M:%S}' if run.plan.end_at else
                      f'Clicking at X={self.point[0]}, Y={self.point[1]}')
            self.status.set(f'{run.completed}{total} actions completed\n'
                            f'Next click in {hours:02}:{minutes:02}:{seconds:02}\n{timing}')
            if run.plan.pattern:
                size = len(run.plan.pattern)
                self.status.set(f'{run.completed}{total} actions | {run.completed // size} cycles completed\n'
                                f'Next: step {run.completed % size + 1} / {size} in {hours:02}:{minutes:02}:{seconds:02}\n{timing}')
        except Exception as error:
            self.finish(f'Stopped after {self.run.completed} action(s): {error}')
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
        self.pick_callback = None
        self.set_busy(False)
        try:
            self.mouse.keep_awake(False)
        except (RuntimeError, OSError) as error:
            message += f'\n{error}'
        self.status.set(message)
        if self.pattern_editor is not None:
            self.pattern_editor.window.grab_set()
            self.pattern_editor.window.focus_force()

    def cancel(self):
        count = self.run.completed if self.run is not None else 0
        self.finish(f'Cancelled. {count} action(s) completed.')

    def close(self):
        if self.pattern_editor is not None:
            self.pattern_editor.close()
        self.cancel()
        self.root.destroy()


class PatternEditor:
    def __init__(self, app):
        self.app = app
        self.steps = list(app.pattern)
        self.window = tk.Toplevel(app.root)
        self.window.title('Click pattern')
        self.window.transient(app.root)
        self.window.protocol('WM_DELETE_WINDOW', self.close)
        self.window.bind('<Escape>', lambda event: self.close())
        frame = ttk.Frame(self.window, padding=14)
        frame.grid(sticky='nsew')
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        ttk.Label(frame, text='Build your click sequence', style='Title.TLabel').grid(row=0, sticky='w', pady=(0, 10))
        self.tree = ttk.Treeview(frame, columns=('step', 'x', 'y', 'delay', 'action'), show='headings', height=6,
                                 selectmode='browse')
        for name, title, width in (('step', 'Step', 55), ('x', 'X', 95), ('y', 'Y', 95),
                                   ('delay', 'Wait after (s)', 130), ('action', 'Action', 120)):
            self.tree.heading(name, text=title)
            self.tree.column(name, width=width, minwidth=45, anchor='center')
        self.tree.grid(row=1, sticky='nsew')
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=self.tree.yview)
        scrollbar.grid(row=1, column=1, sticky='ns')
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind('<<TreeviewSelect>>', self.selected)
        tools = ttk.Frame(frame)
        tools.grid(row=2, sticky='ew', pady=(6, 10))
        for column, (label, command) in enumerate((('Move up', lambda: self.move(-1)),
                                                  ('Move down', lambda: self.move(1)), ('Remove', self.remove))):
            ttk.Button(tools, text=label, command=command).grid(row=0, column=column, padx=(0, 6))
        fields = ttk.Frame(frame)
        fields.grid(row=3, sticky='ew')
        self.x = tk.StringVar(value=app.x.get())
        self.y = tk.StringVar(value=app.y.get())
        self.delay = tk.StringVar(value='1')
        self.action = tk.StringVar(value='left')
        self.key = tk.StringVar(value='enter')
        for column, (label, variable) in enumerate((('X', self.x), ('Y', self.y), ('Wait after (seconds)', self.delay))):
            ttk.Label(fields, text=label).grid(row=0, column=column, sticky='w')
            ttk.Entry(fields, textvariable=variable, width=16).grid(row=1, column=column, padx=(0, 8), sticky='ew')
            fields.columnconfigure(column, weight=1)
        ttk.Combobox(fields, textvariable=self.action, values=('left', 'right', 'middle', 'key'),
                     state='readonly', width=16).grid(row=2, column=0, sticky='ew', pady=8)
        ttk.Label(fields, text='Key / shortcut').grid(row=2, column=1)
        ttk.Entry(fields, textvariable=self.key, width=16).grid(row=2, column=2, sticky='ew')
        actions = ttk.Frame(frame)
        actions.grid(row=4, sticky='ew', pady=10)
        for column, (label, command) in enumerate((('Pick point', self.pick), ('Add step', self.add),
                                                  ('Update selected', self.update))):
            ttk.Button(actions, text=label, command=command).grid(row=0, column=column, padx=(0, 6))
        self.status = tk.StringVar(value='Each cycle runs top to bottom. The last delay separates cycles.')
        ttk.Label(frame, textvariable=self.status, wraplength=470).grid(row=5, sticky='ew', pady=(0, 10))
        footer = ttk.Frame(frame)
        footer.grid(row=6, sticky='ew')
        for column, (label, command) in enumerate((('Load...', self.load), ('Save...', self.save),
                                                  ('Use pattern', self.apply), ('Cancel', self.close))):
            ttk.Button(footer, text=label, command=command).grid(row=0, column=column, padx=(0, 6))
        self.refresh()
        self.window.update_idletasks()
        self.window.minsize(self.window.winfo_reqwidth(), self.window.winfo_reqheight())
        self.window.grab_set()

    def refresh(self, selection=None):
        self.tree.delete(*self.tree.get_children())
        for index, step in enumerate(self.steps):
            self.tree.insert('', 'end', iid=str(index), values=(index + 1, step.x, step.y, f'{step.delay:g}',
                                                              step.key if step.action == 'key' else step.action))
        if selection is not None and 0 <= selection < len(self.steps):
            self.tree.selection_set(str(selection))
            self.tree.see(str(selection))

    def index(self):
        selection = self.tree.selection()
        if not selection:
            self.status.set('Select a step in the list first.')
            return None
        return int(selection[0])

    def selected(self, event=None):
        selection = self.tree.selection()
        if selection:
            step = self.steps[int(selection[0])]
            self.x.set(str(step.x))
            self.y.set(str(step.y))
            self.delay.set(f'{step.delay:g}')
            self.action.set(step.action)
            self.key.set(step.key)

    def read_step(self):
        if self.action.get() == 'key':
            return ClickStep(0, 0, read_seconds(self.delay.get(), 'Step delay', minimum=0.05), 'key', self.key.get())
        try:
            x, y = int(self.x.get()), int(self.y.get())
        except ValueError:
            raise ValueError('Enter whole numbers for X and Y.') from None
        if not self.app.valid_point(x, y):
            raise ValueError('That point is outside your screens. Pick it again.')
        return ClickStep(x, y, read_seconds(self.delay.get(), 'Step delay', minimum=0.05), self.action.get(), '')

    def add(self):
        try:
            step = self.read_step()
        except ValueError as error:
            self.status.set(str(error))
            return
        self.steps.append(step)
        self.refresh(len(self.steps) - 1)
        self.status.set(f'Added step {len(self.steps)}. Pick another point to add the next step.')

    def update(self):
        index = self.index()
        if index is None:
            return
        try:
            self.steps[index] = self.read_step()
        except ValueError as error:
            self.status.set(str(error))
            return
        self.refresh(index)
        self.status.set(f'Updated step {index + 1}.')

    def move(self, offset):
        index = self.index()
        if index is not None and 0 <= index + offset < len(self.steps):
            self.steps[index], self.steps[index + offset] = self.steps[index + offset], self.steps[index]
            self.refresh(index + offset)

    def remove(self):
        index = self.index()
        if index is not None:
            del self.steps[index]
            self.refresh(min(index, len(self.steps) - 1))

    def pick(self):
        self.app.pick(lambda x, y: (self.x.set(str(x)), self.y.set(str(y))))

    def apply(self):
        if not self.steps:
            self.status.set('Add at least one step before using this pattern.')
            return
        self.app.pattern = tuple(self.steps)
        self.app.target_mode.set('pattern')
        self.app.status.set(f'Pattern ready: {len(self.steps)} steps. Set the cycle count, then start.')
        self.close()

    def save(self):
        if not self.steps:
            self.status.set('Add at least one step before saving.')
            return
        path = filedialog.asksaveasfilename(parent=self.window, defaultextension='.json',
                                           filetypes=[('Click patterns', '*.json')])
        if path:
            try:
                data = {'version': 2, 'steps': [dict(x=s.x, y=s.y, delay=s.delay, action=s.action, key=s.key) for s in self.steps]}
                Path(path).write_text(json.dumps(data, indent=2), encoding='utf-8')
                self.status.set('Pattern saved.')
            except OSError as error:
                self.status.set(f'Could not save: {error}')

    def load(self):
        path = filedialog.askopenfilename(parent=self.window, filetypes=[('Click patterns', '*.json')])
        if path:
            try:
                data = json.loads(Path(path).read_text(encoding='utf-8'))
                if not isinstance(data, dict) or data.get('version') not in (1, 2) or not isinstance(data.get('steps'), list):
                    raise ValueError('Choose a version 1 or 2 pattern JSON file.')
                steps = [ClickStep(**step) for step in data['steps']]
                if not steps:
                    raise ValueError('The pattern contains no steps.')
                self.steps = steps
                self.refresh(0)
                self.status.set('Pattern loaded. Check the points before choosing Use pattern.')
            except (OSError, ValueError, TypeError, OverflowError) as error:
                self.status.set(f'Could not load: {error}')

    def close(self):
        if self.app.overlay is not None:
            self.app.cancel()
        self.window.grab_release()
        self.window.destroy()
        self.app.pattern_editor = None


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
