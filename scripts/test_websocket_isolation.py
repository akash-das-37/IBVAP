import asyncio
import json
from unittest.mock import AsyncMock
from backend.websocket.manager import ConnectionManager
from scripts.test_tenant_isolation import ORG_A_ID, ORG_B_ID

async def test_websocket_manager_isolation():
    print("=" * 70)
    print("TESTING WEBSOCKET CONNECTION MANAGER MULTI-TENANT ISOLATION")
    print("=" * 70)

    mgr = ConnectionManager()

    # Create mock WebSockets for Org A and Org B
    mock_ws_a1 = AsyncMock()
    mock_ws_a2 = AsyncMock()
    mock_ws_b1 = AsyncMock()

    # Register sockets to their respective organizations
    mgr._register_socket(mock_ws_a1, ORG_A_ID, "user-a-1", "userA@test.com")
    mgr._register_socket(mock_ws_a2, ORG_A_ID, "user-a-2", "userA2@test.com")
    mgr._register_socket(mock_ws_b1, ORG_B_ID, "user-b-1", "userB@test.com")

    print("  [PASS] Registered 2 sockets to Org North and 1 socket to Org South")
    assert len(mgr.org_connections[ORG_A_ID]) == 2
    assert len(mgr.org_connections[ORG_B_ID]) == 1

    # 1. Dispatch an alert targeted to Org A
    alert_a = {
        "type": "NEW_ALERT",
        "data": {
            "alert_id": "ALT-EXCLUSIVE-A",
            "organization_id": ORG_A_ID,
            "description": "Restricted border breach in Sector North"
        }
    }
    await mgr.send_to_org(ORG_A_ID, alert_a)

    # 2. Verify Org A sockets received the alert
    mock_ws_a1.send_json.assert_called_once_with(alert_a)
    mock_ws_a2.send_json.assert_called_once_with(alert_a)
    print("  [PASS] Both Org North clients received the alert")

    # 3. Verify Org B socket NEVER received the alert
    mock_ws_b1.send_json.assert_not_called()
    print("  [PASS] Org South client was NEVER sent the alert (0 calls, strict isolation)")

    # 4. Dispatch an alert targeted to Org B
    alert_b = {
        "type": "NEW_ALERT",
        "data": {
            "alert_id": "ALT-EXCLUSIVE-B",
            "organization_id": ORG_B_ID,
            "description": "Restricted border breach in Sector South"
        }
    }
    mock_ws_a1.reset_mock()
    mock_ws_a2.reset_mock()
    mock_ws_b1.reset_mock()

    await mgr.send_to_org(ORG_B_ID, alert_b)

    mock_ws_b1.send_json.assert_called_once_with(alert_b)
    mock_ws_a1.send_json.assert_not_called()
    mock_ws_a2.send_json.assert_not_called()
    print("  [PASS] Org South client received Org B alert; Org North clients received NOTHING")

    # 5. Test disconnection cleanup
    mgr.disconnect(mock_ws_b1)
    assert ORG_B_ID not in mgr.org_connections
    print("  [PASS] Org connection list cleanly pruned upon socket disconnection")

    print("\n" + "=" * 70)
    print("ALL WEBSOCKET MULTI-TENANT ISOLATION TESTS PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_websocket_manager_isolation())
