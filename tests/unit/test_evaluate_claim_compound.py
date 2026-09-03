"""spec Edge Cases: multiple simultaneous violations are all recorded together."""

from decimal import Decimal

from src.models.expense_claim import ClaimStatus, ViolationCode
from src.services.policy_engine.evaluate_claim import evaluate_claim
from tests.unit.conftest import SUNDAY, make_claim_input, now_utc


def test_compound_violations_all_reported_together(rule_set):
    claim = make_claim_input(
        category="Meals", amount=Decimal("120.00"), expense_date=SUNDAY, receipt_attached=False
    )
    result = evaluate_claim(claim, rule_set, prior_claims=[], submission_date=now_utc())
    codes = {v.code for v in result.violations}
    assert codes == {
        ViolationCode.OVER_CATEGORY_CAP,
        ViolationCode.MISSING_REQUIRED_RECEIPT,
        ViolationCode.WEEKEND_POLICY_VIOLATION,
    }
    assert result.status == ClaimStatus.PENDING_REVIEW
