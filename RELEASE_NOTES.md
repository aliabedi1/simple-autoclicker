# Simple Autoclicker v0.1.0

First public release, with self-contained packages for Windows x64 and Linux x64.
Python and Node.js are not required on the destination computer.

- Left, right, and middle mouse clicks, keyboard keys, and shortcuts.
- Repeat at a chosen interval; start after a delay or on a date/time.
- Stop by action count, cycle count, or end date/time.
- Mixed multi-point patterns, per-step waits, and compatible JSON save/load.
- Native point picker, progress, Stop/Cancel, and Windows sleep prevention.
- Local shadcn/ui interface that follows the system light/dark theme.

## Downloads

- **Windows:** run `SimpleAutoclicker-0.1.0-windows-x64-setup.exe` for a per-user installation with a Start menu shortcut and uninstaller. The ZIP is a portable alternative: extract the whole folder and run `SimpleAutoclicker.exe`.
- **Ubuntu/Debian:** install `SimpleAutoclicker-0.1.0-linux-amd64.deb` with `sudo apt install ./SimpleAutoclicker-0.1.0-linux-amd64.deb`. Launch Simple Autoclicker from the applications menu or run `simple-autoclicker`.
- **Other Linux distributions:** extract the `.tar.gz` and run `./SimpleAutoclicker/SimpleAutoclicker`. Requires glibc 2.35+ and the X11/Tk runtime dependencies listed in the README.
- `SHA256SUMS.txt` contains download checksums.

Linux requires an **X11/Xorg** session; Wayland is unsupported. Linux users disable automatic sleep manually. Keyboard actions target the focused application. Closing the browser tab does not stop a run: use **Stop** or **Quit app**. Windows packages are unsigned.
