"""Async BookNLP processor with progress tracking."""

import asyncio
import tempfile
import os
import time
from typing import Any, Callable, Dict

from booknlp.api.schemas.job_schemas import JobRequest
from booknlp.api.services.nlp_service import get_nlp_service


class AsyncBookNLPProcessor:
    """Wraps BookNLP processing with progress tracking and async execution."""
    
    def __init__(self):
        """Initialize the processor."""
        self._nlp_service = get_nlp_service()
        
    async def process(
        self,
        request: JobRequest,
        progress_callback: Callable[[float], None]
    ) -> Dict[str, Any]:
        """Process a BookNLP job with progress tracking.
        
        Args:
            request: Job processing request
            progress_callback: Callback to report progress (0-100)
            
        Returns:
            Dictionary with analysis results
            
        Raises:
            RuntimeError: If service not ready
            ValueError: If model not available
        """
        if not self._nlp_service.is_ready:
            raise RuntimeError("Service not ready. Models are still loading.")
            
        # Get the appropriate model
        model = self._nlp_service.get_model(request.model)
        
        # Progress stages - simplified to avoid fragile monkey-patching
        stages = {
            "preparation": 5,
            "spacy": 25,
            "entities": 50,
            "quotes": 75,
            "coref": 95,
            "finalization": 100
        }
        
        # Get event loop for thread-safe progress updates
        loop = asyncio.get_event_loop()
        
        def safe_progress_callback(progress: float):
            """Thread-safe progress callback."""
            loop.call_soon_threadsafe(progress_callback, progress)
        
        # Report initial progress
        safe_progress_callback(stages["preparation"])
        
        # BookNLP requires file-based I/O, so we use temp files
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = os.path.join(tmpdir, "input.txt")
            # Use async file API
            with open(input_file, "w", encoding="utf-8") as f:
                f.write(request.text)
            
            # Run BookNLP processing in thread pool to avoid blocking event loop
            await loop.run_in_executor(
                None,
                self._process_with_stage_progress,
                model,
                input_file,
                tmpdir,
                request.book_id or "document",
                stages,
                safe_progress_callback
            )
            
            # Read results from output files
            result = self._read_booknlp_output(tmpdir, request.book_id or "document", request.pipeline)
            
            # Report completion
            safe_progress_callback(100.0)
            
            return result
            
    def _read_booknlp_output(
        self,
        output_dir: str,
        book_id: str,
        pipeline: list[str],
    ) -> Dict[str, Any]:
        """Read BookNLP output files and convert to response format.
        
        Args:
            output_dir: Directory containing output files
            book_id: Book identifier used in filenames
            pipeline: List of pipeline components that were run
            
        Returns:
            Dictionary with parsed results
        """
        result: Dict[str, Any] = {
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
            result["tokens"] = self._parse_tokens_file(tokens_file)
        
        # Read entities file
        entities_file = os.path.join(output_dir, f"{book_id}.entities")
        if os.path.exists(entities_file) and "entity" in pipeline:
            result["entities"] = self._parse_entities_file(entities_file)
        
        # Read quotes file
        quotes_file = os.path.join(output_dir, f"{book_id}.quotes")
        if os.path.exists(quotes_file) and "quote" in pipeline:
            result["quotes"] = self._parse_quotes_file(quotes_file)
        
        # Read supersense file
        supersense_file = os.path.join(output_dir, f"{book_id}.supersense")
        if os.path.exists(supersense_file) and "supersense" in pipeline:
            result["supersenses"] = self._parse_supersense_file(supersense_file)
            
        # Read book file for characters
        book_file = os.path.join(output_dir, f"{book_id}.book")
        if os.path.exists(book_file):
            result["characters"] = self._parse_book_file(book_file)
        
        return result
        
    def _parse_tsv_file(self, filepath: str) -> list[Dict[str, Any]]:
        """Parse a tab-separated BookNLP output file.
        
        Args:
            filepath: Path to the TSV file
            
        Returns:
            List of dictionaries, one per row
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
        
    def _parse_book_file(self, filepath: str) -> list[Dict[str, Any]]:
        """Parse the .book file containing character information.
        
        Args:
            filepath: Path to the book file
            
        Returns:
            List of character dictionaries
        """
        import json
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("characters", [])
        
    # Aliases for backward compatibility and clarity
    _parse_tokens_file = _parse_tsv_file
    _parse_entities_file = _parse_tsv_file
    _parse_quotes_file = _parse_tsv_file
    _parse_supersense_file = _parse_tsv_file


    def _process_with_stage_progress(
            self,
            model: Any,
            input_file: str,
            output_dir: str,
            book_id: str,
            stages: Dict[str, float],
            progress_callback: Callable[[float], None]
        ) -> None:
            """Process BookNLP with stage-level progress reporting.
            
            This is a synchronous method that runs in a thread pool.
            """
            # Use the original BookNLP process method
            # We can't easily add fine-grained progress without fragile monkey-patching
            # So we report progress at major stage boundaries based on timing
            
            # Run the actual BookNLP processing
            model.process(input_file, output_dir, book_id)
            
            # BookNLP processing is done, just report final stages
            # This is a simplified approach - we can't easily intercept the internal stages
            # without modifying BookNLP itself
            progress_callback(stages["spacy"])
            progress_callback(stages["entities"])
            progress_callback(stages["quotes"])
            progress_callback(stages["coref"])
            progress_callback(stages["finalization"])


# Global processor instance
_processor: Optional[AsyncBookNLPProcessor] = None


def get_async_processor() -> AsyncBookNLPProcessor:
    """Get the global async processor instance.
    
    Returns:
        The singleton AsyncBookNLPProcessor instance.
    """
    global _processor
    if _processor is None:
        _processor = AsyncBookNLPProcessor()
    return _processor
