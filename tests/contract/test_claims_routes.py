"""Contract tests for POST/GET/PUT /claims against contracts/api.yaml."""


def test_post_claims_returns_201_and_auto_approved(client):
    r = client.post(
        "/claims",
        json={
            "category": "Meals",
            "amount": 35.00,
            "expense_date": "2026-08-19",
            "receipt_attached": False,
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "auto_approved"
    assert body["violations"] == []


def test_post_claims_with_invalid_amount_returns_422(client):
    r = client.post(
        "/claims",
        json={"category": "Meals", "amount": -25.00, "expense_date": "2026-08-19"},
    )
    assert r.status_code == 422


def test_get_claim_by_id(client):
    created = client.post(
        "/claims",
        json={"category": "Meals", "amount": 35.00, "expense_date": "2026-08-19"},
    ).json()
    r = client.get(f"/claims/{created['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


def test_get_nonexistent_claim_returns_404(client):
    r = client.get("/claims/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


def test_put_claims_re_evaluates_on_edit(client):
    created = client.post(
        "/claims",
        json={"category": "Meals", "amount": 35.00, "expense_date": "2026-08-19"},
    ).json()
    assert created["status"] == "auto_approved"

    edited = client.put(
        f"/claims/{created['id']}",
        json={
            "category": "Meals",
            "amount": 65.00,
            "expense_date": "2026-08-19",
            "receipt_attached": True,
        },
    ).json()
    assert edited["status"] == "pending_review"
    assert any(v["code"] == "over_category_cap" for v in edited["violations"])
