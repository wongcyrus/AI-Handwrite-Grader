import pytest
from services.storage_service import StorageService
import uuid

class TestStorageServiceWithAzurite:
    @pytest.fixture
    def storage_service(self):
        """Create real storage service for Azurite testing"""
        return StorageService()

    def test_create_entity_success(self, storage_service):
        """Test successful entity creation with Azurite"""
        unique_id = str(uuid.uuid4())[:8]
        entity = {'PartitionKey': 'test', 'RowKey': f'test_{unique_id}', 'data': 'value'}
        
        result = storage_service.create_entity('testtable', entity)
        
        assert result is True

    def test_create_entity_already_exists(self, storage_service):
        """Test entity creation when entity already exists"""
        unique_id = str(uuid.uuid4())[:8]
        entity = {'PartitionKey': 'test', 'RowKey': f'duplicate_{unique_id}', 'data': 'value'}
        
        # Create entity first time
        result1 = storage_service.create_entity('testtable', entity)
        assert result1 is True
        
        # Try to create same entity again
        result2 = storage_service.create_entity('testtable', entity)
        assert result2 is False

    def test_get_entity_success(self, storage_service):
        """Test successful entity retrieval"""
        unique_id = str(uuid.uuid4())[:8]
        entity = {'PartitionKey': 'test', 'RowKey': f'get_{unique_id}', 'data': 'value'}
        
        # Create entity first
        storage_service.create_entity('testtable', entity)
        
        # Retrieve entity
        result = storage_service.get_entity('testtable', 'test', f'get_{unique_id}')
        
        assert result is not None
        assert result['PartitionKey'] == 'test'
        assert result['RowKey'] == f'get_{unique_id}'
        assert result['data'] == 'value'

    def test_get_entity_not_found(self, storage_service):
        """Test entity retrieval when entity not found"""
        result = storage_service.get_entity('testtable', 'nonexistent', 'nonexistent')
        
        assert result is None

    def test_query_entities_with_filter(self, storage_service):
        """Test querying entities with filter"""
        unique_id = str(uuid.uuid4())[:8]
        # Create test entities
        entity1 = {'PartitionKey': f'querytest_{unique_id}', 'RowKey': 'test1', 'data': 'value1'}
        entity2 = {'PartitionKey': f'querytest_{unique_id}', 'RowKey': 'test2', 'data': 'value2'}
        
        storage_service.create_entity('testtable', entity1)
        storage_service.create_entity('testtable', entity2)
        
        # Query entities
        result = storage_service.query_entities('testtable', f"PartitionKey eq 'querytest_{unique_id}'")
        
        assert len(result) >= 2
        partition_keys = [entity['PartitionKey'] for entity in result]
        assert all(pk == f'querytest_{unique_id}' for pk in partition_keys)

    def test_update_entity(self, storage_service):
        """Test entity update"""
        unique_id = str(uuid.uuid4())[:8]
        entity = {'PartitionKey': 'test', 'RowKey': f'update_{unique_id}', 'data': 'original_value'}
        
        # Create entity
        storage_service.create_entity('testtable', entity)
        
        # Update entity
        entity['data'] = 'updated_value'
        result = storage_service.update_entity('testtable', entity)
        
        assert result is True
        
        # Verify update
        retrieved = storage_service.get_entity('testtable', 'test', f'update_{unique_id}')
        assert retrieved['data'] == 'updated_value'

    def test_upload_file_success(self, storage_service):
        """Test successful file upload"""
        from unittest.mock import Mock
        
        # Create test containers first
        try:
            storage_service.blob_client.create_container('testcontainer')
        except:
            pass  # Container might already exist
        
        mock_file = Mock()
        mock_file.filename = 'test.txt'
        mock_file.read.return_value = b'test file content'
        
        result = storage_service.upload_file(mock_file, 'testcontainer', 'project-123')
        
        assert result is not None
        assert 'test.txt' in result

    def test_download_file_success(self, storage_service):
        """Test successful file download"""
        from unittest.mock import Mock
        
        # Create test containers first
        try:
            storage_service.blob_client.create_container('testcontainer')
        except:
            pass
        
        # Upload a file first
        mock_file = Mock()
        mock_file.filename = 'download_test.txt'
        mock_file.read.return_value = b'download test content'
        
        storage_service.upload_file(mock_file, 'testcontainer', 'project-123')
        
        # Download the file
        result = storage_service.download_file('testcontainer', 'project-123/download_test.txt')
        
        assert result == b'download test content'

    def test_log_audit(self, storage_service):
        """Test audit logging"""
        result = storage_service.log_audit('user-123', 'test_action', 'project-456', {'test': 'data'})
        
        assert result is True
