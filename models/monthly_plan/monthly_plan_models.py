from sqlalchemy import Column, Date, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB

from db import Base


# Store one ASM team day-plan row per team and date, including all MR plans in JSON.
class MonthlyPlan(Base):
	__tablename__ = "asm_day_plans"
	__table_args__ = (
		UniqueConstraint("asm_id", "team_id", "mr_id", "plan_date", name="uq_asm_team_mr_plan_date"),
	)

	id = Column(Integer, primary_key=True, index=True, autoincrement=True)
	asm_id = Column(String(32), nullable=False, index=True)
	team_id = Column(Integer, nullable=False, index=True)
	mr_id = Column(String(32), nullable=False, index=True)
	plan_date = Column(Date, nullable=False, index=True)
	status = Column(String(20), nullable=False, default="draft", server_default="draft")
	activities = Column(JSONB, nullable=False)
	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	updated_at = Column(
		DateTime(timezone=True),
		server_default=func.now(),
		onupdate=func.now(),
		nullable=False,
	)
