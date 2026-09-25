import requests
from core.result import Result

def validate_github(email: str) -> Result:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; OSINT-Tool/1.0)"}
    try:
        r = requests.get(
            f"https://api.github.com/search/users?q={email}+in:email",
            headers=headers,
            timeout=10
        )
        exists = r.status_code == 200 and r.json().get("total_count", 0) > 0
        return Result(site="GitHub", exists=exists, info={"status_code": r.status_code})
    except Exception as e:
        return Result(site="GitHub", exists=None, info={}, error=str(e))
