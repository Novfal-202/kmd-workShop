"""FR-014 and spec Edge Cases: ExpenseClaimInput validation boundary."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.models.expense_claim import ExpenseClaimInput


def test_zero_amount_is_rejected():
    with pytest.raises(ValidationError):
        ExpenseClaimInput(category="Meals", amount=Decimal("0.00"), expense_date="2026-08-19")


def test_negative_amount_is_rejected():
    with pytest.raises(ValidationError):
        ExpenseClaimInput(category="Meals", amount=Decimal("-25.00"), expense_date="2026-08-19")


def test_malformed_date_is_rejected():
    with pytest.raises(ValidationError):
        ExpenseClaimInput(category="Meals", amount=Decimal("30.00"), expense_date="2026-13-45")


def test_missing_category_is_rejected():
    with pytest.raises(ValidationError):
        ExpenseClaimInput(category=None, amount=Decimal("30.00"), expense_date="2026-08-19")


def test_empty_category_is_rejected():
    with pytest.raises(ValidationError):
        ExpenseClaimInput(category="", amount=Decimal("30.00"), expense_date="2026-08-19")


def test_sql_injection_style_description_is_stored_as_opaque_text():
    payload = "'; DROP TABLE claims; --"
    claim = ExpenseClaimInput(
        category="Equipment",
        amount=Decimal("45.00"),
        expense_date="2026-08-19",
        description=payload,
    )
    assert claim.description == payload
