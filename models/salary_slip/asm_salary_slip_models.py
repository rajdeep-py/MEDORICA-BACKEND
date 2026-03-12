from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func

from db import Base


# Store salary slip upload details for an area sales manager.
class ASMSalarySlip(Base):
	__tablename__ = "asm_salary_slips"

	id = Column(Integer, primary_key=True, index=True, autoincrement=True)
	asm_id = Column(
		String(32),
		ForeignKey("area_sales_manager.asm_id", ondelete="CASCADE"),
		nullable=False,
		unique=True,
		index=True,
	)
	salary_slip_url = Column(Text, nullable=False)
	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	updated_at = Column(
		DateTime(timezone=True),
		server_default=func.now(),
		onupdate=func.now(),
		nullable=False,
	)
