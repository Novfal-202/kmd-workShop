"""Integration test for the full reviewer flow (US2)."""

import src.api.review_routes as review_routes


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


def test_review_queue_listing_shows_violation_reasons(client):
    claim = _submit_flagged_claim(client)
    queue = client.get("/review-queue").json()
    entry = next(c for c in queue if c["id"] == claim["id"])
    assert any(v["code"] == "over_category_cap" for v in entry["violations"])


def test_approve_flagged_claim(client):
    claim = _submit_flagged_claim(client)
    r = client.post(f"/claims/{claim['id']}/decisions", json={"decision": "approved"})
    assert r.status_code == 200
    assert r.json()["status"] == "approved"


def test_reject_without_reason_is_422(client):
    claim = _submit_flagged_claim(client)
    r = client.post(f"/claims/{claim['id']}/decisions", json={"decision": "rejected"})
    assert r.status_code == 422


def test_self_review_is_blocked_with_403(client, monkeypatch):
    claim = _submit_flagged_claim(client)
    # Simulate the same identity being both submitter and reviewer.
    monkeypatch.setattr(review_routes, "CURRENT_REVIEWER_ID", "current-employee")
    r = client.post(f"/claims/{claim['id']}/decisions", json={"decision": "approved"})
    assert r.status_code == 403
    # Claim remains available for a different reviewer.
    queue_ids = [c["id"] for c in client.get("/review-queue").json()]
    assert claim["id"] in queue_ids


def test_concurrent_decisions_first_wins_second_gets_409(client):
    claim = _submit_flagged_claim(client)
    first = client.post(f"/claims/{claim['id']}/decisions", json={"decision": "approved"})
    second = client.post(
        f"/claims/{claim['id']}/decisions", json={"decision": "rejected", "reason": "duplicate"}
    )
    assert first.status_code == 200
    assert second.status_code == 409
    assert client.get(f"/claims/{claim['id']}").json()["status"] == "approved"
