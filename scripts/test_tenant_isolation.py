import sys
import time
import requests

SUPABASE_URL = "https://epgibdkihcswaaresftw.supabase.co"
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVwZ2liZGtpaGNzd2FhcmVzZnR3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODkwNjMxOTcsImV4cCI6MjEwNDYzOTE5N30.echJzPzlM0UYhLjZ__TW7ldf_o52CFHDNtPfqhpMovU"
FASTAPI_BASE = "http://127.0.0.1:8000/api/v1"

USER_A_EMAIL = "iamnegative37@gmail.com"
ORG_A_ID = "11111111-1111-1111-1111-111111111111"

USER_B_EMAIL = "akashdas200x@gmail.com"
ORG_B_ID = "22222222-2222-2222-2222-222222222222"

PASSWORD = "Surveillance2026!"

def login(email: str):
    res = requests.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        headers={"apikey": ANON_KEY},
        json={"email": email, "password": PASSWORD},
        timeout=10
    )
    if res.status_code != 200:
        raise Exception(f"Failed to log in {email}: {res.status_code} {res.text}")
    data = res.json()
    return data["access_token"], data["user"]["id"]

def run_suite():
    print("=" * 70)
    print("IBVAP STRICT MULTI-TENANT ISOLATION & RLS VERIFICATION SUITE")
    print("=" * 70)

    # 1. Login both test users
    print("\n[Step 1] Authenticating Operator Accounts via Supabase Auth...")
    token_a, uid_a = login(USER_A_EMAIL)
    print(f"  [PASS] User A Authenticated: {USER_A_EMAIL} (UID: {uid_a})")
    token_b, uid_b = login(USER_B_EMAIL)
    print(f"  [PASS] User B Authenticated: {USER_B_EMAIL} (UID: {uid_b})")

    headers_anon = {"apikey": ANON_KEY}
    headers_a = {"apikey": ANON_KEY, "Authorization": f"Bearer {token_a}"}
    headers_b = {"apikey": ANON_KEY, "Authorization": f"Bearer {token_b}"}

    # 2. Verify unauthenticated access is completely blocked by RLS
    print("\n[Step 2] Testing Unauthenticated PostgREST Access (RLS Check)...")
    for table in ["alerts", "events", "zones", "cameras", "sites"]:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}", headers=headers_anon, timeout=15)
        rows = r.json() if r.status_code == 200 else []
        assert len(rows) == 0, f"LEAK: Unauthenticated request read rows from {table}!"
        print(f"  [PASS] Anonymous access to {table}: 0 rows returned (RLS protected)")

    # 3. Account 1 provisions Org A test resources
    print("\n[Step 3] Creating Organization A Surveillance Data (Org North)...")
    requests.delete(f"{SUPABASE_URL}/rest/v1/alerts?organization_id=eq.{ORG_A_ID}", headers=headers_a)
    requests.delete(f"{SUPABASE_URL}/rest/v1/events?organization_id=eq.{ORG_A_ID}", headers=headers_a)
    requests.delete(f"{SUPABASE_URL}/rest/v1/zones?organization_id=eq.{ORG_A_ID}", headers=headers_a)
    requests.delete(f"{SUPABASE_URL}/rest/v1/cameras?organization_id=eq.{ORG_A_ID}", headers=headers_a)
    requests.delete(f"{SUPABASE_URL}/rest/v1/sites?organization_id=eq.{ORG_A_ID}", headers=headers_a)

    site_payload = {
        "organization_id": ORG_A_ID,
        "site_id": "SITE-NORTH-01",
        "name": "North Perimeter Outpost",
        "location": "Sector 1A"
    }
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/sites",
        headers={**headers_a, "Prefer": "return=representation"},
        json=site_payload,
        timeout=15
    )
    assert r.status_code in [200, 201], f"Failed to create Site A: {r.text}"
    print("  [PASS] Created Site A in Org A")

    camera_payload = {
        "organization_id": ORG_A_ID,
        "camera_id": "CAM-NORTH-01",
        "name": "Border Cam North 01",
        "source_url": "0",
        "location": "North Wall",
        "status": "ONLINE",
        "enabled": True
    }
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/cameras",
        headers={**headers_a, "Prefer": "return=representation"},
        json=camera_payload,
        timeout=15
    )
    assert r.status_code in [200, 201], f"Failed to create Camera A: {r.text}"
    cam_uuid_a = r.json()[0]["id"]
    print(f"  [PASS] Created Camera A in Org A (UUID: {cam_uuid_a})")

    zone_payload = {
        "organization_id": ORG_A_ID,
        "camera_id": cam_uuid_a,
        "zone_id": "ZONE-NORTH-01",
        "name": "North Fence Restricted Area",
        "zone_type": "polygon",
        "polygon_coords": [[10, 10], [100, 10], [100, 100], [10, 100]],
        "line_coords": [],
        "is_restricted": True,
        "dwell_threshold": 5.0,
        "prohibited_directions": [],
        "color": "#ef4444",
        "enabled": True
    }
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/zones",
        headers={**headers_a, "Prefer": "return=representation"},
        json=zone_payload,
        timeout=15
    )
    assert r.status_code in [200, 201], f"Failed to create Zone A: {r.text}"
    print("  [PASS] Created Zone A in Org A")

    alert_payload = {
        "organization_id": ORG_A_ID,
        "alert_id": "ALT-NORTH-9999",
        "event_type": "INTRUSION",
        "severity": "CRITICAL",
        "camera_id": "CAM-NORTH-01",
        "zone_id": "ZONE-NORTH-01",
        "zone_name": "North Fence Restricted Area",
        "object_type": "person",
        "confidence": 0.95,
        "description": "CRITICAL: Unauthorized intruder detected at North Fence",
        "status": "NEW"
    }
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/alerts",
        headers={**headers_a, "Prefer": "return=representation"},
        json=alert_payload,
        timeout=15
    )
    assert r.status_code in [200, 201], f"Failed to create Alert A: {r.text}"
    print("  [PASS] Created Alert A in Org A")

    event_payload = {
        "organization_id": ORG_A_ID,
        "event_id": "EVT-NORTH-9999",
        "camera_id": "CAM-NORTH-01",
        "event_type": "PERIMETER_BREACH",
        "object_type": "person",
        "confidence": 0.95,
        "zone_name": "North Fence Restricted Area"
    }
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/events",
        headers={**headers_a, "Prefer": "return=representation"},
        json=event_payload,
        timeout=15
    )
    assert r.status_code in [200, 201], f"Failed to create Event A: {r.text}"
    print("  [PASS] Created Event A in Org A")

    # 4. Verify Account 1 sees its own data
    print("\n[Step 4] Verifying User A can read Org A resources...")
    r = requests.get(f"{SUPABASE_URL}/rest/v1/alerts?organization_id=eq.{ORG_A_ID}", headers=headers_a)
    assert len(r.json()) == 1, "User A failed to read own alert!"
    print(f"  [PASS] User A read Alert: {r.json()[0]['alert_id']}")

    # 5. RLS Cross-Tenant Attack Tests for Account 2
    print("\n[Step 5] Attempting Cross-Tenant Exploit with User B (Org South) credentials...")
    
    # 5a. Direct SELECT without filters
    r = requests.get(f"{SUPABASE_URL}/rest/v1/alerts", headers=headers_b)
    rows = r.json()
    assert len(rows) == 0, f"SECURITY VIOLATION: User B saw {len(rows)} alerts from other tenants!"
    print("  [PASS] User B blanket query returned 0 alerts (RLS block confirmed)")

    # 5b. Direct SELECT targeting Org A explicitly
    r = requests.get(f"{SUPABASE_URL}/rest/v1/alerts?organization_id=eq.{ORG_A_ID}", headers=headers_b)
    rows = r.json()
    assert len(rows) == 0, f"SECURITY VIOLATION: User B targeted Org A and read {len(rows)} rows!"
    print("  [PASS] User B targeted query on Org A returned 0 alerts (RLS block confirmed)")

    # 5c. Cross-tenant INSERT into Org A using User B's token
    malicious_insert = {
        "organization_id": ORG_A_ID,  # Spoofing Org A
        "alert_id": "ALT-HACK-001",
        "event_type": "INTRUSION",
        "severity": "HIGH",
        "camera_id": "CAM-NORTH-01",
        "description": "Cross-tenant injected alert",
        "status": "NEW"
    }
    r = requests.post(f"{SUPABASE_URL}/rest/v1/alerts", headers=headers_b, json=malicious_insert)
    assert r.status_code not in [200, 201], "SECURITY VIOLATION: User B inserted alert into Org A!"
    print(f"  [PASS] User B spoofed INSERT into Org A was rejected (HTTP {r.status_code})")

    # 5d. Cross-tenant UPDATE on Org A alert
    r = requests.patch(
        f"{SUPABASE_URL}/rest/v1/alerts?alert_id=eq.ALT-NORTH-9999",
        headers={**headers_b, "Prefer": "return=representation"},
        json={"status": "TAMPERED"}
    )
    rows = r.json() if r.status_code == 200 else []
    assert len(rows) == 0, "SECURITY VIOLATION: User B updated Org A alert!"
    print("  [PASS] User B UPDATE on Org A alert modified 0 rows (RLS block confirmed)")

    # 5e. Cross-tenant DELETE on Org A alert
    r = requests.delete(
        f"{SUPABASE_URL}/rest/v1/alerts?alert_id=eq.ALT-NORTH-9999",
        headers={**headers_b, "Prefer": "return=representation"}
    )
    rows = r.json() if r.status_code == 200 else []
    assert len(rows) == 0, "SECURITY VIOLATION: User B deleted Org A alert!"
    print("  [PASS] User B DELETE on Org A alert modified 0 rows (RLS block confirmed)")

    # 6. Backend FastAPI Multi-Tenant Endpoint Verification
    print("\n[Step 6] Testing FastAPI Backend Endpoints (/api/v1/*)...")
    
    # 6a. Missing token -> 401
    r = requests.get(f"{FASTAPI_BASE}/alerts/", timeout=15)
    assert r.status_code == 401, f"Expected 401 on unauthenticated backend request, got {r.status_code}"
    print("  [PASS] FastAPI /alerts/ without token: HTTP 401 Unauthorized")

    # 6b. User A token -> returns Org A alert
    r = requests.get(f"{FASTAPI_BASE}/alerts/", headers={"Authorization": f"Bearer {token_a}"}, timeout=15)
    assert r.status_code == 200, f"Failed: {r.status_code} {r.text}"
    data_a = r.json()
    assert len(data_a) == 1 and data_a[0]["alert_id"] == "ALT-NORTH-9999", f"User A unexpected alerts: {data_a}"
    print(f"  [PASS] FastAPI /alerts/ with User A token returned 1 alert: {data_a[0]['alert_id']}")

    # 6c. User B token -> returns 0 alerts
    r = requests.get(f"{FASTAPI_BASE}/alerts/", headers={"Authorization": f"Bearer {token_b}"}, timeout=15)
    assert r.status_code == 200, f"Failed: {r.status_code} {r.text}"
    data_b = r.json()
    assert len(data_b) == 0, f"SECURITY VIOLATION: FastAPI returned alerts to User B: {data_b}"
    print(f"  [PASS] FastAPI /alerts/ with User B token returned 0 alerts (Strict Isolation)")

    # 6d. FastAPI /events/stats endpoint check
    r = requests.get(f"{FASTAPI_BASE}/events/stats", headers={"Authorization": f"Bearer {token_a}"})
    stats_a = r.json()
    print(f"  [PASS] User A Stats: active_alerts={stats_a.get('active_alerts')}, events_today={stats_a.get('events_today')}")
    assert stats_a.get("active_alerts") == 1

    r = requests.get(f"{FASTAPI_BASE}/events/stats", headers={"Authorization": f"Bearer {token_b}"})
    stats_b = r.json()
    print(f"  [PASS] User B Stats: active_alerts={stats_b.get('active_alerts')}, events_today={stats_b.get('events_today')}")
    assert stats_b.get("active_alerts") == 0

    # 7. Clean up test data
    print("\n[Step 7] Cleaning Up Test Records for Clean Slate...")
    requests.delete(f"{SUPABASE_URL}/rest/v1/alerts?alert_id=eq.ALT-NORTH-9999", headers=headers_a)
    requests.delete(f"{SUPABASE_URL}/rest/v1/events?event_id=eq.EVT-NORTH-9999", headers=headers_a)
    requests.delete(f"{SUPABASE_URL}/rest/v1/zones?zone_id=eq.ZONE-NORTH-01", headers=headers_a)
    requests.delete(f"{SUPABASE_URL}/rest/v1/cameras?camera_id=eq.CAM-NORTH-01", headers=headers_a)
    requests.delete(f"{SUPABASE_URL}/rest/v1/sites?site_id=eq.SITE-NORTH-01", headers=headers_a)

    # Verify test alert is gone
    r = requests.get(f"{SUPABASE_URL}/rest/v1/alerts?alert_id=eq.ALT-NORTH-9999", headers=headers_a)
    assert len(r.json()) == 0, "Test alert cleanup incomplete!"
    print("  [PASS] Test records cleaned up successfully")

    print("\n" + "=" * 70)
    print("ALL MULTI-TENANT ISOLATION & RLS GUARANTEES VERIFIED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_suite()
