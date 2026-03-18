from datetime import date, datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from models.monthly_plan.monthly_plan_models import MonthlyPlan
from models.onboarding.asm_onboarding_models import AreaSalesManager
from models.onboarding.mr_onbooarding_models import MedicalRepresentative
from models.team.team_models import Team

router = APIRouter(prefix="/monthly-plan", tags=["Monthly Plan"])

# Update and Delete schemas
class MonthlyPlanUpdateSchema(BaseModel):
	status: Optional[Literal["draft", "published", "cancelled"]] = None
	member_day_plans: Optional[list[MemberDayPlanSchema]] = None

class DeleteResponseSchema(BaseModel):
	detail: str


class ActivitySchema(BaseModel):
	slot: str
	type: str
	location: Optional[str] = None
	notes: Optional[str] = None


class MemberDayPlanSchema(BaseModel):
	mr_id: str
	mr_name: Optional[str] = None
	activities: list[ActivitySchema]


class MonthlyPlanCreateSchema(BaseModel):
	asm_id: str
	team_id: int
	plan_date: date
	status: Literal["draft", "published", "cancelled"] = "draft"
	member_day_plans: list[MemberDayPlanSchema]


class MonthlyPlanResponseSchema(BaseModel):
	id: int
	asm_id: str
	team_id: int
	plan_date: date
	status: str
	member_day_plans: list[MemberDayPlanSchema]
	created_at: datetime
	updated_at: datetime

	class Config:
		from_attributes = True


class MRDayPlanResponseSchema(BaseModel):
	id: int
	asm_id: str
	team_id: int
	plan_date: date
	status: str
	mr_plan: MemberDayPlanSchema
	created_at: datetime
	updated_at: datetime


def _extract_mr_plan(record: MonthlyPlan, mr_id: str) -> Optional[dict]:
	member_day_plans = record.member_day_plans if isinstance(record.member_day_plans, list) else []
	for member_plan in member_day_plans:
		if isinstance(member_plan, dict) and member_plan.get("mr_id") == mr_id:
			return {
				"id": record.id,
				"asm_id": record.asm_id,
				"team_id": record.team_id,
				"plan_date": record.plan_date,
				"status": record.status,
				"mr_plan": member_plan,
				"created_at": record.created_at,
				"updated_at": record.updated_at,
			}
	return None


def _get_team_or_404(team_id: int, db: Session) -> Team:
	team = db.query(Team).filter(Team.team_id == team_id).first()
	if not team:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
	return team


def _validate_asm_leads_team(asm_id: str, team: Team, db: Session) -> None:
	asm_record = db.query(AreaSalesManager).filter(AreaSalesManager.asm_id == asm_id).first()
	if not asm_record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ASM not found")
	if team.team_leader_asm_id != asm_id:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="ASM is not the leader of the provided team",
		)


def _validate_member_payload(team: Team, member_day_plans: list[MemberDayPlanSchema], db: Session) -> None:
	team_member_ids = team.team_members_mr_ids if isinstance(team.team_members_mr_ids, list) else []
	if not team_member_ids:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Team has no MR members assigned",
		)

	provided_ids = [member.mr_id for member in member_day_plans]
	if len(provided_ids) != len(set(provided_ids)):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate MR IDs in member_day_plans")

	for mr_id in provided_ids:
		if mr_id not in team_member_ids:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail=f"MR {mr_id} is not a member of team {team.team_id}",
			)

	existing_members = (
		db.query(MedicalRepresentative.mr_id)
		.filter(MedicalRepresentative.mr_id.in_(provided_ids))
		.all()
	)
	existing_member_ids = {row[0] for row in existing_members}
	missing_mr_ids = [mr_id for mr_id in provided_ids if mr_id not in existing_member_ids]
	if missing_mr_ids:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"Invalid MR IDs: {', '.join(missing_mr_ids)}",
		)


@router.post("/post", response_model=MonthlyPlanResponseSchema, status_code=status.HTTP_201_CREATED)
def create_monthly_plan(payload: MonthlyPlanCreateSchema, db: Session = Depends(get_db)):
	team = _get_team_or_404(payload.team_id, db)
	_validate_asm_leads_team(payload.asm_id, team, db)
	_validate_member_payload(team, payload.member_day_plans, db)

	existing = (
		db.query(MonthlyPlan)
		.filter(
			MonthlyPlan.asm_id == payload.asm_id,
			MonthlyPlan.team_id == payload.team_id,
			MonthlyPlan.plan_date == payload.plan_date,
		)
		.first()
	)
	if existing:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="A plan already exists for this ASM, team, and date",
		)

	new_plan = MonthlyPlan(
		asm_id=payload.asm_id,
		team_id=payload.team_id,
		plan_date=payload.plan_date,
		status=payload.status,
		member_day_plans=[member.model_dump() for member in payload.member_day_plans],
	)

	db.add(new_plan)
	db.commit()
	db.refresh(new_plan)
	return new_plan


@router.get("/get-all", response_model=list[MonthlyPlanResponseSchema])
def get_all_monthly_plans(db: Session = Depends(get_db)):
	return db.query(MonthlyPlan).all()


@router.get("/get-by/{plan_id}", response_model=MonthlyPlanResponseSchema)
def get_monthly_plan_by_id(plan_id: int, db: Session = Depends(get_db)):
	record = db.query(MonthlyPlan).filter(MonthlyPlan.id == plan_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monthly plan not found")
	return record


@router.get("/get-by-mr/{mr_id}", response_model=list[MRDayPlanResponseSchema])
def get_monthly_plans_by_mr_id(mr_id: str, db: Session = Depends(get_db)):
	mr_record = db.query(MedicalRepresentative).filter(MedicalRepresentative.mr_id == mr_id).first()
	if not mr_record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MR not found")

	records = (
		db.query(MonthlyPlan)
		.filter(MonthlyPlan.member_day_plans.contains([{"mr_id": mr_id}]))
		.order_by(MonthlyPlan.plan_date.desc())
		.all()
	)

	result: list[dict] = []
	for record in records:
		mr_plan_payload = _extract_mr_plan(record, mr_id)
		if mr_plan_payload is not None:
			result.append(mr_plan_payload)

	return result


@router.get("/get-by-mr/{mr_id}/date/{plan_date}", response_model=MRDayPlanResponseSchema)
def get_monthly_plan_by_mr_id_and_date(mr_id: str, plan_date: date, db: Session = Depends(get_db)):
	mr_record = db.query(MedicalRepresentative).filter(MedicalRepresentative.mr_id == mr_id).first()
	if not mr_record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MR not found")

	record = (
		db.query(MonthlyPlan)
		.filter(
			MonthlyPlan.plan_date == plan_date,
			MonthlyPlan.member_day_plans.contains([{"mr_id": mr_id}]),
		)
		.first()
	)
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monthly plan not found for MR on this date")

	mr_plan_payload = _extract_mr_plan(record, mr_id)
	if mr_plan_payload is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monthly plan not found for MR on this date")

	return mr_plan_payload

# Update MonthlyPlan by ASM
@router.put("/update/{plan_id}", response_model=MonthlyPlanResponseSchema)
def update_monthly_plan(plan_id: int, payload: MonthlyPlanUpdateSchema, db: Session = Depends(get_db)):

    record = db.query(MonthlyPlan).filter(MonthlyPlan.id == plan_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monthly plan not found")

    team = _get_team_or_404(record.team_id, db)
    _validate_asm_leads_team(record.asm_id, team, db)

    if payload.status:
        record.status = payload.status
    if payload.member_day_plans is not None:
        _validate_member_payload(team, payload.member_day_plans, db)
        record.member_day_plans = [member.model_dump() for member in payload.member_day_plans]

    db.commit()
    db.refresh(record)
    return record

# Delete MonthlyPlan by ASM
@router.delete("/delete/{plan_id}", response_model=DeleteResponseSchema)
def delete_monthly_plan(plan_id: int, db: Session = Depends(get_db)):
    record = db.query(MonthlyPlan).filter(MonthlyPlan.id == plan_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monthly plan not found")

    team = _get_team_or_404(record.team_id, db)
    _validate_asm_leads_team(record.asm_id, team, db)

    db.delete(record)
    db.commit()
    return {"detail": "Monthly plan deleted successfully"}
