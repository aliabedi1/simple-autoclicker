from datetime import datetime
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, call

from autoclicker import Mouse
from schedule import ClickPlan, ClickStep, parse_keys


class ActionTests(unittest.TestCase):
    def backend(self):
        mouse = Mouse.__new__(Mouse)
        mouse.controller = Mock()
        mouse.controller.position = (99, 100)
        mouse.buttons = {'left': 'LEFT', 'right': 'RIGHT', 'middle': 'MIDDLE'}
        mouse.keyboard = Mock()
        mouse.key_enum = SimpleNamespace(ctrl='CTRL', shift='SHIFT', enter='ENTER', space='SPACE', f12='F12')
        return mouse

    def test_mouse_button_dispatch(self):
        for action, button in [('left', 'LEFT'), ('right', 'RIGHT'), ('middle', 'MIDDLE')]:
            with self.subTest(action=action):
                mouse = self.backend()
                mouse.perform((10, 20), action)
                self.assertEqual(mouse.controller.position, (10, 20))
                mouse.controller.click.assert_called_once_with(button)
                mouse.keyboard.press.assert_not_called()

    def test_named_key_tap_does_not_move_mouse(self):
        mouse = self.backend()
        mouse.perform((0, 0), 'key', 'Enter')
        self.assertEqual(mouse.keyboard.method_calls, [call.press('ENTER'), call.release('ENTER')])
        self.assertEqual(mouse.controller.position, (99, 100))
        mouse.controller.click.assert_not_called()

    def test_shortcut_releases_in_reverse_order(self):
        mouse = self.backend()
        mouse.perform((0, 0), 'key', 'CTRL+Shift+S')
        self.assertEqual(mouse.keyboard.method_calls, [call.press('CTRL'), call.press('SHIFT'), call.press('s'),
                                                     call.release('s'), call.release('SHIFT'), call.release('CTRL')])

    def test_failure_still_releases_all_pressed_keys(self):
        mouse = self.backend()
        mouse.keyboard.press.side_effect = [None, RuntimeError('Press failed')]
        with self.assertRaisesRegex(RuntimeError, 'Press failed'):
            mouse.perform((0, 0), 'key', 'ctrl+s')
        self.assertEqual(mouse.keyboard.release.call_args_list, [call('s'), call('CTRL')])
        # A release failure must not prevent the remaining modifiers being released.
        mouse = self.backend()
        mouse.keyboard.release.side_effect = [RuntimeError('Release failed'), None]
        with self.assertRaisesRegex(RuntimeError, 'Release failed'):
            mouse.perform((0, 0), 'key', 'ctrl+s')
        self.assertEqual(mouse.keyboard.release.call_args_list, [call('s'), call('CTRL')])

    def test_validation_and_aliases(self):
        self.assertEqual(parse_keys('Control + Return'), ('ctrl', 'enter'))
        self.assertEqual(parse_keys('arrowLeft'), ('left',))
        self.assertEqual(parse_keys('ctrl+plus'), ('ctrl', '+'))
        self.assertEqual(parse_keys('F24'), ('f24',))
        for key in ('', 'invalid_key', 'ctrl+', 'ctrl+ctrl+a', 'a+b', 'ctrl+invalid', 'f25'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                ClickStep(0, 0, action='key', key=key)
        with self.assertRaises(ValueError):
            ClickPlan(datetime.now(), 1, action='unknown')
        self.assertEqual(ClickStep(10, 20).action, 'left')


if __name__ == '__main__':
    unittest.main()
