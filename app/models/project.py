from services.storage_service import StorageService
import uuid
import json
from datetime import datetime

storage_service = StorageService()

class Project:
    def __init__(self, id, name, description, user_id, status='created', 
                 pdf_url=None, excel_url=None, job_id=None, created_at=None):
        self.id = id
        self.name = name
        self.description = description
        self.user_id = user_id
        self.status = status  # created, processing, annotated, scored, completed
        self.pdf_url = pdf_url
        self.excel_url = excel_url
        self.job_id = job_id
        self.created_at = created_at or datetime.now().isoformat()
    
    @staticmethod
    def create(name, description, user_id):
        project_id = str(uuid.uuid4())
        
        entity = {
            'PartitionKey': user_id,
            'RowKey': project_id,
            'name': name,
            'description': description,
            'user_id': user_id,
            'status': 'created',
            'created_at': datetime.now().isoformat()
        }
        
        if storage_service.create_entity('projects', entity):
            return Project(project_id, name, description, user_id)
        return None
    
    @staticmethod
    def get_by_id(project_id):
        # Need to query across all partitions to find project
        entities = storage_service.query_entities('projects', f"RowKey eq '{project_id}'")
        if entities:
            entity = entities[0]
            return Project(
                entity['RowKey'],
                entity['name'],
                entity['description'],
                entity['user_id'],
                entity.get('status', 'created'),
                entity.get('pdf_url'),
                entity.get('excel_url'),
                entity.get('job_id'),
                entity.get('created_at')
            )
        return None
    
    @staticmethod
    def get_by_user(user_id):
        entities = storage_service.query_entities('projects', f"PartitionKey eq '{user_id}'")
        projects = []
        for entity in entities:
            projects.append(Project(
                entity['RowKey'],
                entity['name'],
                entity['description'],
                entity['user_id'],
                entity.get('status', 'created'),
                entity.get('pdf_url'),
                entity.get('excel_url'),
                entity.get('job_id'),
                entity.get('created_at')
            ))
        return projects
    
    def update_files(self, pdf_url, excel_url):
        entity = {
            'PartitionKey': self.user_id,
            'RowKey': self.id,
            'name': self.name,
            'description': self.description,
            'user_id': self.user_id,
            'status': self.status,
            'pdf_url': pdf_url,
            'excel_url': excel_url,
            'job_id': self.job_id,
            'created_at': self.created_at,
            'updated_at': datetime.now().isoformat()
        }
        
        if storage_service.update_entity('projects', entity):
            self.pdf_url = pdf_url
            self.excel_url = excel_url
            return True
        return False
    
    def update_status(self, status, job_id=None):
        entity = {
            'PartitionKey': self.user_id,
            'RowKey': self.id,
            'name': self.name,
            'description': self.description,
            'user_id': self.user_id,
            'status': status,
            'pdf_url': self.pdf_url,
            'excel_url': self.excel_url,
            'job_id': job_id or self.job_id,
            'created_at': self.created_at,
            'updated_at': datetime.now().isoformat()
        }
        
        if storage_service.update_entity('projects', entity):
            self.status = status
            if job_id:
                self.job_id = job_id
            return True
        return False
