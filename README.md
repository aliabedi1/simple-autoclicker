# Simple Autoclicker

<img src="assets/icon.png" alt="Simple Autoclicker: a mouse pointer with a golden clock on a blue tile" width="96" height="96">

A simple desktop interface for scheduling mouse clicks, keyboard keys, shortcuts, and mixed action patterns on **Windows or Linux (X11)**. Uses a local shadcn/ui interface connected to Python 3.10+, Tkinter, and pynput. The interface opens in your browser and follows the system light/dark theme. No cloud service or Node.js installation is needed to run the bundled app.

## Install the app

Download the first public release from [GitHub Releases](https://github.com/aliabedi1/simple-autoclicker/releases/latest). Packaged builds include Python and the interface; you do not need Python or Node.js installed.

### Windows x64

Run `SimpleAutoclicker-0.1.0-windows-x64-setup.exe`. It installs for your user account, adds a Start menu entry, offers a desktop shortcut, and includes an uninstaller. Windows packages are unsigned. The portable ZIP is an alternative: extract the entire folder and run `SimpleAutoclicker.exe`.

### Linux x64

Ubuntu 22.04+/Debian 12+: download the `.deb`, then run:

```sh
sudo apt install ./SimpleAutoclicker-0.1.0-linux-amd64.deb
```

Open **Simple Autoclicker** in your applications menu or run `simple-autoclicker`. Uninstall with `sudo apt remove simple-autoclicker`.

Other distributions can extract the `.tar.gz` and run `./SimpleAutoclicker/SimpleAutoclicker`. Requires glibc 2.35+, an X11/Xorg desktop, X11/XTest/Xi/Xss, fontconfig/freetype, and `xdg-open` from xdg-utils. Wayland is unsupported. Disable automatic sleep on Linux while waiting.

`SHA256SUMS.txt` accompanies each release. On Linux use `sha256sum -c SHA256SUMS.txt` alongside the downloaded packages, or compare a Windows download using `Get-FileHash -Algorithm SHA256 <file>`.

## Run from source on Windows

Install Python from [python.org](https://www.python.org/downloads/windows/) with the Python launcher and Tcl/Tk components enabled. In a terminal opened in this folder, run once:

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Then double-click **Start Clicker.cmd**.

## Run from source on Linux

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
2. Choose **Single action**, then select **Left click**, **Right click**, **Middle click**, or **Keyboard key**. For mouse actions, enter X/Y or use **Pick a point on screen**. For keyboard actions, enter the key or shortcut.
3. Choose the wait between actions and its unit. Minimum wait: 50 milliseconds.
4. Under **Schedule**, choose a start delay or a start date/time, and an action count or end date/time.
5. Choose **Start actions**. Progress and the next click appear beside the run controls.
6. Choose **Stop**, or press **Esc while the browser tab is focused**, to cancel.
7. Choose **Quit app** to stop clicking and close the desktop process. You can then close the browser tab. Closing a browser tab by itself does **not** stop the desktop process or its scheduled run.

The header theme button cycles between system, light, and dark. System is the default and updates when your OS theme changes.

### Click patterns

Choose **Click pattern** to build a sequence in the same screen:

1. Choose **Add first step** or **Add step**.
2. Select the step action. For a mouse click, enter X/Y or choose **Pick a point on screen**. For a keyboard step, enter its key or shortcut.
3. Set **Wait after action, in seconds**, then choose **Add step**.
4. Use each row's edit, move up/down, and remove buttons to arrange the sequence.
5. Set the number of **cycles** or an end date, then choose **Start actions**.

Each step performs one mouse click or one key/shortcut press and release. Its delay is the wait before the next step; the last step's delay separates cycles. A cycle runs the full list once: **3 steps x 2 cycles = 6 actions**. An end date can stop the sequence partway through a cycle.

**Save** downloads a version 2 JSON pattern file containing each step’s action and key. **Load** accepts version 1 and version 2 files. Older version 1 steps default to left click. Coordinates are absolute screen positions, so check loaded patterns after changing monitors or display scaling. The interface supports up to 1000 steps per pattern.

### Keyboard keys and shortcuts

Choose **Keyboard key** and enter a single character, `enter`, `space`, `tab`, `esc`, `backspace`, `delete`, `insert`, `home`, `end`, `page_up`, `page_down`, `up`, `down`, `left`, `right`, `caps_lock`, or `f1` through `f24`. Shortcuts join modifiers with `+`, for example `ctrl+a`, `ctrl+shift+s`, or `alt+tab`. Supported modifiers are `ctrl`, `alt`, `shift`, and `cmd` (Windows/Super); `win`, `windows`, `super`, `control`, and `escape` aliases are accepted. Use `plus` for the literal plus key, such as `ctrl+plus`. Names are case-insensitive; use `shift+a` for an uppercase letter.

Keyboard actions send a press and release to the **currently focused application**. They do not move the pointer or automatically focus a window. Use the start delay to switch to the intended application, or put a mouse-click step before the keyboard step to focus the target. For example: left-click a text field, wait 0.2 seconds, then press `ctrl+a`. Count limits count whole actions; a shortcut counts as one action. Pressed keys are released even if a shortcut fails.

Dates use **YYYY-MM-DD**, and times use **HH:MM:SS** in your computer's local 24-hour clock. An explicit start date must be in the future; an end date must be later than the start. No actions start once the end time is reached, even if the next click would otherwise be due.

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

## Build installers

Build on the target OS; PyInstaller cannot cross-compile. Install Python build dependencies with `python -m pip install -r requirements-build.txt`, build the frontend, then run:

```sh
python scripts/build.py
```

This writes the self-contained app to `dist/SimpleAutoclicker/`. On Windows, compile `packaging/windows.iss` with Inno Setup. On Linux, run `python scripts/package_linux.py` to create the `.deb` and portable `.tar.gz`. Use the packaged binary's `--smoke-test` flag to validate the interface, icon, Tk, and native input backends without emitting input or opening a browser.

The **Build installers** GitHub Actions workflow builds and tests the frontend, runs Python tests on Windows and Linux, creates packages, and tests installation/removal. Run it with **Create a draft release** enabled to assemble the version from `app_version.py` and `RELEASE_NOTES.md`. It creates a draft only after both platforms pass; verify checksums and assets before publishing. Build tools and bundled dependency license notices are preserved with each package.
