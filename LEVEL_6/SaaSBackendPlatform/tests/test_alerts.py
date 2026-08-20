def test_create_and_get_alerts(client, auth_headers):
    # Create org
    org_res = client.post(
        "/api/v1/organizations",
        json={"name": "Alert Org", "slug": "alert-org"},
        headers=auth_headers
    )
    org_id = org_res.json()["data"]["id"]

    headers = {**auth_headers, "X-Organization-ID": str(org_id)}

    # Create alert
    alert_res = client.post(
        "/api/v1/alerts",
        json={
            "title": "Test Quota Warning",
            "message": "API Quota near limit",
            "severity": "WARNING"
        },
        headers=headers
    )
    assert alert_res.status_code == 201
    alert_data = alert_res.json()
    assert alert_data["success"] is True
    alert_id = alert_data["data"]["id"]

    # Get alerts
    list_res = client.get("/api/v1/alerts", headers=headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["success"] is True
    assert len(list_data["data"]) >= 1

    # Delete alert
    del_res = client.delete(f"/api/v1/alerts/{alert_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True
