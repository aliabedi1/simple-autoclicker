"""Serve the bundled shadcn interface and dispatch native actions on Tk's thread."""

import ctypes
from datetime import datetime
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
from queue import Empty, Queue
import secrets
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox
import webbrowser

from autoclicker import ClickerApp, Mouse
from schedule import ClickStep

ROOT = Path(__file__).resolve().parent
SETTING_NAMES = ('target_mode', 'x', 'y', 'interval', 'unit', 'start_mode', 'delay',
                 'start_date', 'clock', 'stop_mode', 'count', 'end_date', 'end_clock')


class DesktopBridge:
    def __init__(self, app):
        self.app = app
        self.commands = Queue()
        self.selection = None
        self.limit = None

    def snapshot(self):
        run = self.app.run
        return {
            'settings': {name: getattr(self.app, name).get() for name in SETTING_NAMES},
            'pattern': [dict(x=s.x, y=s.y, delay=s.delay) for s in self.app.pattern],
            'running': run is not None,
            'picking': self.app.overlay is not None,
            'status': self.app.status.get().strip(),
            'completed': run.completed if run is not None else self.app.last_completed,
            'limit': self.limit,
            'next_in': run.remaining(datetime.now(), time.monotonic()) if run is not None else None,
            'step': run.completed % len(run.plan.pattern) + 1 if run is not None and run.plan.pattern else None,
            'selection': self.selection,
            'platform': sys.platform,
        }

    def execute(self, action, payload):
        if action == 'state':
            return self.snapshot()
        if action == 'stop':
            self.app.cancel()
            return self.snapshot()
        if action == 'quit':
            self.app.cancel()
            self.app.root.after(200, self.app.close)
            return {'closed': True}
        if self.app.run is not None or self.app.overlay is not None:
            raise ValueError('Stop the current action before changing it.')
        if action == 'pick':
            selection_id = str(payload.get('id', 'single'))[:100]

            def selected(x, y):
                self.selection = {'id': selection_id, 'x': x, 'y': y, 'nonce': secrets.token_hex(8)}
                if selection_id == 'single':
                    self.app.x.set(str(x))
                    self.app.y.set(str(y))

            self.app.pick(selected)
            return self.snapshot()
        if action != 'start':
            raise ValueError('Unknown action.')
        settings = payload.get('settings', {})
        if not isinstance(settings, dict):
            raise ValueError('Settings must be an object.')
        choices = {'target_mode': ('single', 'pattern'), 'unit': ('seconds', 'minutes', 'milliseconds'),
                   'start_mode': ('delay', 'date'), 'stop_mode': ('count', 'date')}
        for name, options in choices.items():
            if name in settings and settings[name] not in options:
                raise ValueError(f'Invalid {name}.')
        data = payload.get('pattern', [])
        if not isinstance(data, list) or len(data) > 1000:
            raise ValueError('A pattern must contain at most 1000 steps.')
        try:
            pattern = tuple(ClickStep(**step) for step in data)
        except (TypeError, OverflowError) as error:
            raise ValueError('Each step needs integer X/Y coordinates and a numeric delay.') from error
        for name in SETTING_NAMES:
            if name in settings:
                getattr(self.app, name).set(str(settings[name]))
        self.app.pattern = pattern
        plan = self.app.build_plan(datetime.now())
        self.limit = plan.limit
        self.app.last_completed = 0
        self.app.schedule()
        if self.app.run is None and self.app.last_completed == 0:
            raise ValueError(self.app.status.get())
        return self.snapshot()

    def poll(self):
        # HTTP workers never touch Tk; all commands run on the desktop thread.
        for _ in range(20):
            try:
                action, payload, response, deadline = self.commands.get_nowait()
            except Empty:
                break
            if time.monotonic() > deadline:
                response.put((503, {'error': 'The request expired. Try again.'}))
                continue
            try:
                response.put((200, self.execute(action, payload)))
            except (ValueError, TypeError, OverflowError, OSError) as error:
                response.put((400, {'error': str(error)}))
            except Exception:
                response.put((500, {'error': 'The desktop action failed. Check the app terminal.'}))
        self.app.root.after(20, self.poll)


class LocalServer(ThreadingHTTPServer):
    daemon_threads = True


class LocalHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, bridge, token, dist, **kwargs):
        self.bridge, self.token, self.dist = bridge, token, dist
        super().__init__(*args, **kwargs)

    def log_message(self, *_args):
        pass

    def reply(self, status, content, mime='application/json'):
        if mime == 'application/json':
            content = json.dumps(content).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(content)

    def valid_host(self):
        return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}'

    def do_GET(self):
        if not self.valid_host():
            return self.reply(403, {'error': 'Local access only.'})
        path = self.path.split('?', 1)[0]
        if path == '/':
            file = self.dist / 'index.html'
        elif path == '/icon.png':
            file = ROOT / 'assets' / 'icon.png'
        elif path.startswith('/assets/'):
            file = (self.dist / path.lstrip('/')).resolve()
            if not file.is_relative_to(self.dist.resolve() / 'assets'):
                return self.reply(404, {'error': 'Not found.'})
        else:
            return self.reply(404, {'error': 'Not found.'})
        if not file.is_file():
            return self.reply(404, {'error': 'Interface files are missing. Build web/ first.'})
        mime = {'.js': 'text/javascript', '.css': 'text/css', '.html': 'text/html'}.get(file.suffix)
        return self.reply(200, file.read_bytes(), mime or mimetypes.guess_type(file)[0] or 'application/octet-stream')

    def do_POST(self):
        expected_origin = f'http://127.0.0.1:{self.server.server_port}'
        if (not self.valid_host() or self.headers.get('Origin', expected_origin) != expected_origin
                or not secrets.compare_digest(self.headers.get('X-Clicker-Token', ''), self.token)):
            return self.reply(403, {'error': 'Open this interface from the app launcher.'})
        if self.path != '/api/action':
            return self.reply(404, {'error': 'Not found.'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 262144:
                return self.reply(413, {'error': 'Request is too large or empty.'})
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict) or not isinstance(data.get('payload', {}), dict):
                raise ValueError('Invalid action request.')
        except (ValueError, UnicodeError):
            return self.reply(400, {'error': 'Invalid action request.'})
        response = Queue(maxsize=1)
        self.bridge.commands.put((data.get('action'), data.get('payload', {}), response, time.monotonic() + 4))
        try:
            status, result = response.get(timeout=5)
        except Empty:
            return self.reply(503, {'error': 'The desktop app is not responding. Restart it from the launcher.'})
        return self.reply(status, result)


def make_server(bridge, dist=ROOT / 'web' / 'dist'):
    token = secrets.token_urlsafe(32)
    server = LocalServer(('127.0.0.1', 0), partial(LocalHandler, bridge=bridge, token=token, dist=Path(dist)))
    return server, token


def main():
    if sys.platform == 'win32':
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('SimpleAutoclicker.Desktop')
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            ctypes.windll.user32.SetProcessDPIAware()
    root = tk.Tk()
    root.withdraw()
    try:
        if not (ROOT / 'web' / 'dist' / 'index.html').is_file():
            raise RuntimeError('The web interface is missing. In web/, run npm ci and npm run build.')
        app = ClickerApp(root, Mouse())
    except Exception as error:
        messagebox.showerror('Simple Autoclicker - setup needed', str(error), parent=root)
        root.destroy()
        return 1
    bridge = DesktopBridge(app)
    server, token = make_server(bridge)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    bridge.poll()
    url = f'http://127.0.0.1:{server.server_port}/#token={token}'
    print('Simple Autoclicker is running locally. Use Quit app in the interface to exit.')
    if not webbrowser.open(url):
        print(f'Open this address in your browser: {url}')
    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.close()
    finally:
        app.mouse.keep_awake(False)
        server.shutdown()
        server.server_close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
