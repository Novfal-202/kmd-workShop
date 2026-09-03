"""Integration test for employee claim history (US3): reflects reviewer decisions and
withdrawals without further employee action (Acceptance Scenarios 2 and 3).
"""


def test_history_reflects_reviewer_decision_without_employee_action(client):
    claim = client.post(
        "/claims",
        json={
            "category": "Meals",
            "amount": 65.00,
            "expense_date": "2026-08-19",
            "receipt_attached": True,
        },
    ).json()
    client.post(f"/claims/{claim['id']}/decisions", json={"decision": "approved"})

    history = client.get("/claims").json()
    entry = next(c for c in history if c["id"] == claim["id"])
    assert entry["status"] == "approved"


def test_history_reflects_withdrawal(client):
    claim = client.post(
        "/claims",
        json={
            "category": "Meals",
            "amount": 65.00,
            "expense_date": "2026-08-19",
            "receipt_attached": True,
        },
    ).json()
    client.post(f"/claims/{claim['id']}/withdraw")

    history = client.get("/claims").json()
    entry = next(c for c in history if c["id"] == claim["id"])
    assert entry["status"] == "withdrawn"

    queue_ids = [c["id"] for c in client.get("/review-queue").json()]
    assert claim["id"] not in queue_ids
