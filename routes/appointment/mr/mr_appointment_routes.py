import json
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from models.appointment.mr.mr_appointment_models import MRAppointment
from models.doctor_network.mr_doctor_network_models import MRDoctorNetwork
from models.onboarding.mr_onbooarding_models import MedicalRepresentative
from services.appointment.mr.mr_appointment_id_generator import generate_mr_appointment_id
from services.appointment.mr.mr_appointment_upload import (
    delete_mr_appointment_assets,
    save_mr_appointment_completion_photo,
)

router = APIRouter(prefix="/appointment/mr", tags=["MR Appointment"])

class MRAppointmentResponseSchema(BaseModel):
    id: int
    appointment_id: str
    mr_id: str
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
    return parsed

# Validate appointment status.
def _validate_status(status_value: str) -> bool:
    allowed_status = {"pending", "ongoing", "cancelled", "completed"}
    return status_value in allowed_status

# Create a new appointment record for an MR with a doctor.
@router.post("/post", response_model=MRAppointmentResponseSchema, status_code=status.HTTP_201_CREATED)
def create_mr_appointment(
    mr_id: str = Form(...),
    doctor_id: str = Form(...),
    appointment_date: str = Form(...),
    appointment_time: str = Form(...),
    place: Optional[str] = Form(None),
    status: str = Form("pending"),
    visual_ads: Optional[str] = Form(None),
    completion_photo_proof: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    if not _validate_status(status):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status value")

    appointment_id = generate_mr_appointment_id()
    visual_ads_parsed = _parse_visual_ads_json(visual_ads)

    completion_photo_path = None
    if completion_photo_proof:
        completion_photo_path = save_mr_appointment_completion_photo(completion_photo_proof, appointment_id)

    new_appointment = MRAppointment(
        appointment_id=appointment_id,
        mr_id=mr_id,
        doctor_id=doctor_id,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        place=place,
        status=status,
        completion_photo_proof=completion_photo_path,
        visual_ads=visual_ads_parsed,
    )

    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)
    return new_appointment

# Fetch all appointments.
@router.get("/get-all", response_model=list[MRAppointmentResponseSchema])
def get_all_mr_appointments(db: Session = Depends(get_db)):
    return db.query(MRAppointment).all()

# Fetch all appointments for a specific MR.
@router.get("/get-by-mr/{mr_id}", response_model=list[MRAppointmentResponseSchema])
def get_mr_appointments_by_mr(mr_id: str, db: Session = Depends(get_db)):
    return db.query(MRAppointment).filter(MRAppointment.mr_id == mr_id).all()

# Fetch all appointments for a specific doctor.
@router.get("/get-by-doctor/{doctor_id}", response_model=list[MRAppointmentResponseSchema])
def get_mr_appointments_by_doctor(doctor_id: str, db: Session = Depends(get_db)):
    return db.query(MRAppointment).filter(MRAppointment.doctor_id == doctor_id).all()

# Fetch all appointments between a specific MR and doctor.
@router.get("/get-by-mr-doctor/{mr_id}/{doctor_id}", response_model=list[MRAppointmentResponseSchema])
def get_mr_appointments_by_mr_doctor(mr_id: str, doctor_id: str, db: Session = Depends(get_db)):
    return db.query(MRAppointment).filter(
        MRAppointment.mr_id == mr_id,
        MRAppointment.doctor_id == doctor_id
    ).all()

# Fetch a specific appointment by appointment ID.
@router.get("/get-by/{appointment_id}", response_model=MRAppointmentResponseSchema)
def get_mr_appointment_by_id(appointment_id: str, db: Session = Depends(get_db)):
    record = db.query(MRAppointment).filter(MRAppointment.appointment_id == appointment_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    return record

# Update an appointment by appointment ID.
@router.put("/update-by/{appointment_id}", response_model=MRAppointmentResponseSchema)
def update_mr_appointment_by_id(
    appointment_id: str,
    mr_id: Optional[str] = Form(None),
    doctor_id: Optional[str] = Form(None),
    appointment_date: Optional[str] = Form(None),
    appointment_time: Optional[str] = Form(None),
    place: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    visual_ads: Optional[str] = Form(None),
    completion_photo_proof: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    record = db.query(MRAppointment).filter(MRAppointment.appointment_id == appointment_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    if mr_id is not None:
        record.mr_id = mr_id
    if doctor_id is not None:
        record.doctor_id = doctor_id
    if appointment_date is not None:
        record.appointment_date = appointment_date
    if appointment_time is not None:
        record.appointment_time = appointment_time
    if place is not None:
        record.place = place
    if status is not None:
        if not _validate_status(status):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status value")
        record.status = status
    if visual_ads is not None:
        record.visual_ads = _parse_visual_ads_json(visual_ads)
    if completion_photo_proof is not None:
        record.completion_photo_proof = save_mr_appointment_completion_photo(completion_photo_proof, appointment_id)

    db.commit()
    db.refresh(record)
    return record

# Delete an appointment by appointment ID and remove associated assets.
@router.delete("/delete-by/{appointment_id}", status_code=status.HTTP_200_OK)
def delete_mr_appointment_by_id(appointment_id: str, db: Session = Depends(get_db)):
    record = db.query(MRAppointment).filter(MRAppointment.appointment_id == appointment_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    delete_mr_appointment_assets(appointment_id)
    db.delete(record)
    db.commit()
    return {"detail": "Appointment deleted successfully"}
