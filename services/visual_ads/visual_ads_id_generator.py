# Generate Visual Ad ID in the format: AD + auto-incrementing number (AD1, AD2, AD3, etc.).
def generate_visual_ad_id(db_session) -> str:
	from models.visual_ads.visual_ads_models import VisualAd

	# Get the highest existing ad_id number
	last_ad = db_session.query(VisualAd).order_by(VisualAd.id.desc()).first()
	
	if last_ad is None:
		return "AD1"
	
	# Extract the number from the ad_id
	try:
		ad_number = int(last_ad.ad_id[2:])
		return f"AD{ad_number + 1}"
	except (ValueError, IndexError):
		# Fallback if parsing fails
		return f"AD{last_ad.id + 1}"
