from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from models.about_us.about_us_models import AboutUs

router = APIRouter(prefix="/about-us", tags=["About Us"])


class AboutUsBaseSchema(BaseModel):
	company_about: Optional[str] = None
	director_message: Optional[str] = None
	phn_no: Optional[str] = None
	email: Optional[str] = None
	website: Optional[str] = None
	address: Optional[str] = None
	office_address: Optional[str] = None
	instagram_link: Optional[str] = None
	facebook_link: Optional[str] = None
	linkedin_link: Optional[str] = None
	youtube_link: Optional[str] = None


class AboutUsCreateSchema(AboutUsBaseSchema):
	pass


class AboutUsUpdateSchema(AboutUsBaseSchema):
	pass


class AboutUsResponseSchema(AboutUsBaseSchema):
	id: int
	created_at: datetime
	updated_at: datetime

	class Config:
		from_attributes = True


@router.post("/post", response_model=AboutUsResponseSchema, status_code=status.HTTP_201_CREATED)
# Create a new About Us record.
def create_about_us(payload: AboutUsCreateSchema, db: Session = Depends(get_db)):
	new_record = AboutUs(**payload.model_dump())
	db.add(new_record)
	db.commit()
	db.refresh(new_record)
	return new_record


@router.get("/get-all", response_model=list[AboutUsResponseSchema])
# Fetch all About Us records.
def get_all_about_us(db: Session = Depends(get_db)):
	return db.query(AboutUs).all()


@router.get("/get-by/{about_us_id}", response_model=AboutUsResponseSchema)
# Fetch a single About Us record by its ID.
def get_about_us_by_id(about_us_id: int, db: Session = Depends(get_db)):
	record = db.query(AboutUs).filter(AboutUs.id == about_us_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="About Us entry not found")
	return record


@router.put("/update-by/{about_us_id}", response_model=AboutUsResponseSchema)
# Update an existing About Us record by its ID.
def update_about_us_by_id(about_us_id: int, payload: AboutUsUpdateSchema, db: Session = Depends(get_db)):
	record = db.query(AboutUs).filter(AboutUs.id == about_us_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="About Us entry not found")

	for field, value in payload.model_dump(exclude_unset=True).items():
		setattr(record, field, value)

	db.commit()
	db.refresh(record)
	return record


@router.delete("/delete-by/{about_us_id}", status_code=status.HTTP_200_OK)
# Delete an About Us record by its ID.
def delete_about_us_by_id(about_us_id: int, db: Session = Depends(get_db)):
	record = db.query(AboutUs).filter(AboutUs.id == about_us_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="About Us entry not found")

	db.delete(record)
	db.commit()
	return {"message": f"About Us entry with id {about_us_id} deleted successfully"}

