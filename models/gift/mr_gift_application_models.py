# SQLAlchemy model for MR Gift Application
from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from db import Base

class MRGiftApplication(Base):
	__tablename__ = "mr_gift_applications"

	request_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
	mr_id = Column(String(32), ForeignKey("medical_representatives.mr_id"), nullable=False, index=True)
	doctor_id = Column(String(64), ForeignKey("mr_doctor_network.doctor_id"), nullable=False, index=True)
	gift_id = Column(Integer, ForeignKey("gift_inventory.gift_id"), nullable=False, index=True)
	occassion = Column(String(255), nullable=True)
	message = Column(Text, nullable=True)
	gift_date = Column(Date, nullable=True)
	remarks = Column(Text, nullable=True)
	status = Column(String(32), nullable=False, default="pending")  # pending, approved, shipped, delivered
	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
