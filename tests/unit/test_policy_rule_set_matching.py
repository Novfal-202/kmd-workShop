"""FR-001, FR-002: PolicyRuleSet's case-insensitive category-matching methods."""

from decimal import Decimal

from src.models.policy_rule_set import PolicyRuleSet

RULE_SET = PolicyRuleSet(
    category_caps={
        "Meals": Decimal("50.00"),
        "Travel": Decimal("1000.00"),
        "Equipment": Decimal("500.00"),
    },
    receipt_required_threshold=Decimal("100.00"),
    auto_approval_threshold=Decimal("200.00"),
    weekend_exempt_categories=["Travel", "Lodging"],
)


def test_get_category_cap_matches_exact_case():
    assert RULE_SET.get_category_cap("Meals") == Decimal("50.00")


def test_get_category_cap_matches_lowercase():
    assert RULE_SET.get_category_cap("meals") == Decimal("50.00")


def test_get_category_cap_matches_uppercase():
    assert RULE_SET.get_category_cap("MEALS") == Decimal("50.00")


def test_get_category_cap_matches_mixed_case():
    assert RULE_SET.get_category_cap("MeAlS") == Decimal("50.00")


def test_get_category_cap_returns_none_for_unconfigured_category_under_any_casing():
    assert RULE_SET.get_category_cap("Supplies") is None
    assert RULE_SET.get_category_cap("supplies") is None
    assert RULE_SET.get_category_cap("SUPPLIES") is None


def test_is_weekend_exempt_matches_exact_case():
    assert RULE_SET.is_weekend_exempt("Travel") is True


def test_is_weekend_exempt_matches_lowercase():
    assert RULE_SET.is_weekend_exempt("travel") is True


def test_is_weekend_exempt_matches_uppercase():
    assert RULE_SET.is_weekend_exempt("LODGING") is True


def test_is_weekend_exempt_returns_false_for_non_exempt_category_under_any_casing():
    assert RULE_SET.is_weekend_exempt("Meals") is False
    assert RULE_SET.is_weekend_exempt("meals") is False
