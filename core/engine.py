from typing import List, Callable
from .result import Result
import re
import subprocess
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed


PHONEINFOGA = os.path.expanduser("~/phoneinfoga/phoneinfoga")
SPIDERFOOT = os.path.expanduser("~/spiderfoot/sf.py")


def run_phoneinfoga(phone: str) -> List[Result]:
    """Run PhoneInfoga and convert its output into My OSINT results."""
    results = []

    try:
        process = subprocess.run(
            [
                PHONEINFOGA,
                "scan",
                "-n",
                phone
            ],
            capture_output=True,
            text=True,
            timeout=120
        )

        output = process.stdout + "\n" + process.stderr

        if process.returncode != 0:
            return [
                Result(
                    site="Phone information",
                    exists=None,
                    info={},
                    error="Phone scanner failed"
                )
            ]

        found = False

        for line in output.splitlines():
            line = line.strip()

            if not line:
                continue

            # Keep useful structured-looking information.
            if ":" in line and not line.startswith("DEBU"):
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                if key and value:
                    results.append(
                        Result(
                            site="Phone information",
                            exists=True,
                            info={key: value}
                        )
                    )
                    found = True

        if not found:
            results.append(
                Result(
                    site="Phone information",
                    exists=True,
                    info={"status": "Scan completed"}
                )
            )

    except subprocess.TimeoutExpired:
        results.append(
            Result(
                site="Phone information",
                exists=None,
                info={},
                error="Scanner timed out"
            )
        )

    except Exception as e:
        results.append(
            Result(
                site="Phone information",
                exists=None,
                info={},
                error=str(e)
            )
        )

    return results


def run_spiderfoot(target: str, module: str) -> List[Result]:
    """Run one restricted SpiderFoot module and convert JSON events."""
    results = []

    try:
        process = subprocess.run(
            [
                "python",
                SPIDERFOOT,
                "-s",
                target,
                "-m",
                module,
                "-o",
                "json",
                "-q"
            ],
            capture_output=True,
            text=True,
            timeout=180,
            cwd=os.path.expanduser("~/spiderfoot")
        )

        output = process.stdout

        for line in output.splitlines():
            line = line.strip()

            if not line.startswith("{"):
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue

            event_type = item.get("type")
            data = item.get("data")

            if not event_type or not data:
                continue

            # Ignore SpiderFoot's own target echo.
            if event_type in ("Email Address", "Phone Number"):
                if str(data).strip() == target.strip():
                    continue

            results.append(
                Result(
                    site="OSINT result",
                    exists=True,
                    info={
                        "type": event_type,
                        "data": data
                    }
                )
            )

        if not results and process.returncode != 0:
            results.append(
                Result(
                    site="OSINT result",
                    exists=None,
                    info={},
                    error="SpiderFoot module failed"
                )
            )

    except subprocess.TimeoutExpired:
        results.append(
            Result(
                site="OSINT result",
                exists=None,
                info={},
                error="OSINT module timed out"
            )
        )

    except Exception as e:
        results.append(
            Result(
                site="OSINT result",
                exists=None,
                info={},
                error=str(e)
            )
        )

    return results


def run_spiderfoot_modules(target: str, modules: List[str]) -> List[Result]:
    """Run selected SpiderFoot modules concurrently."""
    results = []

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(run_spiderfoot, target, module)
            for module in modules
        ]

        for future in as_completed(futures):
            try:
                results.extend(future.result())
            except Exception as e:
                results.append(
                    Result(
                        site="OSINT result",
                        exists=None,
                        info={},
                        error=str(e)
                    )
                )

    return results


def run_modules(
    target: str,
    modules: List[Callable],
    max_workers: int = 8
) -> List[Result]:

    results = []

    # Run the user's existing modules.
    for mod in modules:
        try:
            result = mod(target)

            if isinstance(result, list):
                results.extend(result)
            else:
                results.append(result)

        except Exception as e:
            results.append(
                Result(
                    site="unknown",
                    exists=None,
                    info={},
                    error=str(e)
                )
            )

    # -------------------------
    # EMAIL
    # -------------------------
    if re.fullmatch(
        r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
        target
    ):

        backend_tasks = []

        # Holehe
        try:
            from email_modules.holehe_adapter import validate_holehe
            backend_tasks.append(
                ("holehe", lambda: validate_holehe(target))
            )
        except Exception:
            pass

        # SpiderFoot
        email_modules = [
            "sfp_email",
            "sfp_accounts",
            "sfp_emailformat",
            "sfp_debounce",
            "sfp_emailrep"
        ]

        for module in email_modules:
            backend_tasks.append(
                (
                    module,
                    lambda m=module: run_spiderfoot(target, m)
                )
            )

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(task): name
                for name, task in backend_tasks
            }

            for future in as_completed(futures):
                try:
                    backend_results = future.result()

                    if isinstance(backend_results, list):
                        results.extend(backend_results)
                    elif backend_results:
                        results.append(backend_results)

                except Exception as e:
                    results.append(
                        Result(
                            site="Email Services",
                            exists=None,
                            info={},
                            error=str(e)
                        )
                    )

    # -------------------------
    # PHONE
    # -------------------------
    elif re.fullmatch(
        r'\+?[0-9][0-9\s().-]{6,}',
        target
    ):

        backend_tasks = [
            (
                "phoneinfoga",
                lambda: run_phoneinfoga(target)
            ),
            (
                "spiderfoot",
                lambda: run_spiderfoot(
                    target,
                    "sfp_phone"
                )
            )
        ]

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(task): name
                for name, task in backend_tasks
            }

            for future in as_completed(futures):
                try:
                    backend_results = future.result()

                    if isinstance(backend_results, list):
                        results.extend(backend_results)

                except Exception as e:
                    results.append(
                        Result(
                            site="Phone Services",
                            exists=None,
                            info={},
                            error=str(e)
                        )
                    )

    return results
