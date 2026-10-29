# Simple Autoclicker

<img src="assets/icon.png" alt="Simple Autoclicker: a mouse pointer with a golden clock on a blue tile" width="96" height="96">

A simple desktop interface for scheduling one left mouse click on **Windows or Linux (X11)**. Uses Python 3.10+, Tkinter, and pynput.

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

1. Enter the click time as **HH:MM:SS** using the local 24-hour clock.
2. Enter screen coordinates, or choose **Pick position in 3 seconds** and move your pointer to the target.
3. Choose **Schedule click**. The countdown shows the scheduled date and time.
4. **Cancel**, **Esc**, or closing the window cancels the pending click or position capture.

Times that have already passed run tomorrow. Keep the window open and the target visible. Windows sleep prevention is enabled only while a click is scheduled, then restored on cancellation, completion, or exit. The app clicks once and does not repeat daily. Timing depends on OS scheduling and is not guaranteed to be exact.

The original Windows-only PowerShell versions remain available as `clicker.ps1` (console) and `clicker-ui.ps1` (native UI). The Windows and Linux launchers both use the shared Python interface.

## Tests

```sh
python -m unittest discover -s tests -v
```

UI tests need a graphical desktop. For a headless Linux X11 test environment with Xvfb installed, use `xvfb-run -a python -m unittest discover -s tests -v`.
