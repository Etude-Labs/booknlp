"""Analyze endpoint for text processing."""

import time
import tempfile
import os
from typing import Any

from fastapi import APIRouter, HTTPException, status, Depends, Request

from booknlp.api.schemas.requests import AnalyzeRequest
from booknlp.api.schemas.responses import AnalyzeResponse
from booknlp.api.services.nlp_service import get_nlp_service
from booknlp.api.dependencies import verify_api_key
from booknlp.api.rate_limit import rate_limit

router = APIRouter(tags=["Analysis"])


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze text",
    description="Run BookNLP analysis on provided text.",
    responses={
        200: {"description": "Analysis completed successfully"},
        400: {"description": "Invalid input"},
        503: {"description": "Service not ready"},
    },
)
@rate_limit("10/minute")  # Same as job submission
async def analyze(
    request: AnalyzeRequest,
    http_request: Request,
    api_key: str = Depends(verify_api_key)
) -> AnalyzeResponse:
    """Analyze text using BookNLP.
    
    Args:
        request: Analysis request with text and options.
        
    Returns:
        Analysis results including tokens, entities, quotes, etc.
        
    Raises:
        HTTPException: If service not ready or processing fails.
    """
    nlp_service = get_nlp_service()
    
    if not nlp_service.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready. Models are still loading.",
        )
    
    start_time = time.time()
    
    try:
        result = _process_text(request, nlp_service)
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return AnalyzeResponse(
            book_id=request.book_id,
            model=request.model,
            processing_time_ms=processing_time_ms,
            token_count=len(result.get("tokens", [])),
            tokens=result.get("tokens", []),
            entities=result.get("entities", []),
            quotes=result.get("quotes", []),
            characters=result.get("characters", []),
            events=result.get("events", []),
            supersenses=result.get("supersenses", []),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}",
        )


def _process_text(request: AnalyzeRequest, nlp_service: Any) -> dict[str, Any]:
    """Process text using BookNLP.
    
    Args:
        request: Analysis request.
        nlp_service: NLP service instance.
        
    Returns:
        Dictionary with analysis results.
    """
    model = nlp_service.get_model(request.model)
    
    # BookNLP requires file-based I/O, so we use temp files
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = os.path.join(tmpdir, "input.txt")
        with open(input_file, "w", encoding="utf-8") as f:
            f.write(request.text)
        
        # Run BookNLP processing
        model.process(input_file, tmpdir, request.book_id)
        
        # Read results from output files
        result = _read_booknlp_output(tmpdir, request.book_id, request.pipeline)
    
    return result


def _read_booknlp_output(
    output_dir: str,
    book_id: str,
    pipeline: list[str],
) -> dict[str, Any]:
    """Read BookNLP output files and convert to response format.
    
    Args:
        output_dir: Directory containing output files.
        book_id: Book identifier used in filenames.
        pipeline: List of pipeline components that were run.
        
    Returns:
        Dictionary with parsed results.
    """
    result: dict[str, Any] = {
        "tokens": [],
        "entities": [],
        "quotes": [],
        "characters": [],
        "events": [],
        "supersenses": [],
    }
    
    # Read tokens file
    tokens_file = os.path.join(output_dir, f"{book_id}.tokens")
    if os.path.exists(tokens_file):
        result["tokens"] = _parse_tokens_file(tokens_file)
    
    # Read entities file
    entities_file = os.path.join(output_dir, f"{book_id}.entities")
    if os.path.exists(entities_file) and "entity" in pipeline:
        result["entities"] = _parse_entities_file(entities_file)
    
    # Read quotes file
    quotes_file = os.path.join(output_dir, f"{book_id}.quotes")
    if os.path.exists(quotes_file) and "quote" in pipeline:
        result["quotes"] = _parse_quotes_file(quotes_file)
    
    # Read supersense file
    supersense_file = os.path.join(output_dir, f"{book_id}.supersense")
    if os.path.exists(supersense_file) and "supersense" in pipeline:
        result["supersenses"] = _parse_supersense_file(supersense_file)
    
    # Read book file for characters (requires coref pipeline)
    book_file = os.path.join(output_dir, f"{book_id}.book")
    if os.path.exists(book_file) and "coref" in pipeline:
        result["characters"] = _parse_book_file(book_file)
    
    return result


def _parse_book_file(filepath: str) -> list[dict[str, Any]]:
    """Parse the .book JSON file containing character information."""
    import json
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("characters", [])


def _parse_tsv_file(filepath: str) -> list[dict[str, Any]]:
    """Parse a tab-separated BookNLP output file.
    
    Args:
        filepath: Path to the TSV file.
        
    Returns:
        List of dictionaries, one per row.
    """
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        header = f.readline().strip().split("\t")
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) >= len(header):
                row = dict(zip(header, parts))
                rows.append(row)
    return rows


# Aliases for backward compatibility and clarity
_parse_tokens_file = _parse_tsv_file
_parse_entities_file = _parse_tsv_file
_parse_quotes_file = _parse_tsv_file
_parse_supersense_file = _parse_tsv_file
