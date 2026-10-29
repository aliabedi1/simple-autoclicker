"""Schedule one mouse click on Windows or a Linux X11 desktop."""

import ctypes
from datetime import datetime, timedelta
import math
import os
from pathlib import Path
import sys
import time
import tkinter as tk
from tkinter import messagebox, ttk


def next_click_time(value, now):
    """Resolve a local HH:MM:SS time to its next occurrence."""
    try:
        clock = datetime.strptime(value.strip(), "%H:%M:%S").time()
    except ValueError:
        raise ValueError("Enter a valid time as HH:MM:SS, for example 14:30:00.") from None
    target = datetime.combine(now.date(), clock)
    return target + timedelta(days=1) if target <= now else target


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
        self.root = root
        self.mouse = mouse
        self.target = None
        self.pick_at = None
        self.point = None
        self.job = None
        root.title("Simple Autoclicker")
        assets = Path(__file__).resolve().parent / "assets"
        self.icon = tk.PhotoImage(master=root, file=str(assets / "icon.png"))
        root.iconphoto(True, self.icon)
        if sys.platform == "win32":
            root.iconbitmap(str(assets / "icon.ico"))
        root.configure(background="#F3F6FA")
        root.resizable(True, True)
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.bind("<Escape>", lambda event: self.cancel())

        font = "Segoe UI" if sys.platform == "win32" else "DejaVu Sans"
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TFrame", background="#F3F6FA")
        style.configure("TLabel", background="#F3F6FA", foreground="#20334D", font=(font, 10))
        style.configure("Title.TLabel", font=(font, 19, "bold"))
        style.configure("TButton", font=(font, 10), padding=(12, 8))
        style.configure("Primary.TButton", background="#245DB5", foreground="white")
        style.map("Primary.TButton", background=[("disabled", "#CED7E4"), ("active", "#194A96")])
        style.configure("TEntry", padding=6, font=(font, 11))

        frame = ttk.Frame(root, padding=24)
        frame.grid(sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="One click. Right on time.", style="Title.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(frame, text="Schedule a single left click on your screen.").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(8, 24))
        ttk.Label(frame, text="Click time (24-hour, HH:MM:SS)").grid(
            row=2, column=0, columnspan=2, sticky="w")
        self.clock = tk.StringVar(value=(datetime.now() + timedelta(minutes=1)).strftime("%H:%M:%S"))
        self.time_entry = ttk.Entry(frame, textvariable=self.clock, width=16)
        self.time_entry.grid(row=3, column=0, sticky="ew", pady=(6, 20), padx=(0, 12))
        ttk.Label(frame, text="Screen position X").grid(row=4, column=0, sticky="w")
        ttk.Label(frame, text="Screen position Y").grid(row=4, column=1, sticky="w")
        x, y = mouse.position()
        self.x = tk.StringVar(value=str(x))
        self.y = tk.StringVar(value=str(y))
        self.x_entry = ttk.Entry(frame, textvariable=self.x, width=16)
        self.y_entry = ttk.Entry(frame, textvariable=self.y, width=16)
        self.x_entry.grid(row=5, column=0, sticky="ew", pady=(6, 14), padx=(0, 12))
        self.y_entry.grid(row=5, column=1, sticky="ew", pady=(6, 14))
        self.pick_button = ttk.Button(frame, text="Pick position in 3 seconds", command=self.pick)
        self.pick_button.grid(row=6, column=0, columnspan=2, sticky="ew")
        self.status = tk.StringVar(value="Ready. Past times are scheduled for tomorrow.")
        ttk.Label(frame, textvariable=self.status, wraplength=410).grid(
            row=7, column=0, columnspan=2, sticky="ew", pady=(18, 8))
        hint = "Keep this window open and your session unlocked."
        if sys.platform == "linux":
            hint += " Disable automatic sleep while waiting."
        ttk.Label(frame, text=hint, wraplength=410).grid(
            row=8, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        self.start_button = ttk.Button(frame, text="Schedule click", style="Primary.TButton", command=self.schedule)
        self.start_button.grid(row=9, column=0, sticky="ew", padx=(0, 12))
        self.cancel_button = ttk.Button(frame, text="Cancel (Esc)", command=self.cancel, state="disabled")
        self.cancel_button.grid(row=9, column=1, sticky="ew")
        root.update_idletasks()
        root.minsize(root.winfo_reqwidth(), root.winfo_reqheight())
        self.time_entry.focus_set()

    def set_busy(self, busy):
        for widget in (self.time_entry, self.x_entry, self.y_entry, self.pick_button, self.start_button):
            widget.configure(state="disabled" if busy else "normal")
        self.cancel_button.configure(state="normal" if busy else "disabled")

    def valid_point(self, x, y):
        if not (-100000 <= x <= 100000 and -100000 <= y <= 100000):
            return False
        if sys.platform == "win32":
            from ctypes import wintypes
            return bool(ctypes.windll.user32.MonitorFromPoint(wintypes.POINT(x, y), 0))
        left, top = self.root.winfo_vrootx(), self.root.winfo_vrooty()
        return (left <= x < left + self.root.winfo_vrootwidth()
                and top <= y < top + self.root.winfo_vrootheight())

    def schedule(self):
        if self.target is not None or self.pick_at is not None:
            return
        try:
            target = next_click_time(self.clock.get(), datetime.now())
            try:
                point = (int(self.x.get()), int(self.y.get()))
            except ValueError:
                raise ValueError("Enter whole numbers for X and Y, or use Pick position.") from None
            if not self.valid_point(*point):
                raise ValueError("That position is outside your screens. Pick a position again.")
            self.mouse.keep_awake(True)
        except (ValueError, RuntimeError, OSError) as error:
            self.status.set(str(error))
            return
        self.target, self.point = target, point
        self.set_busy(True)
        self.tick()

    def pick(self):
        if self.target is not None or self.pick_at is not None:
            return
        self.pick_at = time.monotonic() + 3
        self.set_busy(True)
        self.tick()

    def tick(self):
        self.job = None
        try:
            if self.pick_at is not None:
                remaining = self.pick_at - time.monotonic()
                if remaining <= 0:
                    x, y = self.mouse.position()
                    self.x.set(str(x))
                    self.y.set(str(y))
                    self.finish(f"Position captured: X={x}, Y={y}.")
                    return
                self.status.set(f"Move your pointer to the target. Capturing in {math.ceil(remaining)} seconds...")
            elif self.target is not None:
                now = datetime.now()
                if now >= self.target:
                    # Disarm first: later UI events must never repeat the click.
                    self.target = None
                    self.mouse.click(self.point)
                    self.finish(f"Click completed at {now:%H:%M:%S}.")
                    return
                seconds = math.ceil((self.target - now).total_seconds())
                hours, rest = divmod(seconds, 3600)
                minutes, seconds = divmod(rest, 60)
                self.status.set(f"Click at {self.target:%a, %b %d %H:%M:%S}\n"
                                f"{hours:02}:{minutes:02}:{seconds:02} remaining")
            else:
                return
        except Exception as error:
            self.finish(f"Could not complete the action: {error}")
            return
        self.job = self.root.after(50, self.tick)

    def finish(self, message):
        if self.job is not None:
            self.root.after_cancel(self.job)
            self.job = None
        self.target = None
        self.pick_at = None
        self.set_busy(False)
        try:
            self.mouse.keep_awake(False)
        except (RuntimeError, OSError) as error:
            message += f"\n{error}"
        self.status.set(message)

    def cancel(self):
        self.finish("Cancelled. Ready for a new schedule.")

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
