import requests
from core.result import Result

def validate_instagram(email: str) -> Result:
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36"
    }
    try:
        # Basic existence signal (Instagram is strict, this is limited)
        r = requests.get(
            f"https://www.instagram.com/accounts/account_recovery/?email={email}",
            headers=headers,
            timeout=12,
            allow_redirects=False
        )
        exists = r.status_code in [200, 302]
        return Result(site="Instagram", exists=exists, info={"status_code": r.status_code})
    except Exception as e:
        return Result(site="Instagram", exists=None, info={}, error=str(e))
