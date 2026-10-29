import http.client
import json
from queue import Queue
import threading
import tkinter as tk
import unittest

from autoclicker import ClickerApp
from desktop import DesktopBridge, make_server
from test_autoclicker import FakeMouse


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = ClickerApp(self.root, FakeMouse())
        self.bridge = DesktopBridge(self.app)

    def tearDown(self):
        self.app.close()

    def test_browser_start_and_stop(self):
        state = self.bridge.execute('start', {'settings': {'count': '4', 'delay': '10'}})
        self.assertTrue(state['running'])
        self.assertEqual(state['limit'], 4)
        stopped = self.bridge.execute('stop', {})
        self.assertFalse(stopped['running'])
        self.assertFalse(self.app.mouse.awake)

    def test_pattern_and_invalid_choices(self):
        state = self.bridge.execute('start', {'settings': {'target_mode': 'pattern', 'count': '2'},
                                            'pattern': [{'x': 10, 'y': 20, 'delay': .05},
                                                        {'x': 30, 'y': 40, 'delay': .5}]})
        self.assertEqual(state['limit'], 4)
        self.assertEqual(state['step'], 1)
        with self.assertRaisesRegex(ValueError, 'Stop'):
            self.bridge.execute('pick', {})
        self.bridge.execute('stop', {})
        with self.assertRaisesRegex(ValueError, 'Invalid'):
            self.bridge.execute('start', {'settings': {'unit': 'days'}})

    def test_previous_completion_does_not_hide_invalid_position(self):
        self.app.last_completed = 10
        with self.assertRaisesRegex(ValueError, 'outside'):
            self.bridge.execute('start', {'settings': {'x': '-99999'}})


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.commands = Queue()
        self.server, self.token = make_server(type('Bridge', (), {'commands': self.commands})())
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, path='/', body=None, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        connection.request('GET' if body is None else 'POST', path, body=body, headers=headers or {})
        response = connection.getresponse()
        result = response.status, response.read(), response.getheaders()
        connection.close()
        return result

    def test_bundle_and_path_traversal(self):
        status, body, headers = self.request()
        self.assertEqual(status, 200)
        self.assertIn(b'Simple Autoclicker', body)
        self.assertIn('Content-Security-Policy', dict(headers))
        self.assertEqual(self.request('/assets/../../desktop.py')[0], 404)

    def test_no_token_and_foreign_origin_are_rejected(self):
        body = json.dumps({'action': 'start'})
        self.assertEqual(self.request('/api/action', body)[0], 403)
        self.assertEqual(self.request('/api/action', body, {'X-Clicker-Token': self.token,
                                                           'Origin': 'https://example.org'})[0], 403)
        self.assertTrue(self.commands.empty())
        self.assertEqual(self.request('/', headers={'Host': 'foreign.example'})[0], 403)

    def test_authorized_command_and_malformed_json(self):
        headers = {'X-Clicker-Token': self.token}
        self.assertEqual(self.request('/api/action', '{', headers)[0], 400)

        def respond():
            action, payload, response, _deadline = self.commands.get(timeout=2)
            response.put((200, {'action': action, 'payload': payload}))

        worker = threading.Thread(target=respond)
        worker.start()
        status, body, _ = self.request('/api/action', json.dumps({'action': 'state'}), headers)
        worker.join()
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['action'], 'state')


if __name__ == '__main__':
    unittest.main()
