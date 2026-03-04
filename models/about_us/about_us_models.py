from sqlalchemy import Column, DateTime, Integer, Text, func

from db import Base


# Store About Us content and contact/social details for the company.
class AboutUs(Base):
	__tablename__ = "about_us"

	# Unique identifier for each About Us record.
	id = Column(Integer, primary_key=True, index=True)
	# Main company description text.
	company_about = Column(Text, nullable=True)
	# Director's message text.
	director_message = Column(Text, nullable=True)
	# Primary phone number.
	phn_no = Column(Text, nullable=True)
	# Contact email address.
	email = Column(Text, nullable=True)
	# Company website URL.
	website = Column(Text, nullable=True)
	# General address.
	address = Column(Text, nullable=True)
	# Office-specific address.
	office_address = Column(Text, nullable=True)
	# Instagram profile link.
	instagram_link = Column(Text, nullable=True)
	# Facebook page link.
	facebook_link = Column(Text, nullable=True)
	# LinkedIn profile or page link.
	linkedin_link = Column(Text, nullable=True)
	# YouTube channel link.
	youtube_link = Column(Text, nullable=True)
	# Timestamp when the record is created.
	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	# Timestamp when the record is last updated.
	updated_at = Column(
		DateTime(timezone=True),
		server_default=func.now(),
		onupdate=func.now(),
		nullable=False,
	)

