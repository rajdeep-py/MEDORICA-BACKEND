import re


def _extract_10_digit_phone(phone_no: str) -> str:
	if not phone_no:
		raise ValueError("Phone number is required")

	digits = re.sub(r"\D", "", phone_no)
	if len(digits) != 10:
		raise ValueError("Phone number must contain exactly 10 digits")

	return digits


# Generate Distributor ID in the format: DIST + 10 digit phone number.
def generate_distributor_id(phone_no: str) -> str:
	return f"DIST{_extract_10_digit_phone(phone_no)}"
