"""Create an amd64 Debian installer and a portable Linux tarball."""
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app_version import __version__

if sys.platform != 'linux':
    raise SystemExit('Build Linux packages on Linux.')
app = ROOT / 'dist' / 'SimpleAutoclicker'
output = ROOT / 'release-assets'
output.mkdir(exist_ok=True)
with tarfile.open(output / f'SimpleAutoclicker-{__version__}-linux-x64.tar.gz', 'w:gz') as archive:
    archive.add(app, arcname='SimpleAutoclicker')

# A fresh staging directory avoids retaining files from an older package.
import tempfile
with tempfile.TemporaryDirectory(prefix='autoclicker-deb-') as folder:
    stage = Path(folder)
    shutil.copytree(app, stage / 'opt' / 'simple-autoclicker')
    desktop = stage / 'usr' / 'share' / 'applications'
    desktop.mkdir(parents=True)
    shutil.copy2(ROOT / 'packaging' / 'simple-autoclicker.desktop', desktop)
    icons = stage / 'usr' / 'share' / 'icons' / 'hicolor' / '512x512' / 'apps'
    icons.mkdir(parents=True)
    shutil.copy2(ROOT / 'assets' / 'icon.png', icons / 'simple-autoclicker.png')
    commands = stage / 'usr' / 'bin'
    commands.mkdir(parents=True)
    (commands / 'simple-autoclicker').symlink_to('/opt/simple-autoclicker/SimpleAutoclicker')
    control = stage / 'DEBIAN'
    control.mkdir()
    (control / 'control').write_text(f'''Package: simple-autoclicker
Version: {__version__}
Architecture: amd64
Maintainer: aliabedi1 <aliabedi1@users.noreply.github.com>
Section: utils
Priority: optional
Depends: libc6 (>= 2.35), libx11-6, libxtst6, libxext6, libxrender1, libxi6, libxss1, libfontconfig1, libfreetype6, xdg-utils
Homepage: https://github.com/aliabedi1/simple-autoclicker
Description: Schedule mouse and keyboard actions locally
 A local browser interface for single actions, repeated actions, and patterns.
 Requires an unlocked Linux X11 desktop; Wayland is not supported.
''', encoding='utf-8')
    subprocess.run(['dpkg-deb', '--root-owner-group', '--build', str(stage),
                    str(output / f'SimpleAutoclicker-{__version__}-linux-amd64.deb')], check=True)
