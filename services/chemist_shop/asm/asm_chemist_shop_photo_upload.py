import os
import re
import shutil
from io import BytesIO

from fastapi import UploadFile
from PIL import Image


def _sanitize_filename(value: str) -> str:
	cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value.strip())
	return cleaned.strip("_") or "shop"


# Compress, rename and store chemist shop photo under uploads/chemist_shops/asm/{shop_id}/.
def save_asm_chemist_shop_photo(upload_file: UploadFile, shop_id: str, shop_name: str) -> str:
	base_dir = os.path.join("uploads", "chemist_shops", "asm", shop_id)
	os.makedirs(base_dir, exist_ok=True)

	shop_name_slug = _sanitize_filename(shop_name)
	original_ext = os.path.splitext(upload_file.filename or "")[1].lower()
	allowed_ext = {".jpg", ".jpeg", ".png", ".webp"}
	ext = original_ext if original_ext in allowed_ext else ".jpg"
	filename = f"{shop_name_slug}{ext}"
	abs_path = os.path.join(base_dir, filename)

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


# Compress, rename and store chemist shop bank passbook photo under uploads/chemist_shops/asm/{shop_id}/.
def save_asm_chemist_shop_bank_passbook_photo(upload_file: UploadFile, shop_id: str, shop_name: str) -> str:
	base_dir = os.path.join("uploads", "chemist_shops", "asm", shop_id)
	os.makedirs(base_dir, exist_ok=True)

	shop_name_slug = _sanitize_filename(shop_name)
	original_ext = os.path.splitext(upload_file.filename or "")[1].lower()
	allowed_ext = {".jpg", ".jpeg", ".png", ".webp"}
	ext = original_ext if original_ext in allowed_ext else ".jpg"
	filename = f"{shop_name_slug}_passbook{ext}"
	abs_path = os.path.join(base_dir, filename)

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


# Delete all stored chemist shop assets for a given shop ID.
def delete_asm_chemist_shop_assets(shop_id: str) -> None:
	base_dir = os.path.join("uploads", "chemist_shops", "asm", shop_id)
	if os.path.exists(base_dir):
		shutil.rmtree(base_dir)
