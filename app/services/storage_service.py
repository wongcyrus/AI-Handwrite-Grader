import os
from azure.data.tables import TableServiceClient
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError
import json
from datetime import datetime

class StorageService:
    def __init__(self):
        connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
        self.table_client = TableServiceClient.from_connection_string(connection_string)
        self.blob_client = BlobServiceClient.from_connection_string(connection_string)
    
    def create_entity(self, table_name, entity):
        """Create entity in table storage"""
        try:
            table_client = self.table_client.get_table_client(table_name)
            table_client.create_entity(entity)
            return True
        except ResourceExistsError:
            return False
        except Exception as e:
            print(f"Error creating entity: {e}")
            return False
    
    def get_entity(self, table_name, partition_key, row_key):
        """Get entity from table storage"""
        try:
            table_client = self.table_client.get_table_client(table_name)
            return table_client.get_entity(partition_key, row_key)
        except Exception:
            return None
    
    def query_entities(self, table_name, filter_query=None):
        """Query entities from table storage"""
        try:
            table_client = self.table_client.get_table_client(table_name)
            if filter_query:
                return list(table_client.query_entities(filter_query))
            return list(table_client.list_entities())
        except Exception as e:
            print(f"Error querying entities: {e}")
            return []
    
    def update_entity(self, table_name, entity):
        """Update entity in table storage"""
        try:
            table_client = self.table_client.get_table_client(table_name)
            table_client.update_entity(entity, mode='merge')
            return True
        except Exception as e:
            print(f"Error updating entity: {e}")
            return False
    
    def upload_file(self, file, container_name, project_id):
        """Upload file to blob storage"""
        try:
            blob_name = f"{project_id}/{file.filename}"
            blob_client = self.blob_client.get_blob_client(
                container=container_name, 
                blob=blob_name
            )
            blob_client.upload_blob(file.read(), overwrite=True)
            return blob_client.url
        except Exception as e:
            print(f"Error uploading file: {e}")
            raise e
    
    def download_file(self, container_name, blob_name):
        """Download file from blob storage"""
        try:
            blob_client = self.blob_client.get_blob_client(
                container=container_name, 
                blob=blob_name
            )
            return blob_client.download_blob().readall()
        except Exception as e:
            print(f"Error downloading file: {e}")
            return None
    
    def log_audit(self, user_id, action, project_id=None, details=None):
        """Log audit trail"""
        entity = {
            'PartitionKey': datetime.now().strftime('%Y-%m-%d'),
            'RowKey': f"{datetime.now().isoformat()}_{user_id}",
            'user_id': user_id,
            'action': action,
            'project_id': project_id or '',
            'details': json.dumps(details) if details else '',
            'timestamp': datetime.now().isoformat()
        }
        return self.create_entity('auditlog', entity)
