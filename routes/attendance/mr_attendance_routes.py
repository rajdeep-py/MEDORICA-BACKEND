import os
from datetime import date, datetime
from io import BytesIO
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from PIL import Image
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from models.attendance.mr_attendance_models import MRAttendance
from models.onboarding.mr_onbooarding_models import MedicalRepresentative

router = APIRouter(prefix="/attendance/mr", tags=["MR Attendance"])

VALID_STATUSES = {"present", "absent"}


class MRAttendanceResponseSchema(BaseModel):
	id: int
	mr_id: str
	date: date
	check_in_time: Optional[datetime] = None
	check_in_selfie: Optional[str] = None
	check_out_time: Optional[datetime] = None
	check_out_selfie: Optional[str] = None
	status: str
	created_at: datetime
	updated_at: datetime

	class Config:
		from_attributes = True


# Save and compress a selfie upload to uploads/attendance/mr/{mr_id}/{date}/{selfie_type}_selfie{ext}.
def _save_selfie(upload_file: UploadFile, mr_id: str, attendance_date: date, selfie_type: str) -> str:
	date_str = attendance_date.isoformat()
	base_dir = os.path.join("uploads", "attendance", "mr", mr_id, date_str)
	os.makedirs(base_dir, exist_ok=True)

	original_ext = os.path.splitext(upload_file.filename or "")[1].lower()
	allowed_ext = {".jpg", ".jpeg", ".png", ".webp"}
	ext = original_ext if original_ext in allowed_ext else ".jpg"
	filename = f"{selfie_type}_selfie{ext}"
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


# Remove selfie files from disk when an attendance record is deleted.
def _delete_selfie_files(check_in_selfie: Optional[str], check_out_selfie: Optional[str]) -> None:
	for path in [check_in_selfie, check_out_selfie]:
		if path and os.path.exists(path):
			os.remove(path)


# Create a new MR attendance record. Accepts form data including optional check-in/check-out selfie uploads.
@router.post("/post", response_model=MRAttendanceResponseSchema, status_code=status.HTTP_201_CREATED)
def create_mr_attendance(
	mr_id: str = Form(...),
	attendance_date: date = Form(...),
	attendance_status: str = Form("present"),
	check_in_time: Optional[datetime] = Form(None),
	check_out_time: Optional[datetime] = Form(None),
	check_in_selfie: Optional[UploadFile] = File(None),
	check_out_selfie: Optional[UploadFile] = File(None),
	db: Session = Depends(get_db),
):
	if attendance_status not in VALID_STATUSES:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}",
		)

	mr = db.query(MedicalRepresentative).filter(MedicalRepresentative.mr_id == mr_id).first()
	if not mr:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MR not found")

	existing = (
		db.query(MRAttendance)
		.filter(MRAttendance.mr_id == mr_id, MRAttendance.date == attendance_date)
		.first()
	)
	if existing:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Attendance record already exists for this MR on the given date",
		)

	record = MRAttendance(
		mr_id=mr_id,
		date=attendance_date,
		status=attendance_status,
		check_in_time=check_in_time,
		check_out_time=check_out_time,
	)

	if check_in_selfie is not None:
		try:
			record.check_in_selfie = _save_selfie(check_in_selfie, mr_id, attendance_date, "checkin")
		except Exception as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid check-in selfie") from exc

	if check_out_selfie is not None:
		try:
			record.check_out_selfie = _save_selfie(check_out_selfie, mr_id, attendance_date, "checkout")
		except Exception as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid check-out selfie") from exc

	db.add(record)
	db.commit()
	db.refresh(record)
	return record


# Fetch all MR attendance records across all MRs.
@router.get("/get-all", response_model=list[MRAttendanceResponseSchema])
def get_all_mr_attendance(db: Session = Depends(get_db)):
	return db.query(MRAttendance).all()


# Fetch all attendance records for a specific MR by MR ID.
@router.get("/get-by/{mr_id}", response_model=list[MRAttendanceResponseSchema])
def get_attendance_by_mr_id(mr_id: str, db: Session = Depends(get_db)):
	mr = db.query(MedicalRepresentative).filter(MedicalRepresentative.mr_id == mr_id).first()
	if not mr:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MR not found")
	return db.query(MRAttendance).filter(MRAttendance.mr_id == mr_id).all()


# Fetch a specific attendance record by MR ID and attendance record ID.
@router.get("/get-by/{mr_id}/{attendance_id}", response_model=MRAttendanceResponseSchema)
def get_attendance_by_mr_and_id(mr_id: str, attendance_id: int, db: Session = Depends(get_db)):
	record = (
		db.query(MRAttendance)
		.filter(MRAttendance.mr_id == mr_id, MRAttendance.id == attendance_id)
		.first()
	)
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found")
	return record


# Update an existing MR attendance record by MR ID and attendance record ID.
@router.put("/update-by/{mr_id}/{attendance_id}", response_model=MRAttendanceResponseSchema)
def update_mr_attendance(
	mr_id: str,
	attendance_id: int,
	attendance_status: Optional[str] = Form(None),
	check_in_time: Optional[datetime] = Form(None),
	check_out_time: Optional[datetime] = Form(None),
	check_in_selfie: Optional[UploadFile] = File(None),
	check_out_selfie: Optional[UploadFile] = File(None),
	db: Session = Depends(get_db),
):
	record = (
		db.query(MRAttendance)
		.filter(MRAttendance.mr_id == mr_id, MRAttendance.id == attendance_id)
		.first()
	)
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found")

	if attendance_status is not None:
		if attendance_status not in VALID_STATUSES:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}",
			)
		record.status = attendance_status

	if check_in_time is not None:
		record.check_in_time = check_in_time
	if check_out_time is not None:
		record.check_out_time = check_out_time

	if check_in_selfie is not None:
		try:
			record.check_in_selfie = _save_selfie(check_in_selfie, mr_id, record.date, "checkin")
		except Exception as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid check-in selfie") from exc

	if check_out_selfie is not None:
		try:
			record.check_out_selfie = _save_selfie(check_out_selfie, mr_id, record.date, "checkout")
		except Exception as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid check-out selfie") from exc

	db.commit()
	db.refresh(record)
	return record


# Delete an MR attendance record by attendance record ID and clean up associated selfie files.
@router.delete("/delete-by/{attendance_id}", status_code=status.HTTP_200_OK)
def delete_mr_attendance(attendance_id: int, db: Session = Depends(get_db)):
	record = db.query(MRAttendance).filter(MRAttendance.id == attendance_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found")

	try:
		_delete_selfie_files(record.check_in_selfie, record.check_out_selfie)
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Failed to delete attendance selfie files",
		) from exc

	db.delete(record)
	db.commit()
	return {"message": f"Attendance record with id {attendance_id} deleted successfully"}
