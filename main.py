import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from db import init_db
from routes.about_us.about_us_routes import router as about_us_router
from routes.appointment.asm.asm_appointment_routes import router as asm_appointment_router
from routes.appointment.mr.mr_appointment_routes import router as mr_appointment_router
from routes.attendance.asm_attendance_routes import router as asm_attendance_router
from routes.attendance.mr_attendance_routes import router as mr_attendance_router
from routes.chemist_shop.asm_chemist_shop_network_routes import router as asm_chemist_shop_network_router
from routes.chemist_shop.mr_chemist_shop_network_routes import router as mr_chemist_shop_network_router
from routes.doctor_network.asm_doctor_network_routes import router as asm_doctor_network_router
from routes.doctor_network.mr_doctor_network_routes import router as mr_doctor_network_router
from routes.distributor.distributor_routes import router as distributor_router
from routes.gift.gift_inventory_routes import router as gift_inventory_router
from routes.gift.mr_gift_application_routes import router as mr_gift_application_router
from routes.monthly_plan.monthly_plan_routes import router as monthly_plan_router
from routes.monthly_target.asm_monthly_target_routes import router as asm_monthly_target_router
from routes.monthly_target.mr_monhtly_target_routes import router as mr_monthly_target_router
from routes.notification.notification_routes import router as notification_router
from routes.order.asm_order_routes import router as asm_order_router
from routes.order.mr_order_routes import router as mr_order_router
from routes.salary_slip.asm_salary_slip_routes import router as asm_salary_slip_router
from routes.salary_slip.mr_salary_slip_routes import router as mr_salary_slip_router
from routes.onboarding.asm_onboarding_routes import router as asm_onboarding_router
from routes.onboarding.mr_onboarding_routes import router as mr_onboarding_router
from routes.team.team_routes import router as team_router
from routes.visual_ads.visual_ads_routes import router as visual_ads_router

load_dotenv()

logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("medorica_backend")

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
	init_db()
	logger.info("Database initialized and tables created (if not existing).")
	yield

app = FastAPI(title="Medorica Backend", lifespan=lifespan)

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

cors_origins_raw = os.getenv("CORS_ORIGINS", "*")
cors_origins = [origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()]

app.add_middleware(
	CORSMiddleware,
	allow_origins=cors_origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)




@app.get("/health", tags=["Health"])
# Return a simple health status response for uptime checks.
def healthcheck():
	return {"status": "ok", "message": "Backend is running"}


app.include_router(asm_onboarding_router)
app.include_router(asm_appointment_router)
app.include_router(asm_attendance_router)
app.include_router(mr_attendance_router)
app.include_router(asm_chemist_shop_network_router)
app.include_router(mr_chemist_shop_network_router)
app.include_router(asm_doctor_network_router)
app.include_router(mr_doctor_network_router)
app.include_router(about_us_router)
app.include_router(distributor_router)
app.include_router(gift_inventory_router)
app.include_router(mr_gift_application_router)
app.include_router(monthly_plan_router)
app.include_router(asm_monthly_target_router)
app.include_router(mr_monthly_target_router)
app.include_router(asm_order_router)
app.include_router(mr_order_router)
app.include_router(asm_salary_slip_router)
app.include_router(mr_salary_slip_router)
app.include_router(notification_router)
app.include_router(mr_onboarding_router)
app.include_router(team_router)
app.include_router(visual_ads_router)
app.include_router(mr_appointment_router)


if __name__ == "__main__":
	import uvicorn

	host = os.getenv("HOST", "0.0.0.0")
	port = int(os.getenv("PORT", "8000"))
	logger.info("Starting server on %s:%s", host, port)
	uvicorn.run("main:app", host=host, port=port, reload=True)

