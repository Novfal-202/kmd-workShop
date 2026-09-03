import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Fresh isolated SQLite DB per test so contract/integration tests don't leak state."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("EXPENSE_ENGINE_DB_URL", f"sqlite:///{db_path}")

    # Reset module-level singletons so they pick up the fresh DB URL.
    import src.repositories.db as db_module

    db_module.engine = db_module.build_engine()
    db_module.SessionLocal = db_module.sessionmaker(bind=db_module.engine)

    import src.api.claims_routes as claims_routes
    import src.api.review_routes as review_routes
    from src.repositories.audit_repository import AuditRepository
    from src.repositories.claim_repository import ClaimRepository

    claims_routes.claim_repository = ClaimRepository(db_module.engine)
    claims_routes.audit_repository = AuditRepository(db_module.engine)
    review_routes.claim_repository = claims_routes.claim_repository

    from src.api.main import app

    return TestClient(app)
