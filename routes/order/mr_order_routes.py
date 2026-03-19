import json
from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from models.chemist_shop.mr_chemist_shop_network_models import MRChemistShopNetwork
from models.distributor.distributor_models import Distributor
from models.doctor_network.mr_doctor_network_models import MRDoctorNetwork
from models.monthly_target.mr_monthly_target_models import MRMonthlyTarget
from models.onboarding.mr_onbooarding_models import MedicalRepresentative
from models.order.mr_order_models import MROrder
from services.order.mr_order_id_generatory import generate_mr_order_id

router = APIRouter(prefix="/order/mr", tags=["MR Orders"])

ALLOWED_ORDER_STATUSES = {"pending", "approved", "shipped", "delivered"}

class MROrderResponseSchema(BaseModel):
    id: int
    order_id: str
    mr_id: str
    distributor_id: Optional[str] = None
    chemist_shop_id: Optional[str] = None
    doctor_id: Optional[str] = None
    products_with_price: Any
    total_amount_rupees: float
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

def _parse_products_with_price_json(products_with_price: str) -> Any:
    if products_with_price is None or products_with_price.strip() == "":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="products_with_price is required")
    try:
        parsed = json.loads(products_with_price)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="products_with_price must be valid JSON",
        ) from exc
    if parsed is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="products_with_price cannot be null",
        )
    if not isinstance(parsed, (list, dict)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="products_with_price must be a JSON array or object",
        )
    return parsed

def _normalize_order_status(status_value: str) -> str:
    if status_value is None or status_value.strip() == "":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="status is required")
    normalized = status_value.strip().lower()
    if normalized not in ALLOWED_ORDER_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="status must be one of: pending, approved, shipped, delivered",
        )
    return normalized

def _validate_optional_links(
    db: Session,
    mr_id: str,
    distributor_id: Optional[str],
    chemist_shop_id: Optional[str],
    doctor_id: Optional[str],
):
    if distributor_id is not None:
        distributor = db.query(Distributor).filter(Distributor.dist_id == distributor_id).first()
        if not distributor:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Distributor not found")
    if chemist_shop_id is not None:
        shop = (
            db.query(MRChemistShopNetwork)
            .filter(
                MRChemistShopNetwork.shop_id == chemist_shop_id,
                MRChemistShopNetwork.mr_id == mr_id,
            )
            .first()
        )
        if not shop:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Chemist shop not found or not linked to MR")
    if doctor_id is not None:
        doctor = (
            db.query(MRDoctorNetwork)
            .filter(
                MRDoctorNetwork.doctor_id == doctor_id,
                MRDoctorNetwork.mr_id == mr_id,
            )
            .first()
        )
        if not doctor:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Doctor not found or not linked to MR")

def _deduct_monthly_target_on_approval(
    db: Session,
    mr_record: MedicalRepresentative,
    order_amount_rupees: float,
):
    today = date.today()
    month = today.month
    year = today.year
    monthly_target_record = (
        db.query(MRMonthlyTarget)
        .filter(
            MRMonthlyTarget.mr_id == mr_record.mr_id,
            MRMonthlyTarget.month == month,
            MRMonthlyTarget.year == year,
        )
        .with_for_update()
        .first()
    )
    if monthly_target_record is None:
        opening_target = mr_record.monthly_target_rupees or 0.0
        monthly_target_record = MRMonthlyTarget(
            mr_id=mr_record.mr_id,
            month=month,
            year=year,
            opening_target_rupees=opening_target,
            deducted_target_rupees=0.0,
            remaining_target_rupees=opening_target,
        )
        db.add(monthly_target_record)
        db.flush()
    remaining_before = monthly_target_record.remaining_target_rupees or 0.0
    if remaining_before < order_amount_rupees:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Monthly target exceeded")
    monthly_target_record.deducted_target_rupees = (monthly_target_record.deducted_target_rupees or 0.0) + order_amount_rupees
    monthly_target_record.remaining_target_rupees = remaining_before - order_amount_rupees

# Create a new order for an MR by MR ID.
@router.post("/post-by/{mr_id}", response_model=MROrderResponseSchema, status_code=status.HTTP_201_CREATED)
def create_mr_order(
    mr_id: str,
    distributor_id: Optional[str] = Form(None),
    chemist_shop_id: Optional[str] = Form(None),
    doctor_id: Optional[str] = Form(None),
    products_with_price: str = Form(...),
    total_amount_rupees: float = Form(...),
    status_value: str = Form("pending", alias="status"),
    db: Session = Depends(get_db),
):
    _validate_optional_links(db, mr_id, distributor_id, chemist_shop_id, doctor_id)
    mr_record = db.query(MedicalRepresentative).filter(MedicalRepresentative.mr_id == mr_id).first()
    if not mr_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MR not found")
    order_id = generate_mr_order_id(mr_id)
    products_parsed = _parse_products_with_price_json(products_with_price)
    status = _normalize_order_status(status_value)
    new_order = MROrder(
        order_id=order_id,
        mr_id=mr_id,
        distributor_id=distributor_id,
        chemist_shop_id=chemist_shop_id,
        doctor_id=doctor_id,
        products_with_price=products_parsed,
        total_amount_rupees=total_amount_rupees,
        status=status,
    )
    db.add(new_order)
    if status != "pending":
        _deduct_monthly_target_on_approval(db, mr_record, total_amount_rupees)
    db.commit()
    db.refresh(new_order)
    return new_order

# Fetch all MR orders.
@router.get("/get-all", response_model=list[MROrderResponseSchema])
def get_all_mr_orders(db: Session = Depends(get_db)):
    return db.query(MROrder).all()

# Fetch all orders for a specific MR.
@router.get("/get-by-mr/{mr_id}", response_model=list[MROrderResponseSchema])
def get_orders_by_mr_id(mr_id: str, db: Session = Depends(get_db)):
    return db.query(MROrder).filter(MROrder.mr_id == mr_id).all()

# Fetch one order by MR ID and order ID.
@router.get("/get-by/{mr_id}/{order_id}", response_model=MROrderResponseSchema)
def get_order_by_mr_and_order_id(mr_id: str, order_id: str, db: Session = Depends(get_db)):
    record = db.query(MROrder).filter(MROrder.mr_id == mr_id, MROrder.order_id == order_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return record

# Update an order by order ID.
@router.put("/update-by/{order_id}", response_model=MROrderResponseSchema)
def update_order_by_order_id(
    order_id: str,
    distributor_id: Optional[str] = Form(None),
    chemist_shop_id: Optional[str] = Form(None),
    doctor_id: Optional[str] = Form(None),
    products_with_price: Optional[str] = Form(None),
    total_amount_rupees: Optional[float] = Form(None),
    status_value: Optional[str] = Form(None, alias="status"),
    db: Session = Depends(get_db),
):
    record = db.query(MROrder).filter(MROrder.order_id == order_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if distributor_id is not None:
        record.distributor_id = distributor_id
    if chemist_shop_id is not None:
        record.chemist_shop_id = chemist_shop_id
    if doctor_id is not None:
        record.doctor_id = doctor_id
    if products_with_price is not None:
        record.products_with_price = _parse_products_with_price_json(products_with_price)
    if total_amount_rupees is not None:
        record.total_amount_rupees = total_amount_rupees
    if status_value is not None:
        status = _normalize_order_status(status_value)
        record.status = status
        if status != "pending":
            mr_record = db.query(MedicalRepresentative).filter(MedicalRepresentative.mr_id == record.mr_id).first()
            if mr_record:
                _deduct_monthly_target_on_approval(db, mr_record, record.total_amount_rupees)
    db.commit()
    db.refresh(record)
    return record

# Delete an order by order ID.
@router.delete("/delete-by/{order_id}", status_code=status.HTTP_200_OK)
def delete_order_by_order_id(order_id: str, db: Session = Depends(get_db)):
    record = db.query(MROrder).filter(MROrder.order_id == order_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    db.delete(record)
    db.commit()
    return {"detail": "Order deleted successfully"}
