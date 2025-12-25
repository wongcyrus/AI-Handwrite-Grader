import pytest
import asyncio
from unittest.mock import Mock, patch
from services.async_job_processor import AsyncJobProcessor
from services.ai_foundry_service import AIFoundryService

class TestAsyncJobProcessor:
    
    @pytest.fixture
    def mock_ai_service(self):
        """Mock AI Foundry service for testing."""
        service = Mock(spec=AIFoundryService)
        service._delegate_to_agent.return_value = {"status": "completed", "response": "Mock response"}
        return service
    
    @pytest.fixture
    def job_processor(self, mock_ai_service):
        """Create job processor with mocked AI service."""
        return AsyncJobProcessor(mock_ai_service)
    
    @pytest.mark.asyncio
    async def test_queue_job(self, job_processor):
        """Test job queuing functionality."""
        job_id = "test_job_123"
        
        await job_processor.queue_job(job_id, "project1", "pdf_url", "excel_url")
        
        # Check job was queued
        assert job_id in job_processor.job_status
        assert job_processor.job_status[job_id]["status"] == "queued"
        assert job_processor.job_queue.qsize() == 1
    
    @pytest.mark.asyncio
    async def test_process_job_success(self, job_processor, mock_ai_service):
        """Test successful job processing through all stages."""
        job_data = {
            "job_id": "test_job_123",
            "project_id": "project1",
            "pdf_url": "pdf_url",
            "excel_url": "excel_url"
        }
        
        # Process job
        await job_processor.process_job(job_data)
        
        # Verify final status
        status = job_processor.get_job_status("test_job_123")
        assert status["status"] == "completed"
        assert status["progress"] == 100
        
        # Verify all agents were called
        assert mock_ai_service._delegate_to_agent.call_count == 3  # OCR, content, scoring
    
    @pytest.mark.asyncio
    async def test_process_job_failure(self, job_processor, mock_ai_service):
        """Test job processing with agent failure."""
        # Mock agent failure
        mock_ai_service._delegate_to_agent.return_value = {"status": "error", "message": "Agent failed"}
        
        job_data = {
            "job_id": "test_job_456",
            "project_id": "project1",
            "pdf_url": "pdf_url",
            "excel_url": "excel_url"
        }
        
        # Process job
        await job_processor.process_job(job_data)
        
        # Verify error status
        status = job_processor.get_job_status("test_job_456")
        assert status["status"] == "error"
        assert "Agent failed" in status["current_step"]
    
    def test_get_job_status_not_found(self, job_processor):
        """Test getting status for non-existent job."""
        status = job_processor.get_job_status("nonexistent_job")
        
        assert status["status"] == "not_found"
        assert status["message"] == "Job not found"
    
    def test_update_job_status(self, job_processor):
        """Test job status updates."""
        job_id = "test_job_789"
        
        job_processor.update_job_status(job_id, "processing", 50, "Test step")
        
        status = job_processor.get_job_status(job_id)
        assert status["status"] == "processing"
        assert status["progress"] == 50
        assert status["current_step"] == "Test step"
        assert "estimated_completion" in status
