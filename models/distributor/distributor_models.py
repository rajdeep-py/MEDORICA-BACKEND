from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text, func

from db import Base


# Store distributor information and business details.
class Distributor(Base):
	__tablename__ = "distributor"

	id = Column(Integer, primary_key=True, index=True)
	dist_id = Column(String(32), unique=True, nullable=False, index=True)
	dist_name = Column(String(555), nullable=False)
	dist_location = Column(Text, nullable=True)
	dist_phone_no = Column(String(20), unique=True, nullable=False, index=True)
	dist_email = Column(String(255), nullable=True)
	dist_description = Column(Text, nullable=True)
	dist_photo = Column(Text, nullable=True)
	dist_min_order_value_rupees = Column(Float, nullable=True)
	dist_products = Column(JSON, nullable=True)
	dist_expected_delivery_time_days = Column(Integer, nullable=True)
	payment_terms = Column(Text, nullable=True)
	bank_name = Column(String(255), nullable=True)
	bank_ac_no = Column(String(100), nullable=True)
	branch_name = Column(String(255), nullable=True)
	ifsc_code = Column(String(50), nullable=True)
	delivery_territories = Column(JSON, nullable=True)
	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	updated_at = Column(
		DateTime(timezone=True),
		server_default=func.now(),
		onupdate=func.now(),
		nullable=False,
	)
