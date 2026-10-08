# aimaths

An English-language AI and mathematics research digest, generated with Codex
and published as HTML by a standalone Python script.

Requires Python 3.9 or later on a Unix-like system and the Codex CLI for research
and synthesis. The Python script uses only the standard library.

```sh
python3 aim-cron.py --help
python3 aim-cron.py --init --private-dir /path/to/private-data --output-dir /path/to/html
python3 aim-cron.py --private-dir /path/to/private-data --output-dir /path/to/html
```

Keep private configuration, state, and logs outside the public HTML directory
and outside this repository. The script can be run periodically using cron.
See `--help` for source management, HTML rebuilding, and historical editions.

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
