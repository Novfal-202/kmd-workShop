"""Replays every claim in tests/fixtures/synthetic_expenses.json end-to-end and asserts the
engine's actual status/violations match each claim's expected_status/expected_violations.

For the edge_malformed partition, "rejected" means the API returns HTTP 422 at submission
(the ExpenseClaimInput validation boundary) rather than reaching evaluate_claim, so those
cases assert on the HTTP status rather than a ViolationReason list — see
contracts/policy-engine-contract.md's "Input validation boundary" section.
"""

import json
from pathlib import Path

import pytest

FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "synthetic_expenses.json"


def _load_claims():
    data = json.loads(FIXTURE_PATH.read_text())
    return data["claims"]


@pytest.mark.parametrize("claim", _load_claims(), ids=lambda c: c["id"])
def test_synthetic_claim_matches_expected_outcome(client, claim):
    payload = {
        "category": claim["category"],
        "amount": claim["amount"],
        "description": claim.get("description", ""),
        "expense_date": claim["expense_date"],
        "receipt_attached": claim.get("receipt_attached", False),
    }

    # category=None (EM-05) and malformed dates are still sent as-is to exercise the
    # validation boundary at the HTTP layer, matching how a real client would submit them.
    response = client.post("/claims", json=payload)

    if claim["expected_status"] == "rejected":
        assert response.status_code == 422, (
            f"{claim['id']}: expected HTTP 422 (rejected at validation), "
            f"got {response.status_code}: {response.text}"
        )
        return

    assert response.status_code == 201, f"{claim['id']}: {response.text}"
    body = response.json()
    assert body["status"] == claim["expected_status"], f"{claim['id']}: {body}"

    actual_codes = sorted(v["code"] for v in body["violations"])
    expected_codes = sorted(claim["expected_violations"])
    assert actual_codes == expected_codes, f"{claim['id']}: {body['violations']}"
