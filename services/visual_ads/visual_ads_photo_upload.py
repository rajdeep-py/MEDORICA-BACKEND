import os
import re
import shutil
from io import BytesIO

from fastapi import UploadFile
from PIL import Image


def _sanitize_filename(value: str) -> str:
	cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value.strip())
	return cleaned.strip("_") or "ad_image"


# Compress, rename and store the uploaded ad image.
def save_visual_ad_image(upload_file: UploadFile, ad_id: str) -> str:
	os.makedirs("uploads", exist_ok=True)
	base_dir = os.path.join("uploads", "visual_ads")
	os.makedirs(base_dir, exist_ok=True)

	original_ext = os.path.splitext(upload_file.filename or "")[1].lower()
	allowed_ext = {".jpg", ".jpeg", ".png", ".webp"}
	ext = original_ext if original_ext in allowed_ext else ".jpg"
	filename = f"{ad_id}_image{ext}"
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


# Delete ad image assets.
def delete_visual_ad_image(ad_id: str) -> None:
	base_dir = os.path.join("uploads", "visual_ads")
	for ext in {".jpg", ".jpeg", ".png", ".webp"}:
		image_path = os.path.join(base_dir, f"{ad_id}_image{ext}")
		if os.path.exists(image_path):
			os.remove(image_path)
