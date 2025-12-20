"""Response schemas for BookNLP API."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response schema for health endpoint."""

    status: str = Field(description="Health status")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Current server timestamp",
    )


class ReadyResponse(BaseModel):
    """Response schema for readiness endpoint."""

    status: str = Field(description="Readiness status: 'ready' or 'loading'")
    model_loaded: bool = Field(description="Whether models are loaded")
    default_model: str = Field(description="Default model name")
    available_models: list[str] = Field(description="List of available models")


class AnalyzeResponse(BaseModel):
    """Response schema for analysis endpoint."""

    book_id: str = Field(description="Document identifier")
    model: str = Field(description="Model used for analysis")
    processing_time_ms: int = Field(description="Processing time in milliseconds")
    token_count: int = Field(description="Number of tokens processed")
    tokens: list[dict[str, Any]] = Field(default_factory=list, description="Token data")
    entities: list[dict[str, Any]] = Field(default_factory=list, description="Named entities")
    quotes: list[dict[str, Any]] = Field(default_factory=list, description="Detected quotes")
    characters: list[dict[str, Any]] = Field(default_factory=list, description="Character data")
    events: list[dict[str, Any]] = Field(default_factory=list, description="Event data")
    supersenses: list[dict[str, Any]] = Field(default_factory=list, description="Supersense tags")


class ErrorResponse(BaseModel):
    """Response schema for error responses."""

    detail: str = Field(description="Error message")
    error_code: str | None = Field(default=None, description="Error code")
    request_id: str | None = Field(default=None, description="Request ID for tracing")
