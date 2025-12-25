import pytest
from unittest.mock import Mock, patch

class TestTemplateIntegration:
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

    def test_project_detail_template_created_status(self, client):
        """Test project detail template with created status"""
        mock_user = Mock()
        mock_user.id = 'test-user'
        mock_user.is_authenticated = True
        
        mock_project = Mock()
        mock_project.id = 'test-project'
        mock_project.user_id = 'test-user'
        mock_project.name = 'Test Project'
        mock_project.description = 'Test Description'
        mock_project.status = 'created'
        mock_project.created_at = '2023-01-01T00:00:00'
        mock_project.pdf_url = None
        mock_project.excel_url = None
        
        with patch('flask_login.current_user', mock_user):
            with patch('models.project.Project.get_by_id', return_value=mock_project):
                response = client.get('/project/test-project')
                
                assert response.status_code == 200
                assert b'Upload Files' in response.data
                assert b'Test Project' in response.data

    def test_project_detail_template_processing_status(self, client):
        """Test project detail template with processing status"""
        mock_user = Mock()
        mock_user.id = 'test-user'
        mock_user.is_authenticated = True
        
        mock_project = Mock()
        mock_project.id = 'test-project'
        mock_project.user_id = 'test-user'
        mock_project.name = 'Test Project'
        mock_project.description = 'Test Description'
        mock_project.status = 'processing'
        mock_project.created_at = '2023-01-01T00:00:00'
        mock_project.pdf_url = 'test.pdf'
        mock_project.excel_url = 'test.xlsx'
        
        with patch('flask_login.current_user', mock_user):
            with patch('models.project.Project.get_by_id', return_value=mock_project):
                response = client.get('/project/test-project')
                
                assert response.status_code == 200
                assert b'AI Processing Status' in response.data
                assert b'progress-bar' in response.data

    def test_project_detail_template_annotated_status(self, client):
        """Test project detail template with annotated status"""
        mock_user = Mock()
        mock_user.id = 'test-user'
        mock_user.is_authenticated = True
        
        mock_project = Mock()
        mock_project.id = 'test-project'
        mock_project.user_id = 'test-user'
        mock_project.name = 'Test Project'
        mock_project.description = 'Test Description'
        mock_project.status = 'annotated'
        mock_project.created_at = '2023-01-01T00:00:00'
        mock_project.pdf_url = 'test.pdf'
        mock_project.excel_url = 'test.xlsx'
        
        with patch('flask_login.current_user', mock_user):
            with patch('models.project.Project.get_by_id', return_value=mock_project):
                response = client.get('/project/test-project')
                
                assert response.status_code == 200
                assert b'Review AI Annotations' in response.data
                assert b'Review Annotations' in response.data

    def test_annotation_template_renders_with_data(self, client):
        """Test annotation template renders with annotation data"""
        mock_user = Mock()
        mock_user.id = 'test-user'
        mock_user.is_authenticated = True
        
        mock_project = Mock()
        mock_project.id = 'test-project'
        mock_project.user_id = 'test-user'
        mock_project.name = 'Test Project'
        mock_project.status = 'annotated'
        
        mock_annotations = [
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
        
        with patch('flask_login.current_user', mock_user):
            with patch('models.project.Project.get_by_id', return_value=mock_project):
                with patch('app.get_project_annotations', return_value=mock_annotations):
                    response = client.get('/project/test-project/annotations')
                    
                    assert response.status_code == 200
                    assert b'Review Annotations' in response.data
                    assert b'Annotation Tools' in response.data
                    assert b'Page 1' in response.data

class TestFileUploadIntegration:
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

    def test_file_upload_form_validation(self, client):
        """Test file upload form validation"""
        mock_user = Mock()
        mock_user.id = 'test-user'
        mock_user.is_authenticated = True
        
        mock_project = Mock()
        mock_project.id = 'test-project'
        mock_project.user_id = 'test-user'
        
        with patch('flask_login.current_user', mock_user):
            with patch('models.project.Project.get_by_id', return_value=mock_project):
                # Test with no files
                response = client.post('/project/test-project/upload', data={})
                assert response.status_code == 400
                
                data = response.get_json()
                assert 'error' in data

    def test_file_upload_success_flow(self, client):
        """Test successful file upload flow"""
        import tempfile
        import io
        
        mock_user = Mock()
        mock_user.id = 'test-user'
        mock_user.is_authenticated = True
        
        mock_project = Mock()
        mock_project.id = 'test-project'
        mock_project.user_id = 'test-user'
        mock_project.update_files = Mock(return_value=True)
        mock_project.update_status = Mock(return_value=True)
        
        with patch('flask_login.current_user', mock_user):
            with patch('models.project.Project.get_by_id', return_value=mock_project):
                with patch('services.storage_service.StorageService.upload_file') as mock_upload:
                    with patch('services.ai_foundry_service.AIFoundryService.start_annotation_job') as mock_job:
                        mock_upload.return_value = 'https://storage.blob.core.windows.net/test.pdf'
                        mock_job.return_value = 'job-123'
                        
                        # Create fake files
                        pdf_data = io.BytesIO(b'fake pdf content')
                        excel_data = io.BytesIO(b'fake excel content')
                        
                        response = client.post('/project/test-project/upload', 
                            data={
                                'pdf_file': (pdf_data, 'test.pdf'),
                                'excel_file': (excel_data, 'test.xlsx')
                            },
                            content_type='multipart/form-data'
                        )
                        
                        assert response.status_code == 200
                        data = response.get_json()
                        assert data['success'] is True
                        assert 'job_id' in data

class TestResponsiveDesign:
    def test_css_file_exists(self):
        """Test that CSS file exists and contains responsive rules"""
        import os
        css_path = '/home/developer/Documents/data-disk/AI-Handwrite-Grader/app/static/css/style.css'
        
        assert os.path.exists(css_path)
        
        with open(css_path, 'r') as f:
            css_content = f.read()
            
        # Check for responsive design elements
        assert '@media' in css_content
        assert 'max-width: 768px' in css_content
        assert '.sticky-top' in css_content

class TestErrorHandling:
    @pytest.fixture
    def client(self):
        """Create test client"""
        from app import app
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret'
        
        with app.test_client() as client:
            with app.app_context():
                yield client

    def test_unauthorized_access_redirects(self, client):
        """Test that unauthorized access redirects to login"""
        response = client.get('/project/test-project')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_project_not_found_handling(self, client):
        """Test project not found error handling"""
        mock_user = Mock()
        mock_user.id = 'test-user'
        mock_user.is_authenticated = True
        
        with patch('flask_login.current_user', mock_user):
            with patch('models.project.Project.get_by_id', return_value=None):
                response = client.get('/project/nonexistent')
                assert response.status_code == 302  # Redirect to dashboard

    def test_wrong_user_access_denied(self, client):
        """Test that users can't access other users' projects"""
        mock_user = Mock()
        mock_user.id = 'test-user'
        mock_user.is_authenticated = True
        
        mock_project = Mock()
        mock_project.id = 'test-project'
        mock_project.user_id = 'other-user'  # Different user
        
        with patch('flask_login.current_user', mock_user):
            with patch('models.project.Project.get_by_id', return_value=mock_project):
                response = client.get('/project/test-project')
                assert response.status_code == 302  # Redirect to dashboard

class TestJavaScriptIntegration:
    def test_annotation_template_has_javascript(self):
        """Test that annotation template includes necessary JavaScript"""
        template_path = '/home/developer/Documents/data-disk/AI-Handwrite-Grader/app/templates/project/annotations.html'
        
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Check for key JavaScript functionality
        assert 'currentAnnotations' in template_content
        assert 'loadPage' in template_content
        assert 'saveAnnotations' in template_content
        assert 'displayAnnotations' in template_content
        assert 'fetch(' in template_content

    def test_project_detail_has_upload_javascript(self):
        """Test that project detail template includes upload JavaScript"""
        template_path = '/home/developer/Documents/data-disk/AI-Handwrite-Grader/app/templates/project/detail.html'
        
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Check for upload functionality
        assert 'uploadForm' in template_content
        assert 'FormData' in template_content
        assert 'updateStatus' in template_content
        assert 'setInterval' in template_content
