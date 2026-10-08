# aimaths

An English-language AI and mathematics research digest, generated with Codex
and published as HTML by a standalone Python script.

Requires Python 3.9 or later on a Unix-like system and the Codex CLI for research
and synthesis. The Python script uses only the standard library.

```sh
python3 aim-cron.py --help
python3 aim-cron.py --init --private-dir /path/to/private-data --output-dir /path/to/html --logs-dir /path/to/logs
python3 aim-cron.py --private-dir /path/to/private-data --output-dir /path/to/html --logs-dir /path/to/logs
```

Keep private configuration, state, and logs outside the public HTML directory
and outside this repository. The script can be run periodically using cron.
See `--help` for source management, HTML rebuilding, and historical editions.

`--private-dir` (alias `--root`), `--output-dir`, and `--logs-dir` are mandatory
for every run, including initialization and offline actions. `--help` can be
used without them. The supplied HTML and logs paths are saved in the private
configuration on each run; saved values do not replace the required arguments.
The public HTML and private data directories must be separate and must not
contain one another. There are no default paths for these parameters.

`--logs-dir` controls the
rotating application log and Codex event/error logs, including historical runs
and log cleanup. Relative HTML and logs paths are resolved under the private directory.
The logs directory must not overlap the public HTML directory. Changing it
leaves existing logs in their previous location.

For a daily cron run, adapt the paths in [crontab.example](crontab.example),
initialize the directories once, then paste its cron entry into `crontab -e`.
The schedule uses the cron daemon's local timezone.
