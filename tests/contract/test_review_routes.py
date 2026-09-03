"""Contract tests for GET /review-queue and POST /claims/{claimId}/decisions."""


def _submit_flagged_claim(client):
    return client.post(
        "/claims",
        json={
            "category": "Meals",
            "amount": 65.00,
            "expense_date": "2026-08-19",
            "receipt_attached": True,
        },
    ).json()


def test_review_queue_lists_flagged_claims(client):
    claim = _submit_flagged_claim(client)
    r = client.get("/review-queue")
    assert r.status_code == 200
    ids = [c["id"] for c in r.json()]
    assert claim["id"] in ids


def test_approve_decision_returns_200(client):
    claim = _submit_flagged_claim(client)
    r = client.post(f"/claims/{claim['id']}/decisions", json={"decision": "approved"})
    assert r.status_code == 200
    assert r.json()["status"] == "approved"


def test_reject_without_reason_returns_422(client):
    claim = _submit_flagged_claim(client)
    r = client.post(f"/claims/{claim['id']}/decisions", json={"decision": "rejected"})
    assert r.status_code == 422


def test_second_decision_on_already_decided_claim_returns_409(client):
    claim = _submit_flagged_claim(client)
    first = client.post(f"/claims/{claim['id']}/decisions", json={"decision": "approved"})
    assert first.status_code == 200
    second = client.post(
        f"/claims/{claim['id']}/decisions", json={"decision": "rejected", "reason": "too late"}
    )
    assert second.status_code == 409
