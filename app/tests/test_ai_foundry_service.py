import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from services.ai_foundry_service import AIFoundryService, ConnectedAgent

class TestAIFoundryService:
    
    @pytest.fixture
    def mock_azure_services(self):
        """Mock Azure services for Connected Agents testing."""
        with patch.dict(os.environ, {
            'AZURE_AI_PROJECT_ENDPOINT': 'https://test-endpoint.com',
            'AZURE_AI_MODEL_DEPLOYMENT_NAME': 'gpt-4'
        }):
            with patch('services.ai_foundry_service.AIProjectClient') as mock_client, \
                 patch('services.ai_foundry_service.DefaultAzureCredential'):
                
                # Mock the client instance
                mock_client_instance = Mock()
                mock_client.return_value = mock_client_instance
                
                # Mock OpenAI client
                mock_openai_client = Mock()
                mock_client_instance.get_openai_client.return_value = mock_openai_client
                
                # Mock chat completion response
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = "Test agent response"
                mock_response.usage = Mock()
                mock_response.usage.dict.return_value = {"total_tokens": 100}
                
                mock_openai_client.chat.completions.create.return_value = mock_response
                
                yield {
                    'client': mock_client_instance,
                    'openai_client': mock_openai_client,
                    'response': mock_response
                }

    def test_connected_agent_creation(self):
        """Test ConnectedAgent class creation."""
        agent = ConnectedAgent(
            name="test_agent",
            description="Test agent description",
            instructions="Test instructions"
        )
        
        assert agent.name == "test_agent"
        assert agent.description == "Test agent description"
        assert agent.instructions == "Test instructions"
        assert agent.id.startswith("agent_test_agent_")

    def test_initialization_success(self, mock_azure_services):
        """Test successful service initialization with Connected Agents."""
        service = AIFoundryService()
        
        assert service.client is not None
        assert service.openai_client is not None
        assert service.connected_agents is not None
        assert service.main_agent is not None
        assert len(service.connected_agents) == 3  # handwriting, content, scoring agents

    def test_initialization_missing_endpoint(self):
        """Test initialization failure when endpoint is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                AIFoundryService()
            assert "AZURE_AI_PROJECT_ENDPOINT" in str(exc_info.value)

    def test_delegate_to_agent(self, mock_azure_services):
        """Test delegating tasks to connected agents."""
        service = AIFoundryService()
        
        result = service._delegate_to_agent(
            "handwriting_analyzer",
            "Analyze this handwriting sample",
            {"question_id": "q1"}
        )
        
        assert result["status"] == "completed"
        assert result["agent"] == "handwriting_analyzer"
        assert result["response"] == "Test agent response"
        
        # Verify OpenAI client was called
        mock_azure_services['openai_client'].chat.completions.create.assert_called_once()

    def test_delegate_to_agent_with_retry(self, mock_azure_services):
        """Test agent delegation with retry logic."""
        service = AIFoundryService()
        
        # Mock first call to fail, second to succeed
        mock_azure_services['openai_client'].chat.completions.create.side_effect = [
            Exception("Temporary failure"),
            mock_azure_services['response']
        ]
        
        result = service._delegate_to_agent(
            "handwriting_analyzer",
            "Test task with retry",
            {"test": "context"}
        )
        
        assert result["status"] == "completed"
        assert result["attempt"] == 2
        assert mock_azure_services['openai_client'].chat.completions.create.call_count == 2

    def test_delegate_to_agent_max_retries_exceeded(self, mock_azure_services):
        """Test agent delegation when max retries exceeded."""
        service = AIFoundryService()
        
        # Mock all calls to fail
        mock_azure_services['openai_client'].chat.completions.create.side_effect = Exception("Persistent failure")
        
        result = service._delegate_to_agent("handwriting_analyzer", "Test task")
        
        assert result["status"] == "error"
        assert result["attempts"] == 3  # Default max retries
        assert "Persistent failure" in result["message"]

    def test_delegate_to_unknown_agent(self, mock_azure_services):
        """Test delegating to unknown agent raises error."""
        service = AIFoundryService()
        
        with pytest.raises(ValueError) as exc_info:
            service._delegate_to_agent("unknown_agent", "Test task")
        
        assert "Unknown agent: unknown_agent" in str(exc_info.value)

    def test_start_annotation_job(self, mock_azure_services):
        """Test starting an annotation job asynchronously."""
        service = AIFoundryService()
        
        job_id = service.start_annotation_job(
            project_id='test-project',
            pdf_url='https://example.com/test.pdf',
            excel_url='https://example.com/test.xlsx'
        )
        
        # Verify the job ID format
        assert job_id.startswith('test-project_job_')
        
        # Job submission should be immediate (no OpenAI client calls yet)
        # OpenAI client will be called during background processing
        assert mock_azure_services['openai_client'].chat.completions.create.call_count == 0

    def test_get_job_status_processing_stages(self, mock_azure_services):
        """Test getting job status shows realistic processing stages."""
        service = AIFoundryService()
        
        # Create a job and test different stages
        job_id = service.start_annotation_job('test-project', 'pdf_url', 'excel_url')
        
        status = service.get_job_status(job_id)
        
        # Should be in initializing stage for new jobs
        assert status['status'] in ['initializing', 'processing_ocr', 'processing_content', 'finalizing_scores', 'completed']
        assert 'current_step' in status
        assert 'estimated_completion' in status
        assert status['project_id'] == 'test-project'

    def test_get_job_status_invalid_format(self, mock_azure_services):
        """Test getting job status with invalid job ID format."""
        service = AIFoundryService()
        
        status = service.get_job_status('invalid-job-id')
        
        assert status['status'] == 'invalid'
        assert 'Invalid job ID format' in status['message']

    def test_process_handwriting_analysis(self, mock_azure_services):
        """Test handwriting analysis returns job ID immediately."""
        service = AIFoundryService()
        
        job_id = service.process_handwriting_analysis(b'fake_image_data', 'question_1')
        
        # Should return job ID immediately (async processing)
        assert job_id.startswith('handwriting_question_1_')
        
        # No immediate OpenAI client calls (processed in background)
        assert mock_azure_services['openai_client'].chat.completions.create.call_count == 0

    def test_evaluate_answer(self, mock_azure_services):
        """Test answer evaluation returns job ID immediately."""
        service = AIFoundryService()
        
        job_id = service.evaluate_answer(
            student_answer="Student's response",
            standard_answer="Expected answer",
            rubric={"total_points": 10, "criteria": ["accuracy", "completeness"]}
        )
        
        # Should return job ID immediately (async processing)
        assert job_id.startswith('evaluation_')
        
        # No immediate OpenAI client calls (processed in background)
        assert mock_azure_services['openai_client'].chat.completions.create.call_count == 0

    def test_evaluate_answer_evaluation_failed(self, mock_azure_services):
        """Test answer evaluation when service fails."""
        service = AIFoundryService()
        
        # Mock service to raise exception
        with patch.object(service, 'evaluate_answer', side_effect=Exception("Service error")):
            with pytest.raises(Exception) as exc_info:
                service.evaluate_answer("student", "standard", {})
            
            assert "Service error" in str(exc_info.value)

    def test_cleanup_agents(self, mock_azure_services):
        """Test agent cleanup functionality."""
        service = AIFoundryService()
        
        # Should not raise any errors
        service.cleanup_agents()

    def test_start_annotation_job_exception(self, mock_azure_services):
        """Test annotation job start with exception."""
        service = AIFoundryService()
        
        # Mock service to raise exception during job creation
        with patch.object(service, 'start_annotation_job', side_effect=Exception("Job creation error")):
            with pytest.raises(Exception) as exc_info:
                service.start_annotation_job('test-project', 'pdf_url', 'excel_url')
            
            assert "Job creation error" in str(exc_info.value)

    def test_process_handwriting_analysis_exception(self, mock_azure_services):
        """Test handwriting analysis with exception."""
        service = AIFoundryService()
        
        # Mock service to raise exception
        with patch.object(service, 'process_handwriting_analysis', side_effect=Exception("Analysis Error")):
            with pytest.raises(Exception) as exc_info:
                service.process_handwriting_analysis(b'data', 'q1')
            
            assert "Analysis Error" in str(exc_info.value)
