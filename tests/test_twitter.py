"""Offline checks: no real tokens, API calls or paid reads."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

spec = importlib.util.spec_from_file_location('aim', Path(__file__).resolve().parents[1] / 'aim-cron.py')
aim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(aim)


class Response:
    def __init__(self, payload):
        self.body = json.dumps(payload).encode()
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, limit):
        return self.body[:limit]


class TwitterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'private').mkdir()
        (self.root / 'sources.json').write_text(json.dumps(['Alice — X : @alice']))
        self.credentials = self.root / 'twitter.json'
        self.credentials.write_text('{"bearer_token":"FAKE_SECRET"}')
        self.credentials.chmod(0o600)
        self.options = patch.dict(aim.TWITTER_OPTIONS, credentials=self.credentials,
                                  budget_cents=500, max_posts=30)
        self.options.start()
        self.addCleanup(self.options.stop)
        self.end = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(seconds=1)
        self.start = self.end - timedelta(days=1)
        self.calls = []

    def fetch(self, payloads):
        def open_request(req, timeout):
            self.calls.append(req)
            self.assertLessEqual(timeout, 10)
            self.assertEqual(req.get_header('Authorization'), 'Bearer FAKE_SECRET')
            value = next(payloads)
            if isinstance(value, Exception):
                raise value
            return Response(value)
        with patch.object(aim, 'build_opener') as build:
            build.return_value.open.side_effect = open_request
            return aim.collect_twitter(self.root, self.start, self.end)

    def user(self):
        return {'data': {'id': '123', 'username': 'alice'}}

    def post(self, pid='456'):
        return {'id': pid, 'created_at': (self.start + timedelta(hours=1)).isoformat(),
                'text': 'short', 'note_post': {'text': 'Full mathematical announcement'},
                'entities': {'urls': [{'expanded_url': 'https://example.org/paper'}]}}

    def state(self):
        return aim.load(self.root / 'private/twitter-state.json')

    def test_dated_posts_and_cache_avoid_overlapping_paid_reads(self):
        result = self.fetch(iter([self.user(), {'data': [self.post()], 'meta': {}}]))
        self.assertEqual(result[0]['status'], 'ok')
        self.assertEqual(result[0]['posts'][0]['text'], 'Full mathematical announcement')
        self.assertEqual(self.state()['reserved_milliusd'], 15)
        params = parse_qs(urlsplit(self.calls[-1].full_url).query)
        self.assertEqual(params['exclude'], ['replies,retweets'])
        self.assertEqual(params['max_results'], ['5'])
        self.assertEqual(params['post.fields'], ['created_at,text,entities,note_post'])
        result = self.fetch(iter([]))
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(len(result[0]['posts']), 1)
        self.assertEqual(result[0]['status'], 'ok')
        self.assertNotIn('FAKE_SECRET', json.dumps(result) + json.dumps(self.state()))

    def test_budget_reserves_before_request_and_refuses_overrun(self):
        aim.TWITTER_OPTIONS['budget_cents'] = 3  # Cannot fund lookup + minimum page.
        result = self.fetch(iter([]))
        self.assertEqual(self.calls, [])
        self.assertIn('monthly budget', result[0]['limitations'])
        aim.TWITTER_OPTIONS['budget_cents'] = 4
        result = self.fetch(iter([self.user(), TimeoutError('FAKE_SECRET')]))
        self.assertEqual(self.state()['reserved_milliusd'], 35)
        self.assertNotIn('FAKE_SECRET', json.dumps(result))
        self.fetch(iter([]))
        self.assertEqual(len(self.calls), 2)

    def test_pagination_partial_and_rotation(self):
        (self.root / 'sources.json').write_text(json.dumps(['Alice — X : @alice', 'Bob — X : @bob']))
        aim.TWITTER_OPTIONS['max_posts'] = 5
        result = self.fetch(iter([self.user(), {'data': [self.post(str(i)) for i in range(5)],
                                                  'meta': {'next_token': 'next'}}]))
        self.assertEqual(result[0]['status'], 'partial')
        self.assertEqual(result[1]['status'], 'unavailable')
        self.assertEqual(self.state()['rotation'], 1)
        self.assertEqual(self.state()['accounts']['alice']['ranges'], [])
        self.fetch(iter([{'data': {'id': '124', 'username': 'bob'}},
                         {'data': [self.post(str(i + 10)) for i in range(5)], 'meta': {}}]))
        self.assertIn('/username/bob', self.calls[2].full_url)

    def test_auth_failure_stops_all_accounts_without_exposing_response(self):
        (self.root / 'sources.json').write_text(json.dumps(['Alice — X : @alice', 'Bob — X : @bob']))
        result = self.fetch(iter([HTTPError('https://api.x.com', 401, 'FAKE_SECRET', {}, None)]))
        self.assertEqual(len(self.calls), 1)
        self.assertTrue(all('HTTP 401' in r['limitations'] for r in result))
        self.assertNotIn('FAKE_SECRET', json.dumps(result))

    def test_budget_month_reset_and_id_reuse(self):
        self.fetch(iter([self.user(), {'data': [], 'meta': {}}]))
        state = self.state()
        state.update(month='2000-01', reserved_milliusd=5000)
        state['accounts']['alice']['ranges'] = []
        aim.atomic_write(self.root / 'private/twitter-state.json', aim.dumps(state))
        self.fetch(iter([{'data': [], 'meta': {}}]))
        self.assertEqual(len(self.calls), 3)
        self.assertEqual(self.state()['reserved_milliusd'], 0)

    def test_private_credentials_and_disabled_collection(self):
        self.credentials.chmod(0o644)
        with self.assertRaisesRegex(ValueError, '0600'):
            aim.twitter_credentials(self.credentials)
        self.credentials.chmod(0o600)
        symlink = self.root / 'link.json'
        symlink.symlink_to(self.credentials)
        with self.assertRaises(ValueError):
            aim.twitter_credentials(symlink)
        aim.TWITTER_OPTIONS['credentials'] = None
        result = self.fetch(iter([]))
        self.assertEqual(result[0]['status'], 'unavailable')
        self.assertFalse((self.root / 'private/twitter-state.json').exists())

    def test_historical_window_does_not_reuse_newer_coverage(self):
        self.fetch(iter([self.user(), {'data': [self.post()], 'meta': {}}]))
        self.start -= timedelta(days=10)
        self.end -= timedelta(days=10)
        result = self.fetch(iter([{'data': [], 'meta': {}}]))
        self.assertEqual(result[0]['posts'], [])
        self.assertEqual(len(self.calls), 3)

    def test_redirects_never_forward_token(self):
        self.assertIsNone(aim.NoTwitterRedirect().redirect_request(
            None, None, 302, '', {}, 'https://example.org'))


if __name__ == '__main__':
    unittest.main()
