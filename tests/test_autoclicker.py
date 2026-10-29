from datetime import datetime, timedelta
import os
import time
import tkinter as tk
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from autoclicker import ClickerApp, Mouse
from schedule import ClickPlan, ClickRun, read_datetime, read_seconds


class ScheduleTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 12, 31, 23, 30)

    def test_count_and_interval(self):
        run = ClickRun(ClickPlan(self.now, 2, limit=3))
        self.assertTrue(run.ready(self.now, 100))
        run.record_click(100)
        self.assertFalse(run.ready(self.now, 101.99))
        self.assertTrue(run.ready(self.now, 102))
        run.record_click(102)
        self.assertTrue(run.ready(self.now, 104))
        run.record_click(104)
        self.assertEqual(run.completed, 3)
        self.assertFalse(run.ready(self.now, 200))

    def test_waits_for_start_date(self):
        start = self.now + timedelta(days=1)
        run = ClickRun(ClickPlan(start, 1))
        self.assertFalse(run.ready(self.now, 100))
        self.assertEqual(run.remaining(self.now, 100), 86400)
        self.assertTrue(run.ready(start, 200))

    def test_end_date_is_exclusive_even_when_click_due(self):
        end = self.now + timedelta(seconds=5)
        run = ClickRun(ClickPlan(self.now, 10, limit=None, end_at=end))
        self.assertTrue(run.ready(self.now, 0))
        run.record_click(0)
        self.assertFalse(run.ready(end, 10))
        self.assertFalse(run.active)
        self.assertEqual(run.completed, 1)

    def test_expired_before_start_never_clicks(self):
        run = ClickRun(ClickPlan(self.now, 1, None, self.now + timedelta(seconds=2)))
        self.assertFalse(run.ready(self.now + timedelta(seconds=10), 100))
        self.assertEqual(run.completed, 0)

    def test_late_tick_does_not_replay_missed_clicks(self):
        run = ClickRun(ClickPlan(self.now, 1, limit=100))
        run.record_click(10)
        self.assertTrue(run.ready(self.now, 1000))
        run.record_click(1000)
        self.assertFalse(run.ready(self.now, 1000))
        self.assertEqual(run.completed, 2)

    def test_interval_uses_monotonic_time_after_first_click(self):
        run = ClickRun(ClickPlan(self.now, 2, limit=3))
        run.record_click(10)
        self.assertFalse(run.ready(self.now + timedelta(days=1), 11))
        self.assertTrue(run.ready(self.now - timedelta(days=1), 12))

    def test_invalid_inputs(self):
        for value in ('nan', 'inf', '-1', 'abc', '999999999999999999'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                read_seconds(value, 'Delay')
        for interval, limit, end in ((0, 1, None), (float('nan'), 1, None), (1, 0, None),
                                      (1, -1, None), (1, None, None), (1, None, self.now)):
            with self.subTest(interval=interval, limit=limit), self.assertRaises(ValueError):
                ClickPlan(self.now, interval, limit, end)
        with self.assertRaises(ValueError):
            read_datetime('2026-02-30', '25:00:00', 'Start')
        self.assertEqual(read_datetime('2027-01-01', '00:00:00', 'Start'), datetime(2027, 1, 1))
        self.assertEqual(read_seconds('500', 'Delay', .001, .05), .5)

    def test_linux_setup_errors(self):
        with patch('autoclicker.sys.platform', 'linux'):
            with patch.dict(os.environ, {'XDG_SESSION_TYPE': 'wayland'}, clear=True):
                with self.assertRaisesRegex(RuntimeError, 'X11'):
                    Mouse()
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaisesRegex(RuntimeError, 'display'):
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
            raise RuntimeError('Mouse unavailable')
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

    def schedule(self, count=1):
        self.app.count.set(str(count))
        self.app.schedule()
        self.assertIsNotNone(self.app.run)

    def run_due_tick(self):
        self.root.after_cancel(self.app.job)
        self.app.job = None
        with patch('autoclicker.datetime') as clock:
            clock.now.return_value = self.app.run.plan.start_at + timedelta(seconds=1)
            with patch('autoclicker.time.monotonic', return_value=100):
                self.app.tick()

    def test_cancel_disarms_and_restores_power(self):
        self.schedule()
        self.assertTrue(self.mouse.awake)
        self.assertTrue(self.app.start_button.instate(['disabled']))
        self.app.cancel()
        self.app.tick()
        self.assertIsNone(self.app.run)
        self.assertIsNone(self.app.job)
        self.assertFalse(self.mouse.awake)
        self.assertEqual(self.mouse.clicks, [])

    def test_one_click_and_done(self):
        self.schedule()
        self.run_due_tick()
        self.app.tick()
        self.assertEqual(self.mouse.clicks, [(10, 10)])
        self.assertFalse(self.mouse.awake)
        self.assertIsNone(self.app.run)
        self.assertIn('Completed 1', self.app.status.get())

    def test_repeat_and_cancel(self):
        self.schedule(3)
        self.run_due_tick()
        self.assertEqual(self.app.run.completed, 1)
        self.assertTrue(self.mouse.awake)
        self.assertIsNotNone(self.app.job)
        self.app.cancel()
        self.app.tick()
        self.assertEqual(len(self.mouse.clicks), 1)
        self.assertIn('1 click', self.app.status.get())

    def test_click_failure_disarms_and_restores_power(self):
        self.schedule(3)
        self.mouse.fail = True
        self.run_due_tick()
        self.assertFalse(self.mouse.awake)
        self.assertIsNone(self.app.run)
        self.assertIn('Mouse unavailable', self.app.status.get())

    def test_invalid_coordinates_never_arm(self):
        for value in ('abc', '-99999', '1.5'):
            with self.subTest(value=value):
                self.app.x.set(value)
                self.app.schedule()
                self.assertIsNone(self.app.run)
                self.assertFalse(self.mouse.awake)

    def test_invalid_schedule_never_arms(self):
        for field, value in ((self.app.count, '0'), (self.app.count, '1.5'),
                             (self.app.interval, 'nan'), (self.app.delay, '-1')):
            original = field.get()
            field.set(value)
            self.app.schedule()
            self.assertIsNone(self.app.run)
            self.assertFalse(self.mouse.awake)
            field.set(original)

    def test_start_and_end_dates(self):
        self.app.start_mode.set('date')
        self.app.stop_mode.set('date')
        self.app.start_date.set('2035-12-31')
        self.app.clock.set('23:00:00')
        self.app.end_date.set('2036-01-01')
        self.app.end_clock.set('01:00:00')
        self.app.schedule()
        self.assertEqual(self.app.run.plan.start_at, datetime(2035, 12, 31, 23))
        self.assertEqual(self.app.run.plan.end_at, datetime(2036, 1, 1, 1))
        self.assertIsNone(self.app.run.plan.limit)

    def test_past_start_or_early_end_rejected(self):
        self.app.start_mode.set('date')
        self.app.start_date.set('2000-01-01')
        self.app.schedule()
        self.assertIsNone(self.app.run)
        self.assertIn('future', self.app.status.get())
        self.app.start_mode.set('delay')
        self.app.stop_mode.set('date')
        self.app.end_date.set('2000-01-01')
        self.app.schedule()
        self.assertIsNone(self.app.run)
        self.assertIn('later', self.app.status.get())

    def test_picker_capture_and_cancel(self):
        self.app.pick()
        self.assertIsNotNone(self.app.overlay)
        self.app.cancel()
        self.assertIsNone(self.app.overlay)
        self.app.pick()
        self.app.capture_point(SimpleNamespace(x_root=10, y_root=20))
        self.assertEqual((self.app.x.get(), self.app.y.get()), ('10', '20'))
        self.assertIsNone(self.app.overlay)
        self.assertTrue(self.app.start_button.instate(['!disabled']))

    def test_irrelevant_fields_disabled(self):
        self.assertTrue(self.app.date_entry.instate(['disabled']))
        self.assertTrue(self.app.end_date_entry.instate(['disabled']))
        self.app.start_mode.set('date')
        self.assertTrue(self.app.date_entry.instate(['!disabled']))
        self.assertTrue(self.app.delay_entry.instate(['disabled']))
        self.app.stop_mode.set('date')
        self.assertTrue(self.app.count_entry.instate(['disabled']))

    def test_units_and_unused_fields(self):
        self.app.interval.set('500')
        self.app.unit.set('milliseconds')
        self.app.start_date.set('unused')
        self.app.end_date.set('unused')
        self.assertEqual(self.app.build_plan(datetime.now()).interval, .5)
        self.app.interval.set('2')
        self.app.unit.set('minutes')
        self.assertEqual(self.app.build_plan(datetime.now()).interval, 120)

    def test_close_cancels_pending_work(self):
        self.schedule(100)
        with patch.object(self.root, 'destroy') as destroy:
            self.app.close()
            destroy.assert_called_once()
        self.assertFalse(self.mouse.awake)
        self.assertIsNone(self.app.job)
        self.assertIsNone(self.app.run)


if __name__ == '__main__':
    unittest.main()
