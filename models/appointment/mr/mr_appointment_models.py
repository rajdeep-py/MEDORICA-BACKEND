from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func

from db import Base

# Store appointment details scheduled by an MR with doctors, including visual ads to be shown.
class MRAppointment(Base):
    __tablename__ = "mr_appointment"
    __table_args__ = (
        UniqueConstraint("mr_id", "doctor_id", "appointment_date", "appointment_time", name="uq_mr_doctor_datetime"),
    )

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(String(64), unique=True, nullable=False, index=True)
    mr_id = Column(String(32), ForeignKey("medical_representatives.mr_id"), nullable=False, index=True)
    doctor_id = Column(String(64), ForeignKey("mr_doctor_network.doctor_id"), nullable=False, index=True)
    appointment_date = Column(String(20), nullable=False)  # Format: YYYY-MM-DD
    appointment_time = Column(String(20), nullable=False)  # Format: HH:MM
    place = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="pending", server_default="pending")  # pending, ongoing, cancelled, completed
    completion_photo_proof = Column(Text, nullable=True)
    visual_ads = Column(JSON, nullable=True)  # List of {id, medicine_name}
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
