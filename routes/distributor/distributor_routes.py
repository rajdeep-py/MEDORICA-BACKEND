import json
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from models.distributor.distributor_models import Distributor
from services.distributor.distributor_id_generator import generate_distributor_id
from services.distributor.distributor_photo_upload import delete_distributor_photo_assets, save_distributor_photo

router = APIRouter(prefix="/distributor", tags=["Distributor"])


class DistributorResponseSchema(BaseModel):
	id: int
	dist_id: str
	dist_name: str
	dist_location: Optional[str] = None
	dist_phone_no: str
	dist_email: Optional[str] = None
	dist_description: Optional[str] = None
	dist_photo: Optional[str] = None
	dist_min_order_value_rupees: Optional[float] = None
	dist_products: Optional[Any] = None
	dist_expected_delivery_time_days: Optional[int] = None
	payment_terms: Optional[str] = None
	bank_name: Optional[str] = None
	bank_ac_no: Optional[str] = None
	branch_name: Optional[str] = None
	ifsc_code: Optional[str] = None
	delivery_territories: Optional[Any] = None
	created_at: datetime
	updated_at: datetime

	class Config:
		from_attributes = True


# Helper function to parse products into a Python object. Accepts valid JSON or comma-separated strings. Returns None if input is empty.
def _parse_products_json(products: Optional[str]) -> Optional[Any]:
	if products is None or products.strip() == "":
		return None
	try:
		return json.loads(products)
	except json.JSONDecodeError:
		# If not valid JSON, treat as comma-separated string and convert to array
		products_list = [p.strip() for p in products.split(",") if p.strip()]
		return products_list if products_list else None


# Helper function to parse delivery territories into a Python object. Accepts valid JSON or comma-separated strings. Returns None if input is empty.
def _parse_territories_json(territories: Optional[str]) -> Optional[Any]:
	if territories is None or territories.strip() == "":
		return None
	try:
		return json.loads(territories)
	except json.JSONDecodeError:
		# If not valid JSON, treat as comma-separated string and convert to array
		territories_list = [t.strip() for t in territories.split(",") if t.strip()]
		return territories_list if territories_list else None


# Create a new Distributor record. Accepts form data for all fields, including a required photo upload. Returns the created Distributor details if successful, otherwise appropriate error messages.
@router.post("/post", response_model=DistributorResponseSchema, status_code=status.HTTP_201_CREATED)
def create_distributor(
	dist_name: str = Form(...),
	dist_phone_no: str = Form(...),
	dist_location: str = Form(...),
	dist_products: str = Form(...),
	payment_terms: str = Form(...),
	dist_email: Optional[str] = Form(None),
	dist_description: Optional[str] = Form(None),
	dist_min_order_value_rupees: Optional[float] = Form(None),
	dist_expected_delivery_time_days: Optional[int] = Form(None),
	bank_name: Optional[str] = Form(None),
	bank_ac_no: Optional[str] = Form(None),
	branch_name: Optional[str] = Form(None),
	ifsc_code: Optional[str] = Form(None),
	delivery_territories: Optional[str] = Form(None),
	dist_photo: Optional[UploadFile] = File(None),
	db: Session = Depends(get_db),
):
	try:
		dist_id = generate_distributor_id(dist_phone_no)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

	existing_distributor = db.query(Distributor).filter(Distributor.dist_id == dist_id).first()
	if existing_distributor:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Distributor already exists")

	existing_phone = db.query(Distributor).filter(Distributor.dist_phone_no == dist_phone_no).first()
	if existing_phone:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number already in use")

	new_distributor = Distributor(
		dist_id=dist_id,
		dist_name=dist_name,
		dist_phone_no=dist_phone_no,
		dist_location=dist_location,
		dist_email=dist_email,
		dist_description=dist_description,
		dist_min_order_value_rupees=dist_min_order_value_rupees,
		dist_products=_parse_products_json(dist_products),
		dist_expected_delivery_time_days=dist_expected_delivery_time_days,
		payment_terms=payment_terms,
		bank_name=bank_name,
		bank_ac_no=bank_ac_no,
		branch_name=branch_name,
		ifsc_code=ifsc_code,
		delivery_territories=_parse_territories_json(delivery_territories),
	)

	if dist_photo is not None:
		try:
			new_distributor.dist_photo = save_distributor_photo(dist_photo, dist_id, dist_name)
		except Exception as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid photo") from exc

	db.add(new_distributor)
	db.commit()
	db.refresh(new_distributor)
	return new_distributor


# Fetch a Distributor record by its Distributor ID. Returns the Distributor details if found, otherwise a 404 error.
@router.get("/get-by/{dist_id}", response_model=DistributorResponseSchema)
def get_distributor_by_id(dist_id: str, db: Session = Depends(get_db)):
	record = db.query(Distributor).filter(Distributor.dist_id == dist_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Distributor not found")
	return record


# Fetch all Distributor records. Returns a list of Distributor details.
@router.get("/get-all", response_model=list[DistributorResponseSchema])
def get_all_distributors(db: Session = Depends(get_db)):
	return db.query(Distributor).all()


# Update an existing Distributor record by its Distributor ID. Accepts form data for all fields, including an optional photo upload. Returns the updated Distributor details if successful, otherwise appropriate error messages.
@router.put("/update-by/{dist_id}", response_model=DistributorResponseSchema)
def update_distributor_by_id(
	dist_id: str,
	dist_name: Optional[str] = Form(None),
	dist_phone_no: Optional[str] = Form(None),
	dist_location: Optional[str] = Form(None),
	dist_email: Optional[str] = Form(None),
	dist_description: Optional[str] = Form(None),
	dist_min_order_value_rupees: Optional[float] = Form(None),
	dist_products: Optional[str] = Form(None),
	dist_expected_delivery_time_days: Optional[int] = Form(None),
	payment_terms: Optional[str] = Form(None),
	bank_name: Optional[str] = Form(None),
	bank_ac_no: Optional[str] = Form(None),
	branch_name: Optional[str] = Form(None),
	ifsc_code: Optional[str] = Form(None),
	delivery_territories: Optional[str] = Form(None),
	dist_photo: Optional[UploadFile] = File(None),
	db: Session = Depends(get_db),
):
	record = db.query(Distributor).filter(Distributor.dist_id == dist_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Distributor not found")

	if dist_phone_no is not None:
		try:
			new_dist_id = generate_distributor_id(dist_phone_no)
		except ValueError as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

		if new_dist_id != record.dist_id:
			existing_with_new_id = (
				db.query(Distributor)
				.filter(Distributor.dist_id == new_dist_id, Distributor.id != record.id)
				.first()
			)
			if existing_with_new_id:
				raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number already in use")
			record.dist_id = new_dist_id
		record.dist_phone_no = dist_phone_no

	if dist_name is not None:
		record.dist_name = dist_name
	if dist_location is not None:
		record.dist_location = dist_location
	if dist_email is not None:
		record.dist_email = dist_email
	if dist_description is not None:
		record.dist_description = dist_description
	if dist_min_order_value_rupees is not None:
		record.dist_min_order_value_rupees = dist_min_order_value_rupees
	if dist_products is not None:
		record.dist_products = _parse_products_json(dist_products)
	if dist_expected_delivery_time_days is not None:
		record.dist_expected_delivery_time_days = dist_expected_delivery_time_days
	if payment_terms is not None:
		record.payment_terms = payment_terms
	if bank_name is not None:
		record.bank_name = bank_name
	if bank_ac_no is not None:
		record.bank_ac_no = bank_ac_no
	if branch_name is not None:
		record.branch_name = branch_name
	if ifsc_code is not None:
		record.ifsc_code = ifsc_code
	if delivery_territories is not None:
		record.delivery_territories = _parse_territories_json(delivery_territories)

	if dist_photo is not None:
		final_dist_name = dist_name if dist_name is not None else record.dist_name
		try:
			record.dist_photo = save_distributor_photo(dist_photo, record.dist_id, final_dist_name)
		except Exception as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid photo") from exc

	db.commit()
	db.refresh(record)
	return record


# Delete a Distributor record by its Distributor ID. Returns a success message on successful deletion.
@router.delete("/delete-by/{dist_id}", status_code=status.HTTP_200_OK)
def delete_distributor_by_id(dist_id: str, db: Session = Depends(get_db)):
	record = db.query(Distributor).filter(Distributor.dist_id == dist_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Distributor not found")

	try:
		delete_distributor_photo_assets(record.dist_id)
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Failed to delete distributor photo assets",
		) from exc

	db.delete(record)
	db.commit()
	return {"message": f"Distributor with id {dist_id} deleted successfully"}
