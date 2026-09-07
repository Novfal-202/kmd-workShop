"""PolicyRuleSet configuration source (research.md §5; specs/005-category-cap-coverage §1).

Centralizes the configurable policy parameters in one place rather than hardcoding them
inside evaluate_claim — finance/policy administrators are expected to change these without
a code deploy. This in-memory default stands in for the eventual admin-configurable store;
swapping its backing (e.g., a database table) only requires changing this module.
"""

from decimal import Decimal

from src.models.policy_rule_set import PolicyRuleSet

DEFAULT_POLICY_RULE_SET = PolicyRuleSet(
    category_caps={
        "Meals": Decimal("50.00"),
        "Travel": Decimal("1000.00"),
        "Equipment": Decimal("500.00"),
        # Added by 005-category-cap-coverage: these three are offered as options on the
        # portal's own claim form but previously had no configured cap at all, so they could
        # never be auto-approved — every claim in them always hit uncapped_category regardless
        # of amount. Values are reasonable starting defaults, not audited finance policy (same
        # framing as the three caps above) — see research.md §1 for rationale.
        "Lodging": Decimal("300.00"),
        "Supplies": Decimal("100.00"),
        "Entertainment": Decimal("150.00"),
    },
    receipt_required_threshold=Decimal("100.00"),
    auto_approval_threshold=Decimal("200.00"),
    weekend_exempt_categories=["Travel", "Lodging"],
)


class PolicyRuleSetRepository:
    def __init__(self, rule_set: PolicyRuleSet = DEFAULT_POLICY_RULE_SET):
        self._rule_set = rule_set

    def get_active_rule_set(self) -> PolicyRuleSet:
        return self._rule_set
