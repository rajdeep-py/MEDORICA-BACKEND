import json
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from models.appointment.asm.asm_appointment_models import ASMAppointment
from models.doctor_network.asm_doctor_network_models import ASMDoctorNetwork
from models.onboarding.asm_onboarding_models import AreaSalesManager
from services.appointment.asm.asm_appointment_id_generator import generate_asm_appointment_id
from services.appointment.asm.asm_appointment_upload import (
	delete_asm_appointment_assets,
	save_asm_appointment_completion_photo,
)

router = APIRouter(prefix="/appointment/asm", tags=["ASM Appointment"])


class ASMAppointmentResponseSchema(BaseModel):
	id: int
	appointment_id: str
	asm_id: str
	doctor_id: str
	appointment_date: str
	appointment_time: str
	place: Optional[str] = None
	status: str
	completion_photo_proof: Optional[str] = None
	visual_ads: Optional[Any] = None
	created_at: datetime
	updated_at: datetime

	class Config:
		from_attributes = True


# Parse visual ads from JSON string input. Accepts valid JSON array only.
def _parse_visual_ads_json(visual_ads: Optional[str]) -> Optional[Any]:
	if visual_ads is None or visual_ads.strip() == "":
		return None
	try:
		parsed = json.loads(visual_ads)
	except json.JSONDecodeError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="visual_ads must be valid JSON") from exc

	if parsed is None:
		return None

	if not isinstance(parsed, list):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="visual_ads must be a JSON array")

	for ad in parsed:
		if not isinstance(ad, dict):
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Each visual ad must be a JSON object with id and medicine_name",
			)
		if "id" not in ad or "medicine_name" not in ad:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Each visual ad must have id and medicine_name fields",
			)

	return parsed


# Validate appointment status.
def _validate_status(status_value: str) -> bool:
	valid_statuses = {"pending", "ongoing", "cancelled", "completed"}
	return status_value.lower() in valid_statuses


# Create a new appointment record for an ASM with a doctor.
@router.post("/post", response_model=ASMAppointmentResponseSchema, status_code=status.HTTP_201_CREATED)
def create_asm_appointment(
	asm_id: str = Form(...),
	doctor_id: str = Form(...),
	appointment_date: str = Form(...),
	appointment_time: str = Form(...),
	place: Optional[str] = Form(None),
	status: Optional[str] = Form("pending"),
	visual_ads: Optional[str] = Form(None),
	completion_photo_proof: Optional[UploadFile] = File(None),
	db: Session = Depends(get_db),
):
	asm_record = db.query(AreaSalesManager).filter(AreaSalesManager.asm_id == asm_id).first()
	if not asm_record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ASM not found")

	doctor_record = db.query(ASMDoctorNetwork).filter(ASMDoctorNetwork.doctor_id == doctor_id).first()
	if not doctor_record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

	if doctor_record.asm_id != asm_id:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Doctor does not belong to this ASM",
		)

	if not _validate_status(status):
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Invalid status. Must be one of: pending, ongoing, cancelled, completed",
		)

	existing_appointment = (
		db.query(ASMAppointment)
		.filter(
			ASMAppointment.asm_id == asm_id,
			ASMAppointment.doctor_id == doctor_id,
			ASMAppointment.appointment_date == appointment_date,
			ASMAppointment.appointment_time == appointment_time,
		)
		.first()
	)
	if existing_appointment:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Appointment already exists for this ASM, doctor, date, and time",
		)

	appointment_id = generate_asm_appointment_id()

	new_appointment = ASMAppointment(
		appointment_id=appointment_id,
		asm_id=asm_id,
		doctor_id=doctor_id,
		appointment_date=appointment_date,
		appointment_time=appointment_time,
		place=place,
		status=status.lower(),
		visual_ads=_parse_visual_ads_json(visual_ads),
	)

	if completion_photo_proof is not None:
		try:
			new_appointment.completion_photo_proof = save_asm_appointment_completion_photo(
				completion_photo_proof, appointment_id
			)
		except Exception as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid completion photo") from exc

	db.add(new_appointment)
	db.commit()
	db.refresh(new_appointment)
	return new_appointment


# Fetch all appointments.
@router.get("/get-all", response_model=list[ASMAppointmentResponseSchema])
def get_all_asm_appointments(db: Session = Depends(get_db)):
	return db.query(ASMAppointment).all()


# Fetch all appointments for a specific ASM.
@router.get("/get-by-asm/{asm_id}", response_model=list[ASMAppointmentResponseSchema])
def get_appointments_by_asm_id(asm_id: str, db: Session = Depends(get_db)):
	asm_record = db.query(AreaSalesManager).filter(AreaSalesManager.asm_id == asm_id).first()
	if not asm_record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ASM not found")
	return db.query(ASMAppointment).filter(ASMAppointment.asm_id == asm_id).all()


# Fetch all appointments for a specific doctor.
@router.get("/get-by-doctor/{doctor_id}", response_model=list[ASMAppointmentResponseSchema])
def get_appointments_by_doctor_id(doctor_id: str, db: Session = Depends(get_db)):
	doctor_record = db.query(ASMDoctorNetwork).filter(ASMDoctorNetwork.doctor_id == doctor_id).first()
	if not doctor_record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
	return db.query(ASMAppointment).filter(ASMAppointment.doctor_id == doctor_id).all()


# Fetch all appointments between a specific ASM and doctor.
@router.get("/get-by-asm-doctor/{asm_id}/{doctor_id}", response_model=list[ASMAppointmentResponseSchema])
def get_appointments_by_asm_and_doctor(asm_id: str, doctor_id: str, db: Session = Depends(get_db)):
	asm_record = db.query(AreaSalesManager).filter(AreaSalesManager.asm_id == asm_id).first()
	if not asm_record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ASM not found")

	doctor_record = db.query(ASMDoctorNetwork).filter(ASMDoctorNetwork.doctor_id == doctor_id).first()
	if not doctor_record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

	if doctor_record.asm_id != asm_id:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Doctor does not belong to this ASM",
		)

	return (
		db.query(ASMAppointment)
		.filter(ASMAppointment.asm_id == asm_id, ASMAppointment.doctor_id == doctor_id)
		.all()
	)


# Fetch a specific appointment by appointment ID.
@router.get("/get-by/{appointment_id}", response_model=ASMAppointmentResponseSchema)
def get_appointment_by_id(appointment_id: str, db: Session = Depends(get_db)):
	record = db.query(ASMAppointment).filter(ASMAppointment.appointment_id == appointment_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
	return record


# Update an appointment by appointment ID.
@router.put("/update-by/{appointment_id}", response_model=ASMAppointmentResponseSchema)
def update_appointment_by_id(
	appointment_id: str,
	appointment_date: Optional[str] = Form(None),
	appointment_time: Optional[str] = Form(None),
	place: Optional[str] = Form(None),
	status: Optional[str] = Form(None),
	visual_ads: Optional[str] = Form(None),
	completion_photo_proof: Optional[UploadFile] = File(None),
	db: Session = Depends(get_db),
):
	record = db.query(ASMAppointment).filter(ASMAppointment.appointment_id == appointment_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

	if status is not None and not _validate_status(status):
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Invalid status. Must be one of: pending, ongoing, cancelled, completed",
		)

	if appointment_date is not None or appointment_time is not None:
		new_date = appointment_date if appointment_date is not None else record.appointment_date
		new_time = appointment_time if appointment_time is not None else record.appointment_time

		existing_appointment = (
			db.query(ASMAppointment)
			.filter(
				ASMAppointment.asm_id == record.asm_id,
				ASMAppointment.doctor_id == record.doctor_id,
				ASMAppointment.appointment_date == new_date,
				ASMAppointment.appointment_time == new_time,
				ASMAppointment.id != record.id,
			)
			.first()
		)
		if existing_appointment:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Appointment already exists for this ASM, doctor, date, and time",
			)

		if appointment_date is not None:
			record.appointment_date = appointment_date
		if appointment_time is not None:
			record.appointment_time = appointment_time

	if place is not None:
		record.place = place
	if status is not None:
		record.status = status.lower()
	if visual_ads is not None:
		record.visual_ads = _parse_visual_ads_json(visual_ads)

	if completion_photo_proof is not None:
		try:
			record.completion_photo_proof = save_asm_appointment_completion_photo(completion_photo_proof, appointment_id)
		except Exception as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid completion photo") from exc

	db.commit()
	db.refresh(record)
	return record


# Delete an appointment by appointment ID and remove associated assets.
@router.delete("/delete-by/{appointment_id}", status_code=status.HTTP_200_OK)
def delete_appointment_by_id(appointment_id: str, db: Session = Depends(get_db)):
	record = db.query(ASMAppointment).filter(ASMAppointment.appointment_id == appointment_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

	try:
		delete_asm_appointment_assets(record.appointment_id)
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Failed to delete appointment assets",
		) from exc

	db.delete(record)
	db.commit()
	return {"message": f"Appointment with id {appointment_id} deleted successfully"}
