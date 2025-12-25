from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from services.storage_service import StorageService
import uuid
from datetime import datetime

storage_service = StorageService()

class User(UserMixin):
    def __init__(self, id, email, password_hash, role, created_at=None):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.role = role  # admin, teacher, grader
        self.created_at = created_at or datetime.now().isoformat()
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def create(email, password, role='teacher'):
        user_id = str(uuid.uuid4())
        password_hash = generate_password_hash(password)
        
        entity = {
            'PartitionKey': 'users',
            'RowKey': user_id,
            'email': email,
            'password_hash': password_hash,
            'role': role,
            'created_at': datetime.now().isoformat()
        }
        
        if storage_service.create_entity('users', entity):
            return User(user_id, email, password_hash, role)
        return None
    
    @staticmethod
    def get_by_id(user_id):
        entity = storage_service.get_entity('users', 'users', user_id)
        if entity:
            return User(
                entity['RowKey'],
                entity['email'],
                entity['password_hash'],
                entity['role'],
                entity.get('created_at')
            )
        return None
    
    @staticmethod
    def get_by_email(email):
        entities = storage_service.query_entities('users', f"email eq '{email}'")
        if entities:
            entity = entities[0]
            return User(
                entity['RowKey'],
                entity['email'],
                entity['password_hash'],
                entity['role'],
                entity.get('created_at')
            )
        return None
