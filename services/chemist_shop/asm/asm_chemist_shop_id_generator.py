import re


# Generate chemist shop ID in the pattern: SHOP{phone_no_digits}.
def generate_asm_chemist_shop_id(phone_no: str) -> str:
	if phone_no is None or phone_no.strip() == "":
		raise ValueError("Phone number is required")

	phone_digits = re.sub(r"\D", "", phone_no)
	if phone_digits == "":
		raise ValueError("Phone number must contain digits")

	return f"SHOP{phone_digits}"
