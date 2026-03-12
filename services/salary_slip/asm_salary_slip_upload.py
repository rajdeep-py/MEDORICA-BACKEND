import os
import shutil
from io import BytesIO

from fastapi import UploadFile
from pypdf import PdfReader, PdfWriter


# Compress and save the uploaded PDF salary slip for an ASM.
def save_asm_salary_slip(upload_file: UploadFile, asm_id: str) -> str:
	base_dir = os.path.join("uploads", "salary_slips", asm_id)
	os.makedirs(base_dir, exist_ok=True)

	abs_path = os.path.join(base_dir, "salary_slip.pdf")

	pdf_bytes = upload_file.file.read()

	try:
		reader = PdfReader(BytesIO(pdf_bytes))
		writer = PdfWriter()
		for page in reader.pages:
			page.compress_content_streams()
			writer.add_page(page)
		output = BytesIO()
		writer.write(output)
		compressed_bytes = output.getvalue()
	except Exception:
		# If PDF is malformed or compression fails, save the original bytes.
		compressed_bytes = pdf_bytes

	with open(abs_path, "wb") as f:
		f.write(compressed_bytes)

	return abs_path.replace("\\", "/")


# Delete the salary slip directory for an ASM.
def delete_asm_salary_slip_assets(asm_id: str) -> None:
	base_dir = os.path.join("uploads", "salary_slips", asm_id)
	if os.path.exists(base_dir):
		shutil.rmtree(base_dir)
