from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text, func

from db import Base


# Store daily attendance records for medical representatives.
class MRAttendance(Base):
	__tablename__ = "mr_attendance"

	id = Column(Integer, primary_key=True, index=True)
	mr_id = Column(String(32), ForeignKey("medical_representatives.mr_id"), nullable=False, index=True)
	date = Column(Date, nullable=False)
	check_in_time = Column(DateTime(timezone=True), nullable=True)
	check_in_selfie = Column(Text, nullable=True)
	check_out_time = Column(DateTime(timezone=True), nullable=True)
	check_out_selfie = Column(Text, nullable=True)
	status = Column(String(10), nullable=False, default="present")  # "present" or "absent"
	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	updated_at = Column(
		DateTime(timezone=True),
		server_default=func.now(),
		onupdate=func.now(),
		nullable=False,
	)
