import requests
from core.result import Result

def validate_twitter(email: str) -> Result:
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36"
    }
    try:
        r = requests.get(
            f"https://api.twitter.com/i/users/email_available.json?email={email}",
            headers=headers,
            timeout=12
        )
        # This endpoint sometimes still responds
        data = r.json() if r.status_code == 200 else {}
        exists = data.get("taken", False) if isinstance(data, dict) else False
        return Result(site="Twitter/X", exists=exists, info={"status_code": r.status_code, "raw": data})
    except Exception as e:
        return Result(site="Twitter/X", exists=None, info={}, error=str(e))
