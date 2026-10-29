"""Build a self-contained app on the current OS."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app_version import __version__


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--frontend', type=Path, default=ROOT / 'web' / 'dist')
    args = parser.parse_args()
    frontend = args.frontend.resolve()
    if not (frontend / 'index.html').is_file():
        parser.error('Build the frontend first with npm ci and npm run build in web/.')
    licenses = ROOT / 'build' / 'licenses'
    licenses.mkdir(parents=True, exist_ok=True)
    versions = {}
    for name in ('pynput', 'six', 'python-xlib', 'evdev', 'pyinstaller'):
        try:
            distribution = importlib.metadata.distribution(name)
        except importlib.metadata.PackageNotFoundError:
            continue
        versions[name] = distribution.version
        for file in distribution.files or ():
            if Path(file).name.lower().startswith(('license', 'copying', 'notice')):
                source = distribution.locate_file(file)
                if source.is_file():
                    target = licenses / name / str(file).replace('..', '_')
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
    python_license = Path(sys.base_prefix) / 'LICENSE.txt'
    if python_license.is_file():
        shutil.copy2(python_license, licenses / 'PYTHON-LICENSE.txt')
    (licenses / 'BUILD-INFO.json').write_text(json.dumps({
        'app': __version__, 'python': sys.version, 'platform': sys.platform, 'dependencies': versions,
    }, indent=2), encoding='utf-8')
    env = os.environ.copy()
    env['AUTOCLICKER_FRONTEND'] = str(frontend)
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
                    str(ROOT / 'SimpleAutoclicker.spec')], cwd=ROOT, env=env, check=True)


if __name__ == '__main__':
    main()
