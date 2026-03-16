import os
import shutil
from io import BytesIO

from fastapi import UploadFile
from pypdf import PdfReader, PdfWriter

# Compress and save the uploaded PDF salary slip for a Medical Representative.
def save_mr_salary_slip(upload_file: UploadFile, mr_id: str) -> str:
	base_dir = os.path.join("uploads", "salary_slips", mr_id)
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

# Delete the salary slip directory for a Medical Representative.
def delete_mr_salary_slip_assets(mr_id: str) -> None:
	base_dir = os.path.join("uploads", "salary_slips", mr_id)
	if os.path.exists(base_dir):
		shutil.rmtree(base_dir)
