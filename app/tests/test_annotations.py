import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime

class TestAnnotationRoutes:
    @pytest.fixture
    def client(self):
        """Create test client"""
        from app import app
        
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret'
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['LOGIN_DISABLED'] = True
        
        with app.test_client() as client:
            with app.app_context():
                yield client

    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user"""
        user = Mock()
        user.id = 'test-user-123'
        user.is_authenticated = True
        return user

    @pytest.fixture
    def mock_project(self):
        """Mock project"""
        project = Mock()
        project.id = 'test-project-123'
        project.user_id = 'test-user-123'
        project.name = 'Test Project'
        project.status = 'annotated'
        return project

    def test_review_annotations_success(self, client, mock_user, mock_project):
        """Test successful annotation review page load"""
        with patch('flask_login.login_required', lambda f: f):  # Disable login_required
            with patch('flask_login.current_user', mock_user):
                with patch('models.project.Project.get_by_id', return_value=mock_project):
                    with patch('app.get_project_annotations') as mock_get_annotations:
                        mock_get_annotations.return_value = [
                            {
                                'page': '1',
                                'data': {'questions': []},
                                'confidence': 0.9,
                                'created_at': '2023-01-01T00:00:00'
                            }
                        ]
                        
                        response = client.get('/project/test-project-123/annotations')
                        assert response.status_code == 200

    def test_review_annotations_project_not_found(self, client, mock_user):
        """Test annotation review with non-existent project"""
        with patch('flask_login.current_user', mock_user):
            with patch('models.project.Project.get_by_id', return_value=None):
                response = client.get('/project/nonexistent/annotations')
                assert response.status_code == 302  # Redirect

    def test_review_annotations_wrong_status(self, client, mock_user, mock_project):
        """Test annotation review with wrong project status"""
        mock_project.status = 'created'
        
        with patch('flask_login.current_user', mock_user):
            with patch('models.project.Project.get_by_id', return_value=mock_project):
                response = client.get('/project/test-project-123/annotations')
                assert response.status_code == 302  # Redirect

    def test_save_annotations_success(self, client, mock_user, mock_project):
        """Test successful annotation saving"""
        annotations_data = {
            '1': {
                'questions': [
                    {
                        'id': 'Q1',
                        'bbox': [100, 100, 200, 200],
                        'confidence': 0.95
                    }
                ]
            }
        }
        
        with patch('flask_login.login_required', lambda f: f):  # Disable login_required
            with patch('flask_login.current_user', mock_user):
                with patch('models.project.Project.get_by_id', return_value=mock_project):
                    with patch('app.save_project_annotations') as mock_save:
                        with patch.object(mock_project, 'update_status') as mock_update:
                            with patch('services.storage_service.StorageService.log_audit') as mock_audit:
                                response = client.post(
                                    '/project/test-project-123/annotations',
                                    json=annotations_data,
                                    content_type='application/json'
                                )
                                
                                assert response.status_code == 200
                                data = response.get_json()
                                assert data['success'] is True
                                
                                mock_save.assert_called_once()
                                mock_update.assert_called_once_with('scored')
                                mock_audit.assert_called_once()

    def test_save_annotations_project_not_found(self, client, mock_user):
        """Test annotation saving with non-existent project"""
        with patch('flask_login.login_required', lambda f: f):  # Disable login_required
            with patch('flask_login.current_user', mock_user):
                with patch('models.project.Project.get_by_id', return_value=None):
                    response = client.post(
                        '/project/nonexistent/annotations',
                        json={},
                        content_type='application/json'
                    )
                    assert response.status_code == 404

    def test_save_annotations_exception(self, client, mock_user, mock_project):
        """Test annotation saving with exception"""
        with patch('flask_login.login_required', lambda f: f):  # Disable login_required
            with patch('flask_login.current_user', mock_user):
                with patch('models.project.Project.get_by_id', return_value=mock_project):
                    with patch('app.save_project_annotations', side_effect=Exception("Save error")):
                        response = client.post(
                            '/project/test-project-123/annotations',
                            json={'1': {'questions': []}},
                            content_type='application/json'
                        )
                        
                        assert response.status_code == 500
                        data = response.get_json()
                        assert 'error' in data

class TestAnnotationHelpers:
    @pytest.fixture
    def mock_storage(self):
        """Mock storage service"""
        with patch('app.storage_service') as mock:
            yield mock

    def test_get_project_annotations_with_data(self, mock_storage):
        """Test getting annotations when data exists"""
        from app import get_project_annotations
        
        mock_entities = [
            {
                'RowKey': '1',
                'annotation_data': json.dumps({
                    'questions': [{'id': 'Q1', 'confidence': 0.9}]
                }),
                'confidence': 0.9,
                'created_at': '2023-01-01T00:00:00'
            }
        ]
        mock_storage.query_entities.return_value = mock_entities
        
        result = get_project_annotations('test-project')
        
        assert len(result) == 1
        assert result[0]['page'] == '1'
        assert result[0]['confidence'] == 0.9
        mock_storage.query_entities.assert_called_once()

    def test_get_project_annotations_no_data(self, mock_storage):
        """Test getting annotations when no data exists (returns sample)"""
        from app import get_project_annotations
        
        mock_storage.query_entities.return_value = []
        
        result = get_project_annotations('test-project')
        
        # Should return sample data
        assert len(result) == 2
        assert result[0]['page'] == '1'
        assert result[1]['page'] == '2'

    def test_get_project_annotations_exception(self, mock_storage):
        """Test getting annotations with exception (returns sample)"""
        from app import get_project_annotations
        
        mock_storage.query_entities.side_effect = Exception("Query error")
        
        result = get_project_annotations('test-project')
        
        # Should return sample data on exception
        assert len(result) == 2

    def test_save_project_annotations_success(self, mock_storage):
        """Test saving annotations successfully"""
        from app import save_project_annotations
        
        annotations_data = {
            '1': {
                'questions': [{'id': 'Q1', 'confidence': 0.9}],
                'confidence': 0.9
            }
        }
        
        with patch('flask_login.current_user') as mock_user:
            mock_user.id = 'test-user'
            mock_user.is_authenticated = True
            
            save_project_annotations('test-project', annotations_data)
            
            mock_storage.create_entity.assert_called_once()
            call_args = mock_storage.create_entity.call_args[0]
            assert call_args[0] == 'annotations'
            entity = call_args[1]
            assert entity['PartitionKey'] == 'test-project'
            assert entity['RowKey'] == '1'

    def test_save_project_annotations_exception(self, mock_storage):
        """Test saving annotations with exception"""
        from app import save_project_annotations
        
        mock_storage.create_entity.side_effect = Exception("Save error")
        
        with patch('flask_login.current_user') as mock_user:
            mock_user.id = 'test-user'
            
            with pytest.raises(Exception) as exc_info:
                save_project_annotations('test-project', {'1': {}})
            
            assert "Save error" in str(exc_info.value)

    def test_create_sample_annotations(self):
        """Test sample annotation creation"""
        from app import create_sample_annotations
        
        result = create_sample_annotations('test-project')
        
        assert len(result) == 2
        assert result[0]['page'] == '1'
        assert result[1]['page'] == '2'
        
        # Check structure
        assert 'data' in result[0]
        assert 'questions' in result[0]['data']
        assert 'confidence' in result[0]
        assert 'created_at' in result[0]
        
        # Check question structure
        question = result[0]['data']['questions'][0]
        assert 'id' in question
        assert 'type' in question
        assert 'bbox' in question
        assert 'confidence' in question
        assert 'extracted_text' in question

class TestTemplateRendering:
    @pytest.fixture
    def client(self):
        """Create test client"""
        from app import app
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            with app.app_context():
                yield client

    def test_login_template_renders(self, client):
        """Test login template renders without errors"""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Sign In' in response.data

    def test_register_template_renders(self, client):
        """Test register template renders without errors"""
        response = client.get('/register')
        assert response.status_code == 200
        assert b'Register' in response.data

    def test_index_template_renders(self, client):
        """Test index template renders without errors"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'AI Handwriting Grader' in response.data

class TestProjectStatusUpdates:
    def test_project_status_completed_updates_to_annotated(self):
        """Test that completed AI processing updates project status"""
        from app import project_status
        
        mock_project = Mock()
        mock_project.id = 'test-project'
        mock_project.user_id = 'test-user'
        mock_project.job_id = 'test-job'
        mock_project.update_status = Mock()
        
        mock_user = Mock()
        mock_user.id = 'test-user'
        
        mock_status = {
            'status': 'completed',
            'progress': 100,
            'message': 'Processing complete'
        }
        
        with patch('flask_login.login_required', lambda f: f):  # Disable login_required
            with patch('flask_login.current_user', mock_user):
                with patch('models.project.Project.get_by_id', return_value=mock_project):
                    with patch('services.ai_foundry_service.AIFoundryService.get_job_status', return_value=mock_status):
                        from flask import Flask
                        app = Flask(__name__)
                        
                        with app.test_request_context():
                            result = project_status('test-project')
                            
                            # Should update project status to annotated
                            mock_project.update_status.assert_called_once_with('annotated')

class TestAnnotationDataStructure:
    def test_annotation_json_structure(self):
        """Test that annotation data follows expected JSON structure"""
        from app import create_sample_annotations
        
        annotations = create_sample_annotations('test-project')
        
        for annotation in annotations:
            # Validate top-level structure
            assert isinstance(annotation['page'], str)
            assert isinstance(annotation['data'], dict)
            assert isinstance(annotation['confidence'], float)
            assert isinstance(annotation['created_at'], str)
            
            # Validate questions structure
            questions = annotation['data']['questions']
            assert isinstance(questions, list)
            
            for question in questions:
                assert isinstance(question['id'], str)
                assert isinstance(question['type'], str)
                assert isinstance(question['bbox'], list)
                assert len(question['bbox']) == 4  # [x1, y1, x2, y2]
                assert isinstance(question['confidence'], float)
                assert isinstance(question['extracted_text'], str)
                
                # Validate bbox coordinates
                x1, y1, x2, y2 = question['bbox']
                assert x2 > x1  # Width > 0
                assert y2 > y1  # Height > 0
