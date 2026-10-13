"""Execution settings must not leak between runs through saved configuration."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_twitter import aim


class CliTests(unittest.TestCase):
    def test_stale_configuration_is_ignored_and_preserved(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.dict(aim.RUNTIME_OPTIONS), patch.dict(aim.TWITTER_OPTIONS):
            base = Path(directory)
            root = base / 'private-data'
            root.mkdir()
            config = root / 'config.json'
            old = '{"logs_dir":"/chome/unavailable", "codex_bin":"missing"}\n'
            config.write_text(old)
            common = ['--private-dir', str(root), '--output-dir', str(base / 'html')]
            self.assertEqual(aim.main(common + ['--demo', '--logs-dir', str(base / 'events'),
                                              '--codex-bin', '/custom/codex', '--model', 'chosen',
                                              '--extra-path', '/custom/bin', '--timeout-seconds', '60']), 0)
            self.assertTrue((base / 'html/demo.html').is_file())
            self.assertTrue((base / 'events').is_dir())
            self.assertEqual(aim.runtime_config(root)['codex_bin'], '/custom/codex')
            self.assertEqual(config.read_text(), old)
            self.assertEqual(aim.main(common + ['--init']), 0)
            self.assertEqual(aim.runtime_config(root)['logs_dir'], 'logs')
            self.assertEqual(aim.runtime_config(root)['codex_bin'], 'codex')
            self.assertEqual(aim.runtime_config(root)['extra_path'], [])

    def test_initialization_does_not_create_configuration_json(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.dict(aim.RUNTIME_OPTIONS), patch.dict(aim.TWITTER_OPTIONS):
            base = Path(directory)
            root = base / 'private-data'
            self.assertEqual(aim.main(['--init', '--private-dir', str(root),
                                       '--output-dir', str(base / 'html')]), 0)
            self.assertFalse((root / 'config.json').exists())
