from typing import List, Callable
from .result import Result
import re
import subprocess
import json
import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Allow platform-specific integrations to be configured without changing the CLI.
# Missing third-party tools return structured errors; core modules still work.
PHONEINFOGA = os.path.expanduser(os.environ.get(
    "MYOSINT_PHONEINFOGA", str(Path.home() / "phoneinfoga" / "phoneinfoga")
))
SPIDERFOOT = os.path.expanduser(os.environ.get(
    "MYOSINT_SPIDERFOOT", str(Path.home() / "spiderfoot" / "sf.py")
))
SPIDERFOOT_DIR = os.path.expanduser(os.environ.get(
    "MYOSINT_SPIDERFOOT_DIR", str(Path(SPIDERFOOT).parent)
))


def run_phoneinfoga(phone: str) -> List[Result]:
    """Run PhoneInfoga and convert its output into My OSINT results."""
    results = []
    try:
        process = subprocess.run(
            [PHONEINFOGA, "scan", "-n", phone],
            capture_output=True, text=True, timeout=120
        )
        output = process.stdout + "\n" + process.stderr
        if process.returncode != 0:
            return [Result(site="Phone information", exists=None, info={},
                           error="Phone scanner failed")]
        found = False
        for line in output.splitlines():
            line = line.strip()
            if line and ":" in line and not line.startswith("DEBU"):
                key, value = line.split(":", 1)
                key, value = key.strip(), value.strip()
                if key and value:
                    results.append(Result(site="Phone information", exists=True, info={key: value}))
                    found = True
        if not found:
            results.append(Result(site="Phone information", exists=True, info={"status": "Scan completed"}))
    except subprocess.TimeoutExpired:
        results.append(Result(site="Phone information", exists=None, info={}, error="Scanner timed out"))
    except Exception as e:
        results.append(Result(site="Phone information", exists=None, info={}, error=str(e)))
    return results


def run_spiderfoot(target: str, module: str) -> List[Result]:
    """Run one configured SpiderFoot module and convert JSON events."""
    results = []
    try:
        process = subprocess.run(
            [sys.executable, SPIDERFOOT, "-s", target, "-m", module, "-o", "json", "-q"],
            capture_output=True, text=True, timeout=180, cwd=SPIDERFOOT_DIR
        )
        for line in process.stdout.splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            event_type, data = item.get("type"), item.get("data")
            if not event_type or not data:
                continue
            if event_type in ("Email Address", "Phone Number") and str(data).strip() == target.strip():
                continue
            results.append(Result(site="OSINT result", exists=True, info={"type": event_type, "data": data}))
        if not results and process.returncode != 0:
            results.append(Result(site="OSINT result", exists=None, info={}, error="SpiderFoot module failed"))
    except subprocess.TimeoutExpired:
        results.append(Result(site="OSINT result", exists=None, info={}, error="OSINT module timed out"))
    except Exception as e:
        results.append(Result(site="OSINT result", exists=None, info={}, error=str(e)))
    return results


def run_spiderfoot_modules(target: str, modules: List[str]) -> List[Result]:
    results = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(run_spiderfoot, target, module) for module in modules]
        for future in as_completed(futures):
            try:
                results.extend(future.result())
            except Exception as e:
                results.append(Result(site="OSINT result", exists=None, info={}, error=str(e)))
    return results


def run_modules(target: str, modules: List[Callable], max_workers: int = 8) -> List[Result]:
    results = []
    # Preserve the original modules and result format used by main.py.
    for mod in modules:
        try:
            result = mod(target)
            results.extend(result if isinstance(result, list) else [result])
        except Exception as e:
            results.append(Result(site=getattr(mod, "__name__", "unknown"), exists=None, info={}, error=str(e)))

    if re.fullmatch(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', target):
        backend_tasks = []
        try:
            from email_modules.holehe_adapter import validate_holehe
            backend_tasks.append(("holehe", lambda: validate_holehe(target)))
        except Exception as e:
            results.append(Result(site="Holehe", exists=None, info={}, error=f"Could not load Holehe: {e}"))
        for module in ["sfp_email", "sfp_accounts", "sfp_emailformat", "sfp_debounce", "sfp_emailrep"]:
            backend_tasks.append((module, lambda m=module: run_spiderfoot(target, m)))
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(task): name for name, task in backend_tasks}
            for future in as_completed(futures):
                try:
                    value = future.result()
                    if isinstance(value, list):
                        results.extend(value)
                    elif value:
                        results.append(value)
                except Exception as e:
                    results.append(Result(site="Email Services", exists=None, info={}, error=str(e)))
    elif re.fullmatch(r'\+?[0-9][0-9\s().-]{6,}', target):
        backend_tasks = [
            ("phoneinfoga", lambda: run_phoneinfoga(target)),
            ("spiderfoot", lambda: run_spiderfoot(target, "sfp_phone"))
        ]
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {executor.submit(task): name for name, task in backend_tasks}
            for future in as_completed(futures):
                try:
                    value = future.result()
                    if isinstance(value, list):
                        results.extend(value)
                except Exception as e:
                    results.append(Result(site="Phone Services", exists=None, info={}, error=str(e)))
    return results
