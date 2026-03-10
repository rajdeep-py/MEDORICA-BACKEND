from sqlalchemy import Column, DateTime, Integer, String, Text, func

from db import Base


# Store visual advertisement details for medicines.
class VisualAd(Base):
	__tablename__ = "visual_ad"

	id = Column(Integer, primary_key=True, index=True)
	ad_id = Column(String(32), unique=True, nullable=False, index=True)
	medicine_name = Column(String(255), nullable=False)
	ad_image = Column(Text, nullable=True)
	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	updated_at = Column(
		DateTime(timezone=True),
		server_default=func.now(),
		onupdate=func.now(),
		nullable=False,
	)
