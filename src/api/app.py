"""Production FastAPI Service for AppleSupport AI Agent."""

import logging
import time
import uuid
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.pipeline import CustomerSupportPipeline
from src.schemas.models import SupportRequest, SupportResponse

logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
)
logger = logging.getLogger("support_api")

app = FastAPI(
    title="AppleSupport AI Customer Service Agent API",
    version="1.0.0",
    description="Evidence-grounded, safety-critical customer support agent for AppleSupport.",
)

# Pipeline singleton
pipeline: CustomerSupportPipeline = None


@app.on_event("startup")
def load_pipeline():
    global pipeline
    try:
        pipeline = CustomerSupportPipeline()
        logger.info("Customer support pipeline loaded successfully.")
    except Exception as e:
        logger.error("Failed to initialize pipeline: %s", e)
        raise RuntimeError(f"Pipeline startup failed: {e}")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "details": exc.errors(),
        },
    )


@app.get("/health", tags=["System"])
def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy" if pipeline is not None else "degraded",
        "service": "apple_support_ai_agent",
        "version": "1.0.0",
    }


@app.post(
    "/v1/support/respond",
    response_model=SupportResponse,
    status_code=status.HTTP_200_OK,
    tags=["Support"],
)
async def respond_to_customer(request: SupportRequest) -> SupportResponse:
    """Processes customer inquiry and returns an evidence-grounded response with escalation decision."""
    global pipeline
    if pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model and vector pipeline currently unavailable.",
        )

    request_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        response = pipeline.process(request)
        latency_ms = round((time.time() - start_time) * 1000, 2)

        # Structured audit log
        logger.info(
            f"REQUEST_AUDIT | request_id={request_id} | latency_ms={latency_ms} | "
            f"intent={response.intent} | decision={response.decision} | "
            f"confidence={response.confidence} | evidence_count={len(response.evidence)}"
        )
        return response

    except ValueError as ve:
        logger.warning(f"Bad request: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Internal server error processing request_id={request_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating the support response.",
        )
