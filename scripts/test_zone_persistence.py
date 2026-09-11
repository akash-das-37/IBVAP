import sys
import time
import requests
from scripts.test_tenant_isolation import (
    login,
    SUPABASE_URL,
    ANON_KEY,
    FASTAPI_BASE,
    USER_A_EMAIL,
    ORG_A_ID,
    USER_B_EMAIL,
    ORG_B_ID,
    PASSWORD
)

def run_zone_persistence_suite():
    print("=" * 75)
    print("IBVAP ZONE PERSISTENCE & MULTI-TENANT HIERARCHY VERIFICATION SUITE")
    print("=" * 75)

    # 1. Login User A and User B
    print("\n[Step 1] Authenticating Operator Accounts...")
    token_a, uid_a = login(USER_A_EMAIL)
    print(f"  [PASS] User A Logged In: {USER_A_EMAIL} (Org North: {ORG_A_ID})")
    token_b, uid_b = login(USER_B_EMAIL)
    print(f"  [PASS] User B Logged In: {USER_B_EMAIL} (Org South: {ORG_B_ID})")

    headers_a = {"apikey": ANON_KEY, "Authorization": f"Bearer {token_a}"}
    headers_b = {"apikey": ANON_KEY, "Authorization": f"Bearer {token_b}"}

    # 2. Verify User A's Camera & Site linkage
    print("\n[Step 2] Verifying Camera & Site Hierarchy for Org North...")
    r = requests.get(f"{FASTAPI_BASE}/cameras/", headers={"Authorization": f"Bearer {token_a}"})
    assert r.status_code == 200, f"Failed to get cameras: {r.text}"
    cams_a = r.json()
    assert len(cams_a) > 0, "No camera found for Org North!"
    cam_a = cams_a[0]
    camera_uuid = cam_a["id"]
    site_uuid = cam_a.get("site_id")
    print(f"  [PASS] Resolved Camera: '{cam_a['name']}' (UUID: {camera_uuid})")
    print(f"  [PASS] Resolved Site UUID: {site_uuid}")
    assert camera_uuid is not None, "Camera UUID cannot be null"
    assert site_uuid is not None, "Site UUID cannot be null"

    # 3. Save Zone for Org A (using camera display ID 'CAM-01')
    print("\n[Step 3] Creating & Persisting Polygon Zone via Backend API...")
    zone_payload = {
        "zone_id": "ZONE-CUSTOM-001",
        "camera_id": "CAM-01",  # Test backend resolution of 'CAM-01' -> camera_uuid
        "name": "Custom Border Sector 1",
        "zone_type": "polygon",
        "polygon_data": [
            {"x": 0.25, "y": 0.20},
            {"x": 0.75, "y": 0.20},
            {"x": 0.80, "y": 0.70},
            {"x": 0.30, "y": 0.70}
        ],
        "polygon_coords": [],
        "line_coords": [],
        "is_restricted": True,
        "dwell_threshold": 10.0,
        "prohibited_directions": [],
        "color": "#ef4444",
        "enabled": True
    }

    r = requests.post(
        f"{FASTAPI_BASE}/zones/",
        headers={"Authorization": f"Bearer {token_a}", "Content-Type": "application/json"},
        json=zone_payload,
        timeout=10
    )
    assert r.status_code in [200, 201], f"Failed to save zone: {r.status_code} {r.text}"
    res_data = r.json()
    print(f"  [PASS] Zone Saved via Backend: {res_data.get('message')}")
    print(f"         camera_id saved as UUID: {res_data.get('camera_id')}")
    print(f"         site_id saved as UUID: {res_data.get('site_id')}")
    assert res_data.get("camera_id") == camera_uuid, "Camera ID was not resolved to the camera UUID!"
    assert res_data.get("site_id") == site_uuid, "Site ID was not resolved to the site UUID!"

    # 4. Direct Supabase PostgREST Check for User A
    print("\n[Step 4] Checking Supabase Database Table 'zones' directly...")
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/zones?organization_id=eq.{ORG_A_ID}",
        headers=headers_a,
        timeout=5
    )
    assert r.status_code == 200, f"Failed Supabase query: {r.text}"
    db_rows = r.json()
    assert len(db_rows) == 1, f"Expected 1 zone in Supabase, found: {len(db_rows)}"
    z_row = db_rows[0]
    print(f"  [PASS] Row verified in Supabase: id={z_row['id']}")
    print(f"         organization_id: {z_row['organization_id']}")
    print(f"         site_id: {z_row['site_id']}")
    print(f"         camera_id: {z_row['camera_id']}")
    print(f"         name: {z_row['name']}")
    print(f"         polygon_data points: {len(z_row['polygon_data'])}")
    assert z_row['organization_id'] == ORG_A_ID
    assert z_row['site_id'] == site_uuid
    assert z_row['camera_id'] == camera_uuid
    assert len(z_row['polygon_data']) == 4
    assert z_row['polygon_data'][0] == {"x": 0.25, "y": 0.20}

    # 5. Query /api/v1/zones/ with User A token
    print("\n[Step 5] Querying Backend /api/v1/zones/ for User A...")
    r = requests.get(f"{FASTAPI_BASE}/zones/", headers={"Authorization": f"Bearer {token_a}"})
    assert r.status_code == 200
    zones_a = r.json()
    assert len(zones_a) == 1
    assert zones_a[0]["zone_id"] == "ZONE-CUSTOM-001"
    print(f"  [PASS] User A retrieves zone: '{zones_a[0]['name']}' (survives refresh)")

    # 6. Multi-Tenant Cross-Account Isolation Test (User B / Org South)
    print("\n[Step 6] Testing Multi-Tenant Isolation with User B (Org South)...")
    
    # 6a. Direct PostgREST query with User B token - ensure NO Org A zones returned
    r = requests.get(f"{SUPABASE_URL}/rest/v1/zones", headers=headers_b)
    user_b_zones = r.json() if r.status_code == 200 else []
    org_a_leaks = [z for z in user_b_zones if z.get("organization_id") == ORG_A_ID]
    assert len(org_a_leaks) == 0, f"SECURITY LEAK: User B saw zones from Org A: {org_a_leaks}"
    print("  [PASS] User B query returned 0 zones from Org A (RLS protected)")

    # 6b. Direct PostgREST query targeting Org A's ID
    r = requests.get(f"{SUPABASE_URL}/rest/v1/zones?organization_id=eq.{ORG_A_ID}", headers=headers_b)
    assert len(r.json() if r.status_code == 200 else []) == 0, f"SECURITY LEAK: User B targeted Org A and saw {r.json()}"
    print("  [PASS] User B targeted Org A Supabase query returned 0 rows (RLS protected)")

    # 6c. Backend API /zones/ query with User B token - ensure NO Org A zones returned
    r = requests.get(f"{FASTAPI_BASE}/zones/", headers={"Authorization": f"Bearer {token_b}"})
    assert r.status_code == 200
    b_api_zones = r.json()
    org_a_backend_leaks = [z for z in b_api_zones if z.get("organization_id") == ORG_A_ID or z.get("zone_id") == "ZONE-CUSTOM-001"]
    assert len(org_a_backend_leaks) == 0, f"SECURITY LEAK: Backend returned Org A zones to User B: {org_a_backend_leaks}"
    print("  [PASS] Backend /api/v1/zones/ returned 0 zones from Org A for User B")

    # 6d. Cross-tenant update attempt by User B
    r = requests.patch(
        f"{SUPABASE_URL}/rest/v1/zones?zone_id=eq.ZONE-CUSTOM-001",
        headers={**headers_b, "Prefer": "return=representation"},
        json={"name": "Hacked Zone"}
    )
    assert len(r.json() if r.status_code == 200 else []) == 0
    print("  [PASS] Cross-tenant UPDATE by User B modified 0 rows (RLS protected)")

    # 6e. Cross-tenant delete attempt by User B
    r = requests.delete(
        f"{SUPABASE_URL}/rest/v1/zones?zone_id=eq.ZONE-CUSTOM-001",
        headers={**headers_b, "Prefer": "return=representation"}
    )
    assert len(r.json() if r.status_code == 200 else []) == 0
    print("  [PASS] Cross-tenant DELETE by User B modified 0 rows (RLS protected)")

    # 7. AI Pipeline & Security Rule Engine Evaluation
    print("\n[Step 7] Testing AI Pipeline & Rule Engine Polygon Containment...")
    from backend.ai.rules import SecurityRuleEngine

    # Test scaling of retrieved zone from Step 5
    scaled = []
    for z in zones_a:
        sz = dict(z)
        pts = sz.get("polygon_data") or sz.get("polygon_coords")
        scaled_pts = []
        for pt in pts:
            if isinstance(pt, dict):
                scaled_pts.append([int(round(float(pt["x"]) * 640)), int(round(float(pt["y"]) * 480))])
            else:
                scaled_pts.append([int(round(float(pt[0]) * 640)), int(round(float(pt[1]) * 480))])
        sz["polygon_coords"] = scaled_pts
        scaled.append(sz)

    assert len(scaled) == 1
    scaled_pts = scaled[0]["polygon_coords"]
    print(f"  [PASS] Normalized points scaled to 640x480 frame: {scaled_pts}")
    # Point 1: 0.25 * 640 = 160, 0.20 * 480 = 96
    assert scaled_pts[0] == [160, 96]
    # Point 2: 0.75 * 640 = 480, 0.20 * 480 = 96
    assert scaled_pts[1] == [480, 96]

    rule_engine = SecurityRuleEngine()
    # Simulate track inside the zone (center of frame: 320, 240)
    test_tracks_inside = [{
        "track_id": 101,
        "class_name": "person",
        "bbox": [300, 200, 340, 280],  # center: (320, 240) -> inside polygon!
        "center": (320, 240),
        "direction": "SOUTH",
        "confidence": 0.92,
        "history": [(320, 240)]
    }]
    violations = rule_engine.evaluate(test_tracks_inside, scaled, now=time.time())
    assert len(violations) == 1, f"Expected 1 intrusion violation, got: {len(violations)}"
    assert "INTRUSION" in violations[0]["rule_type"]
    assert violations[0]["zone_name"] == "Custom Border Sector 1"
    print(f"  [PASS] AI Rule Engine triggered {violations[0]['rule_type']} for person inside '{violations[0]['zone_name']}'")

    # Simulate track outside the zone (x=50, y=50)
    test_tracks_outside = [{
        "track_id": 102,
        "class_name": "person",
        "bbox": [40, 40, 60, 60],  # outside polygon
        "center": (50, 50),
        "direction": "NORTH",
        "confidence": 0.90,
        "history": [(50, 50)]
    }]
    violations_outside = rule_engine.evaluate(test_tracks_outside, scaled, now=time.time())
    assert len(violations_outside) == 0, f"Expected 0 violations for outside track, got: {violations_outside}"
    print("  [PASS] AI Rule Engine ignored person outside the restricted zone")

    # 8. Clean up test zone
    print("\n[Step 8] Cleaning up test zone records...")
    r = requests.delete(
        f"{FASTAPI_BASE}/zones/ZONE-CUSTOM-001",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert r.status_code in [200, 204]
    
    # Confirm clean
    r = requests.get(f"{FASTAPI_BASE}/zones/", headers={"Authorization": f"Bearer {token_a}"})
    assert len(r.json()) == 0
    print("  [PASS] Test zone cleanly deleted. System clean slate verified.")

    print("\n" + "=" * 75)
    print("ALL ZONE PERSISTENCE & MULTI-TENANT TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 75)

if __name__ == "__main__":
    run_zone_persistence_suite()
