import importlib.util
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('patcher', ROOT / 'src/patcher.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
p.SPEAKER = None
GOOD = b'AdVenture Capitalist Access\nGameplay and keyboard reference\nLeft / Right Arrow\n'

class ReadmeTests(unittest.TestCase):
    def test_payload_validation(self):
        for bad in (b'', b'<html>error</html>', GOOD + b'\x00', GOOD + b'x' * p.README_MAX_BYTES, GOOD + b'\xff'):
            with self.subTest(bad=bad[:25]), self.assertRaises((RuntimeError, UnicodeDecodeError)):
                p.validate_readme(bad)
        self.assertEqual(p.validate_readme(GOOD), GOOD.replace(b'\n', b'\r\n'))
        self.assertEqual(p.validate_readme(b'\xef\xbb\xbf'+GOOD), p.validate_readme(GOOD))

    def test_request_only_document_and_bounded_read(self):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = GOOD
        with patch.object(p.urllib.request, 'urlopen', return_value=response) as opened:
            self.assertEqual(p.request_readme(), p.validate_readme(GOOD))
        self.assertEqual(opened.call_args.args[0].full_url, p.README_URL)
        self.assertEqual(response.read.call_args.args, (p.README_MAX_BYTES + 1,))

    def test_atomic_save_failure_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / 'my guide.txt'
            dest.write_text('existing file')
            with patch.object(p.os, 'replace', side_effect=PermissionError('locked')), self.assertRaises(PermissionError):
                p.save_readme(dest, GOOD)
            self.assertEqual(dest.read_text(), 'existing file')
            self.assertEqual(list(Path(temp).iterdir()), [dest])
            with self.assertRaises(RuntimeError): p.save_readme(dest, b'<html>bad response</html>')
            self.assertEqual(dest.read_text(), 'existing file')
            p.save_readme(dest, GOOD)
            self.assertEqual(dest.read_bytes(), p.validate_readme(GOOD))

    def test_included_guide(self):
        data = p.bundled_readme()
        for section in ('THE GAMEPLAY LOOP', 'KEYBOARD COMMANDS', 'MAIN SCREENS', 'EVENTS', 'Shift+W'):
            self.assertIn(section.encode(), data)
        text = data.decode()
        self.assertNotIn('diagnostic', text.lower())
        self.assertNotIn('\u2014', text)
        self.assertNotIn('\u2013', text)
        self.assertNotIn('**', text)
        with patch.object(sys, 'frozen', True, create=True), patch.object(sys, '_MEIPASS', str(ROOT), create=True):
            self.assertEqual(p.bundled_readme(), data)

class ReadmeUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app = p.wx.App(False)
    def setUp(self):
        with patch.object(p.wx, 'CallAfter'):
            self.frame = p.MainFrame()
        self.frame.announce = Mock()
        self.callback = patch.object(p.wx, 'CallAfter', side_effect=lambda fn, *a: fn(*a))
        self.callback.start()
    def tearDown(self):
        self.callback.stop()
        self.frame.Destroy()
        self.app.ProcessPendingEvents()

    def test_document_button_not_blocked_by_update_check(self):
        self.frame.set_busy(True)
        self.assertTrue(self.frame.readme_button.IsEnabled())
        self.assertFalse(self.frame.install_button.IsEnabled())
        self.assertIsNone(self.frame.manifest)

    def test_save_dialog_cancel_does_nothing(self):
        dialog = Mock()
        dialog.__enter__ = Mock(return_value=dialog)
        dialog.__exit__ = Mock(return_value=False)
        dialog.ShowModal.return_value = p.wx.ID_CANCEL
        with patch.object(p.wx, 'FileDialog', return_value=dialog), patch.object(p.threading, 'Thread') as thread:
            self.frame.on_download_readme()
            thread.assert_not_called()
        self.assertFalse(self.frame.readme_busy)

    def test_save_as_uses_selected_location_without_installer(self):
        dialog = Mock()
        dialog.__enter__ = Mock(return_value=dialog)
        dialog.__exit__ = Mock(return_value=False)
        dialog.ShowModal.return_value = p.wx.ID_OK
        dialog.GetPath.return_value = r'C:\chosen folder\game guide.txt'
        with patch.object(p.wx, 'FileDialog', return_value=dialog) as picker, patch.object(p.threading, 'Thread') as thread, patch.object(p, 'Installer') as installer:
            self.frame.on_download_readme()
            self.assertEqual(thread.call_args.kwargs['args'], (Path(dialog.GetPath()),))
            self.assertEqual(picker.call_args.kwargs['defaultFile'], 'readme.txt')
            self.assertTrue(picker.call_args.kwargs['style'] & p.wx.FD_OVERWRITE_PROMPT)
            installer.assert_not_called()
            self.assertTrue(self.frame.readme_busy)

    def test_online_worker_with_no_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / 'guide.txt'
            with patch.object(p, 'request_readme', return_value=GOOD), patch.object(p, 'request_json', side_effect=AssertionError('no manifests')), patch.object(p, 'Installer', side_effect=AssertionError('no installer')):
                self.frame.readme_busy = True
                self.frame._readme_worker(dest)
            self.assertEqual(dest.read_bytes(), p.validate_readme(GOOD))
            self.assertFalse(self.frame.readme_busy)
            self.assertTrue(self.frame.readme_button.IsEnabled())

    def test_offline_decline_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / 'readme.txt'
            dest.write_text('keep me')
            with patch.object(p, 'request_readme', side_effect=OSError('offline')), patch.object(p.wx, 'MessageBox', return_value=p.wx.NO):
                self.frame.readme_busy = True
                self.frame._readme_worker(dest)
            self.assertEqual(dest.read_text(), 'keep me')
            self.assertFalse(self.frame.readme_busy)

    def test_offline_accept_saves_included_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / 'readme.txt'
            with patch.object(p, 'request_readme', side_effect=OSError('offline')), patch.object(p.wx, 'MessageBox', return_value=p.wx.YES), patch.object(p.threading, 'Thread') as thread:
                self.frame._readme_worker(dest)
                self.assertEqual(thread.call_args.kwargs['args'], (dest, True))
            self.frame._readme_worker(dest, True)
            self.assertEqual(dest.read_bytes(), p.bundled_readme())

    def test_only_successful_install_offers_readme(self):
        with patch.object(p.wx, 'MessageBox', return_value=p.wx.NO) as question:
            self.frame._operation_done('Installation failed')
            self.frame._operation_done('Restored game')
            question.assert_not_called()
            self.frame._operation_done('Installation complete', True)
            question.assert_called_once()
        with patch.object(p.wx, 'MessageBox', return_value=p.wx.YES), patch.object(self.frame, 'on_download_readme') as save:
            self.frame._operation_done('Installation complete', True)
            save.assert_called_once()

    def test_patcher_update_check_does_not_download_executable(self):
        release = {'tag_name': '99.0', 'assets': [{'name':'AdCapAccessPatcher.exe', 'digest':'sha256:'+'0'*64}]}
        with patch.object(sys, 'frozen', True, create=True), patch.object(p, 'request_json', return_value=release), patch.object(p.wx, 'MessageBox', return_value=p.wx.NO), patch.object(p, 'download') as download:
            self.frame._check_self_update()
            download.assert_not_called()
        self.assertTrue(self.frame.readme_button.IsEnabled())

    def test_update_completion_cannot_enable_install_during_self_update(self):
        self.frame.updating_patcher = True
        self.frame.set_busy(False)
        self.assertFalse(self.frame.install_button.IsEnabled())

if __name__ == '__main__': unittest.main(verbosity=2)
