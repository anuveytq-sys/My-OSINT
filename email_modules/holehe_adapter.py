import trio
import httpx

from holehe.core import import_submodules, get_functions
from core.result import Result


async def run_one(module, email, client, out, semaphore):
    async with semaphore:
        try:
            await module(email, client, out)
        except Exception as e:
            name = getattr(module, "__name__", "unknown")
            out.append({
                "name": name,
                "domain": name,
                "exists": False,
                "rateLimit": False,
                "error": True,
                "error_message": str(e),
                "emailrecovery": None,
                "phoneNumber": None,
                "others": None
            })


def validate_holehe(email: str):
    async def scan():
        modules = import_submodules("holehe.modules")
        websites = get_functions(modules)

        # Avoid running the same module/domain more than once.
        unique = {}
        for module in websites:
            name = getattr(module, "__name__", "")
            unique[name] = module

        websites = list(unique.values())

        out = []
        semaphore = trio.Semaphore(5)

        timeout = httpx.Timeout(10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            async with trio.open_nursery() as nursery:
                for website in websites:
                    nursery.start_soon(
                        run_one,
                        website,
                        email,
                        client,
                        out,
                        semaphore
                    )

        return out

    try:
        results = trio.run(scan)

        converted = []

        for item in results:
            site = item.get("domain") or item.get("name") or "Unknown"

            if item.get("rateLimit"):
                converted.append(
                    Result(
                        site=site,
                        exists=None,
                        info={},
                        error="Rate limited by service"
                    )
                )

            elif item.get("error"):
                error = item.get("error_message") or "Module error"

                converted.append(
                    Result(
                        site=site,
                        exists=None,
                        info={},
                        error=error
                    )
                )

            elif item.get("exists") is True:
                info = {}

                if item.get("emailrecovery"):
                    info["email_recovery"] = item["emailrecovery"]

                if item.get("phoneNumber"):
                    info["phone_number"] = item["phoneNumber"]

                if item.get("others"):
                    info["additional_info"] = item["others"]

                converted.append(
                    Result(
                        site=site,
                        exists=True,
                        info=info
                    )
                )

            else:
                converted.append(
                    Result(
                        site=site,
                        exists=False,
                        info={}
                    )
                )

        return converted

    except Exception as e:
        return [
            Result(
                site="Email Services",
                exists=None,
                info={},
                error=str(e)
            )
        ]
