import pytest
import json
from unittest.mock import Mock, patch

class TestProjectWorkflow:
    @pytest.fixture
    def client(self):
        """Create test client"""
        from app import app
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret'
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.test_client() as client:
            with app.app_context():
                yield client

    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user"""
        user = Mock()
        user.id = 'test-user-123'
        user.email = 'test@example.com'
        user.is_authenticated = True
        return user

    def test_complete_annotation_workflow(self, client, mock_user):
        """Test complete workflow from project creation to annotation saving"""
        # Mock project creation
        mock_project = Mock()
        mock_project.id = 'test-project-123'
        mock_project.user_id = 'test-user-123'
        mock_project.name = 'Integration Test Project'
        mock_project.description = 'Test Description'
        mock_project.status = 'created'
        mock_project.created_at = '2023-01-01T00:00:00'
        mock_project.pdf_url = None
        mock_project.excel_url = None
        mock_project.job_id = None
        
        with patch('flask_login.current_user', mock_user):
            # Step 1: Create project
            with patch('models.project.Project.create', return_value=mock_project):
                response = client.post('/project/create', data={
                    'name': 'Integration Test Project',
                    'description': 'Test Description'
                })
                assert response.status_code == 302  # Redirect after creation
            
            # Step 2: View project detail
            with patch('models.project.Project.get_by_id', return_value=mock_project):
                response = client.get('/project/test-project-123')
                assert response.status_code == 200
                assert b'Upload Files' in response.data
            
            # Step 3: Upload files
            mock_project.update_files = Mock(return_value=True)
            mock_project.update_status = Mock(return_value=True)
            
            with patch('models.project.Project.get_by_id', return_value=mock_project):
                with patch('services.storage_service.StorageService.upload_file') as mock_upload:
                    with patch('services.ai_foundry_service.AIFoundryService.start_annotation_job') as mock_job:
                        mock_upload.return_value = 'https://storage.blob.core.windows.net/test.pdf'
                        mock_job.return_value = 'job-123'
                        
                        import io
                        pdf_data = io.BytesIO(b'fake pdf content')
                        excel_data = io.BytesIO(b'fake excel content')
                        
                        response = client.post('/project/test-project-123/upload', 
                            data={
                                'pdf_file': (pdf_data, 'test.pdf'),
                                'excel_file': (excel_data, 'test.xlsx')
                            },
                            content_type='multipart/form-data'
                        )
                        
                        assert response.status_code == 200
                        data = response.get_json()
                        assert data['success'] is True
            
            # Step 4: Check processing status
            mock_project.job_id = 'job-123'
            mock_project.status = 'processing'
            
            with patch('models.project.Project.get_by_id', return_value=mock_project):
                with patch('services.ai_foundry_service.AIFoundryService.get_job_status') as mock_status:
                    mock_status.return_value = {
                        'status': 'completed',
                        'progress': 100,
                        'message': 'Processing complete'
                    }
                    
                    response = client.get('/project/test-project-123/status')
                    assert response.status_code == 200
                    data = response.get_json()
                    assert data['status'] == 'completed'
            
            # Step 5: Review annotations
            mock_project.status = 'annotated'
            
            with patch('models.project.Project.get_by_id', return_value=mock_project):
                with patch('app.get_project_annotations') as mock_get_annotations:
                    mock_get_annotations.return_value = [
                        {
                            'page': '1',
                            'data': {
                                'questions': [
                                    {
                                        'id': 'Q1',
                                        'type': 'short_answer',
                                        'bbox': [100, 100, 200, 200],
                                        'confidence': 0.95,
                                        'extracted_text': 'Test question'
                                    }
                                ]
                            },
                            'confidence': 0.95,
                            'created_at': '2023-01-01T00:00:00'
                        }
                    ]
                    
                    response = client.get('/project/test-project-123/annotations')
                    assert response.status_code == 200
                    assert b'Review Annotations' in response.data
            
            # Step 6: Save annotations
            annotations_data = {
                '1': {
                    'questions': [
                        {
                            'id': 'Q1',
                            'type': 'short_answer',
                            'bbox': [100, 100, 200, 200],
                            'confidence': 0.95,
                            'extracted_text': 'Updated question text'
                        }
                    ]
                }
            }
            
            with patch('models.project.Project.get_by_id', return_value=mock_project):
                with patch('app.save_project_annotations') as mock_save:
                    with patch('services.storage_service.StorageService.log_audit') as mock_audit:
                        response = client.post(
                            '/project/test-project-123/annotations',
                            json=annotations_data,
                            content_type='application/json'
                        )
                        
                        assert response.status_code == 200
                        data = response.get_json()
                        assert data['success'] is True
                        
                        # Verify project status updated to scored
                        mock_project.update_status.assert_called_with('scored')

class TestStatusTransitions:
    def test_project_status_transitions(self):
        """Test that project status transitions work correctly"""
        from models.project import Project
        
        # Mock storage service
        with patch('models.project.storage_service') as mock_storage:
            mock_storage.create_entity.return_value = True
            mock_storage.update_entity.return_value = True
            
            # Create project (status: created)
            project = Project.create('Test Project', 'Description', 'user-123')
            assert project.status == 'created'
            
            # Update to processing
            result = project.update_status('processing', 'job-123')
            assert result is True
            assert project.status == 'processing'
            assert project.job_id == 'job-123'
            
            # Update to annotated
            result = project.update_status('annotated')
            assert result is True
            assert project.status == 'annotated'
            
            # Update to scored
            result = project.update_status('scored')
            assert result is True
            assert project.status == 'scored'

class TestDataConsistency:
    def test_annotation_data_consistency(self):
        """Test that annotation data maintains consistency across operations"""
        from app import create_sample_annotations, save_project_annotations, get_project_annotations
        
        # Create sample data
        original_annotations = create_sample_annotations('test-project')
        
        # Verify structure
        assert len(original_annotations) == 2
        for annotation in original_annotations:
            assert 'page' in annotation
            assert 'data' in annotation
            assert 'confidence' in annotation
            assert 'created_at' in annotation
            
            # Verify questions structure
            questions = annotation['data']['questions']
            for question in questions:
                assert all(key in question for key in ['id', 'type', 'bbox', 'confidence', 'extracted_text'])
                assert len(question['bbox']) == 4
        
        # Test save/load cycle
        with patch('services.storage_service.StorageService') as mock_storage:
            with patch('flask_login.current_user') as mock_user:
                mock_user.id = 'test-user'
                mock_storage.create_entity.return_value = True
                
                # Convert to save format
                save_data = {}
                for annotation in original_annotations:
                    save_data[annotation['page']] = annotation['data']
                
                # Save annotations
                save_project_annotations('test-project', save_data)
                
                # Verify save was called correctly
                assert mock_storage.create_entity.call_count == len(original_annotations)

class TestErrorRecovery:
    def test_annotation_error_recovery(self):
        """Test error recovery in annotation operations"""
        from app import get_project_annotations, save_project_annotations
        
        # Test get_project_annotations with storage error
        with patch('services.storage_service.StorageService') as mock_storage:
            mock_storage.query_entities.side_effect = Exception("Storage error")
            
            # Should return sample data on error
            result = get_project_annotations('test-project')
            assert len(result) == 2  # Sample data
            assert result[0]['page'] == '1'
        
        # Test save_project_annotations with storage error
        with patch('services.storage_service.StorageService') as mock_storage:
            with patch('flask_login.current_user') as mock_user:
                mock_user.id = 'test-user'
                mock_storage.create_entity.side_effect = Exception("Save error")
                
                # Should raise exception
                with pytest.raises(Exception) as exc_info:
                    save_project_annotations('test-project', {'1': {}})
                
                assert "Save error" in str(exc_info.value)

class TestPerformance:
    def test_annotation_data_size_limits(self):
        """Test handling of large annotation datasets"""
        from app import create_sample_annotations
        
        # Create sample annotations
        annotations = create_sample_annotations('test-project')
        
        # Verify reasonable data size
        import json
        json_size = len(json.dumps(annotations))
        
        # Should be reasonable size (less than 10KB for sample data)
        assert json_size < 10240
        
        # Verify questions per page is reasonable
        for annotation in annotations:
            questions_count = len(annotation['data']['questions'])
            assert questions_count <= 10  # Reasonable limit

    def test_bbox_coordinate_validation(self):
        """Test that bounding box coordinates are valid"""
        from app import create_sample_annotations
        
        annotations = create_sample_annotations('test-project')
        
        for annotation in annotations:
            for question in annotation['data']['questions']:
                bbox = question['bbox']
                x1, y1, x2, y2 = bbox
                
                # Validate coordinates
                assert x2 > x1, "Width must be positive"
                assert y2 > y1, "Height must be positive"
                assert x1 >= 0, "X coordinate must be non-negative"
                assert y1 >= 0, "Y coordinate must be non-negative"
                assert x2 <= 1000, "X coordinate should be reasonable"
                assert y2 <= 1000, "Y coordinate should be reasonable"
