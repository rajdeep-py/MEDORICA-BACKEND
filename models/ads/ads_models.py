from sqlalchemy import Column, DateTime, Integer, Text, func

from db import Base


# Store advertisement content and media metadata.
class Advertisement(Base):
	__tablename__ = "advertisements"

	# Unique identifier for each advertisement.
	id = Column(Integer, primary_key=True, index=True)
	# Advertisement title text.
	ttitle = Column(Text, nullable=True)
	# Advertisement subtitle text.
	subtitle = Column(Text, nullable=True)
	# Call-to-action button label text.
	cta_button_text = Column(Text, nullable=True)
	# Destination website link for the ad.
	website_link = Column(Text, nullable=True)
	# Stored path of the compressed advertisement image.
	image = Column(Text, nullable=True)
	# Timestamp when the advertisement is created.
	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	# Timestamp when the advertisement is last updated.
	updated_at = Column(
		DateTime(timezone=True),
		server_default=func.now(),
		onupdate=func.now(),
		nullable=False,
	)

