import requests
from core.result import Result

def validate_reddit(email: str) -> Result:
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36"
    }
    try:
        # Simple public check (not perfect but works for basic OSINT)
        url = f"https://www.reddit.com/search/?q={email}&type=user"
        r = requests.get(url, headers=headers, timeout=12)
        exists = r.status_code == 200 and "users" in r.text.lower()
        return Result(site="Reddit", exists=exists, info={"status_code": r.status_code})
    except Exception as e:
        return Result(site="Reddit", exists=None, info={}, error=str(e))
