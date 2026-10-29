# Simple Autoclicker

<img src="assets/icon.png" alt="Simple Autoclicker: a mouse pointer with a golden clock on a blue tile" width="96" height="96">

A simple desktop interface for scheduling single clicks, repeated clicks, or multi-point click patterns on **Windows or Linux (X11)**. Uses a local shadcn/ui interface connected to Python 3.10+, Tkinter, and pynput. The interface opens in your browser and follows the system light/dark theme. No cloud service or Node.js installation is needed to run the bundled app.

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

1. Open **Start Clicker.cmd** on Windows or run **sh start-clicker.sh** on Linux. The launcher starts the local desktop process and opens the interface in your default browser.
2. Choose **Single point**. Enter X/Y or choose **Pick a point on screen**, then click the target in the crosshair overlay. Esc cancels the overlay.
3. Choose the wait between clicks and its unit. Minimum wait: 50 milliseconds.
4. Under **Schedule**, choose a start delay or a start date/time, and a click count or end date/time.
5. Choose **Start clicking**. Progress and the next click appear beside the run controls.
6. Choose **Stop**, or press **Esc while the browser tab is focused**, to cancel.
7. Choose **Quit app** to stop clicking and close the desktop process. You can then close the browser tab. Closing a browser tab by itself does **not** stop the desktop process or its scheduled run.

The header theme button cycles between system, light, and dark. System is the default and updates when your OS theme changes.

### Click patterns

Choose **Click pattern** to build a sequence in the same screen:

1. Choose **Add first step** or **Add step**.
2. Enter X/Y or choose **Pick a point on screen** in the step dialog.
3. Set **Wait after click, in seconds**, then choose **Add step**.
4. Use each row's edit, move up/down, and remove buttons to arrange the sequence.
5. Set the number of **cycles** or an end date, then choose **Start clicking**.

Each step performs one left click. Its delay is the wait before the next step; the last step's delay separates cycles. A cycle runs the full list once: **3 steps x 2 cycles = 6 clicks**. An end date can stop the sequence partway through a cycle.

**Save** downloads a version 1 JSON pattern file. **Load** opens one. Existing pattern files from the native interface are compatible. Coordinates are absolute screen positions, so check loaded patterns after changing monitors or display scaling. The interface supports up to 1000 steps per pattern.

Dates use **YYYY-MM-DD**, and times use **HH:MM:SS** in your computer's local 24-hour clock. An explicit start date must be in the future; an end date must be later than the start. No clicks start once the end time is reached, even if the next click would otherwise be due.

For example: pick a point, set the interval to **2 seconds**, start **after 5 seconds**, and stop **after 10 clicks**. Or schedule a start for tomorrow at **09:00:00**, click every **1 minute**, and stop tomorrow at **10:00:00**.

Keep the desktop process running, the target visible, and your session unlocked. Windows sleep prevention is enabled while a run is scheduled, then restored on cancellation, completion, or exit. On Linux, disable automatic sleep manually. The delay is measured after each completed click; a late timer or resume from sleep does not trigger a burst of missed clicks. Timing depends on OS scheduling and is not guaranteed to be exact.

The original Windows-only PowerShell versions remain available as `clicker.ps1` (console) and `clicker-ui.ps1` (native UI). These legacy versions perform a single click. The original native Python interface is also available with `python autoclicker.py`. Use the Windows or Linux launcher for the redesigned browser interface.

## Tests

```sh
python -m unittest discover -s tests -v
```

UI tests need a graphical desktop. For a headless Linux X11 test environment with Xvfb installed, use `xvfb-run -a python -m unittest discover -s tests -v`.

## Develop the interface

The React + TypeScript frontend lives in `web/` and uses actual shadcn/ui Radix components, Tailwind CSS, and bundled Geist fonts. Production files in `web/dist/` are committed so end users only need Python. After changing the frontend, rebuild and commit its output:

```sh
cd web
npm ci
npm run build
npm run lint
npx playwright test
```

Frontend development needs a Node.js version supported by the checked-in Vite version. Browser tests use installed Chrome and a fake mouse backend, exercising real local API calls and UI timers without injecting clicks into other applications. Install Python dependencies into the project's `.venv` first. On headless Linux, run the tests under Xvfb. The older native tests remain available through `python -m unittest discover -s tests -v`.

`desktop.py` binds to a random port on `127.0.0.1` only. API actions require a per-launch token and reject foreign origins. The interface and fonts are served locally. Browser errors such as missing setup or expired sessions direct you back to the launcher.
