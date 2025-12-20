"""Request schemas for BookNLP API."""

from typing import Literal

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """Request schema for text analysis endpoint."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=500_000,
        description="Text to analyze (max 500K characters)",
    )
    book_id: str = Field(
        default="document",
        description="Identifier for the document",
    )
    model: Literal["small", "big", "custom"] = Field(
        default="small",
        description="Model size to use for analysis",
    )
    pipeline: list[str] = Field(
        default=["entity", "quote", "supersense", "event", "coref"],
        description="Pipeline components to run",
    )
    custom_model_path: str | None = Field(
        default=None,
        description="Path for custom model (only used when model='custom')",
    )
