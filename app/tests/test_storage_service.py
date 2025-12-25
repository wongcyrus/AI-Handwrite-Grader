import pytest
from unittest.mock import Mock, patch, MagicMock
from services.storage_service import StorageService
from azure.core.exceptions import ResourceExistsError

class TestStorageService:
    @pytest.fixture
    def mock_table_client(self):
        with patch('azure.data.tables.TableServiceClient') as mock:
            mock_instance = Mock()
            mock.from_connection_string.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def mock_blob_client(self):
        with patch('azure.storage.blob.BlobServiceClient') as mock:
            mock_instance = Mock()
            mock.from_connection_string.return_value = mock_instance
            yield mock_instance

    def test_create_entity_success(self, mock_table_client):
        """Test successful entity creation"""
        mock_table = Mock()
        mock_table_client.get_table_client.return_value = mock_table
        
        storage = StorageService()
        entity = {'PartitionKey': 'test', 'RowKey': 'test', 'data': 'value'}
        
        result = storage.create_entity('test_table', entity)
        
        assert result is True
        mock_table.create_entity.assert_called_once_with(entity)

    def test_create_entity_already_exists(self, mock_table_client):
        """Test entity creation when entity already exists"""
        mock_table = Mock()
        mock_table.create_entity.side_effect = ResourceExistsError("Entity exists")
        mock_table_client.get_table_client.return_value = mock_table
        
        storage = StorageService()
        entity = {'PartitionKey': 'test', 'RowKey': 'test', 'data': 'value'}
        
        result = storage.create_entity('test_table', entity)
        
        assert result is False

    def test_get_entity_success(self, mock_table_client):
        """Test successful entity retrieval"""
        mock_table = Mock()
        expected_entity = {'PartitionKey': 'test', 'RowKey': 'test', 'data': 'value'}
        mock_table.get_entity.return_value = expected_entity
        mock_table_client.get_table_client.return_value = mock_table
        
        storage = StorageService()
        result = storage.get_entity('test_table', 'test', 'test')
        
        assert result == expected_entity
        mock_table.get_entity.assert_called_once_with('test', 'test')

    def test_get_entity_not_found(self, mock_table_client):
        """Test entity retrieval when entity not found"""
        mock_table = Mock()
        mock_table.get_entity.side_effect = Exception("Not found")
        mock_table_client.get_table_client.return_value = mock_table
        
        storage = StorageService()
        result = storage.get_entity('test_table', 'test', 'test')
        
        assert result is None

    def test_query_entities_with_filter(self, mock_table_client):
        """Test querying entities with filter"""
        mock_table = Mock()
        expected_entities = [
            {'PartitionKey': 'test', 'RowKey': 'test1', 'data': 'value1'},
            {'PartitionKey': 'test', 'RowKey': 'test2', 'data': 'value2'}
        ]
        mock_table.query_entities.return_value = expected_entities
        mock_table_client.get_table_client.return_value = mock_table
        
        storage = StorageService()
        result = storage.query_entities('test_table', "PartitionKey eq 'test'")
        
        assert result == expected_entities
        mock_table.query_entities.assert_called_once_with("PartitionKey eq 'test'")

    def test_upload_file_success(self, mock_blob_client):
        """Test successful file upload"""
        mock_blob = Mock()
        mock_blob.url = 'https://storage.blob.core.windows.net/container/test.pdf'
        mock_blob_client.get_blob_client.return_value = mock_blob
        
        storage = StorageService()
        
        # Mock file object
        mock_file = Mock()
        mock_file.filename = 'test.pdf'
        mock_file.read.return_value = b'fake pdf content'
        
        result = storage.upload_file(mock_file, 'pdfs', 'project-123')
        
        assert result == 'https://storage.blob.core.windows.net/container/test.pdf'
        mock_blob.upload_blob.assert_called_once_with(b'fake pdf content', overwrite=True)

    def test_download_file_success(self, mock_blob_client):
        """Test successful file download"""
        mock_blob = Mock()
        mock_download = Mock()
        mock_download.readall.return_value = b'file content'
        mock_blob.download_blob.return_value = mock_download
        mock_blob_client.get_blob_client.return_value = mock_blob
        
        storage = StorageService()
        result = storage.download_file('pdfs', 'project-123/test.pdf')
        
        assert result == b'file content'
        mock_blob.download_blob.assert_called_once()

    def test_log_audit(self, mock_table_client):
        """Test audit logging"""
        mock_table = Mock()
        mock_table_client.get_table_client.return_value = mock_table
        
        storage = StorageService()
        result = storage.log_audit('user-123', 'login', 'project-456', {'ip': '127.0.0.1'})
        
        assert result is True
        mock_table.create_entity.assert_called_once()
        
        # Verify the entity structure
        call_args = mock_table.create_entity.call_args[0][0]
        assert call_args['user_id'] == 'user-123'
        assert call_args['action'] == 'login'
        assert call_args['project_id'] == 'project-456'
        assert 'timestamp' in call_args
