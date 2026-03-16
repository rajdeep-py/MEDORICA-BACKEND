import os
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from models.onboarding.mr_onbooarding_models import MedicalRepresentative
from models.salary_slip.mr_salary_slip_models import MRSalarySlip
from services.salary_slip.mr_salary_slip_upload import delete_mr_salary_slip_assets, save_mr_salary_slip

router = APIRouter(prefix="/salary-slip/mr", tags=["MR Salary Slip"])

class MRSalarySlipResponseSchema(BaseModel):
	id: int
	mr_id: str
	salary_slip_url: str
	created_at: datetime
	updated_at: datetime

	class Config:
		from_attributes = True

# Upload a salary slip PDF for an MR. Creates a new record; fails if one already exists.
@router.post("/post/{mr_id}", response_model=MRSalarySlipResponseSchema, status_code=status.HTTP_201_CREATED)
def post_mr_salary_slip(
	mr_id: str,
	salary_slip: UploadFile = File(...),
	db: Session = Depends(get_db),
):
	mr_record = db.query(MedicalRepresentative).filter(MedicalRepresentative.mr_id == mr_id).first()
	if not mr_record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MR not found")

	existing = db.query(MRSalarySlip).filter(MRSalarySlip.mr_id == mr_id).first()
	if existing:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Salary slip already exists for this MR. Use the update endpoint to replace it.",
		)

	if not (salary_slip.filename or "").lower().endswith(".pdf"):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are accepted")

	try:
		slip_url = save_mr_salary_slip(salary_slip, mr_id)
	except Exception as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to process PDF") from exc

	new_slip = MRSalarySlip(mr_id=mr_id, salary_slip_url=slip_url)
	db.add(new_slip)
	db.commit()
	db.refresh(new_slip)
	return new_slip

# Replace the existing salary slip PDF for an MR.
@router.put("/update-by/{mr_id}", response_model=MRSalarySlipResponseSchema)
def update_mr_salary_slip(
	mr_id: str,
	salary_slip: UploadFile = File(...),
	db: Session = Depends(get_db),
):
	record = db.query(MRSalarySlip).filter(MRSalarySlip.mr_id == mr_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salary slip not found for this MR")

	if not (salary_slip.filename or "").lower().endswith(".pdf"):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are accepted")

	try:
		slip_url = save_mr_salary_slip(salary_slip, mr_id)
	except Exception as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to process PDF") from exc

	record.salary_slip_url = slip_url
	db.commit()
	db.refresh(record)
	return record

# Fetch all MR salary slip records.
@router.get("/get-all", response_model=list[MRSalarySlipResponseSchema])
def get_all_mr_salary_slips(db: Session = Depends(get_db)):
	return db.query(MRSalarySlip).all()

# Fetch an MR salary slip record by MR ID.
@router.get("/get-by-mr/{mr_id}", response_model=MRSalarySlipResponseSchema)
def get_mr_salary_slip_by_mr_id(mr_id: str, db: Session = Depends(get_db)):
	record = db.query(MRSalarySlip).filter(MRSalarySlip.mr_id == mr_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salary slip not found for this MR")
	return record

# Download the salary slip PDF for an MR by MR ID.
@router.get("/download-by-mr/{mr_id}")
def download_mr_salary_slip_by_mr_id(mr_id: str, db: Session = Depends(get_db)):
	record = db.query(MRSalarySlip).filter(MRSalarySlip.mr_id == mr_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salary slip not found for this MR")
	if not os.path.exists(record.salary_slip_url):
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salary slip file not found on server")
	return FileResponse(
		path=record.salary_slip_url,
		media_type="application/pdf",
		filename=f"{mr_id}_salary_slip.pdf",
		headers={"Content-Disposition": f'attachment; filename="{mr_id}_salary_slip.pdf"'},
	)

# Fetch an MR salary slip record by its row ID.
@router.get("/get-by/{slip_id}", response_model=MRSalarySlipResponseSchema)
def get_mr_salary_slip_by_id(slip_id: int, db: Session = Depends(get_db)):
	record = db.query(MRSalarySlip).filter(MRSalarySlip.id == slip_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salary slip not found")
	return record

# Download the salary slip PDF by its row ID.
@router.get("/download-by/{slip_id}")
def download_mr_salary_slip_by_id(slip_id: int, db: Session = Depends(get_db)):
	record = db.query(MRSalarySlip).filter(MRSalarySlip.id == slip_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salary slip not found")
	if not os.path.exists(record.salary_slip_url):
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salary slip file not found on server")
	return FileResponse(
		path=record.salary_slip_url,
		media_type="application/pdf",
		filename=f"{record.mr_id}_salary_slip.pdf",
		headers={"Content-Disposition": f'attachment; filename="{record.mr_id}_salary_slip.pdf"'},
	)

# Delete an MR salary slip record and its uploaded PDF file by row ID.
@router.delete("/delete-by/{slip_id}", status_code=status.HTTP_200_OK)
def delete_mr_salary_slip_by_id(slip_id: int, db: Session = Depends(get_db)):
	record = db.query(MRSalarySlip).filter(MRSalarySlip.id == slip_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salary slip not found")

	try:
		delete_mr_salary_slip_assets(record.mr_id)
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Failed to delete salary slip file",
		) from exc

	db.delete(record)
	db.commit()
	return {"message": f"Salary slip with id {slip_id} deleted successfully"}
