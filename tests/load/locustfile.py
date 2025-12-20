"""Load testing configuration for BookNLP API using Locust."""

import os
import random
from locust import HttpUser, task, between
from uuid import uuid4

# Constants
HEALTH_ENDPOINT = "/v1/health"


class BookNLPUser(HttpUser):
    """Simulated user for load testing BookNLP API."""
    
    # Wait between requests: 1-5 seconds
    wait_time = between(1, 5)
    
    def on_start(self):
        """Called when a user starts."""
        # Set up authentication
        self.api_key = os.getenv("BOOKNLP_API_KEY", "load-test-key")
        self.headers = {"X-API-Key": self.api_key}
        
        # Test data
        self.test_texts = [
            "Short test text for load testing.",
            "Medium length test text for load testing. " * 5,
            "Longer test document for load testing purposes. " * 10,
            "Very long test document that simulates a real book chapter. " * 20,
        ]
        
        # Check if service is ready
        self.check_health()
    
    def check_health(self):
        """Check if the service is healthy."""
        self.client.get(HEALTH_ENDPOINT)
        # Health check response not needed, just verify it doesn't fail
    
    @task(10)
    def submit_job(self):
        """Submit a new job for processing."""
        text = random.choice(self.test_texts)
        
        response = self.client.post("/v1/jobs", json={
            "text": text,
            "book_id": f"load-test-{uuid4()}",
            "model": "small",
            "pipeline": ["entities", "quotes"]
        }, headers=self.headers)
        
        if response.status_code == 200:
            job_id = response.json()["job_id"]
            # Store job ID for status checking
            if not hasattr(self, 'job_ids'):
                self.job_ids = []
            self.job_ids.append(job_id)
    
    @task(20)
    def check_job_status(self):
        """Check status of submitted jobs."""
        if hasattr(self, 'job_ids') and self.job_ids:
            job_id = random.choice(self.job_ids)
            self.client.get(f"/v1/jobs/{job_id}", headers=self.headers)
            # Don't care about response, just testing the endpoint
    
    @task(5)
    def get_job_result(self):
        """Get results for completed jobs."""
        if hasattr(self, 'job_ids') and self.job_ids:
            job_id = random.choice(self.job_ids)
            self.client.get(f"/v1/jobs/{job_id}/result", headers=self.headers)
            # Don't care about response, just testing the endpoint
    
    @task(15)
    def get_queue_stats(self):
        """Get queue statistics."""
        self.client.get("/v1/jobs/stats", headers=self.headers)
        # Don't care about response, just testing the endpoint
    
    @task(30)
    def check_health_endpoints(self):
        """Check health endpoints (no auth required)."""
        self.client.get(HEALTH_ENDPOINT)
        self.client.get("/v1/ready")
    
    @task(10)
    def check_metrics(self):
        """Check metrics endpoint (no auth required)."""
        self.client.get("/metrics")
    
    @task(5)
    def cancel_job(self):
        """Cancel a pending job."""
        if hasattr(self, 'job_ids') and self.job_ids:
            job_id = random.choice(self.job_ids)
            response = self.client.delete(f"/v1/jobs/{job_id}", headers=self.headers)
            # Remove from list if cancelled
            if response.status_code == 200:
                self.job_ids.remove(job_id)


class AdminUser(HttpUser):
    """Admin user for testing endpoints without rate limiting."""
    
    wait_time = between(0.5, 2)
    
    def on_start(self):
        """Called when an admin user starts."""
        self.api_key = os.getenv("BOOKNLP_API_KEY", "admin-key")
        self.headers = {"X-API-Key": self.api_key}
    
    @task(50)
    def health_check(self):
        """Rapid health checks (not rate limited)."""
        self.client.get("/v1/health")
    
    @task(50)
    def metrics_check(self):
        """Rapid metrics checks (not rate limited)."""
        self.client.get("/metrics")
