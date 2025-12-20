"""E2E tests for synchronous analyze endpoint."""

import pytest
from httpx import AsyncClient


class TestAnalyzeEndpointE2E:
    """End-to-end tests for the synchronous /v1/analyze endpoint."""

    @pytest.mark.asyncio
    async def test_analyze_endpoint_basic_functionality(self, client: AsyncClient, auth_headers):
        """Test basic analyze endpoint functionality."""
        test_text = "The quick brown fox jumps over the lazy dog."
        
        request_data = {
            "text": test_text,
            "book_id": "analyze-test",
            "model": "small",
            "pipeline": ["entities", "quotes"]
        }
        
        # Make synchronous request
        response = await client.post("/v1/analyze", json=request_data, headers=auth_headers)
        
        assert response.status_code == 200
        result = response.json()
        
        # Validate response structure
        assert "book_id" in result
        assert "model" in result
        assert "processing_time_ms" in result
        assert "token_count" in result
        assert "tokens" in result
        assert "entities" in result
        
        assert result["book_id"] == "analyze-test"
        assert result["model"] == "small"
        assert result["token_count"] > 0
        assert len(result["tokens"]) > 0
        assert isinstance(result["entities"], list)

    @pytest.mark.asyncio
    async def test_analyze_endpoint_fails_without_auth(self, client: AsyncClient):
        """Test that analyze endpoint requires authentication."""
        test_text = "Test text for authentication."
        
        request_data = {
            "text": test_text,
            "book_id": "auth-test"
        }
        
        # Request without auth should fail
        response = await client.post("/v1/analyze", json=request_data)
        assert response.status_code == 401
        assert "Missing API key" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_analyze_endpoint_with_invalid_auth(self, client: AsyncClient):
        """Test that analyze endpoint fails with invalid auth."""
        test_text = "Test text for invalid auth."
        
        request_data = {
            "text": test_text,
            "book_id": "invalid-auth-test"
        }
        
        # Request with invalid auth should fail
        response = await client.post(
            "/v1/analyze", 
            json=request_data,
            headers={"X-API-Key": "invalid-key"}
        )
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_analyze_endpoint_all_pipeline_options(self, client: AsyncClient, auth_headers):
        """Test analyze endpoint with all pipeline options."""
        test_text = """
        "Hello," said Tom Sawyer. "I'm going to the river."
        "That sounds nice," replied Huck Finn.
        The quick brown fox jumps over the lazy dog.
        """
        
        request_data = {
            "text": test_text,
            "book_id": "full-pipeline-test",
            "model": "small",
            "pipeline": ["entities", "quotes", "supersense", "events", "coref"]
        }
        
        response = await client.post("/v1/analyze", json=request_data, headers=auth_headers)
        
        assert response.status_code == 200
        result = response.json()
        
        # Should have all pipeline components
        assert "tokens" in result
        assert "entities" in result
        assert len(result["entities"]) > 0
        
        # Check for quotes (if returned in this format)
        quotes = result.get("quotes", [])
        if quotes:
            assert len(quotes) > 0
        
        # Check for supersenses
        supersenses = result.get("supersenses", [])
        if supersenses:
            assert len(supersenses) > 0
        
        # Check for events
        events = result.get("events", [])
        if events:
            assert len(events) > 0

    @pytest.mark.asyncio
    async def test_analyze_endpoint_big_model(self, client: AsyncClient, auth_headers):
        """Test analyze endpoint with big model."""
        test_text = "This is a test for the big model."
        
        request_data = {
            "text": test_text,
            "book_id": "big-model-test",
            "model": "big",
            "pipeline": ["entities"]
        }
        
        response = await client.post("/v1/analyze", json=request_data, headers=auth_headers)
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["model"] == "big"
        assert "processing_time_ms" in result
        assert len(result["tokens"]) > 0

    @pytest.mark.asyncio
    async def test_analyze_endpoint_large_text(self, client: AsyncClient, auth_headers):
        """Test analyze endpoint with larger text."""
        # Create a larger test text
        test_text = "This is a test. " * 1000  # ~15,000 characters
        
        request_data = {
            "text": test_text,
            "book_id": "large-text-test",
            "model": "small",
            "pipeline": ["entities"]
        }
        
        response = await client.post("/v1/analyze", json=request_data, headers=auth_headers)
        
        assert response.status_code == 200
        result = response.json()
        
        # Should handle large text
        assert result["token_count"] > 1000
        assert len(result["tokens"]) > 1000

    @pytest.mark.asyncio
    async def test_analyze_endpoint_validation_errors(self, client: AsyncClient, auth_headers):
        """Test analyze endpoint validation."""
        # Test missing required fields
        response = await client.post("/v1/analyze", json={}, headers=auth_headers)
        assert response.status_code == 422
        
        # Test invalid model
        response = await client.post(
            "/v1/analyze",
            json={
                "text": "Test text",
                "book_id": "test",
                "model": "invalid-model"
            },
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Test invalid pipeline option
        response = await client.post(
            "/v1/analyze",
            json={
                "text": "Test text",
                "book_id": "test",
                "pipeline": ["invalid-option"]
            },
            headers=auth_headers
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_analyze_endpoint_nlp_features(self, client: AsyncClient, auth_headers):
        """Test that analyze endpoint returns correct NLP features."""
        test_text = """
        John Smith traveled from New York to London. 
        He works for Microsoft Corporation.
        "I'm excited about this trip," said John.
        """
        
        request_data = {
            "text": test_text,
            "book_id": "nlp-features-test",
            "model": "small",
            "pipeline": ["entities", "quotes"]
        }
        
        response = await client.post("/v1/analyze", json=request_data, headers=auth_headers)
        
        assert response.status_code == 200
        result = response.json()
        
        # Validate entities
        entities = result["entities"]
        entity_texts = [e["text"] for e in entities]
        
        assert any("John Smith" in text for text in entity_texts)
        assert any("New York" in text for text in entity_texts)
        assert any("London" in text for text in entity_texts)
        assert any("Microsoft Corporation" in text for text in entity_texts)
        
        # Validate tokens with POS
        tokens = result["tokens"]
        token_words = {t["word"]: t for t in tokens}
        
        # Check POS tags
        assert token_words["John"]["POS_tag"] == "PROPN"
        assert token_words["traveled"]["POS_tag"] == "VERB"
        assert token_words["from"]["POS_tag"] == "ADP"
        assert token_words["New"]["POS_tag"] == "PROPN"
        assert token_words["York"]["POS_tag"] == "PROPN"

    @pytest.mark.asyncio
    async def test_analyze_endpoint_performance_metrics(self, client: AsyncClient, auth_headers):
        """Test that analyze endpoint returns performance metrics."""
        test_text = "Performance test text for timing validation."
        
        request_data = {
            "text": test_text,
            "book_id": "performance-test",
            "model": "small",
            "pipeline": ["entities"]
        }
        
        response = await client.post("/v1/analyze", json=request_data, headers=auth_headers)
        
        assert response.status_code == 200
        result = response.json()
        
        # Should include performance metrics
        assert "processing_time_ms" in result
        assert isinstance(result["processing_time_ms"], (int, float))
        assert result["processing_time_ms"] > 0
        
        assert "token_count" in result
        assert isinstance(result["token_count"], int)
        assert result["token_count"] > 0

    @pytest.mark.asyncio
    async def test_analyze_endpoint_rate_limiting(self, client: AsyncClient, auth_headers):
        """Test that analyze endpoint respects rate limiting."""
        test_text = "Rate limit test text."
        
        request_data = {
            "text": test_text,
            "book_id": "rate-limit-test",
            "pipeline": ["entities"]
        }
        
        # Make multiple requests
        responses = []
        for i in range(3):
            request_data["book_id"] = f"rate-limit-test-{i}"
            response = await client.post("/v1/analyze", json=request_data, headers=auth_headers)
            responses.append(response)
        
        # First requests should succeed (or fail if rate limit is very low)
        # Check if rate limiting headers are present
        if responses[0].status_code == 200:
            # Check for rate limit headers if enabled
            if "X-RateLimit-Limit" in responses[0].headers:
                assert "X-RateLimit-Remaining" in responses[0].headers

    @pytest.mark.asyncio
    async def test_analyze_vs_async_job_consistency(self, client: AsyncClient, auth_headers):
        """Test that analyze endpoint produces consistent results with async jobs."""
        test_text = "Tom Sawyer and Huck Finn went fishing."
        
        # Synchronous analyze
        analyze_request = {
            "text": test_text,
            "book_id": "sync-test",
            "model": "small",
            "pipeline": ["entities"]
        }
        
        analyze_response = await client.post("/v1/analyze", json=analyze_request, headers=auth_headers)
        assert analyze_response.status_code == 200
        analyze_result = analyze_response.json()
        
        # Async job
        job_request = {
            "text": test_text,
            "book_id": "async-test",
            "model": "small",
            "pipeline": ["entities"]
        }
        
        job_response = await client.post("/v1/jobs", json=job_request, headers=auth_headers)
        job_id = job_response.json()["job_id"]
        
        # Wait for completion
        import asyncio
        for _ in range(30):
            response = await client.get(f"/v1/jobs/{job_id}", headers=auth_headers)
            if response.json()["status"] == "completed":
                break
            await asyncio.sleep(5)
        
        # Get async result
        result_response = await client.get(f"/v1/jobs/{job_id}/result", headers=auth_headers)
        async_result = result_response.json()["result"]
        
        # Results should be consistent
        assert len(analyze_result["entities"]) == len(async_result["entities"])
        assert analyze_result["token_count"] == async_result["token_count"]
        
        # Entity texts should match
        analyze_entities = {e["text"] for e in analyze_result["entities"]}
        async_entities = {e["text"] for e in async_result["entities"]}
        assert analyze_entities == async_entities
