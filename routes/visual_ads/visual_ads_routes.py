from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from models.visual_ads.visual_ads_models import VisualAd
from services.visual_ads.visual_ads_id_generator import generate_visual_ad_id
from services.visual_ads.visual_ads_photo_upload import delete_visual_ad_image, save_visual_ad_image

router = APIRouter(prefix="/visual-ads", tags=["Visual Ads"])


class VisualAdResponseSchema(BaseModel):
	id: int
	ad_id: str
	medicine_name: str
	ad_image: Optional[str] = None
	created_at: datetime
	updated_at: datetime

	class Config:
		from_attributes = True


# Create a new Visual Ad record. Accepts form data with medicine name and required ad image. Returns the created Visual Ad details if successful, otherwise appropriate error messages.
@router.post("/post", response_model=VisualAdResponseSchema, status_code=status.HTTP_201_CREATED)
def create_visual_ad(
	medicine_name: str = Form(...),
	ad_image: UploadFile = File(...),
	db: Session = Depends(get_db),
):
	try:
		ad_id = generate_visual_ad_id(db)
	except Exception as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to generate ad ID") from exc

	new_ad = VisualAd(
		ad_id=ad_id,
		medicine_name=medicine_name,
	)

	try:
		new_ad.ad_image = save_visual_ad_image(ad_image, ad_id)
	except Exception as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ad image") from exc

	db.add(new_ad)
	db.commit()
	db.refresh(new_ad)
	return new_ad


# Fetch a Visual Ad record by its Ad ID. Returns the Visual Ad details if found, otherwise a 404 error.
@router.get("/get-by/{ad_id}", response_model=VisualAdResponseSchema)
def get_visual_ad_by_id(ad_id: str, db: Session = Depends(get_db)):
	record = db.query(VisualAd).filter(VisualAd.ad_id == ad_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visual Ad not found")
	return record


# Fetch all Visual Ad records. Returns a list of Visual Ad details.
@router.get("/get-all", response_model=list[VisualAdResponseSchema])
def get_all_visual_ads(db: Session = Depends(get_db)):
	return db.query(VisualAd).all()


# Update an existing Visual Ad record by its Ad ID. Accepts form data and optional image upload. Returns the updated Visual Ad details if successful, otherwise appropriate error messages.
@router.put("/update-by/{ad_id}", response_model=VisualAdResponseSchema)
def update_visual_ad_by_id(
	ad_id: str,
	medicine_name: Optional[str] = Form(None),
	ad_image: Optional[UploadFile] = File(None),
	db: Session = Depends(get_db),
):
	record = db.query(VisualAd).filter(VisualAd.ad_id == ad_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visual Ad not found")

	if medicine_name is not None:
		record.medicine_name = medicine_name

	if ad_image is not None:
		try:
			delete_visual_ad_image(record.ad_id)
			record.ad_image = save_visual_ad_image(ad_image, record.ad_id)
		except Exception as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ad image") from exc

	db.commit()
	db.refresh(record)
	return record


# Delete a Visual Ad record by its Ad ID. Returns a success message on successful deletion.
@router.delete("/delete-by/{ad_id}", status_code=status.HTTP_200_OK)
def delete_visual_ad_by_id(ad_id: str, db: Session = Depends(get_db)):
	record = db.query(VisualAd).filter(VisualAd.ad_id == ad_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visual Ad not found")

	try:
		delete_visual_ad_image(record.ad_id)
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Failed to delete visual ad image",
		) from exc

	db.delete(record)
	db.commit()
	return {"message": f"Visual Ad with id {ad_id} deleted successfully"}
