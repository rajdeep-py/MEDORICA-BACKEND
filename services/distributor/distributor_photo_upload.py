import os
import re
import shutil
from io import BytesIO

from fastapi import UploadFile
from PIL import Image


def _sanitize_filename(value: str) -> str:
	cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value.strip())
	return cleaned.strip("_") or "distributor"


# Compress, rename and store the uploaded profile photo for a Distributor.
def save_distributor_photo(upload_file: UploadFile, distributor_id: str, dist_name: str) -> str:
	os.makedirs("uploads", exist_ok=True)
	base_dir = os.path.join("uploads", "distributor", distributor_id)
	os.makedirs(base_dir, exist_ok=True)

	dist_name_slug = _sanitize_filename(dist_name)
	original_ext = os.path.splitext(upload_file.filename or "")[1].lower()
	allowed_ext = {".jpg", ".jpeg", ".png", ".webp"}
	ext = original_ext if original_ext in allowed_ext else ".jpg"
	filename = f"{dist_name_slug}_photo{ext}"
	abs_path = os.path.join(base_dir, filename)

	# Load image in memory, then save with compression tuned to extension type.
	image_bytes = upload_file.file.read()
	with Image.open(BytesIO(image_bytes)) as image:
		if ext in {".jpg", ".jpeg"}:
			if image.mode not in ("RGB", "L"):
				image = image.convert("RGB")
			image.save(abs_path, format="JPEG", optimize=True, quality=70)
		elif ext == ".png":
			image.save(abs_path, format="PNG", optimize=True, compress_level=9)
		elif ext == ".webp":
			if image.mode not in ("RGB", "RGBA"):
				image = image.convert("RGB")
			image.save(abs_path, format="WEBP", quality=70, method=6)
		else:
			if image.mode not in ("RGB", "L"):
				image = image.convert("RGB")
			image.save(abs_path, format="JPEG", optimize=True, quality=70)

	return abs_path.replace("\\", "/")


# Delete profile photo assets for a Distributor.
def delete_distributor_photo_assets(distributor_id: str) -> None:
	base_dir = os.path.join("uploads", "distributor", distributor_id)
	if os.path.exists(base_dir):
		shutil.rmtree(base_dir)
