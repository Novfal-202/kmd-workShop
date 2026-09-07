"""ClaimRepository — storage for ExpenseClaim, including the atomic first-write-wins
transition primitive (FR-019) that both review decisions (US2) and withdrawal (US3) share.

This module is the only place that knows about the storage technology (SQLAlchemy/SQLite);
src/services/policy_engine/ never imports it directly (constitution Article III.1).
"""

import json
import uuid
from collections.abc import Callable, Sequence
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    MetaData,
    Numeric,
    String,
    Table,
    Text,
    select,
    update,
)
from sqlalchemy.engine import Engine

from src.models.expense_claim import ClaimStatus, ExpenseClaim, ViolationReason
from src.models.review_decision import ReviewDecision
from src.repositories.db import engine as default_engine

metadata = MetaData()

claims_table = Table(
    "claims",
    metadata,
    Column("id", String, primary_key=True),
    Column("submitter_id", String, nullable=False),
    Column("category", String, nullable=False),
    Column("amount", Numeric, nullable=False),
    Column("description", Text, nullable=False, default=""),
    Column("expense_date", Date, nullable=False),
    Column("submission_date", DateTime, nullable=False),
    Column("receipt_attached", Boolean, nullable=False, default=False),
    Column("employee_name", String, nullable=False, default=""),
    Column("status", String, nullable=False),
    Column("violations_json", Text, nullable=False, default="[]"),
    Column("review_decisions_json", Text, nullable=False, default="[]"),
)


def _violations_to_json(violations: Sequence[ViolationReason]) -> str:
    return json.dumps([v.model_dump(mode="json") for v in violations])


def _violations_from_json(raw: str) -> list[ViolationReason]:
    return [ViolationReason.model_validate(v) for v in json.loads(raw)]


def _decisions_to_json(decisions: Sequence[ReviewDecision]) -> str:
    return json.dumps([d.model_dump(mode="json") for d in decisions])


def _decisions_from_json(raw: str) -> list[ReviewDecision]:
    return [ReviewDecision.model_validate(d) for d in json.loads(raw)]


def _row_to_claim(row) -> ExpenseClaim:
    return ExpenseClaim(
        id=uuid.UUID(row.id),
        submitter_id=row.submitter_id,
        category=row.category,
        amount=Decimal(str(row.amount)),
        description=row.description or "",
        expense_date=(
            row.expense_date
            if isinstance(row.expense_date, date)
            else date.fromisoformat(row.expense_date)
        ),
        submission_date=(
            row.submission_date
            if isinstance(row.submission_date, datetime)
            else datetime.fromisoformat(row.submission_date)
        ),
        receipt_attached=bool(row.receipt_attached),
        employee_name=row.employee_name or "",
        status=ClaimStatus(row.status),
        violations=_violations_from_json(row.violations_json),
        review_decisions=_decisions_from_json(row.review_decisions_json),
    )


def _ensure_employee_name_column(engine: Engine) -> None:
    """Idempotent migration for a physical SQLite file created before this column existed
    (`metadata.create_all` only creates missing tables, it never alters an existing one)."""
    with engine.begin() as conn:
        existing_columns = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(claims)")}
        if existing_columns and "employee_name" not in existing_columns:
            conn.exec_driver_sql(
                "ALTER TABLE claims ADD COLUMN employee_name TEXT NOT NULL DEFAULT ''"
            )


class ClaimRepository:
    def __init__(self, db_engine: Engine = default_engine):
        self._engine = db_engine
        metadata.create_all(self._engine)
        _ensure_employee_name_column(self._engine)

    def create(self, claim: ExpenseClaim) -> ExpenseClaim:
        with self._engine.begin() as conn:
            conn.execute(
                claims_table.insert().values(
                    id=str(claim.id),
                    submitter_id=claim.submitter_id,
                    category=claim.category,
                    amount=claim.amount,
                    description=claim.description,
                    expense_date=claim.expense_date,
                    submission_date=claim.submission_date,
                    receipt_attached=claim.receipt_attached,
                    employee_name=claim.employee_name,
                    status=claim.status.value,
                    violations_json=_violations_to_json(claim.violations),
                    review_decisions_json=_decisions_to_json(claim.review_decisions),
                )
            )
        return claim

    def get(self, claim_id: uuid.UUID) -> ExpenseClaim | None:
        with self._engine.connect() as conn:
            row = conn.execute(
                select(claims_table).where(claims_table.c.id == str(claim_id))
            ).fetchone()
        return _row_to_claim(row) if row else None

    def list_by_employee(self, submitter_id: str) -> list[ExpenseClaim]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                select(claims_table).where(claims_table.c.submitter_id == submitter_id)
            ).fetchall()
        return [_row_to_claim(r) for r in rows]

    def list_review_queue(self) -> list[ExpenseClaim]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                select(claims_table).where(
                    claims_table.c.status.in_(
                        [ClaimStatus.PENDING_REVIEW.value, ClaimStatus.NEEDS_INFORMATION.value]
                    )
                )
            ).fetchall()
        return [_row_to_claim(r) for r in rows]

    def replace(self, claim: ExpenseClaim) -> ExpenseClaim:
        """Unconditional overwrite, used for edits (FR-016) which are not a race-guarded
        transition."""
        with self._engine.begin() as conn:
            conn.execute(
                update(claims_table)
                .where(claims_table.c.id == str(claim.id))
                .values(
                    category=claim.category,
                    amount=claim.amount,
                    description=claim.description,
                    expense_date=claim.expense_date,
                    submission_date=claim.submission_date,
                    receipt_attached=claim.receipt_attached,
                    employee_name=claim.employee_name,
                    status=claim.status.value,
                    violations_json=_violations_to_json(claim.violations),
                    review_decisions_json=_decisions_to_json(claim.review_decisions),
                )
            )
        return claim

    def try_transition(
        self,
        claim_id: uuid.UUID,
        allowed_from_statuses: Sequence[ClaimStatus],
        mutation: Callable[[ExpenseClaim], ExpenseClaim],
    ) -> ExpenseClaim | None:
        """Atomic first-write-wins transition (FR-019).

        Reads the current claim, applies `mutation` to compute the new state, then performs a
        single conditional UPDATE guarded by `WHERE status IN (allowed_from_statuses)`. If a
        concurrent call already moved the claim out of an allowed status, the UPDATE affects
        zero rows and this returns None — the caller reports "already decided" / "no longer
        available" without ever having applied the mutation's effects.
        """
        current = self.get(claim_id)
        if current is None or current.status not in allowed_from_statuses:
            return None

        updated = mutation(current)

        with self._engine.begin() as conn:
            result = conn.execute(
                update(claims_table)
                .where(
                    claims_table.c.id == str(claim_id),
                    claims_table.c.status.in_([s.value for s in allowed_from_statuses]),
                )
                .values(
                    status=updated.status.value,
                    violations_json=_violations_to_json(updated.violations),
                    review_decisions_json=_decisions_to_json(updated.review_decisions),
                )
            )
            if result.rowcount == 0:
                return None
        return updated
