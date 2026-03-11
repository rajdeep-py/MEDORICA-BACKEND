import time


# Generate appointment ID in the pattern: APT{timestamp_in_milliseconds}.
def generate_asm_appointment_id() -> str:
	timestamp_ms = int(time.time() * 1000)
	return f"APT{timestamp_ms}"
