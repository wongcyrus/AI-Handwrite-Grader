import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from app import app
from models.user import User
from models.project import Project

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def mock_storage():
    """Mock storage service"""
    with patch('services.storage_service.StorageService') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_ai_foundry():
    """Mock AI Foundry service"""
    with patch('services.ai_foundry_service.AIFoundryService') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance

class TestAuth:
    def test_register_success(self, client, mock_storage):
        """Test successful user registration"""
        mock_storage.create_entity.return_value = True
        
        response = client.post('/register', data={
            'email': 'test@example.com',
            'password': 'password123',
            'role': 'teacher'
        })
        
        assert response.status_code == 302  # Redirect after success
        mock_storage.create_entity.assert_called_once()

    def test_register_duplicate_email(self, client, mock_storage):
        """Test registration with existing email"""
        with patch.object(User, 'get_by_email', return_value=Mock()):
            response = client.post('/register', data={
                'email': 'existing@example.com',
                'password': 'password123'
            })
            
            assert b'Email already registered' in response.data

    def test_login_success(self, client):
        """Test successful login"""
        mock_user = Mock()
        mock_user.check_password.return_value = True
        mock_user.id = 'test-user-id'
        
        with patch.object(User, 'get_by_email', return_value=mock_user):
            response = client.post('/login', data={
                'email': 'test@example.com',
                'password': 'password123'
            })
            
            assert response.status_code == 302  # Redirect after success

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        with patch.object(User, 'get_by_email', return_value=None):
            response = client.post('/login', data={
                'email': 'test@example.com',
                'password': 'wrongpassword'
            })
            
            assert b'Invalid email or password' in response.data

class TestProjects:
    def test_create_project_success(self, client, mock_storage):
        """Test successful project creation"""
        mock_user = Mock()
        mock_user.id = 'test-user-id'
        mock_user.is_authenticated = True
        
        mock_project = Mock()
        mock_project.id = 'test-project-id'
        
        with patch('flask_login.current_user', mock_user):
            with patch.object(Project, 'create', return_value=mock_project):
                response = client.post('/project/create', data={
                    'name': 'Test Project',
                    'description': 'Test Description'
                })
                
                assert response.status_code == 302  # Redirect after success

    def test_upload_files_success(self, client, mock_storage, mock_ai_foundry):
        """Test successful file upload"""
        mock_user = Mock()
        mock_user.id = 'test-user-id'
        mock_user.is_authenticated = True
        
        mock_project = Mock()
        mock_project.id = 'test-project-id'
        mock_project.user_id = 'test-user-id'
        mock_project.update_files.return_value = True
        mock_project.update_status.return_value = True
        
        mock_storage.upload_file.return_value = 'https://storage.blob.core.windows.net/test.pdf'
        mock_ai_foundry.start_annotation_job.return_value = 'job-123'
        
        with patch('flask_login.current_user', mock_user):
            with patch.object(Project, 'get_by_id', return_value=mock_project):
                with tempfile.NamedTemporaryFile(suffix='.pdf') as pdf_file:
                    with tempfile.NamedTemporaryFile(suffix='.xlsx') as excel_file:
                        pdf_file.write(b'fake pdf content')
                        excel_file.write(b'fake excel content')
                        pdf_file.seek(0)
                        excel_file.seek(0)
                        
                        response = client.post(f'/project/{mock_project.id}/upload', 
                            data={
                                'pdf_file': (pdf_file, 'test.pdf'),
                                'excel_file': (excel_file, 'test.xlsx')
                            },
                            content_type='multipart/form-data'
                        )
                        
                        assert response.status_code == 200
                        data = response.get_json()
                        assert data['success'] is True
                        assert 'job_id' in data

    def test_upload_files_missing_files(self, client):
        """Test file upload with missing files"""
        mock_user = Mock()
        mock_user.id = 'test-user-id'
        mock_user.is_authenticated = True
        
        mock_project = Mock()
        mock_project.id = 'test-project-id'
        mock_project.user_id = 'test-user-id'
        
        with patch('flask_login.current_user', mock_user):
            with patch.object(Project, 'get_by_id', return_value=mock_project):
                response = client.post(f'/project/{mock_project.id}/upload', 
                    data={},
                    content_type='multipart/form-data'
                )
                
                assert response.status_code == 400
                data = response.get_json()
                assert 'error' in data

class TestModels:
    def test_user_create(self, mock_storage):
        """Test user creation"""
        mock_storage.create_entity.return_value = True
        
        user = User.create('test@example.com', 'password123', 'teacher')
        
        assert user is not None
        assert user.email == 'test@example.com'
        assert user.role == 'teacher'
        mock_storage.create_entity.assert_called_once()

    def test_user_check_password(self):
        """Test password checking"""
        from werkzeug.security import generate_password_hash
        
        password_hash = generate_password_hash('password123')
        user = User('test-id', 'test@example.com', password_hash, 'teacher')
        
        assert user.check_password('password123') is True
        assert user.check_password('wrongpassword') is False

    def test_project_create(self, mock_storage):
        """Test project creation"""
        mock_storage.create_entity.return_value = True
        
        project = Project.create('Test Project', 'Description', 'user-123')
        
        assert project is not None
        assert project.name == 'Test Project'
        assert project.user_id == 'user-123'
        assert project.status == 'created'
        mock_storage.create_entity.assert_called_once()

class TestServices:
    def test_storage_service_create_entity(self):
        """Test storage service entity creation"""
        with patch('azure.data.tables.TableServiceClient') as mock_client:
            mock_table = Mock()
            mock_client.from_connection_string.return_value.get_table_client.return_value = mock_table
            
            from services.storage_service import StorageService
            storage = StorageService()
            
            entity = {'PartitionKey': 'test', 'RowKey': 'test', 'data': 'value'}
            result = storage.create_entity('test_table', entity)
            
            mock_table.create_entity.assert_called_once_with(entity)

    def test_ai_foundry_service_initialization(self):
        """Test AI Foundry service initialization"""
        with patch('azure.ai.projects.AIProjectClient') as mock_client:
            mock_agent = Mock()
            mock_agent.id = 'agent-123'
            mock_client.return_value.agents.create_agent.return_value = mock_agent
            
            from services.ai_foundry_service import AIFoundryService
            service = AIFoundryService()
            
            # Should create 6 specialized agents + 1 main agent
            assert mock_client.return_value.agents.create_agent.call_count == 7

    def test_ai_foundry_start_annotation_job(self):
        """Test starting annotation job"""
        with patch('azure.ai.projects.AIProjectClient') as mock_client:
            mock_thread = Mock()
            mock_thread.id = 'thread-123'
            mock_run = Mock()
            mock_run.id = 'run-123'
            
            mock_client.return_value.agents.threads.create.return_value = mock_thread
            mock_client.return_value.agents.runs.create.return_value = mock_run
            
            from services.ai_foundry_service import AIFoundryService
            service = AIFoundryService()
            
            job_id = service.start_annotation_job('project-123', 'pdf_url', 'excel_url')
            
            assert job_id == 'project-123_thread-123_run-123'
            mock_client.return_value.agents.threads.create.assert_called_once()
            mock_client.return_value.agents.runs.create.assert_called_once()

class TestIntegration:
    def test_full_project_workflow(self, client, mock_storage, mock_ai_foundry):
        """Test complete project workflow"""
        # Setup mocks
        mock_user = Mock()
        mock_user.id = 'test-user-id'
        mock_user.is_authenticated = True
        
        mock_project = Mock()
        mock_project.id = 'test-project-id'
        mock_project.user_id = 'test-user-id'
        mock_project.status = 'created'
        mock_project.update_files.return_value = True
        mock_project.update_status.return_value = True
        
        mock_storage.upload_file.return_value = 'https://storage.blob.core.windows.net/test.pdf'
        mock_ai_foundry.start_annotation_job.return_value = 'job-123'
        mock_ai_foundry.get_job_status.return_value = {'status': 'completed', 'progress': 100}
        
        with patch('flask_login.current_user', mock_user):
            with patch.object(Project, 'create', return_value=mock_project):
                with patch.object(Project, 'get_by_id', return_value=mock_project):
                    # 1. Create project
                    response = client.post('/project/create', data={
                        'name': 'Integration Test Project',
                        'description': 'Test Description'
                    })
                    assert response.status_code == 302
                    
                    # 2. Upload files
                    with tempfile.NamedTemporaryFile(suffix='.pdf') as pdf_file:
                        with tempfile.NamedTemporaryFile(suffix='.xlsx') as excel_file:
                            pdf_file.write(b'fake pdf content')
                            excel_file.write(b'fake excel content')
                            pdf_file.seek(0)
                            excel_file.seek(0)
                            
                            response = client.post(f'/project/{mock_project.id}/upload', 
                                data={
                                    'pdf_file': (pdf_file, 'test.pdf'),
                                    'excel_file': (excel_file, 'test.xlsx')
                                },
                                content_type='multipart/form-data'
                            )
                            
                            assert response.status_code == 200
                            data = response.get_json()
                            assert data['success'] is True
                    
                    # 3. Check status
                    mock_project.job_id = 'job-123'
                    response = client.get(f'/project/{mock_project.id}/status')
                    assert response.status_code == 200
                    data = response.get_json()
                    assert data['status'] == 'completed'
