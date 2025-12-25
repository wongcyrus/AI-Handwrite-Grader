"""Integration Tests for Microservices Workflow"""

import pytest
import json
from unittest.mock import Mock, patch
from services.pdf_processing_service import PDFProcessingService
from services.question_annotation_service import QuestionAnnotationService
from services.ai_scoring_service import AIScoringService
from services.manual_scoring_service import ManualScoringService


class TestWorkflowIntegration:
    """Test integration between microservices"""
    
    @pytest.fixture
    def mock_storage(self):
        """Mock storage service for all services"""
        with patch('services.pdf_processing_service.StorageService') as mock_pdf_storage, \
             patch('services.question_annotation_service.StorageService') as mock_ann_storage, \
             patch('services.ai_scoring_service.StorageService') as mock_ai_storage, \
             patch('services.manual_scoring_service.StorageService') as mock_manual_storage:
            
            # Return the same mock instance for consistency
            mock_instance = Mock()
            mock_pdf_storage.return_value = mock_instance
            mock_ann_storage.return_value = mock_instance
            mock_ai_storage.return_value = mock_instance
            mock_manual_storage.return_value = mock_instance
            
            yield mock_instance
    
    def test_pdf_to_annotation_workflow(self, mock_storage):
        """Test PDF processing to annotation workflow"""
        pdf_service = PDFProcessingService()
        annotation_service = QuestionAnnotationService()
        
        # Mock PDF processing result
        mock_storage.upload_file.return_value = 'https://blob.url/image.png'
        mock_storage.create_entity.return_value = True
        
        # Step 1: Process PDF
        with patch('services.pdf_processing_service.convert_from_path') as mock_convert:
            mock_image = Mock()
            mock_image.save = Mock()
            mock_convert.return_value = [mock_image, mock_image]  # 2 pages
            
            with patch('services.pdf_processing_service.io.BytesIO') as mock_bytes:
                mock_bytes.return_value.getvalue.return_value = b'fake_image_data'
                
                pdf_result = pdf_service.process_pdf('/fake/path.pdf', 'test-project')
        
        assert pdf_result['success'] is True
        processing_id = pdf_result['processing_id']
        
        # Step 2: Create annotation session from PDF processing
        mock_storage.get_entity.return_value = {
            'total_pages': 2,
            'image_urls': '[{"page": 1, "url": "test1.png"}]'
        }
        
        annotation_result = annotation_service.create_annotation_session('test-project', processing_id)
        
        assert annotation_result['success'] is True
        assert annotation_result['total_pages'] == 2
        
        # Verify the workflow connection
        mock_storage.get_entity.assert_called_with('pdf_processing', 'test-project', processing_id)
    
    def test_annotation_to_scoring_workflow(self, mock_storage):
        """Test annotation to AI scoring workflow"""
        annotation_service = QuestionAnnotationService()
        ai_service = AIScoringService()
        
        # Step 1: Complete annotation session
        mock_session = {
            'processing_id': 'processing-123',
            'total_pages': 2,
            'annotations': '{"1": [{"x": 10, "y": 20, "width": 100, "height": 50, "label": "Q1"}]}',
            'created_at': '2023-01-01T00:00:00'
        }
        
        mock_storage.get_entity.return_value = mock_session
        mock_storage.update_entity.return_value = True
        
        complete_result = annotation_service.complete_annotation_session('test-project', 'annotation-123')
        assert complete_result['success'] is True
        
        # Step 2: Create AI scoring session from completed annotation
        mock_storage.get_entity.side_effect = [
            {'status': 'completed', 'annotations': '{"1": [{"x": 10, "y": 20, "width": 100, "height": 50, "label": "Q1"}]}'},  # annotation session
        ]
        
        scoring_result = ai_service.create_scoring_session('test-project', 'annotation-123')
        
        assert scoring_result['success'] is True
        assert scoring_result['confidence_threshold'] == 0.8
        
        # Verify the workflow connection
        mock_storage.get_entity.assert_called_with('annotation_sessions', 'test-project', 'annotation-123')
    
    def test_ai_to_manual_scoring_workflow(self, mock_storage):
        """Test AI scoring to manual scoring workflow"""
        manual_service = ManualScoringService()
        
        # Mock AI scoring session with processed status
        mock_ai_questions = [
            {'question_id': 'q1', 'ai_score': 85, 'label': 'Q1', 'confidence': 0.9}
        ]
        
        mock_storage.get_entity.return_value = {
            'status': 'processed',
            'questions_data': json.dumps(mock_ai_questions)
        }
        mock_storage.create_entity.return_value = True
        
        manual_result = manual_service.create_manual_session('test-project', 'ai-scoring-123')
        
        assert manual_result['success'] is True
        assert manual_result['total_questions'] == 1
        
        # Verify the workflow connection
        mock_storage.get_entity.assert_called_with('scoring_sessions', 'test-project', 'ai-scoring-123')
    
    def test_complete_workflow_data_flow(self, mock_storage):
        """Test data flow through complete workflow"""
        # Simulate the complete workflow with realistic data
        
        # 1. PDF Processing creates image URLs
        pdf_data = {
            'total_pages': 2,
            'image_urls': '[{"page": 1, "url": "page1.png"}, {"page": 2, "url": "page2.png"}]'
        }
        
        # 2. Annotation creates question boundaries
        annotation_data = {
            'status': 'completed',
            'annotations': '{"1": [{"x": 10, "y": 20, "width": 100, "height": 50, "label": "Q1"}, {"x": 200, "y": 300, "width": 150, "height": 75, "label": "NAME"}], "2": [{"x": 10, "y": 20, "width": 100, "height": 50, "label": "Q1"}]}'
        }
        
        # 3. AI Scoring processes annotations
        ai_questions = [
            {'question_id': 'q1', 'page': 1, 'label': 'Q1', 'ai_score': 85, 'confidence': 0.9},
            {'question_id': 'q2', 'page': 1, 'label': 'NAME', 'ai_score': 95, 'confidence': 0.95},
            {'question_id': 'q3', 'page': 2, 'label': 'Q1', 'ai_score': 75, 'confidence': 0.7}
        ]
        
        ai_data = {
            'status': 'processed',
            'questions_data': json.dumps(ai_questions)
        }
        
        # 4. Manual Scoring allows adjustments
        manual_service = ManualScoringService()
        
        mock_storage.get_entity.return_value = ai_data
        mock_storage.create_entity.return_value = True
        
        manual_result = manual_service.create_manual_session('test-project', 'ai-session-123')
        
        assert manual_result['success'] is True
        assert manual_result['total_questions'] == 3
        
        # 5. Calculate student totals
        mock_storage.get_entity.return_value = {
            'questions_data': json.dumps([
                {'question_id': 'q1', 'page': 1, 'label': 'Q1', 'manual_score': 90, 'ai_score': 85},
                {'question_id': 'q3', 'page': 2, 'label': 'Q1', 'manual_score': 80, 'ai_score': 75}
            ])
        }
        
        totals_result = manual_service.calculate_student_totals('test-project', 'manual-session-123')
        
        assert totals_result['success'] is True
        assert totals_result['total_students'] == 2
        
        # Verify student scores
        student_scores = totals_result['student_scores']
        student1 = next(s for s in student_scores if s['student_page'] == 1)
        student2 = next(s for s in student_scores if s['student_page'] == 2)
        
        assert student1['total_score'] == 90
        assert student2['total_score'] == 80
    
    def test_error_propagation_through_workflow(self, mock_storage):
        """Test error handling across workflow steps"""
        annotation_service = QuestionAnnotationService()
        ai_service = AIScoringService()
        
        # Test annotation session not found
        mock_storage.get_entity.return_value = None
        
        result = ai_service.create_scoring_session('test-project', 'nonexistent-annotation')
        
        assert result['success'] is False
        assert 'not found' in result['error']
        
        # Test incomplete annotation session
        mock_storage.get_entity.return_value = {
            'status': 'in_progress',
            'annotations': '{}'
        }
        
        result = ai_service.create_scoring_session('test-project', 'incomplete-annotation')
        
        assert result['success'] is False
        assert 'not completed' in result['error']
