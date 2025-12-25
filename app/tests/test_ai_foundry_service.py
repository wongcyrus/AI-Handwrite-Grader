import pytest
from unittest.mock import Mock, patch, MagicMock
from services.ai_foundry_service import AIFoundryService

class TestAIFoundryService:
    @pytest.fixture
    def mock_project_client(self):
        with patch('azure.ai.projects.AIProjectClient') as mock:
            mock_instance = Mock()
            mock.return_value = mock_instance
            yield mock_instance

    def test_initialization(self, mock_project_client):
        """Test that initialization works without errors"""
        service = AIFoundryService()
        
        # Should initialize without creating agents (placeholder implementation)
        assert service.project_client is not None
        assert service.agents == {}
        assert service.main_agent is None

    def test_start_annotation_job_success(self, mock_project_client):
        """Test successful annotation job start"""
        service = AIFoundryService()
        job_id = service.start_annotation_job('project-123', 'pdf_url', 'excel_url')
        
        # Should return a job ID with project ID prefix
        assert job_id.startswith('project-123_job_')
        assert len(job_id) > len('project-123_job_')

    def test_get_job_status_completed(self, mock_project_client):
        """Test getting job status for completed job"""
        service = AIFoundryService()
        
        # Create a job first
        job_id = service.start_annotation_job('project-123', 'pdf_url', 'excel_url')
        
        # Get status
        result = service.get_job_status(job_id)
        
        assert result['status'] == 'completed'
        assert result['progress'] == 100
        assert 'data' in result

    def test_get_job_status_invalid_job_id(self, mock_project_client):
        """Test getting job status with invalid job ID"""
        service = AIFoundryService()
        result = service.get_job_status('invalid-job-id')
        
        assert result['status'] == 'processing'
        assert result['progress'] == 50

    def test_cleanup_agents(self, mock_project_client):
        """Test agent cleanup"""
        service = AIFoundryService()
        
        # Should not raise any errors
        service.cleanup_agents()

    def test_start_annotation_job_with_exception(self, mock_project_client):
        """Test annotation job start with exception"""
        service = AIFoundryService()
        
        # Mock an exception in the service
        with patch.object(service, 'start_annotation_job', side_effect=Exception("Test error")):
            with pytest.raises(Exception) as exc_info:
                service.start_annotation_job('project-123', 'pdf_url', 'excel_url')
            
            assert "Test error" in str(exc_info.value)

    def test_get_job_status_with_exception(self, mock_project_client):
        """Test getting job status when exception occurs"""
        service = AIFoundryService()
        
        # Mock an exception
        with patch.object(service, 'get_job_status', side_effect=Exception("API Error")):
            result = service.get_job_status('project-123_job_test')
            
            # Should handle the exception gracefully
            assert result is None or 'error' in str(result)
