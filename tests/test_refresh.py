"""Regression checks for same-day refreshes, without network or Codex calls."""
import copy
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from test_twitter import aim


class RefreshTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 9, 10, tzinfo=aim.PARIS)
        self.digest = aim.demo_digest()
        for number, item in enumerate(self.digest['items']):
            item['sources'] = [{'label': 'Primary source', 'url': 'https://example.org/' + str(number)}]
        self.record = dict(generated_at=(self.now - timedelta(hours=2)).isoformat(),
                           window_start=(self.now - timedelta(days=1)).isoformat(),
                           archive='20261009T060000Z-12345678.html', digest=self.digest)

    def test_empty_refresh_recovers_earlier_items_even_after_empty_edition(self):
        empty = dict(status='partial', summary='Coverage unavailable',
                     coverage=['No feeds accessible'], items=[])
        result = aim.merge_refresh(empty, [self.record, dict(self.record, digest=empty)])
        self.assertEqual(result['items'], self.digest['items'])
        self.assertEqual(result['status'], 'partial')
        for item in result['items']:
            self.assertIn(item['title'], result['summary'])
        self.assertNotIn('Coverage unavailable', result['summary'])
        self.assertIn('Coverage remains incomplete', result['summary'])
        aim.validate_digest(result, self.now.date())
        self.assertEqual(empty['items'], [])

    def test_correction_replaces_saved_item(self):
        corrected = copy.deepcopy(self.digest)
        corrected['items'] = corrected['items'][:1]
        corrected['items'][0]['summary'] = 'Corrected claim'
        result = aim.merge_refresh(corrected, [self.record])
        self.assertEqual(len(result['items']), 3)
        self.assertEqual(result['items'][0]['summary'], 'Corrected claim')

    def test_no_news_with_retained_items_becomes_ok(self):
        result = aim.merge_refresh(dict(status='no_news', summary='No new findings',
                                        coverage=['Web searched'], items=[]), [self.record])
        self.assertEqual(result['status'], 'ok')
        self.assertNotIn('No new findings', result['summary'])
        aim.validate_digest(result, self.now.date())

    def test_full_window_and_today_not_excluded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'private').mkdir()
            (root / 'prompt.md').write_text('Research')
            (root / 'private/edition-20261009T060000Z-12345678.json').write_text(json.dumps(self.record))
            with patch.object(aim, 'source_prompt_entries', return_value=[]), \
                 patch.object(aim, 'collect_bluesky', return_value=[]), \
                 patch.object(aim, 'collect_twitter', return_value=[]):
                prompt, start = aim.build_prompt(root, self.now, self.record, refresh=True)
            context = json.loads(prompt.split('Research context:\n')[1])
            self.assertEqual(start.isoformat(), self.record['window_start'])
            self.assertEqual(context['previous_items'], [])
            self.assertEqual(context['earlier_editions_today'], [self.digest])
