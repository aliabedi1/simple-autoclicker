"""Browser test fixture: real UI and timers, with mouse output recorded in memory."""
import json
from pathlib import Path
import sys
import threading
import tkinter as tk

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from autoclicker import ClickerApp
from desktop import DesktopBridge, make_server
from test_autoclicker import FakeMouse

root = tk.Tk()
root.withdraw()
app = ClickerApp(root, FakeMouse())
bridge = DesktopBridge(app)
server, token = make_server(bridge)
threading.Thread(target=server.serve_forever, daemon=True).start()
bridge.poll()
print(json.dumps({'url': f'http://127.0.0.1:{server.server_port}/#token={token}'}), flush=True)
try:
    root.mainloop()
finally:
    server.shutdown()
    server.server_close()
