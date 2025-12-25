"""Tests for Post-Processing Service"""

import pytest
import json
from unittest.mock import Mock, patch
from services.post_processing_service import PostProcessingService


class TestPostProcessingService:
    """Test post-processing microservice"""
    
    @pytest.fixture
    def post_service(self):
        """Create post-processing service instance"""
        with patch('services.post_processing_service.StorageService') as mock_storage:
            service = PostProcessingService()
            service.storage_service = mock_storage.return_value
            return service
    
    def test_create_post_processing_session_success(self, post_service):
        """Test successful post-processing session creation"""
        mock_manual_session = {
            'status': 'completed',
            'questions_data': '[]'
        }
        
        post_service.storage_service.get_entity.return_value = mock_manual_session
        post_service.storage_service.create_entity.return_value = True
        
        result = post_service.create_post_processing_session('test-project', 'manual-123')
        
        assert result['success'] is True
        assert 'session_id' in result
        assert result['manual_scoring_session_id'] == 'manual-123'
        
        # Verify storage calls
        post_service.storage_service.get_entity.assert_called_once()
        post_service.storage_service.create_entity.assert_called_once()
    
    def test_create_post_processing_session_manual_not_completed(self, post_service):
        """Test post-processing session creation with incomplete manual scoring"""
        mock_manual_session = {
            'status': 'in_progress',
            'questions_data': '[]'
        }
        
        post_service.storage_service.get_entity.return_value = mock_manual_session
        
        result = post_service.create_post_processing_session('test-project', 'manual-123')
        
        assert result['success'] is False
        assert 'not completed' in result['error']
    
    def test_generate_excel_report_success(self, post_service):
        """Test successful Excel report generation"""
        mock_session = {
            'manual_scoring_session_id': 'manual-123',
            'created_at': '2023-01-01T00:00:00'
        }
        
        mock_questions = [
            # Student 1 (page 1)
            {'page': 1, 'label': 'NAME', 'extracted_text': 'John Doe', 'manual_score': 0, 'ai_score': 0},
            {'page': 1, 'label': 'ID', 'extracted_text': '12345', 'manual_score': 0, 'ai_score': 0},
            {'page': 1, 'label': 'Q1', 'extracted_text': 'Answer 1', 'manual_score': 85, 'ai_score': 80},
            {'page': 1, 'label': 'Q2', 'extracted_text': 'Answer 2', 'manual_score': 90, 'ai_score': 85},
            # Student 2 (page 2)
            {'page': 2, 'label': 'NAME', 'extracted_text': 'Jane Smith', 'manual_score': 0, 'ai_score': 0},
            {'page': 2, 'label': 'Q1', 'extracted_text': 'Answer 1', 'manual_score': 75, 'ai_score': 70}
        ]
        
        mock_manual_session = {
            'questions_data': json.dumps(mock_questions)
        }
        
        post_service.storage_service.get_entity.side_effect = [mock_session, mock_manual_session]
        post_service.storage_service.upload_file.return_value = 'https://blob.url/report.xlsx'
        post_service.storage_service.update_entity.return_value = True
        
        result = post_service.generate_excel_report('test-project', 'post-123')
        
        assert result['success'] is True
        assert result['total_students'] == 2
        assert 'report_url' in result
        assert len(result['report_data']) == 2
        
        # Check student data
        student1 = next(s for s in result['report_data'] if s['Name'] == 'John Doe')
        student2 = next(s for s in result['report_data'] if s['Name'] == 'Jane Smith')
        
        assert student1['Total_Score'] == 175  # 85 + 90
        assert student1['Percentage'] == 87.5  # 175/200 * 100
        assert student2['Total_Score'] == 75
        assert student2['Percentage'] == 75.0  # 75/100 * 100
        
        # Verify storage calls
        post_service.storage_service.upload_file.assert_called_once()
        post_service.storage_service.update_entity.assert_called_once()
    
    def test_create_annotated_pdfs_success(self, post_service):
        """Test successful annotated PDF creation"""
        mock_report_data = [
            {
                'Student_Page': 1,
                'Name': 'John Doe',
                'ID': '12345',
                'Total_Score': 175,
                'Percentage': 87.5
            },
            {
                'Student_Page': 2,
                'Name': 'Jane Smith',
                'ID': '67890',
                'Total_Score': 150,
                'Percentage': 75.0
            }
        ]
        
        mock_session = {
            'manual_scoring_session_id': 'manual-123',
            'reports_generated': 1,
            'report_data': json.dumps(mock_report_data),
            'created_at': '2023-01-01T00:00:00'
        }
        
        post_service.storage_service.get_entity.return_value = mock_session
        post_service.storage_service.update_entity.return_value = True
        
        result = post_service.create_annotated_pdfs('test-project', 'post-123')
        
        assert result['success'] is True
        assert result['pdfs_created'] == 2
        assert len(result['pdf_urls']) == 2
        
        # Check PDF data
        pdf1 = next(p for p in result['pdf_urls'] if p['student_name'] == 'John Doe')
        pdf2 = next(p for p in result['pdf_urls'] if p['student_name'] == 'Jane Smith')
        
        assert pdf1['student_page'] == 1
        assert pdf1['total_score'] == 175
        assert pdf2['student_page'] == 2
        assert pdf2['total_score'] == 150
        
        # Verify update call
        post_service.storage_service.update_entity.assert_called_once()
    
    def test_complete_post_processing_success(self, post_service):
        """Test successful post-processing completion"""
        mock_session = {
            'manual_scoring_session_id': 'manual-123',
            'reports_generated': 1,
            'pdfs_created': 2,
            'report_url': 'https://blob.url/report.xlsx',
            'created_at': '2023-01-01T00:00:00'
        }
        
        post_service.storage_service.get_entity.return_value = mock_session
        post_service.storage_service.update_entity.return_value = True
        
        result = post_service.complete_post_processing('test-project', 'post-123')
        
        assert result['success'] is True
        assert result['status'] == 'completed'
        assert result['reports_generated'] == 1
        assert result['pdfs_created'] == 2
        
        # Verify update call with completed status
        post_service.storage_service.update_entity.assert_called_once()
        update_call = post_service.storage_service.update_entity.call_args[0][1]
        assert update_call['status'] == 'completed'
        assert 'completed_at' in update_call
    
    def test_get_post_processing_session_success(self, post_service):
        """Test getting post-processing session details"""
        mock_pdf_urls = [
            {'student_page': 1, 'student_name': 'John Doe', 'pdf_url': 'test1.pdf'}
        ]
        
        mock_report_data = [
            {'Student_Page': 1, 'Name': 'John Doe', 'Total_Score': 175}
        ]
        
        mock_session = {
            'RowKey': 'post-123',
            'manual_scoring_session_id': 'manual-123',
            'status': 'completed',
            'reports_generated': 1,
            'pdfs_created': 1,
            'report_url': 'https://blob.url/report.xlsx',
            'pdf_urls': json.dumps(mock_pdf_urls),
            'report_data': json.dumps(mock_report_data),
            'created_at': '2023-01-01T00:00:00',
            'updated_at': '2023-01-01T02:00:00',
            'completed_at': '2023-01-01T02:30:00'
        }
        
        post_service.storage_service.get_entity.return_value = mock_session
        
        result = post_service.get_post_processing_session('test-project', 'post-123')
        
        assert result['success'] is True
        assert result['session_id'] == 'post-123'
        assert result['status'] == 'completed'
        assert result['reports_generated'] == 1
        assert result['pdfs_created'] == 1
        assert len(result['pdf_urls']) == 1
        assert len(result['report_data']) == 1
        assert result['report_url'] == 'https://blob.url/report.xlsx'
    
    def test_get_post_processing_session_not_found(self, post_service):
        """Test getting non-existent post-processing session"""
        post_service.storage_service.get_entity.return_value = None
        
        result = post_service.get_post_processing_session('test-project', 'fake-id')
        
        assert result['success'] is False
        assert 'not found' in result['error']
    
    def test_generate_excel_report_empty_questions(self, post_service):
        """Test Excel report generation with no questions"""
        mock_session = {
            'manual_scoring_session_id': 'manual-123',
            'created_at': '2023-01-01T00:00:00'
        }
        
        mock_manual_session = {
            'questions_data': '[]'  # No questions
        }
        
        post_service.storage_service.get_entity.side_effect = [mock_session, mock_manual_session]
        post_service.storage_service.upload_file.return_value = 'https://blob.url/report.xlsx'
        post_service.storage_service.update_entity.return_value = True
        
        result = post_service.generate_excel_report('test-project', 'post-123')
        
        assert result['success'] is True
        assert result['total_students'] == 0
        assert result['report_data'] == []
