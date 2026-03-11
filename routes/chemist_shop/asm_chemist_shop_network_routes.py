from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from models.chemist_shop.asm_chemist_shop_network_models import ASMChemistShopNetwork
from models.onboarding.asm_onboarding_models import AreaSalesManager
from services.chemist_shop.asm.asm_chemist_shop_id_generator import generate_asm_chemist_shop_id
from services.chemist_shop.asm.asm_chemist_shop_photo_upload import (
	delete_asm_chemist_shop_assets,
	save_asm_chemist_shop_bank_passbook_photo,
	save_asm_chemist_shop_photo,
)

router = APIRouter(prefix="/chemist-shop/asm", tags=["ASM Chemist Shop Network"])


class ASMChemistShopNetworkResponseSchema(BaseModel):
	id: int
	shop_id: str
	asm_id: str
	shop_name: str
	address: Optional[str] = None
	phone_no: str
	email: Optional[str] = None
	description: Optional[str] = None
	photo: Optional[str] = None
	bank_passbook_photo: Optional[str] = None
	created_at: datetime
	updated_at: datetime

	class Config:
		from_attributes = True


# Create a chemist shop record for an ASM.
@router.post("/post", response_model=ASMChemistShopNetworkResponseSchema, status_code=status.HTTP_201_CREATED)
def create_asm_chemist_shop(
	asm_id: str = Form(...),
	shop_name: str = Form(...),
	phone_no: str = Form(...),
	address: Optional[str] = Form(None),
	email: Optional[str] = Form(None),
	description: Optional[str] = Form(None),
	photo: Optional[UploadFile] = File(None),
	bank_passbook_photo: Optional[UploadFile] = File(None),
	db: Session = Depends(get_db),
):
	asm_record = db.query(AreaSalesManager).filter(AreaSalesManager.asm_id == asm_id).first()
	if not asm_record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ASM not found")

	existing_shop_for_asm = (
		db.query(ASMChemistShopNetwork)
		.filter(ASMChemistShopNetwork.asm_id == asm_id, ASMChemistShopNetwork.phone_no == phone_no)
		.first()
	)
	if existing_shop_for_asm:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Chemist shop with this phone number already exists for this ASM",
		)

	try:
		generated_shop_id = generate_asm_chemist_shop_id(phone_no)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

	new_shop = ASMChemistShopNetwork(
		shop_id=generated_shop_id,
		asm_id=asm_id,
		shop_name=shop_name,
		address=address,
		phone_no=phone_no,
		email=email,
		description=description,
	)

	if photo is not None:
		try:
			new_shop.photo = save_asm_chemist_shop_photo(photo, generated_shop_id, shop_name)
		except Exception as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid shop photo") from exc

	if bank_passbook_photo is not None:
		try:
			new_shop.bank_passbook_photo = save_asm_chemist_shop_bank_passbook_photo(
				bank_passbook_photo, generated_shop_id, shop_name
			)
		except Exception as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid bank passbook photo") from exc

	db.add(new_shop)
	db.commit()
	db.refresh(new_shop)
	return new_shop


# Fetch all chemist shops in the ASM chemist shop network.
@router.get("/get-all", response_model=list[ASMChemistShopNetworkResponseSchema])
def get_all_asm_chemist_shops(db: Session = Depends(get_db)):
	return db.query(ASMChemistShopNetwork).all()


# Fetch all chemist shops linked to a specific ASM ID.
@router.get("/get-by-asm/{asm_id}", response_model=list[ASMChemistShopNetworkResponseSchema])
def get_chemist_shops_by_asm_id(asm_id: str, db: Session = Depends(get_db)):
	asm_record = db.query(AreaSalesManager).filter(AreaSalesManager.asm_id == asm_id).first()
	if not asm_record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ASM not found")
	return db.query(ASMChemistShopNetwork).filter(ASMChemistShopNetwork.asm_id == asm_id).all()


# Fetch a specific chemist shop by ASM ID and shop ID.
@router.get("/get-by/{asm_id}/{shop_id}", response_model=ASMChemistShopNetworkResponseSchema)
def get_chemist_shop_by_asm_and_shop_id(asm_id: str, shop_id: str, db: Session = Depends(get_db)):
	record = (
		db.query(ASMChemistShopNetwork)
		.filter(ASMChemistShopNetwork.asm_id == asm_id, ASMChemistShopNetwork.shop_id == shop_id)
		.first()
	)
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chemist shop not found")
	return record


# Fetch a specific chemist shop by shop ID only.
@router.get("/get-by-shop/{shop_id}", response_model=ASMChemistShopNetworkResponseSchema)
def get_chemist_shop_by_shop_id(shop_id: str, db: Session = Depends(get_db)):
	record = db.query(ASMChemistShopNetwork).filter(ASMChemistShopNetwork.shop_id == shop_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chemist shop not found")
	return record


# Update a chemist shop by ASM ID and shop ID.
@router.put("/update-by/{asm_id}/{shop_id}", response_model=ASMChemistShopNetworkResponseSchema)
def update_chemist_shop_by_asm_and_shop_id(
	asm_id: str,
	shop_id: str,
	shop_name: Optional[str] = Form(None),
	phone_no: Optional[str] = Form(None),
	address: Optional[str] = Form(None),
	email: Optional[str] = Form(None),
	description: Optional[str] = Form(None),
	photo: Optional[UploadFile] = File(None),
	bank_passbook_photo: Optional[UploadFile] = File(None),
	db: Session = Depends(get_db),
):
	record = (
		db.query(ASMChemistShopNetwork)
		.filter(ASMChemistShopNetwork.asm_id == asm_id, ASMChemistShopNetwork.shop_id == shop_id)
		.first()
	)
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chemist shop not found")

	if phone_no is not None:
		existing_for_phone = (
			db.query(ASMChemistShopNetwork)
			.filter(
				ASMChemistShopNetwork.asm_id == asm_id,
				ASMChemistShopNetwork.phone_no == phone_no,
				ASMChemistShopNetwork.id != record.id,
			)
			.first()
		)
		if existing_for_phone:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Chemist shop with this phone number already exists for this ASM",
			)

		try:
			new_shop_id = generate_asm_chemist_shop_id(phone_no)
		except ValueError as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

		if new_shop_id != record.shop_id:
			existing_shop_id = (
				db.query(ASMChemistShopNetwork)
				.filter(ASMChemistShopNetwork.shop_id == new_shop_id, ASMChemistShopNetwork.id != record.id)
				.first()
			)
			if existing_shop_id:
				raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shop ID already in use")
			record.shop_id = new_shop_id

		record.phone_no = phone_no

	if shop_name is not None:
		record.shop_name = shop_name
	if address is not None:
		record.address = address
	if email is not None:
		record.email = email
	if description is not None:
		record.description = description

	if photo is not None:
		photo_shop_name = shop_name if shop_name is not None else record.shop_name
		try:
			record.photo = save_asm_chemist_shop_photo(photo, record.shop_id, photo_shop_name)
		except Exception as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid shop photo") from exc

	if bank_passbook_photo is not None:
		passbook_shop_name = shop_name if shop_name is not None else record.shop_name
		try:
			record.bank_passbook_photo = save_asm_chemist_shop_bank_passbook_photo(
				bank_passbook_photo, record.shop_id, passbook_shop_name
			)
		except Exception as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid bank passbook photo") from exc

	db.commit()
	db.refresh(record)
	return record


# Update a chemist shop by shop ID only.
@router.put("/update-by-shop/{shop_id}", response_model=ASMChemistShopNetworkResponseSchema)
def update_chemist_shop_by_shop_id(
	shop_id: str,
	shop_name: Optional[str] = Form(None),
	phone_no: Optional[str] = Form(None),
	address: Optional[str] = Form(None),
	email: Optional[str] = Form(None),
	description: Optional[str] = Form(None),
	photo: Optional[UploadFile] = File(None),
	bank_passbook_photo: Optional[UploadFile] = File(None),
	db: Session = Depends(get_db),
):
	record = db.query(ASMChemistShopNetwork).filter(ASMChemistShopNetwork.shop_id == shop_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chemist shop not found")

	return update_chemist_shop_by_asm_and_shop_id(
		asm_id=record.asm_id,
		shop_id=record.shop_id,
		shop_name=shop_name,
		phone_no=phone_no,
		address=address,
		email=email,
		description=description,
		photo=photo,
		bank_passbook_photo=bank_passbook_photo,
		db=db,
	)


# Delete a chemist shop by ASM ID and shop ID, and remove associated assets.
@router.delete("/delete-by/{asm_id}/{shop_id}", status_code=status.HTTP_200_OK)
def delete_chemist_shop_by_asm_and_shop_id(asm_id: str, shop_id: str, db: Session = Depends(get_db)):
	record = (
		db.query(ASMChemistShopNetwork)
		.filter(ASMChemistShopNetwork.asm_id == asm_id, ASMChemistShopNetwork.shop_id == shop_id)
		.first()
	)
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chemist shop not found")

	try:
		delete_asm_chemist_shop_assets(record.shop_id)
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Failed to delete chemist shop assets",
		) from exc

	db.delete(record)
	db.commit()
	return {"message": f"Chemist shop with id {shop_id} deleted successfully"}


# Delete a chemist shop by shop ID only, and remove associated assets.
@router.delete("/delete-by-shop/{shop_id}", status_code=status.HTTP_200_OK)
def delete_chemist_shop_by_shop_id(shop_id: str, db: Session = Depends(get_db)):
	record = db.query(ASMChemistShopNetwork).filter(ASMChemistShopNetwork.shop_id == shop_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chemist shop not found")

	try:
		delete_asm_chemist_shop_assets(record.shop_id)
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Failed to delete chemist shop assets",
		) from exc

	db.delete(record)
	db.commit()
	return {"message": f"Chemist shop with id {shop_id} deleted successfully"}
