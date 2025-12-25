"""Tests for Question Annotation Service"""

import pytest
import json
from unittest.mock import Mock, patch
from services.question_annotation_service import QuestionAnnotationService


class TestQuestionAnnotationService:
    """Test question annotation microservice"""
    
    @pytest.fixture
    def annotation_service(self):
        """Create annotation service instance"""
        with patch('services.question_annotation_service.StorageService') as mock_storage:
            service = QuestionAnnotationService()
            service.storage_service = mock_storage.return_value
            return service
    
    def test_create_annotation_session_success(self, annotation_service):
        """Test successful annotation session creation"""
        # Mock PDF processing data
        mock_pdf_processing = {
            'total_pages': 3,
            'image_urls': '[{"page": 1, "url": "test1.png"}]'
        }
        
        annotation_service.storage_service.get_entity.return_value = mock_pdf_processing
        annotation_service.storage_service.create_entity.return_value = True
        
        result = annotation_service.create_annotation_session('test-project', 'processing-123')
        
        assert result['success'] is True
        assert 'session_id' in result
        assert result['total_pages'] == 3
        assert len(result['image_urls']) == 1
        
        # Verify storage calls
        annotation_service.storage_service.get_entity.assert_called_once_with(
            'pdf_processing', 'test-project', 'processing-123'
        )
        annotation_service.storage_service.create_entity.assert_called_once()
    
    def test_create_annotation_session_pdf_not_found(self, annotation_service):
        """Test annotation session creation with missing PDF processing"""
        annotation_service.storage_service.get_entity.return_value = None
        
        result = annotation_service.create_annotation_session('test-project', 'fake-processing')
        
        assert result['success'] is False
        assert 'not found' in result['error']
    
    def test_save_page_annotations_success(self, annotation_service):
        """Test successful page annotation saving"""
        mock_session = {
            'processing_id': 'processing-123',
            'total_pages': 3,
            'annotations': '{"1": [{"x": 10, "y": 20, "width": 100, "height": 50, "label": "Q1"}]}',
            'created_at': '2023-01-01T00:00:00'
        }
        
        annotation_service.storage_service.get_entity.return_value = mock_session
        annotation_service.storage_service.update_entity.return_value = True
        
        annotations = [
            {'x': 50, 'y': 60, 'width': 200, 'height': 100, 'label': 'Q2'}
        ]
        
        result = annotation_service.save_page_annotations('test-project', 'session-123', 2, annotations)
        
        assert result['success'] is True
        assert result['page'] == 2
        assert result['annotation_count'] == 1
        assert result['total_annotations'] == 2  # 1 existing + 1 new
        
        # Verify update call
        annotation_service.storage_service.update_entity.assert_called_once()
    
    def test_get_page_annotations_success(self, annotation_service):
        """Test getting page annotations"""
        mock_session = {
            'annotations': '{"2": [{"x": 10, "y": 20, "width": 100, "height": 50, "label": "Q1"}]}'
        }
        
        annotation_service.storage_service.get_entity.return_value = mock_session
        
        result = annotation_service.get_page_annotations('test-project', 'session-123', 2)
        
        assert result['success'] is True
        assert result['page'] == 2
        assert len(result['annotations']) == 1
        assert result['annotations'][0]['label'] == 'Q1'
    
    def test_get_page_annotations_empty_page(self, annotation_service):
        """Test getting annotations for page with no annotations"""
        mock_session = {
            'annotations': '{"1": [{"x": 10, "y": 20, "width": 100, "height": 50, "label": "Q1"}]}'
        }
        
        annotation_service.storage_service.get_entity.return_value = mock_session
        
        result = annotation_service.get_page_annotations('test-project', 'session-123', 2)
        
        assert result['success'] is True
        assert result['page'] == 2
        assert result['annotations'] == []
    
    def test_complete_annotation_session_success(self, annotation_service):
        """Test successful annotation session completion"""
        mock_session = {
            'processing_id': 'processing-123',
            'total_pages': 3,
            'current_page': 3,
            'annotations': '{"1": [{"x": 10, "y": 20, "width": 100, "height": 50, "label": "Q1"}], "2": [{"x": 30, "y": 40, "width": 150, "height": 75, "label": "Q2"}]}',
            'created_at': '2023-01-01T00:00:00'
        }
        
        annotation_service.storage_service.get_entity.return_value = mock_session
        annotation_service.storage_service.update_entity.return_value = True
        
        result = annotation_service.complete_annotation_session('test-project', 'session-123')
        
        assert result['success'] is True
        assert result['status'] == 'completed'
        assert result['total_pages'] == 3
        assert result['total_annotations'] == 2
        
        # Verify update call with completed status
        annotation_service.storage_service.update_entity.assert_called_once()
        update_call = annotation_service.storage_service.update_entity.call_args[0][1]
        assert update_call['status'] == 'completed'
        assert 'completed_at' in update_call
    
    def test_get_annotation_session_success(self, annotation_service):
        """Test getting annotation session details"""
        mock_session = {
            'RowKey': 'session-123',
            'processing_id': 'processing-123',
            'total_pages': 3,
            'current_page': 2,
            'status': 'in_progress',
            'annotations': '{"1": [{"x": 10, "y": 20, "width": 100, "height": 50, "label": "Q1"}]}',
            'created_at': '2023-01-01T00:00:00',
            'updated_at': '2023-01-01T01:00:00'
        }
        
        annotation_service.storage_service.get_entity.return_value = mock_session
        
        result = annotation_service.get_annotation_session('test-project', 'session-123')
        
        assert result['success'] is True
        assert result['session_id'] == 'session-123'
        assert result['processing_id'] == 'processing-123'
        assert result['total_pages'] == 3
        assert result['current_page'] == 2
        assert result['status'] == 'in_progress'
        assert result['total_annotations'] == 1
    
    def test_list_project_sessions(self, annotation_service):
        """Test listing project annotation sessions"""
        mock_entities = [
            {
                'RowKey': 'session-1',
                'processing_id': 'processing-1',
                'total_pages': 2,
                'status': 'completed',
                'annotations': '{"1": [{"x": 10, "y": 20, "width": 100, "height": 50, "label": "Q1"}]}',
                'created_at': '2023-01-01T00:00:00',
                'updated_at': '2023-01-01T01:00:00'
            },
            {
                'RowKey': 'session-2',
                'processing_id': 'processing-2',
                'total_pages': 3,
                'status': 'in_progress',
                'annotations': '{}',
                'created_at': '2023-01-02T00:00:00',
                'updated_at': '2023-01-02T00:30:00'
            }
        ]
        
        annotation_service.storage_service.query_entities.return_value = mock_entities
        
        results = annotation_service.list_project_sessions('test-project')
        
        assert len(results) == 2
        assert results[0]['session_id'] == 'session-1'
        assert results[0]['status'] == 'completed'
        assert results[0]['total_annotations'] == 1
        assert results[1]['session_id'] == 'session-2'
        assert results[1]['status'] == 'in_progress'
        assert results[1]['total_annotations'] == 0
