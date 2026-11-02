import sys, os
sys.path.insert(0, os.path.abspath('.'))

from app.core.database import SessionLocal
from app.services.instagram_service import InstagramService
from app.models.source import SocialSource
from app.core.constants import SourceType

db = SessionLocal()
service = InstagramService(db)

# Ensure baseline keywords and city feeds
service._ensure_baseline_keywords("GJ-CYBER-8921")
service._ensure_city_investigation_feed()

# Connect karan_gohel0 as authorized active source
source = service._ensure_or_update_source(
    target_identifier="karan_gohel0",
    name="Gujarat Police Cyber Crime Cell - @karan_gohel0",
    access_token="MOCK_IG_TOKEN_AUTHORIZED_PROTOTYPE_SECURE",
    mandate_ref="COMM-CYBER-2026-MANDATE",
    officer_badge="GJ-CYBER-8921",
    scopes=["instagram_basic", "pages_show_list", "pages_read_engagement"]
)

# Run keyword matcher and telemetry
data = service.get_monitoring_dashboard_data()

print(f"SUCCESS: Connected source {source.name} (ID: {source.id})")
print(f"Items in DB: {data['metrics']['total_items_retrieved']} | Matches: {data['metrics']['total_keyword_matches']}")
print(f"Results rows: {len(data['results'])}")
