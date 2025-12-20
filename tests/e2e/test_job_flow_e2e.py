"""E2E tests for complete job flow with authentication."""

import os
import pytest
import asyncio
from uuid import UUID
from httpx import AsyncClient


class TestJobFlowE2E:
    """End-to-end tests for the complete job processing flow."""

    @pytest.mark.asyncio
    async def test_full_job_flow_with_auth(self, client: AsyncClient, auth_headers):
        """Test complete job submission → status polling → result flow with authentication."""
        # Submit a job
        job_request = {
            "text": "This is a test document for end-to-end testing. " * 10,
            "book_id": "e2e-test-book",
            "model": "small",
            "pipeline": ["entities", "quotes"]
        }
        
        response = await client.post("/v1/jobs", json=job_request, headers=auth_headers)
        assert response.status_code == 200
        
        job_data = response.json()
        assert "job_id" in job_data
        assert job_data["status"] == "pending"
        
        job_id = UUID(job_data["job_id"])
        
        # Poll job status until complete
        max_attempts = 60  # Max 5 minutes for processing
        for attempt in range(max_attempts):
            response = await client.get(f"/v1/jobs/{job_id}", headers=auth_headers)
            assert response.status_code == 200
            
            status_data = response.json()
            assert status_data["job_id"] == str(job_id)
            
            if status_data["status"] == "completed":
                break
            elif status_data["status"] == "failed":
                pytest.fail(f"Job failed: {status_data.get('error', 'Unknown error')}")
            
            # Wait 5 seconds before next poll
            await asyncio.sleep(5)
        else:
            pytest.fail("Job did not complete within 5 minutes")
        
        # Get job results
        response = await client.get(f"/v1/jobs/{job_id}/result", headers=auth_headers)
        assert response.status_code == 200
        
        result_data = response.json()
        assert result_data["status"] == "completed"
        assert "result" in result_data
        
        # Verify result structure
        result = result_data["result"]
        assert "tokens" in result
        assert "entities" in result
        assert isinstance(result["tokens"], list)
        assert isinstance(result["entities"], list)
        
        # Verify we got some tokens
        assert len(result["tokens"]) > 0
        
        # Verify token structure
        token = result["tokens"][0]
        assert "word" in token
        assert "lemma" in token
        assert "POS_tag" in token

    @pytest.mark.asyncio
    async def test_job_flow_fails_without_auth(self, client: AsyncClient):
        """Test that job flow fails without authentication."""
        job_request = {
            "text": "Test text",
            "book_id": "test-book"
        }
        
        # Submit job without auth
        response = await client.post("/v1/jobs", json=job_request)
        assert response.status_code == 401
        assert "Missing API key" in response.json()["detail"]
        
        # Try to check status without auth
        response = await client.get("/v1/jobs/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_job_flow_fails_with_invalid_auth(self, client: AsyncClient, invalid_auth_headers):
        """Test that job flow fails with invalid authentication."""
        job_request = {
            "text": "Test text",
            "book_id": "test-book"
        }
        
        # Submit job with invalid auth
        response = await client.post("/v1/jobs", json=job_request, headers=invalid_auth_headers)
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_multiple_concurrent_jobs(self, client: AsyncClient, auth_headers):
        """Test processing multiple jobs concurrently."""
        # Submit 3 jobs
        job_ids = []
        for i in range(3):
            job_request = {
                "text": f"Test document {i}. " * 20,
                "book_id": f"test-book-{i}",
                "model": "small"
            }
            
            response = await client.post("/v1/jobs", json=job_request, headers=auth_headers)
            assert response.status_code == 200
            job_ids.append(UUID(response.json()["job_id"]))
        
        # Wait for all jobs to complete
        completed_jobs = set()
        max_attempts = 60
        
        for attempt in range(max_attempts):
            for job_id in job_ids:
                if job_id in completed_jobs:
                    continue
                    
                response = await client.get(f"/v1/jobs/{job_id}", headers=auth_headers)
                assert response.status_code == 200
                
                status = response.json()["status"]
                if status == "completed":
                    completed_jobs.add(job_id)
                elif status == "failed":
                    pytest.fail(f"Job {job_id} failed")
            
            if len(completed_jobs) == len(job_ids):
                break
                
            await asyncio.sleep(5)
        else:
            pytest.fail(f"Only {len(completed_jobs)}/{len(job_ids)} jobs completed")
        
        # Verify all results
        for job_id in job_ids:
            response = await client.get(f"/v1/jobs/{job_id}/result", headers=auth_headers)
            assert response.status_code == 200
            assert "result" in response.json()

    @pytest.mark.asyncio
    async def test_job_cancellation_flow(self, client: AsyncClient, auth_headers):
        """Test job cancellation flow."""
        # Submit a job
        job_request = {
            "text": "Large document for cancellation test. " * 100,
            "book_id": "cancellation-test",
            "model": "big"  # Use larger model to ensure it stays in queue
        }
        
        response = await client.post("/v1/jobs", json=job_request, headers=auth_headers)
        assert response.status_code == 200
        
        job_id = UUID(response.json()["job_id"])
        
        # Cancel the job
        response = await client.delete(f"/v1/jobs/{job_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["cancelled"] is True
        
        # Verify job status
        response = await client.get(f"/v1/jobs/{job_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_queue_statistics(self, client: AsyncClient, auth_headers):
        """Test queue statistics endpoint."""
        # Get initial stats
        response = await client.get("/v1/jobs/stats", headers=auth_headers)
        assert response.status_code == 200
        
        stats = response.json()
        assert "queue_size" in stats
        assert "total_jobs" in stats
        assert "jobs_by_status" in stats
        
        # Submit a job
        job_request = {
            "text": "Test for stats",
            "book_id": "stats-test"
        }
        
        await client.post("/v1/jobs", json=job_request, headers=auth_headers)
        
        # Check stats again
        response = await client.get("/v1/jobs/stats", headers=auth_headers)
        assert response.status_code == 200
        
        # Stats should reflect the new job
        new_stats = response.json()
        assert new_stats["total_jobs"] >= stats["total_jobs"]
