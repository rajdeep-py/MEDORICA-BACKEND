from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
import re

router = APIRouter(prefix="/mr-app-updates", tags=["MR App Updates"])

APK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../apk-builds/mr-app'))
# Debug print to verify resolved APK_DIR path
print(f"MR APK_DIR resolved to: {APK_DIR}")

def get_apk_versions():
	files = os.listdir(APK_DIR)
	apk_pattern = re.compile(r"mr-app-(\d+)\.apk")
	versions = []
	for f in files:
		m = apk_pattern.match(f)
		if m:
			versions.append((int(m.group(1)), f))
	versions.sort(reverse=True)
	return versions

@router.get("/download/{version}", summary="Download MR app APK for specific version")
def download_mr_app_version(version: int):
	apk_name = f"mr-app-{version}.apk"
	apk_path = os.path.join(APK_DIR, apk_name)
	if not os.path.isfile(apk_path):
		raise HTTPException(status_code=404, detail="APK not found for this version")
	return FileResponse(apk_path, filename=apk_name, media_type="application/vnd.android.package-archive")

@router.get("/download/latest", summary="Download latest MR app APK")
def download_latest_mr_app():
	versions = get_apk_versions()
	if not versions:
		raise HTTPException(status_code=404, detail="No APKs found")
	latest_version, latest_apk = versions[0]
	apk_path = os.path.join(APK_DIR, latest_apk)
	return FileResponse(apk_path, filename=latest_apk, media_type="application/vnd.android.package-archive")

@router.get("/versions", summary="List available MR app versions")
def list_mr_app_versions():
	versions = get_apk_versions()
	return {"versions": [v for v, _ in versions]}
