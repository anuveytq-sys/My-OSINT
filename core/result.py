from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class Result:
    site: str
    exists: Optional[bool]
    info: Dict[str, Any]
    error: Optional[str] = None
