# FastAPI routes for MR Gift Applications
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from models.gift.mr_gift_application_models import MRGiftApplication
from models.onboarding.mr_onbooarding_models import MedicalRepresentative
from models.doctor_network.mr_doctor_network_models import MRDoctorNetwork
from models.gift.gift_inventory_models import GiftInventory

router = APIRouter(prefix="/gift-application/mr", tags=["MR Gift Application"])

class MRGiftApplicationResponseSchema(BaseModel):
	request_id: int
	mr_id: str
	doctor_id: str
	gift_id: int
	occassion: Optional[str] = None
	message: Optional[str] = None
	gift_date: Optional[date] = None
	remarks: Optional[str] = None
	status: str
	created_at: datetime
	updated_at: datetime
	# Extra fields for display
	mr_name: Optional[str] = None
	doctor_name: Optional[str] = None
	mr_phone_no: Optional[str] = None
	doctor_phone_no: Optional[str] = None
	gift_name: Optional[str] = None

	class Config:
		from_attributes = True
		from_attributes = True

# Helper to enrich application with related info
def enrich_application(app: MRGiftApplication, db: Session):
	mr = db.query(MedicalRepresentative).filter(MedicalRepresentative.mr_id == app.mr_id).first()
	doctor = db.query(MRDoctorNetwork).filter(MRDoctorNetwork.doctor_id == app.doctor_id).first()
	gift = db.query(GiftInventory).filter(GiftInventory.gift_id == app.gift_id).first()
	return {
		**app.__dict__,
		"mr_name": mr.full_name if mr else None,
		"doctor_name": doctor.doctor_name if doctor else None,
		"mr_phone_no": mr.phone_no if mr else None,
		"doctor_phone_no": doctor.doctor_phone_no if doctor else None,
		"gift_name": gift.product_name if gift else None,
	}

# Create a new MR Gift Application
@router.post("/post", response_model=MRGiftApplicationResponseSchema, status_code=status.HTTP_201_CREATED)
def create_mr_gift_application(
	mr_id: str = Form(...),
	doctor_id: str = Form(...),
	gift_id: int = Form(...),
	occassion: Optional[str] = Form(None),
	message: Optional[str] = Form(None),
	gift_date: Optional[date] = Form(None),
	remarks: Optional[str] = Form(None),
	db: Session = Depends(get_db),
):
	# Optionally, check if MR, doctor, and gift exist
	new_app = MRGiftApplication(
		mr_id=mr_id,
		doctor_id=doctor_id,
		gift_id=gift_id,
		occassion=occassion,
		message=message,
		gift_date=gift_date,
		remarks=remarks,
		status="pending",
	)
	db.add(new_app)
	db.commit()
	db.refresh(new_app)
	return enrich_application(new_app, db)

# Get all MR Gift Applications
@router.get("/get-all", response_model=List[MRGiftApplicationResponseSchema])
def get_all_mr_gift_applications(db: Session = Depends(get_db)):
	apps = db.query(MRGiftApplication).all()
	return [enrich_application(app, db) for app in apps]

# Get MR Gift Applications by MR ID
@router.get("/get-by-mr/{mr_id}", response_model=List[MRGiftApplicationResponseSchema])
def get_mr_gift_applications_by_mr_id(mr_id: str, db: Session = Depends(get_db)):
	apps = db.query(MRGiftApplication).filter(MRGiftApplication.mr_id == mr_id).all()
	return [enrich_application(app, db) for app in apps]

# Update MR Gift Application by MR ID and Request ID
@router.put("/update-by/{mr_id}/{request_id}", response_model=MRGiftApplicationResponseSchema)
def update_mr_gift_application(
	mr_id: str,
	request_id: int,
	doctor_id: Optional[str] = Form(None),
	occassion: Optional[str] = Form(None),
	message: Optional[str] = Form(None),
	gift_date: Optional[date] = Form(None),
	remarks: Optional[str] = Form(None),
	status: Optional[str] = Form(None),
	db: Session = Depends(get_db),
):
	app = db.query(MRGiftApplication).filter(MRGiftApplication.mr_id == mr_id, MRGiftApplication.request_id == request_id).first()
	if not app:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MR Gift Application not found")
	if doctor_id is not None:
		app.doctor_id = doctor_id
	if occassion is not None:
		app.occassion = occassion
	if message is not None:
		app.message = message
	if gift_date is not None:
		app.gift_date = gift_date
	if remarks is not None:
		app.remarks = remarks
	if status is not None:
		app.status = status
	db.commit()
	db.refresh(app)
	return enrich_application(app, db)

# Delete MR Gift Application by Request ID
@router.delete("/delete-by/{request_id}", status_code=status.HTTP_200_OK)
def delete_mr_gift_application(request_id: int, db: Session = Depends(get_db)):
	app = db.query(MRGiftApplication).filter(MRGiftApplication.request_id == request_id).first()
	if not app:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MR Gift Application not found")
	db.delete(app)
	db.commit()
	return {"message": f"MR Gift Application with id {request_id} deleted successfully"}
