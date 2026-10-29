from datetime import datetime, timedelta
import os
import time
import tkinter as tk
import unittest
from unittest.mock import patch

from autoclicker import ClickerApp, Mouse, next_click_time


class TimeTests(unittest.TestCase):
    def test_future_and_past_times(self):
        now = datetime(2026, 12, 31, 23, 30)
        self.assertEqual(next_click_time("23:45:00", now), datetime(2026, 12, 31, 23, 45))
        self.assertEqual(next_click_time("00:00:00", now), datetime(2027, 1, 1))
        self.assertEqual(next_click_time("23:30:00", now), datetime(2027, 1, 1, 23, 30))

    def test_invalid_times(self):
        for value in ("24:00:00", "12:60:00", "hello", "", "12:00"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                next_click_time(value, datetime.now())

    def test_linux_setup_errors(self):
        with patch("autoclicker.sys.platform", "linux"):
            with patch.dict(os.environ, {"XDG_SESSION_TYPE": "wayland"}, clear=True):
                with self.assertRaisesRegex(RuntimeError, "X11"):
                    Mouse()
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaisesRegex(RuntimeError, "display"):
                    Mouse()


class FakeMouse:
    def __init__(self):
        self.clicks = []
        self.awake = False
        self.fail = False

    def position(self):
        return 10, 10

    def click(self, point):
        if self.fail:
            raise RuntimeError("Mouse unavailable")
        self.clicks.append(point)

    def keep_awake(self, enabled):
        self.awake = enabled


class UITests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.mouse = FakeMouse()
        self.app = ClickerApp(self.root, self.mouse)

    def tearDown(self):
        self.app.close()

    def schedule(self):
        self.app.clock.set((datetime.now() + timedelta(hours=1)).strftime("%H:%M:%S"))
        self.app.schedule()
        self.assertIsNotNone(self.app.target)

    def run_due_tick(self):
        # Cancel the real timer before advancing the test clock.
        self.root.after_cancel(self.app.job)
        self.app.job = None
        self.app.target = datetime.now() - timedelta(seconds=1)
        self.app.tick()

    def test_cancel_disarms_and_restores_power(self):
        self.schedule()
        self.assertTrue(self.mouse.awake)
        self.assertTrue(self.app.start_button.instate(["disabled"]))
        self.app.cancel()
        self.app.tick()
        self.assertIsNone(self.app.target)
        self.assertIsNone(self.app.job)
        self.assertFalse(self.mouse.awake)
        self.assertEqual(self.mouse.clicks, [])
        self.assertTrue(self.app.start_button.instate(["!disabled"]))

    def test_due_click_fires_exactly_once(self):
        self.schedule()
        self.run_due_tick()
        self.app.tick()
        self.assertEqual(self.mouse.clicks, [(10, 10)])
        self.assertFalse(self.mouse.awake)
        self.assertIsNone(self.app.target)
        self.assertIn("completed", self.app.status.get())

    def test_click_failure_disarms_and_restores_power(self):
        self.schedule()
        self.mouse.fail = True
        self.run_due_tick()
        self.app.tick()
        self.assertFalse(self.mouse.awake)
        self.assertIsNone(self.app.target)
        self.assertIn("Mouse unavailable", self.app.status.get())

    def test_invalid_coordinates_never_arm(self):
        for value in ("abc", "-99999", "1.5"):
            with self.subTest(value=value):
                self.app.x.set(value)
                self.app.schedule()
                self.assertIsNone(self.app.target)
                self.assertFalse(self.mouse.awake)

    def test_picker_capture_and_cancel(self):
        self.app.pick()
        self.app.cancel()
        self.assertIsNone(self.app.pick_at)
        self.app.pick()
        self.root.after_cancel(self.app.job)
        self.app.job = None
        self.app.pick_at = time.monotonic() - 1
        self.app.tick()
        self.assertEqual((self.app.x.get(), self.app.y.get()), ("10", "10"))
        self.assertIsNone(self.app.pick_at)
        self.assertTrue(self.app.start_button.instate(["!disabled"]))


if __name__ == "__main__":
    unittest.main()
