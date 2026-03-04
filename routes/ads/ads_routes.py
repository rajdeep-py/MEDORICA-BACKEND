import os
import shutil
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from PIL import Image
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from models.ads.ads_models import Advertisement

router = APIRouter(prefix="/ads", tags=["Advertisements"])


class AdvertisementResponseSchema(BaseModel):
	id: int
	ttitle: Optional[str] = None
	subtitle: Optional[str] = None
	cta_button_text: Optional[str] = None
	website_link: Optional[str] = None
	image: Optional[str] = None
	created_at: datetime
	updated_at: datetime

	class Config:
		from_attributes = True


# Compress and save an uploaded image into the advertisement-specific upload folder.
def save_compressed_ad_image(ad_id: int, image_file: UploadFile) -> str:
	upload_dir = os.path.join("uploads", "ads", str(ad_id))
	os.makedirs(upload_dir, exist_ok=True)

	image_path = os.path.join(upload_dir, "image.jpg")
	pil_image = Image.open(image_file.file)
	if pil_image.mode not in ("RGB",):
		pil_image = pil_image.convert("RGB")
	pil_image.save(image_path, format="JPEG", optimize=True, quality=70)

	return f"/uploads/ads/{ad_id}/image.jpg"


# Create a new advertisement and optionally upload/compress its image.
@router.post("/", response_model=AdvertisementResponseSchema, status_code=status.HTTP_201_CREATED)
def create_advertisement(
	ttitle: Optional[str] = Form(default=None),
	subtitle: Optional[str] = Form(default=None),
	cta_button_text: Optional[str] = Form(default=None),
	website_link: Optional[str] = Form(default=None),
	image: Optional[UploadFile] = File(default=None),
	db: Session = Depends(get_db),
):
	new_ad = Advertisement(
		ttitle=ttitle,
		subtitle=subtitle,
		cta_button_text=cta_button_text,
		website_link=website_link,
	)
	db.add(new_ad)
	db.commit()
	db.refresh(new_ad)

	if image is not None:
		new_ad.image = save_compressed_ad_image(new_ad.id, image)
		db.commit()
		db.refresh(new_ad)

	return new_ad


# Fetch all advertisements.
@router.get("/", response_model=list[AdvertisementResponseSchema])
def get_all_advertisements(db: Session = Depends(get_db)):
	return db.query(Advertisement).all()


# Fetch a single advertisement by its ID.
@router.get("/{ad_id}", response_model=AdvertisementResponseSchema)
def get_advertisement_by_id(ad_id: int, db: Session = Depends(get_db)):
	ad = db.query(Advertisement).filter(Advertisement.id == ad_id).first()
	if not ad:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Advertisement not found")
	return ad


# Update an advertisement by its ID and optionally replace its image.
@router.put("/{ad_id}", response_model=AdvertisementResponseSchema)
def update_advertisement_by_id(
	ad_id: int,
	ttitle: Optional[str] = Form(default=None),
	subtitle: Optional[str] = Form(default=None),
	cta_button_text: Optional[str] = Form(default=None),
	website_link: Optional[str] = Form(default=None),
	image: Optional[UploadFile] = File(default=None),
	db: Session = Depends(get_db),
):
	ad = db.query(Advertisement).filter(Advertisement.id == ad_id).first()
	if not ad:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Advertisement not found")

	if ttitle is not None:
		ad.ttitle = ttitle
	if subtitle is not None:
		ad.subtitle = subtitle
	if cta_button_text is not None:
		ad.cta_button_text = cta_button_text
	if website_link is not None:
		ad.website_link = website_link

	if image is not None:
		upload_dir = os.path.join("uploads", "ads", str(ad_id))
		if os.path.isdir(upload_dir):
			shutil.rmtree(upload_dir)
		ad.image = save_compressed_ad_image(ad_id, image)

	db.commit()
	db.refresh(ad)
	return ad


# Delete an advertisement by its ID and remove its upload directory.
@router.delete("/{ad_id}", status_code=status.HTTP_200_OK)
def delete_advertisement_by_id(ad_id: int, db: Session = Depends(get_db)):
	ad = db.query(Advertisement).filter(Advertisement.id == ad_id).first()
	if not ad:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Advertisement not found")

	upload_dir = os.path.join("uploads", "ads", str(ad_id))
	if os.path.isdir(upload_dir):
		shutil.rmtree(upload_dir)

	db.delete(ad)
	db.commit()
	return {"message": f"Advertisement with id {ad_id} deleted successfully"}

