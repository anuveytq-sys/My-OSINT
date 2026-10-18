# My-OSINT Desktop

A browser-based dashboard for the existing My-OSINT email, phone, and username workflows. The CLI remains available; the web app is an additional interface that calls the existing Python modules and engine.

**Important:** scans make real requests to external services. Service APIs and website behaviour change; requests may be rate-limited, blocked, incomplete, or return false signals. A result is not proof of identity. Use only for lawful, authorized research.

## Features

- Dark neon investigation dashboard, responsive on desktop and mobile.
- Email scans using the existing GitHub, Reddit, Instagram, X and Holehe modules, plus configured SpiderFoot email modules.
- Phone scans using existing number metadata modules and optional PhoneInfoga / SpiderFoot integrations.
- Username scans through the existing `user-scanner -u` command.
- Live scan state and operation feed, structured results, local SQLite history, JSON export.
- The original `python main.py -e`, `-p`, and `-u` CLI remains available.

## Run on Windows (PowerShell)

Install Python 3.11 or newer from [python.org](https://www.python.org/downloads/), and enable **Add Python to PATH** during setup. Then open PowerShell:

```powershell
git clone https://github.com/anuveytq-sys/My-OSINT.git
cd My-OSINT
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run-web.ps1
```

Open **http://127.0.0.1:5050** in your browser. Keep the PowerShell window open while using the app. Stop it with Ctrl+C.

The first run creates a local `.venv` and installs the Python requirements. The SQLite scan history is stored locally in `myosint_history.sqlite3` (ignored by Git).

## Run on Termux / Linux / macOS

```bash
git clone https://github.com/anuveytq-sys/My-OSINT.git
cd My-OSINT
python -m venv .venv
# Termux may need its supported Python packages and pip workflow.
. .venv/bin/activate
python -m pip install -r requirements.txt
python webapp.py
```

Open **http://127.0.0.1:5050** on the same device. On Android, a browser on the same device can access the local server. The existing Termux-specific `install.sh` is still available for its original setup.

## CLI remains available

```bash
python main.py -e "example@example.com"
python main.py -p "+919876543210"
python main.py -u "example_username"
```

## Optional third-party integrations

PhoneInfoga and SpiderFoot are optional external programs, not Python modules bundled by this web UI. If installed outside the default locations, configure their paths before starting the app.

PowerShell example:

```powershell
$env:MYOSINT_PHONEINFOGA = "C:\\tools\\phoneinfoga\\phoneinfoga.exe"
$env:MYOSINT_SPIDERFOOT = "C:\\tools\\spiderfoot\\sf.py"
$env:MYOSINT_SPIDERFOOT_DIR = "C:\\tools\\spiderfoot"
.\run-web.ps1
```

The configured files and their own dependencies must exist. If a backend is not installed or compatible with your operating system, its result will show an error; the other modules can still run. External tool behaviour is not guaranteed across platforms.

## Security and deployment

By default, the server binds to **127.0.0.1**, so it is accessible only from your own device. Do not change the host to `0.0.0.0` or expose this dashboard to the public internet as-is. Before public hosting, add authentication, CSRF protections, rate limiting, job limits, secure secret handling, deployment-grade server configuration, and a review of data retention. Scan targets and results are stored locally in the SQLite history file.

## Notes on accuracy

- “FOUND” is a candidate signal, not confirmation that a person owns an account.
- “NOT FOUND” can mean a service did not expose a signal; it does not prove absence.
- “ERROR / UNKNOWN” includes module failures, blocked requests, and unavailable integrations.
- Phone metadata such as region, carrier and time zones is based on numbering-plan metadata; it does not reveal a live GPS location.
- The current app preserves the existing module set; it cannot make third-party APIs return data they do not expose.

## License

My-OSINT's original code is licensed under MIT. Third-party projects retain their own licenses and terms.
