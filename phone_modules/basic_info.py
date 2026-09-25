import phonenumbers
from phonenumbers import carrier, geocoder, timezone
from core.result import Result

def validate_phone(number: str) -> Result:
    try:
        parsed = phonenumbers.parse(number, None)
        if not phonenumbers.is_valid_number(parsed):
            return Result(site="PhoneBasic", exists=False, info={"valid": False})
        
        info = {
            "country": geocoder.description_for_number(parsed, "en"),
            "carrier": carrier.name_for_number(parsed, "en"),
            "timezone": list(timezone.time_zones_for_number(parsed)),
            "national": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL),
            "international": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
        }
        return Result(site="PhoneBasic", exists=True, info=info)
    except Exception as e:
        return Result(site="PhoneBasic", exists=None, info={}, error=str(e))
