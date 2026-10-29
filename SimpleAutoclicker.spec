# Build on each target OS; PyInstaller does not cross-compile.
from pathlib import Path
import os
import sys

root = Path(SPECPATH)
frontend = Path(os.environ.get('AUTOCLICKER_FRONTEND', root / 'web' / 'dist'))
backend = '_win32' if sys.platform == 'win32' else '_xorg'
a = Analysis(
    [str(root / 'desktop.py')],
    pathex=[str(root)],
    binaries=[],
    datas=[(str(root / 'assets'), 'assets'), (str(frontend), 'web/dist'),
           (str(root / 'build' / 'licenses'), 'licenses'),
           (str(root / 'packaging' / 'THIRD_PARTY.md'), '.')],
    hiddenimports=[f'pynput.mouse.{backend}', f'pynput.keyboard.{backend}'],
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True, name='SimpleAutoclicker',
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
    console=sys.platform != 'win32',
    icon=str(root / 'assets' / 'icon.ico') if sys.platform == 'win32' else None,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='SimpleAutoclicker')
