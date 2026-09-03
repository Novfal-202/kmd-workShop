"""AuditRepository — append-only storage for AuditLogEntry (FR-017).

Insert-only: no update or delete methods exist, preserving a full compliance history
even across edits that re-trigger evaluation (FR-016).
"""

import json
import uuid

from sqlalchemy import Column, DateTime, MetaData, String, Table, Text, select
from sqlalchemy.engine import Engine

from src.models.audit_log_entry import AuditLogEntry, EvaluationOutcome
from src.models.expense_claim import ViolationReason
from src.repositories.db import engine as default_engine

metadata = MetaData()

audit_log_table = Table(
    "audit_log",
    metadata,
    Column("id", String, primary_key=True),
    Column("claim_id", String, nullable=False),
    Column("evaluated_at", DateTime, nullable=False),
    Column("rules_evaluated_json", Text, nullable=False, default="[]"),
    Column("outcome", String, nullable=False),
    Column("violations_json", Text, nullable=False, default="[]"),
)


def _row_to_entry(row) -> AuditLogEntry:
    return AuditLogEntry(
        id=uuid.UUID(row.id),
        claim_id=uuid.UUID(row.claim_id),
        evaluated_at=row.evaluated_at,
        rules_evaluated=json.loads(row.rules_evaluated_json),
        outcome=EvaluationOutcome(row.outcome),
        violations=[ViolationReason.model_validate(v) for v in json.loads(row.violations_json)],
    )


class AuditRepository:
    def __init__(self, db_engine: Engine = default_engine):
        self._engine = db_engine
        metadata.create_all(self._engine)

    def append(self, entry: AuditLogEntry) -> AuditLogEntry:
        with self._engine.begin() as conn:
            conn.execute(
                audit_log_table.insert().values(
                    id=str(entry.id),
                    claim_id=str(entry.claim_id),
                    evaluated_at=entry.evaluated_at,
                    rules_evaluated_json=json.dumps(entry.rules_evaluated),
                    outcome=entry.outcome.value,
                    violations_json=json.dumps(
                        [v.model_dump(mode="json") for v in entry.violations]
                    ),
                )
            )
        return entry

    def list_for_claim(self, claim_id: uuid.UUID) -> list[AuditLogEntry]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                select(audit_log_table)
                .where(audit_log_table.c.claim_id == str(claim_id))
                .order_by(audit_log_table.c.evaluated_at)
            ).fetchall()
        return [_row_to_entry(r) for r in rows]
