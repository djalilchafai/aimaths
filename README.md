# aimaths

An English-language AI and mathematics research digest, generated with Codex
and published as HTML by a standalone Python script.

Requires Python 3.9 or later on a Unix-like system and the Codex CLI for research
and synthesis. The Python script uses only the standard library.

Before daily or historical synthesis, the script reads configured Bluesky feeds
through the public API without credentials, including handles in legacy source
entries. It passes dated posts and collection limitations to Codex. Reads are
bounded to 10 accounts, 3 pages (300 posts) per account, 10 seconds per request,
and a 60-second collection budget. Replies, reposts and pinned posts are excluded;
historical coverage can be incomplete. Failures become coverage gaps and do not
stop other research. HTML-only rebuilds make no feed requests.

X collection is optional and uses the official paid API, not browser automation.
Without a credential parameter, X handles remain search leads and timeline access
is reported as unavailable. Normal X Premium subscriptions are not required.

```sh
python3 aim-cron.py --help
python3 aim-cron.py --init --private-dir /path/to/private-data --output-dir /path/to/html
python3 aim-cron.py --private-dir /path/to/private-data --output-dir /path/to/html
```

Keep private configuration, state, and logs outside the public HTML directory
and outside this repository. The script can be run periodically using cron.
See `--help` for source management, HTML rebuilding, and historical editions.

After changing the webpage interface, use `--force` to rebuild the latest page,
archive pages, and archive browser from saved editions without calling Codex:

```sh
python3 aim-cron.py --force --private-dir /path/to/private-data --output-dir /path/to/html
```

`--render-only` and `--rebuild-html` are aliases. A saved edition is required.
Previously, `--force` started a new research run; it now only refreshes HTML.

`--private-dir` (alias `--root`) and `--output-dir` are mandatory for every
run, including initialization and offline actions. `--help` can be used without
them. The supplied HTML path is saved in the private configuration on each run;
the saved value does not replace the required argument. The public HTML and
private data directories must be separate and must not contain one another.
There are no default paths for these parameters.

Application messages go to stdout; argument and initialization errors go to
stderr. The script does not create a rotating application log. For cron, redirect
both streams to a private log file as shown in the example, and arrange rotation
if needed. The script sets its own private-file umask.

Codex event/error files are kept in `logs/` under the private directory, with
automatic cleanup. Existing installations retain their saved `logs_dir` setting;
there is no `--logs-dir` command-line parameter. The logs directory must not
overlap the public HTML directory.

For a daily cron run, adapt the paths in [crontab.example](crontab.example),
initialize the directories once, then paste its cron entry into `crontab -e`.
The schedule uses the cron daemon's local timezone.

## Optional Twitter/X API coverage

Create an app in the [X Developer Console](https://console.x.com/) and obtain its
Bearer Token. API access uses prepaid credits. Set a **$5 spending limit** in the
console; this is the authoritative account-wide billing safeguard.
See [access instructions](https://docs.x.com/x-api/getting-started/getting-access)
and [pricing](https://docs.x.com/x-api/getting-started/pricing).

Create a private text file, for example `/path/to/private-data/twitter.token`,
containing **only the Bearer Token** copied from your app's **Keys and tokens**
section. A trailing newline is fine. Keep the file **outside this repository and
the public HTML directory**. Do not put your Gmail password in it.

The file must belong to the current user, be a regular file (not a symlink), and
have no group/other permissions:

```sh
chmod 600 /path/to/private-data/twitter.token
```

Enable collection on each research run, including in your cron command:

```sh
python3 aim-cron.py --private-dir /path/to/private-data --output-dir /path/to/html \
  --twitter-token-file /path/to/private-data/twitter.token \
  --twitter-monthly-budget 500 --twitter-max-posts 30
```

`--twitter-monthly-budget` is in **USD cents**: `500` means $5, `200` means $2.
The default is 500. `--twitter-max-posts` defaults to 30 reads per research window,
shared across accounts. These parameters are not saved in configuration; repeat
them on each run. Omitting both credential options disables all X requests.

The previous JSON format remains supported with
`--twitter-credentials /path/to/private-data/twitter.json`:

```json
{
  "bearer_token": "YOUR_X_API_BEARER_TOKEN"
}
```

Use one credential option at a time. Both formats have the same privacy and file
permission requirements. The token itself is never a command-line argument.
Initialization, source management, demos and HTML-only rebuilding make no X calls.

Enabled X sources, including legacy `Name — X : @handle` entries, are collected.
User IDs and dated posts are cached privately in `private/twitter-state.json`.
Fully collected intervals are reused, so overlapping daily windows do not reread
those posts. Replies and reposts are excluded. Requests use five-post pages,
at most three pages per account and a 60-second collection budget. Account priority
rotates when the run budget prevents all accounts being checked. Busy accounts,
pagination caps and skipped accounts are explicitly reported as coverage gaps.
Partial intervals may be fetched again; the cache does not claim completeness.
Retained evidence covers at most 40 days / 1,500 posts per account. Historical runs
also consume the shared budget, and old timelines may not be available.

The local ledger estimates $0.005 per post and $0.010 per user lookup. It reserves
maximum request cost **before** each request and refunds unused reservations only
after a valid response. Ambiguous failures keep their reservation; this can stop
collection earlier than actual billing. There are no automatic retries. HTTP
401/402/403/429 stops further X collection in that window; other research continues.
Token values and upstream error bodies are never passed to Codex or logged.

The ledger resets at the start of each **UTC calendar month**, which can differ
from X's billing cycle. It tracks this installation only, not other apps or users,
and prices may change. Keep the console spending limit enabled, and do not delete
the state file to resume collection: deleting it loses budget accounting.
At current prices $5 buys roughly 1,000 post reads before user lookup costs;
30 reads/day leaves some room for lookups in a 31-day month. This bounds costs,
but does not guarantee full coverage of all configured accounts.

Run the offline collector checks with:

```sh
python3 -m unittest discover -s tests -v
```
