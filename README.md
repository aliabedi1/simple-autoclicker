# Simple Autoclicker

<img src="assets/icon.png" alt="Simple Autoclicker: a mouse pointer with a golden clock on a blue tile" width="96" height="96">

A simple desktop interface for scheduling single or repeated left mouse clicks on **Windows or Linux (X11)**. Uses Python 3.10+, Tkinter, and pynput.

## Windows

Install Python from [python.org](https://www.python.org/downloads/windows/) with the Python launcher and Tcl/Tk components enabled. In a terminal opened in this folder, run once:

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Then double-click **Start Clicker.cmd**.

## Linux

Use an **X11/Xorg desktop session**. Wayland is not supported: log out and choose an X11/Xorg session from your login screen if available. The app detects Wayland and explains this requirement instead of silently failing to click other applications. See [pynput's platform limitations](https://pynput.readthedocs.io/en/latest/limitations.html).

On Ubuntu/Debian, install Python, Tkinter, and venv:

```sh
sudo apt install python3 python3-tk python3-venv
```

On other distributions, install the equivalent Python 3, Tkinter, and venv packages using your package manager. Then, in this project folder:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
sh start-clicker.sh
```

Run from your desktop, with your session unlocked. Disable automatic sleep while waiting on Linux. No root access is needed to run the app.

## Use

1. Choose **Pick point**, then click the exact target on your screen. The crosshair overlay captures your selection without clicking the underlying application. You can also enter X and Y manually. Press **Esc** to cancel selection.
2. Set the **delay between clicks** in seconds, minutes, or milliseconds (minimum 50 milliseconds). Each repetition is one left click.
3. Choose when to **Start**: after a delay (default 3 seconds), or on a specific date and time.
4. Choose when to **Stop**: after a total click count, or on a specific end date and time. A count of **1** keeps the original single-click behavior.
5. Select **Start clicking**. The status shows clicks completed and time until the next click.
6. Select **Stop / Cancel**, press **Esc while the app is focused**, or close the window to stop.

Dates use **YYYY-MM-DD**, and times use **HH:MM:SS** in your computer's local 24-hour clock. An explicit start date must be in the future; an end date must be later than the start. No clicks start once the end time is reached, even if the next click would otherwise be due.

For example: pick a point, set the interval to **2 seconds**, start **after 5 seconds**, and stop **after 10 clicks**. Or schedule a start for tomorrow at **09:00:00**, click every **1 minute**, and stop tomorrow at **10:00:00**.

Keep the app open, the target visible, and your session unlocked. Windows sleep prevention is enabled while a run is scheduled, then restored on cancellation, completion, or exit. On Linux, disable automatic sleep manually. The delay is measured after each completed click; a late timer or resume from sleep does not trigger a burst of missed clicks. Timing depends on OS scheduling and is not guaranteed to be exact.

The original Windows-only PowerShell versions remain available as `clicker.ps1` (console) and `clicker-ui.ps1` (native UI). These legacy versions perform a single click. Use the Windows or Linux launcher for the shared Python interface and repetition features.

## Tests

```sh
python -m unittest discover -s tests -v
```

UI tests need a graphical desktop. For a headless Linux X11 test environment with Xvfb installed, use `xvfb-run -a python -m unittest discover -s tests -v`.
