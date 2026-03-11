from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func

from db import Base


# Store appointment details scheduled by an ASM with doctors, including visual ads to be shown.
class ASMAppointment(Base):
	__tablename__ = "asm_appointment"
	__table_args__ = (
		UniqueConstraint("asm_id", "doctor_id", "appointment_date", "appointment_time", name="uq_asm_doctor_datetime"),
	)

	id = Column(Integer, primary_key=True, index=True)
	appointment_id = Column(String(64), unique=True, nullable=False, index=True)
	asm_id = Column(String(32), ForeignKey("area_sales_manager.asm_id"), nullable=False, index=True)
	doctor_id = Column(String(64), ForeignKey("asm_doctor_network.doctor_id"), nullable=False, index=True)
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
