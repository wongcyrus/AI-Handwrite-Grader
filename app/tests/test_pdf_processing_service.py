"""Tests for PDF Processing Service"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from services.pdf_processing_service import PDFProcessingService


class TestPDFProcessingService:
    """Test PDF processing microservice"""
    
    @pytest.fixture
    def pdf_service(self):
        """Create PDF processing service instance"""
        with patch('services.pdf_processing_service.StorageService') as mock_storage:
            service = PDFProcessingService()
            service.storage_service = mock_storage.return_value
            return service
    
    @pytest.fixture
    def mock_pdf_images(self):
        """Mock PDF images"""
        mock_image = Mock()
        mock_image.save = Mock()
        return [mock_image, mock_image]  # 2 pages
    
    def test_process_pdf_success(self, pdf_service, mock_pdf_images):
        """Test successful PDF processing"""
        with patch('services.pdf_processing_service.convert_from_path', return_value=mock_pdf_images):
            with patch('services.pdf_processing_service.io.BytesIO') as mock_bytes:
                mock_bytes.return_value.getvalue.return_value = b'fake_image_data'
                
                # Mock storage service methods
                pdf_service.storage_service.upload_file.return_value = 'https://blob.url/image.png'
                pdf_service.storage_service.create_entity.return_value = True
                
                result = pdf_service.process_pdf('/fake/path.pdf', 'test-project')
                
                assert result['success'] is True
                assert result['total_pages'] == 2
                assert len(result['image_urls']) == 2
                assert result['status'] == 'completed'
                
                # Verify storage calls
                assert pdf_service.storage_service.upload_file.call_count == 2
                pdf_service.storage_service.create_entity.assert_called_once()
    
    def test_process_pdf_failure(self, pdf_service):
        """Test PDF processing failure"""
        with patch('services.pdf_processing_service.convert_from_path', side_effect=Exception("PDF error")):
            pdf_service.storage_service.create_entity.return_value = True
            
            result = pdf_service.process_pdf('/fake/path.pdf', 'test-project')
            
            assert result['success'] is False
            assert 'PDF error' in result['error']
            assert result['status'] == 'failed'
            
            # Verify error logging
            pdf_service.storage_service.create_entity.assert_called_once()
    
    def test_get_processing_status_success(self, pdf_service):
        """Test getting processing status"""
        mock_entity = {
            'status': 'completed',
            'total_pages': 3,
            'image_urls': "[{'page': 1, 'url': 'test.png'}]",
            'created_at': '2023-01-01T00:00:00',
            'error': None
        }
        
        pdf_service.storage_service.get_entity.return_value = mock_entity
        
        result = pdf_service.get_processing_status('test-project', 'processing-id')
        
        assert result['success'] is True
        assert result['status'] == 'completed'
        assert result['total_pages'] == 3
        assert len(result['image_urls']) == 1
    
    def test_get_processing_status_not_found(self, pdf_service):
        """Test getting status for non-existent processing"""
        pdf_service.storage_service.get_entity.return_value = None
        
        result = pdf_service.get_processing_status('test-project', 'fake-id')
        
        assert result['success'] is False
        assert 'not found' in result['error']
    
    def test_list_project_processing(self, pdf_service):
        """Test listing project processing records"""
        mock_entities = [
            {
                'RowKey': 'processing-1',
                'status': 'completed',
                'total_pages': 2,
                'created_at': '2023-01-01T00:00:00',
                'error': None
            },
            {
                'RowKey': 'processing-2',
                'status': 'failed',
                'total_pages': None,
                'created_at': '2023-01-02T00:00:00',
                'error': 'Processing error'
            }
        ]
        
        pdf_service.storage_service.query_entities.return_value = mock_entities
        
        results = pdf_service.list_project_processing('test-project')
        
        assert len(results) == 2
        assert results[0]['processing_id'] == 'processing-1'
        assert results[0]['status'] == 'completed'
        assert results[1]['processing_id'] == 'processing-2'
        assert results[1]['status'] == 'failed'
        assert results[1]['error'] == 'Processing error'
    
    def test_list_project_processing_exception(self, pdf_service):
        """Test listing processing records with exception"""
        pdf_service.storage_service.query_entities.side_effect = Exception("Query error")
        
        results = pdf_service.list_project_processing('test-project')
        
        assert results == []
