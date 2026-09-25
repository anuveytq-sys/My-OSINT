import phonenumbers
from phonenumbers import carrier, geocoder, timezone, PhoneNumberType
from core.result import Result

def validate_phone_enhanced(number: str) -> Result:
    try:
        parsed = phonenumbers.parse(number, None)

        if not phonenumbers.is_possible_number(parsed):
            return Result(site="PhoneEnhanced", exists=False, info={"valid": False, "reason": "Not possible"})

        if not phonenumbers.is_valid_number(parsed):
            return Result(site="PhoneEnhanced", exists=False, info={"valid": False, "reason": "Invalid"})

        number_type = phonenumbers.number_type(parsed)
        type_name = {
            PhoneNumberType.MOBILE: "Mobile",
            PhoneNumberType.FIXED_LINE: "Landline",
            PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fixed or Mobile",
            PhoneNumberType.TOLL_FREE: "Toll Free",
            PhoneNumberType.PREMIUM_RATE: "Premium",
            PhoneNumberType.VOIP: "VoIP",
            PhoneNumberType.UNKNOWN: "Unknown"
        }.get(number_type, "Other")

        info = {
            "valid": True,
            "country": geocoder.description_for_number(parsed, "en"),
            "region": geocoder.description_for_number(parsed, "en"),
            "carrier": carrier.name_for_number(parsed, "en") or "Unknown",
            "timezone": list(timezone.time_zones_for_number(parsed)),
            "type": type_name,
            "national": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL),
            "international": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
            "e164": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164),
        }
        return Result(site="PhoneEnhanced", exists=True, info=info)
    except Exception as e:
        return Result(site="PhoneEnhanced", exists=None, info={}, error=str(e))
