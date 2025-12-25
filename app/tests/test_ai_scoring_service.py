"""Tests for AI Scoring Service"""

import pytest
import json
from unittest.mock import Mock, patch
from services.ai_scoring_service import AIScoringService


class TestAIScoringService:
    """Test AI scoring microservice"""
    
    @pytest.fixture
    def scoring_service(self):
        """Create scoring service instance"""
        with patch('services.ai_scoring_service.StorageService') as mock_storage:
            with patch('services.ai_scoring_service.AIFoundryService') as mock_ai:
                service = AIScoringService()
                service.storage_service = mock_storage.return_value
                service.ai_foundry_service = mock_ai.return_value
                return service
    
    def test_create_scoring_session_success(self, scoring_service):
        """Test successful scoring session creation"""
        mock_annotation_session = {
            'status': 'completed',
            'annotations': '{"1": [{"x": 10, "y": 20, "width": 100, "height": 50, "label": "Q1"}]}'
        }
        
        scoring_service.storage_service.get_entity.return_value = mock_annotation_session
        scoring_service.storage_service.create_entity.return_value = True
        
        result = scoring_service.create_scoring_session('test-project', 'annotation-123', 0.75)
        
        assert result['success'] is True
        assert 'session_id' in result
        assert result['confidence_threshold'] == 0.75
        assert result['status'] == 'created'
        
        # Verify storage calls
        scoring_service.storage_service.get_entity.assert_called_once()
        scoring_service.storage_service.create_entity.assert_called_once()
    
    def test_create_scoring_session_annotation_not_completed(self, scoring_service):
        """Test scoring session creation with incomplete annotation"""
        mock_annotation_session = {
            'status': 'in_progress',
            'annotations': '{}'
        }
        
        scoring_service.storage_service.get_entity.return_value = mock_annotation_session
        
        result = scoring_service.create_scoring_session('test-project', 'annotation-123')
        
        assert result['success'] is False
        assert 'not completed' in result['error']
    
    def test_create_scoring_session_default_threshold(self, scoring_service):
        """Test scoring session creation with default threshold"""
        mock_annotation_session = {
            'status': 'completed',
            'annotations': '{}'
        }
        
        scoring_service.storage_service.get_entity.return_value = mock_annotation_session
        scoring_service.storage_service.create_entity.return_value = True
        
        result = scoring_service.create_scoring_session('test-project', 'annotation-123')
        
        assert result['success'] is True
        assert result['confidence_threshold'] == 0.8  # Default threshold
    
    def test_extract_and_score_questions_success(self, scoring_service):
        """Test successful question extraction and scoring"""
        mock_scoring_session = {
            'annotation_session_id': 'annotation-123',
            'confidence_threshold': 0.8,
            'created_at': '2023-01-01T00:00:00'
        }
        
        mock_annotation_session = {
            'annotations': '{"1": [{"x": 10, "y": 20, "width": 100, "height": 50, "label": "Q1"}, {"x": 200, "y": 300, "width": 150, "height": 75, "label": "NAME"}]}'
        }
        
        scoring_service.storage_service.get_entity.side_effect = [
            mock_scoring_session,  # First call for scoring session
            mock_annotation_session  # Second call for annotation session
        ]
        scoring_service.storage_service.update_entity.return_value = True
        
        result = scoring_service.extract_and_score_questions('test-project', 'scoring-123')
        
        assert result['success'] is True
        assert result['total_questions'] == 2
        assert result['confidence_threshold'] == 0.8
        assert len(result['questions']) == 2
        
        # Check question structure
        question = result['questions'][0]
        assert 'question_id' in question
        assert 'extracted_text' in question
        assert 'ai_score' in question
        assert 'confidence' in question
        assert 'needs_review' in question
        
        # Verify update call
        scoring_service.storage_service.update_entity.assert_called_once()
    
    def test_get_scoring_results_success(self, scoring_service):
        """Test getting scoring results"""
        mock_questions = [
            {
                'question_id': 'q1',
                'label': 'Q1',
                'ai_score': 85,
                'confidence': 0.9,
                'needs_review': False
            }
        ]
        
        mock_session = {
            'RowKey': 'scoring-123',
            'status': 'processed',
            'total_questions': 1,
            'low_confidence_count': 0,
            'confidence_threshold': 0.8,
            'questions_data': json.dumps(mock_questions),
            'created_at': '2023-01-01T00:00:00',
            'processed_at': '2023-01-01T01:00:00'
        }
        
        scoring_service.storage_service.get_entity.return_value = mock_session
        
        result = scoring_service.get_scoring_results('test-project', 'scoring-123')
        
        assert result['success'] is True
        assert result['session_id'] == 'scoring-123'
        assert result['status'] == 'processed'
        assert result['total_questions'] == 1
        assert result['low_confidence_count'] == 0
        assert len(result['questions']) == 1
        assert result['questions'][0]['question_id'] == 'q1'
    
    def test_update_confidence_threshold_success(self, scoring_service):
        """Test updating confidence threshold"""
        mock_questions = [
            {'confidence': 0.9, 'needs_review': False},
            {'confidence': 0.7, 'needs_review': False},
            {'confidence': 0.5, 'needs_review': True}
        ]
        
        mock_session = {
            'annotation_session_id': 'annotation-123',
            'status': 'processed',
            'total_questions': 3,
            'processed_questions': 3,
            'questions_data': json.dumps(mock_questions),
            'created_at': '2023-01-01T00:00:00',
            'processed_at': '2023-01-01T01:00:00'
        }
        
        scoring_service.storage_service.get_entity.return_value = mock_session
        scoring_service.storage_service.update_entity.return_value = True
        
        result = scoring_service.update_confidence_threshold('test-project', 'scoring-123', 0.75)
        
        assert result['success'] is True
        assert result['new_threshold'] == 0.75
        assert result['low_confidence_count'] == 2  # 0.7 and 0.5 confidence below 0.75
        assert result['total_questions'] == 3
        
        # Verify update call
        scoring_service.storage_service.update_entity.assert_called_once()
    
    def test_update_confidence_threshold_invalid(self, scoring_service):
        """Test updating with invalid threshold"""
        result = scoring_service.update_confidence_threshold('test-project', 'scoring-123', 1.5)
        
        assert result['success'] is False
        assert 'between 0.1 and 0.99' in result['error']
    
    def test_list_project_scoring_sessions(self, scoring_service):
        """Test listing project scoring sessions"""
        mock_entities = [
            {
                'RowKey': 'scoring-1',
                'annotation_session_id': 'annotation-1',
                'status': 'processed',
                'total_questions': 5,
                'low_confidence_count': 1,
                'confidence_threshold': 0.8,
                'created_at': '2023-01-01T00:00:00',
                'processed_at': '2023-01-01T01:00:00'
            },
            {
                'RowKey': 'scoring-2',
                'annotation_session_id': 'annotation-2',
                'status': 'created',
                'total_questions': 0,
                'low_confidence_count': 0,
                'confidence_threshold': 0.75,
                'created_at': '2023-01-02T00:00:00',
                'processed_at': None
            }
        ]
        
        scoring_service.storage_service.query_entities.return_value = mock_entities
        
        results = scoring_service.list_project_scoring_sessions('test-project')
        
        assert len(results) == 2
        assert results[0]['session_id'] == 'scoring-1'
        assert results[0]['status'] == 'processed'
        assert results[0]['total_questions'] == 5
        assert results[1]['session_id'] == 'scoring-2'
        assert results[1]['status'] == 'created'
    
    def test_process_question_annotation_metadata_fields(self, scoring_service):
        """Test processing metadata fields (NAME, ID, CLASS) have higher confidence"""
        annotation = {'x': 10, 'y': 20, 'width': 100, 'height': 50, 'label': 'NAME'}
        
        # Run multiple times to test confidence distribution
        confidences = []
        for _ in range(10):
            result = scoring_service._process_question_annotation('test-project', '1', annotation, 0.8)
            confidences.append(result['confidence'])
        
        # NAME fields should generally have higher confidence
        avg_confidence = sum(confidences) / len(confidences)
        assert avg_confidence > 0.8  # Should be above threshold on average
        
        # Check result structure
        assert result['label'] == 'NAME'
        assert result['extracted_text'] == 'John Smith'
        assert 'ai_score' in result
        assert 'bbox' in result
    
    def test_process_question_annotation_question_fields(self, scoring_service):
        """Test processing question fields have variable confidence"""
        annotation = {'x': 10, 'y': 20, 'width': 100, 'height': 50, 'label': 'Q1'}
        
        result = scoring_service._process_question_annotation('test-project', '1', annotation, 0.8)
        
        assert result['label'] == 'Q1'
        assert 'Sample answer for Q1' in result['extracted_text']
        assert 0.1 <= result['confidence'] <= 0.99
        assert 0 <= result['ai_score'] <= 100
        assert isinstance(result['needs_review'], bool)
