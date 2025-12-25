"""Tests for Email Distribution Service"""

import pytest
import json
from unittest.mock import Mock, patch
from services.email_distribution_service import EmailDistributionService


class TestEmailDistributionService:
    """Test email distribution service"""
    
    @pytest.fixture
    def email_service(self):
        """Create email service instance"""
        with patch('services.email_distribution_service.StorageService') as mock_storage:
            service = EmailDistributionService()
            service.storage_service = mock_storage.return_value
            return service
    
    def test_create_email_session_success(self, email_service):
        """Test successful email session creation"""
        mock_post_session = {
            'status': 'completed',
            'pdf_urls': '[]'
        }
        
        smtp_config = {
            'email': 'test@example.com',
            'password': 'password123',
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': '587'
        }
        
        email_service.storage_service.get_entity.return_value = mock_post_session
        email_service.storage_service.create_entity.return_value = True
        
        result = email_service.create_email_session('test-project', 'post-123', smtp_config)
        
        assert result['success'] is True
        assert 'session_id' in result
        assert result['post_processing_session_id'] == 'post-123'
        
        # Verify storage calls
        email_service.storage_service.get_entity.assert_called_once()
        email_service.storage_service.create_entity.assert_called_once()
    
    def test_create_email_session_post_not_completed(self, email_service):
        """Test email session creation with incomplete post-processing"""
        mock_post_session = {
            'status': 'in_progress',
            'pdf_urls': '[]'
        }
        
        smtp_config = {
            'email': 'test@example.com',
            'password': 'password123',
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': '587'
        }
        
        email_service.storage_service.get_entity.return_value = mock_post_session
        
        result = email_service.create_email_session('test-project', 'post-123', smtp_config)
        
        assert result['success'] is False
        assert 'not completed' in result['error']
    
    def test_create_email_session_missing_smtp_config(self, email_service):
        """Test email session creation with missing SMTP config"""
        mock_post_session = {
            'status': 'completed',
            'pdf_urls': '[]'
        }
        
        smtp_config = {
            'email': 'test@example.com',
            # Missing password, smtp_server, smtp_port
        }
        
        email_service.storage_service.get_entity.return_value = mock_post_session
        
        result = email_service.create_email_session('test-project', 'post-123', smtp_config)
        
        assert result['success'] is False
        assert 'Missing SMTP configuration' in result['error']
    
    def test_send_student_emails_success(self, email_service):
        """Test successful email sending"""
        mock_email_session = {
            'post_processing_session_id': 'post-123',
            'smtp_config': json.dumps({
                'email': 'test@example.com',
                'password': 'password123',
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': '587'
            })
        }
        
        mock_pdf_urls = [
            {
                'student_page': 1,
                'student_name': 'John Doe',
                'total_score': 85,
                'percentage': 85.0,
                'pdf_url': 'https://blob.url/student1.pdf'
            },
            {
                'student_page': 2,
                'student_name': 'Jane Smith',
                'total_score': 90,
                'percentage': 90.0,
                'pdf_url': 'https://blob.url/student2.pdf'
            }
        ]
        
        mock_post_session = {
            'pdf_urls': json.dumps(mock_pdf_urls)
        }
        
        email_template = {
            'subject': 'Your Results - {student_name}',
            'body': 'Dear {student_name}, your score is {percentage}%.'
        }
        
        email_service.storage_service.get_entity.side_effect = [mock_email_session, mock_post_session]
        email_service.storage_service.update_entity.return_value = True
        
        # Mock successful email sending
        with patch.object(email_service, '_send_individual_email') as mock_send:
            mock_send.return_value = {
                'success': True,
                'student_name': 'Test Student',
                'student_email': 'test@student.edu',
                'subject': 'Test Subject'
            }
            
            result = email_service.send_student_emails('test-project', 'email-123', email_template)
        
        assert result['success'] is True
        assert result['emails_sent'] == 2
        assert result['emails_failed'] == 0
        assert result['total_students'] == 2
        
        # Verify update call
        email_service.storage_service.update_entity.assert_called_once()
    
    def test_send_student_emails_partial_failure(self, email_service):
        """Test email sending with some failures"""
        mock_email_session = {
            'post_processing_session_id': 'post-123',
            'smtp_config': json.dumps({
                'email': 'test@example.com',
                'password': 'password123',
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': '587'
            })
        }
        
        mock_pdf_urls = [
            {'student_page': 1, 'student_name': 'John Doe', 'total_score': 85, 'percentage': 85.0},
            {'student_page': 2, 'student_name': 'Jane Smith', 'total_score': 90, 'percentage': 90.0}
        ]
        
        mock_post_session = {
            'pdf_urls': json.dumps(mock_pdf_urls)
        }
        
        email_service.storage_service.get_entity.side_effect = [mock_email_session, mock_post_session]
        email_service.storage_service.update_entity.return_value = True
        
        # Mock mixed success/failure
        with patch.object(email_service, '_send_individual_email') as mock_send:
            mock_send.side_effect = [
                {'success': True, 'student_name': 'John Doe'},
                {'success': False, 'student_name': 'Jane Smith', 'error': 'SMTP error'}
            ]
            
            result = email_service.send_student_emails('test-project', 'email-123', {})
        
        assert result['success'] is True
        assert result['emails_sent'] == 1
        assert result['emails_failed'] == 1
        assert result['total_students'] == 2
    
    def test_get_student_email(self, email_service):
        """Test student email generation"""
        email = email_service._get_student_email('John Doe')
        assert email == 'john.doe@student.edu'
        
        email = email_service._get_student_email('Jane Smith')
        assert email == 'jane.smith@student.edu'
    
    def test_simulate_smtp_send(self, email_service):
        """Test SMTP simulation"""
        # Since it's random, test multiple times to check it returns boolean
        results = []
        for _ in range(10):
            result = email_service._simulate_smtp_send('test@example.com', 'Subject', 'Body', 'pdf_url')
            results.append(result)
            assert isinstance(result, bool)
        
        # Should have some successes (90% success rate)
        assert any(results)
    
    def test_get_email_session_success(self, email_service):
        """Test getting email session details"""
        mock_email_results = [
            {'success': True, 'student_name': 'John Doe', 'student_email': 'john.doe@student.edu'},
            {'success': False, 'student_name': 'Jane Smith', 'error': 'SMTP error'}
        ]
        
        mock_session = {
            'RowKey': 'email-123',
            'post_processing_session_id': 'post-123',
            'status': 'partial',
            'emails_sent': 1,
            'emails_failed': 1,
            'email_results': json.dumps(mock_email_results),
            'created_at': '2023-01-01T00:00:00',
            'updated_at': '2023-01-01T01:00:00',
            'completed_at': '2023-01-01T01:30:00'
        }
        
        email_service.storage_service.get_entity.return_value = mock_session
        
        result = email_service.get_email_session('test-project', 'email-123')
        
        assert result['success'] is True
        assert result['session_id'] == 'email-123'
        assert result['status'] == 'partial'
        assert result['emails_sent'] == 1
        assert result['emails_failed'] == 1
        assert len(result['email_results']) == 2
    
    def test_get_email_session_not_found(self, email_service):
        """Test getting non-existent email session"""
        email_service.storage_service.get_entity.return_value = None
        
        result = email_service.get_email_session('test-project', 'fake-id')
        
        assert result['success'] is False
        assert 'not found' in result['error']
    
    def test_test_smtp_connection_success(self, email_service):
        """Test SMTP connection testing"""
        smtp_config = {
            'email': 'test@example.com',
            'password': 'password123',
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': '587'
        }
        
        result = email_service.test_smtp_connection(smtp_config)
        
        assert result['success'] is True
        assert 'SMTP connection test successful' in result['message']
        assert result['server'] == 'smtp.gmail.com'
        assert result['port'] == 587
        assert result['email'] == 'test@example.com'
    
    def test_test_smtp_connection_missing_config(self, email_service):
        """Test SMTP connection testing with missing config"""
        smtp_config = {
            'email': 'test@example.com',
            # Missing other required fields
        }
        
        result = email_service.test_smtp_connection(smtp_config)
        
        assert result['success'] is False
        assert 'Missing SMTP configuration' in result['error']
