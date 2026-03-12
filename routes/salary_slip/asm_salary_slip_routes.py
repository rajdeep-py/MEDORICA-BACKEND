import os
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from models.onboarding.asm_onboarding_models import AreaSalesManager
from models.salary_slip.asm_salary_slip_models import ASMSalarySlip
from services.salary_slip.asm_salary_slip_upload import delete_asm_salary_slip_assets, save_asm_salary_slip

router = APIRouter(prefix="/salary-slip/asm", tags=["ASM Salary Slip"])


class ASMSalarySlipResponseSchema(BaseModel):
	id: int
	asm_id: str
	salary_slip_url: str
	created_at: datetime
	updated_at: datetime

	class Config:
		from_attributes = True


# Upload a salary slip PDF for an ASM. Creates a new record; fails if one already exists.
@router.post("/post/{asm_id}", response_model=ASMSalarySlipResponseSchema, status_code=status.HTTP_201_CREATED)
def post_asm_salary_slip(
	asm_id: str,
	salary_slip: UploadFile = File(...),
	db: Session = Depends(get_db),
):
	asm_record = db.query(AreaSalesManager).filter(AreaSalesManager.asm_id == asm_id).first()
	if not asm_record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ASM not found")

	existing = db.query(ASMSalarySlip).filter(ASMSalarySlip.asm_id == asm_id).first()
	if existing:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Salary slip already exists for this ASM. Use the update endpoint to replace it.",
		)

	if not (salary_slip.filename or "").lower().endswith(".pdf"):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are accepted")

	try:
		slip_url = save_asm_salary_slip(salary_slip, asm_id)
	except Exception as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to process PDF") from exc

	new_slip = ASMSalarySlip(asm_id=asm_id, salary_slip_url=slip_url)
	db.add(new_slip)
	db.commit()
	db.refresh(new_slip)
	return new_slip


# Replace the existing salary slip PDF for an ASM.
@router.put("/update-by/{asm_id}", response_model=ASMSalarySlipResponseSchema)
def update_asm_salary_slip(
	asm_id: str,
	salary_slip: UploadFile = File(...),
	db: Session = Depends(get_db),
):
	record = db.query(ASMSalarySlip).filter(ASMSalarySlip.asm_id == asm_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salary slip not found for this ASM")

	if not (salary_slip.filename or "").lower().endswith(".pdf"):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are accepted")

	try:
		slip_url = save_asm_salary_slip(salary_slip, asm_id)
	except Exception as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to process PDF") from exc

	record.salary_slip_url = slip_url
	db.commit()
	db.refresh(record)
	return record


# Fetch all ASM salary slip records.
@router.get("/get-all", response_model=list[ASMSalarySlipResponseSchema])
def get_all_asm_salary_slips(db: Session = Depends(get_db)):
	return db.query(ASMSalarySlip).all()


# Fetch an ASM salary slip record by ASM ID.
@router.get("/get-by-asm/{asm_id}", response_model=ASMSalarySlipResponseSchema)
def get_asm_salary_slip_by_asm_id(asm_id: str, db: Session = Depends(get_db)):
	record = db.query(ASMSalarySlip).filter(ASMSalarySlip.asm_id == asm_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salary slip not found for this ASM")
	return record


# Download the salary slip PDF for an ASM by ASM ID.
@router.get("/download-by-asm/{asm_id}")
def download_asm_salary_slip_by_asm_id(asm_id: str, db: Session = Depends(get_db)):
	record = db.query(ASMSalarySlip).filter(ASMSalarySlip.asm_id == asm_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salary slip not found for this ASM")
	if not os.path.exists(record.salary_slip_url):
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salary slip file not found on server")
	return FileResponse(
		path=record.salary_slip_url,
		media_type="application/pdf",
		filename=f"{asm_id}_salary_slip.pdf",
		headers={"Content-Disposition": f'attachment; filename="{asm_id}_salary_slip.pdf"'},
	)


# Fetch an ASM salary slip record by its row ID.
@router.get("/get-by/{slip_id}", response_model=ASMSalarySlipResponseSchema)
def get_asm_salary_slip_by_id(slip_id: int, db: Session = Depends(get_db)):
	record = db.query(ASMSalarySlip).filter(ASMSalarySlip.id == slip_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salary slip not found")
	return record


# Download the salary slip PDF by its row ID.
@router.get("/download-by/{slip_id}")
def download_asm_salary_slip_by_id(slip_id: int, db: Session = Depends(get_db)):
	record = db.query(ASMSalarySlip).filter(ASMSalarySlip.id == slip_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salary slip not found")
	if not os.path.exists(record.salary_slip_url):
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salary slip file not found on server")
	return FileResponse(
		path=record.salary_slip_url,
		media_type="application/pdf",
		filename=f"{record.asm_id}_salary_slip.pdf",
		headers={"Content-Disposition": f'attachment; filename="{record.asm_id}_salary_slip.pdf"'},
	)


# Delete an ASM salary slip record and its uploaded PDF file by row ID.
@router.delete("/delete-by/{slip_id}", status_code=status.HTTP_200_OK)
def delete_asm_salary_slip_by_id(slip_id: int, db: Session = Depends(get_db)):
	record = db.query(ASMSalarySlip).filter(ASMSalarySlip.id == slip_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salary slip not found")

	try:
		delete_asm_salary_slip_assets(record.asm_id)
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Failed to delete salary slip file",
		) from exc

	db.delete(record)
	db.commit()
	return {"message": f"Salary slip with id {slip_id} deleted successfully"}
