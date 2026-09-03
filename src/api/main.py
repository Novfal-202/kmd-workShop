"""FastAPI app skeleton — routing/serialization only (constitution Article III.1).

Exception handlers here are the ONLY place domain errors are translated to HTTP status
codes; the routes and the policy engine itself never construct an HTTP response.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from src.logging_config import configure_logging
from src.services.policy_engine.errors import (
    AlreadyDecidedError,
    DomainValidationError,
    NotFoundError,
    SelfReviewError,
)

configure_logging()

app = FastAPI(title="Corporate Expense Reimbursement & Policy Engine")


def _register_routers() -> None:
    from src.api.claims_routes import router as claims_router
    from src.api.review_routes import router as review_router

    app.include_router(claims_router)
    app.include_router(review_router)


_register_routers()


def _error_body(code: str, message: str) -> dict:
    return {"error_code": code, "message": message}


@app.exception_handler(PydanticValidationError)
async def handle_pydantic_validation_error(request: Request, exc: PydanticValidationError):
    return JSONResponse(status_code=422, content=_error_body("validation_error", str(exc)))


@app.exception_handler(DomainValidationError)
async def handle_domain_validation_error(request: Request, exc: DomainValidationError):
    return JSONResponse(status_code=422, content=_error_body("validation_error", str(exc)))


@app.exception_handler(SelfReviewError)
async def handle_self_review_error(request: Request, exc: SelfReviewError):
    return JSONResponse(status_code=403, content=_error_body("self_review_blocked", str(exc)))


@app.exception_handler(AlreadyDecidedError)
async def handle_already_decided_error(request: Request, exc: AlreadyDecidedError):
    return JSONResponse(status_code=409, content=_error_body("already_decided", str(exc)))


@app.exception_handler(NotFoundError)
async def handle_not_found_error(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content=_error_body("not_found", str(exc)))
