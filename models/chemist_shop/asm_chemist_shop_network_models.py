from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func

from db import Base


# Store chemist shop network details managed by an ASM.
class ASMChemistShopNetwork(Base):
	__tablename__ = "asm_chemist_shop_network"
	__table_args__ = (
		UniqueConstraint("asm_id", "phone_no", name="uq_asm_chemist_shop_phone"),
	)

	id = Column(Integer, primary_key=True, index=True)
	shop_id = Column(String(64), unique=True, nullable=False, index=True)
	asm_id = Column(String(32), ForeignKey("area_sales_manager.asm_id"), nullable=False, index=True)
	shop_name = Column(String(255), nullable=False)
	address = Column(Text, nullable=True)
	phone_no = Column(String(20), nullable=False, index=True)
	email = Column(String(255), nullable=True)
	description = Column(Text, nullable=True)
	photo = Column(Text, nullable=True)
	bank_passbook_photo = Column(Text, nullable=True)
	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	updated_at = Column(
		DateTime(timezone=True),
		server_default=func.now(),
		onupdate=func.now(),
		nullable=False,
	)
