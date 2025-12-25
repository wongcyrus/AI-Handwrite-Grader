import pytest
from unittest.mock import Mock, patch
from models.user import User
from models.project import Project

class TestUserModel:
    @pytest.fixture
    def mock_storage(self):
        with patch('models.user.storage_service') as mock:
            yield mock

    def test_create_user_success(self, mock_storage):
        """Test successful user creation"""
        mock_storage.create_entity.return_value = True
        
        user = User.create('test@example.com', 'password123', 'teacher')
        
        assert user is not None
        assert user.email == 'test@example.com'
        assert user.role == 'teacher'
        assert user.id is not None
        
        # Verify storage call
        mock_storage.create_entity.assert_called_once()
        call_args = mock_storage.create_entity.call_args[0]
        assert call_args[0] == 'users'  # table name
        entity = call_args[1]
        assert entity['email'] == 'test@example.com'
        assert entity['role'] == 'teacher'
        assert 'password_hash' in entity

    def test_create_user_failure(self, mock_storage):
        """Test user creation failure"""
        mock_storage.create_entity.return_value = False
        
        user = User.create('test@example.com', 'password123', 'teacher')
        
        assert user is None

    def test_get_by_id_success(self, mock_storage):
        """Test successful user retrieval by ID"""
        mock_entity = {
            'RowKey': 'user-123',
            'email': 'test@example.com',
            'password_hash': 'hashed_password',
            'role': 'teacher',
            'created_at': '2023-01-01T00:00:00'
        }
        mock_storage.get_entity.return_value = mock_entity
        
        user = User.get_by_id('user-123')
        
        assert user is not None
        assert user.id == 'user-123'
        assert user.email == 'test@example.com'
        assert user.role == 'teacher'
        
        mock_storage.get_entity.assert_called_once_with('users', 'users', 'user-123')

    def test_get_by_id_not_found(self, mock_storage):
        """Test user retrieval when user not found"""
        mock_storage.get_entity.return_value = None
        
        user = User.get_by_id('nonexistent-user')
        
        assert user is None

    def test_get_by_email_success(self, mock_storage):
        """Test successful user retrieval by email"""
        mock_entity = {
            'RowKey': 'user-123',
            'email': 'test@example.com',
            'password_hash': 'hashed_password',
            'role': 'teacher',
            'created_at': '2023-01-01T00:00:00'
        }
        mock_storage.query_entities.return_value = [mock_entity]
        
        user = User.get_by_email('test@example.com')
        
        assert user is not None
        assert user.id == 'user-123'
        assert user.email == 'test@example.com'
        
        mock_storage.query_entities.assert_called_once_with('users', "email eq 'test@example.com'")

    def test_get_by_email_not_found(self, mock_storage):
        """Test user retrieval by email when user not found"""
        mock_storage.query_entities.return_value = []
        
        user = User.get_by_email('nonexistent@example.com')
        
        assert user is None

    def test_check_password_correct(self):
        """Test password checking with correct password"""
        from werkzeug.security import generate_password_hash
        
        password_hash = generate_password_hash('password123')
        user = User('user-123', 'test@example.com', password_hash, 'teacher')
        
        assert user.check_password('password123') is True

    def test_check_password_incorrect(self):
        """Test password checking with incorrect password"""
        from werkzeug.security import generate_password_hash
        
        password_hash = generate_password_hash('password123')
        user = User('user-123', 'test@example.com', password_hash, 'teacher')
        
        assert user.check_password('wrongpassword') is False

    def test_user_is_authenticated(self):
        """Test that User implements UserMixin correctly"""
        user = User('user-123', 'test@example.com', 'hash', 'teacher')
        
        # UserMixin provides these methods
        assert user.is_authenticated is True
        assert user.is_active is True
        assert user.is_anonymous is False
        assert user.get_id() == 'user-123'

class TestProjectModel:
    @pytest.fixture
    def mock_storage(self):
        with patch('models.project.storage_service') as mock:
            yield mock

    def test_create_project_success(self, mock_storage):
        """Test successful project creation"""
        mock_storage.create_entity.return_value = True
        
        project = Project.create('Test Project', 'Description', 'user-123')
        
        assert project is not None
        assert project.name == 'Test Project'
        assert project.description == 'Description'
        assert project.user_id == 'user-123'
        assert project.status == 'created'
        assert project.id is not None
        
        # Verify storage call
        mock_storage.create_entity.assert_called_once()
        call_args = mock_storage.create_entity.call_args[0]
        assert call_args[0] == 'projects'  # table name
        entity = call_args[1]
        assert entity['name'] == 'Test Project'
        assert entity['user_id'] == 'user-123'

    def test_create_project_failure(self, mock_storage):
        """Test project creation failure"""
        mock_storage.create_entity.return_value = False
        
        project = Project.create('Test Project', 'Description', 'user-123')
        
        assert project is None

    def test_get_by_id_success(self, mock_storage):
        """Test successful project retrieval by ID"""
        mock_entity = {
            'RowKey': 'project-123',
            'name': 'Test Project',
            'description': 'Description',
            'user_id': 'user-123',
            'status': 'created',
            'created_at': '2023-01-01T00:00:00'
        }
        mock_storage.query_entities.return_value = [mock_entity]
        
        project = Project.get_by_id('project-123')
        
        assert project is not None
        assert project.id == 'project-123'
        assert project.name == 'Test Project'
        assert project.user_id == 'user-123'
        
        mock_storage.query_entities.assert_called_once_with('projects', "RowKey eq 'project-123'")

    def test_get_by_id_not_found(self, mock_storage):
        """Test project retrieval when project not found"""
        mock_storage.query_entities.return_value = []
        
        project = Project.get_by_id('nonexistent-project')
        
        assert project is None

    def test_get_by_user_success(self, mock_storage):
        """Test successful project retrieval by user"""
        mock_entities = [
            {
                'RowKey': 'project-1',
                'name': 'Project 1',
                'description': 'Description 1',
                'user_id': 'user-123',
                'status': 'created',
                'created_at': '2023-01-01T00:00:00'
            },
            {
                'RowKey': 'project-2',
                'name': 'Project 2',
                'description': 'Description 2',
                'user_id': 'user-123',
                'status': 'processing',
                'created_at': '2023-01-02T00:00:00'
            }
        ]
        mock_storage.query_entities.return_value = mock_entities
        
        projects = Project.get_by_user('user-123')
        
        assert len(projects) == 2
        assert projects[0].id == 'project-1'
        assert projects[1].id == 'project-2'
        assert all(p.user_id == 'user-123' for p in projects)
        
        mock_storage.query_entities.assert_called_once_with('projects', "PartitionKey eq 'user-123'")

    def test_get_by_user_empty(self, mock_storage):
        """Test project retrieval by user when no projects found"""
        mock_storage.query_entities.return_value = []
        
        projects = Project.get_by_user('user-123')
        
        assert len(projects) == 0

    def test_update_files_success(self, mock_storage):
        """Test successful file update"""
        mock_storage.update_entity.return_value = True
        
        project = Project('project-123', 'Test Project', 'Description', 'user-123')
        result = project.update_files('pdf_url', 'excel_url')
        
        assert result is True
        assert project.pdf_url == 'pdf_url'
        assert project.excel_url == 'excel_url'
        
        mock_storage.update_entity.assert_called_once()

    def test_update_files_failure(self, mock_storage):
        """Test file update failure"""
        mock_storage.update_entity.return_value = False
        
        project = Project('project-123', 'Test Project', 'Description', 'user-123')
        result = project.update_files('pdf_url', 'excel_url')
        
        assert result is False

    def test_update_status_success(self, mock_storage):
        """Test successful status update"""
        mock_storage.update_entity.return_value = True
        
        project = Project('project-123', 'Test Project', 'Description', 'user-123')
        result = project.update_status('processing', 'job-456')
        
        assert result is True
        assert project.status == 'processing'
        assert project.job_id == 'job-456'
        
        mock_storage.update_entity.assert_called_once()

    def test_update_status_without_job_id(self, mock_storage):
        """Test status update without changing job ID"""
        mock_storage.update_entity.return_value = True
        
        project = Project('project-123', 'Test Project', 'Description', 'user-123')
        project.job_id = 'existing-job'
        
        result = project.update_status('completed')
        
        assert result is True
        assert project.status == 'completed'
        assert project.job_id == 'existing-job'  # Should remain unchanged
