import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from db import init_db
from routes.about_us.about_us_routes import router as about_us_router
from routes.distributor.distributor_routes import router as distributor_router
from routes.onboarding.asm_onboarding_routes import router as asm_onboarding_router
from routes.onboarding.mr_onboarding_routes import router as mr_onboarding_router

load_dotenv()

logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("medorica_backend")

app = FastAPI(title="Medorica Backend")

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


@app.on_event("startup")
# Initialize database tables when the FastAPI app starts.
def startup_event():
	init_db()
	logger.info("Database initialized and tables created (if not existing).")


@app.get("/health", tags=["Health"])
# Return a simple health status response for uptime checks.
def healthcheck():
	return {"status": "ok", "message": "Backend is running"}


app.include_router(asm_onboarding_router)
app.include_router(about_us_router)
app.include_router(distributor_router)
app.include_router(mr_onboarding_router)


if __name__ == "__main__":
	import uvicorn

	port = int(os.getenv("PORT", "8000"))
	logger.info("Starting server on 0.0.0.0:%s", port)
	uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

