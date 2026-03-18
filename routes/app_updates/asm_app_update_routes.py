

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse

router = APIRouter(prefix="/asm-app-updates", tags=["ASM App Updates"])

APK_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "apk-builds", "asm-app")

def get_apk_versions():
    files = []
    if os.path.isdir(APK_DIR):
        files = [f for f in os.listdir(APK_DIR) if f.endswith(".apk")]
    return sorted(files)

@router.get("/versions")
def get_all_versions():
    versions = get_apk_versions()
    return {"versions": versions}

@router.get("/download/{filename}")
def download_specific_apk(filename: str):
    file_path = os.path.join(APK_DIR, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="application/vnd.android.package-archive", filename=filename)

@router.get("/download-latest")
def download_latest_apk():
    versions = get_apk_versions()
    if not versions:
        raise HTTPException(status_code=404, detail="No APK files found")
    latest = sorted(versions)[-1]
    file_path = os.path.join(APK_DIR, latest)
    return FileResponse(file_path, media_type="application/vnd.android.package-archive", filename=latest)

@router.get("/latest-version")
def get_latest_version():
    versions = get_apk_versions()
    if not versions:
        return JSONResponse({"version": None, "apk_file": None, "apk_url": None})
    latest = sorted(versions)[-1]
    return {
        "version": latest,
        "apk_file": latest,
        "apk_url": f"/asm-app-updates/download/{latest}"
    }