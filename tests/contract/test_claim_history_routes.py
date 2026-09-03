"""Contract tests for GET /claims (list) and POST /claims/{claimId}/withdraw."""


def test_list_claims_returns_employee_history(client):
    a = client.post(
        "/claims", json={"category": "Meals", "amount": 35.00, "expense_date": "2026-08-19"}
    ).json()
    b = client.post(
        "/claims",
        json={
            "category": "Meals",
            "amount": 65.00,
            "expense_date": "2026-08-19",
            "receipt_attached": True,
        },
    ).json()
    r = client.get("/claims")
    assert r.status_code == 200
    ids = {c["id"] for c in r.json()}
    assert {a["id"], b["id"]} <= ids


def test_withdraw_pending_claim_returns_200(client):
    flagged = client.post(
        "/claims",
        json={
            "category": "Meals",
            "amount": 65.00,
            "expense_date": "2026-08-19",
            "receipt_attached": True,
        },
    ).json()
    r = client.post(f"/claims/{flagged['id']}/withdraw")
    assert r.status_code == 200
    assert r.json()["status"] == "withdrawn"


def test_withdraw_already_decided_claim_returns_409(client):
    flagged = client.post(
        "/claims",
        json={
            "category": "Meals",
            "amount": 65.00,
            "expense_date": "2026-08-19",
            "receipt_attached": True,
        },
    ).json()
    client.post(f"/claims/{flagged['id']}/decisions", json={"decision": "approved"})
    r = client.post(f"/claims/{flagged['id']}/withdraw")
    assert r.status_code == 409
