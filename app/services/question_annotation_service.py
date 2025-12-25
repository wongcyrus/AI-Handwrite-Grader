"""Question Annotation Microservice for AI Handwriting Grader"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from .storage_service import StorageService


class QuestionAnnotationService:
    """Microservice for question annotation and boundary marking"""
    
    def __init__(self):
        self.storage_service = StorageService()
    
    def create_annotation_session(self, project_id: str, processing_id: str) -> Dict[str, Any]:
        """
        Create a new annotation session for a processed PDF
        
        Args:
            project_id: Project identifier
            processing_id: PDF processing identifier
            
        Returns:
            Dict with session details
        """
        try:
            # Get PDF processing results
            pdf_processing = self.storage_service.get_entity('pdf_processing', project_id, processing_id)
            if not pdf_processing:
                return {'success': False, 'error': 'PDF processing not found'}
            
            # Create annotation session
            session_id = str(uuid.uuid4())
            session_data = {
                'PartitionKey': project_id,
                'RowKey': session_id,
                'processing_id': processing_id,
                'total_pages': pdf_processing.get('total_pages', 0),
                'current_page': 1,
                'annotations': '{}',  # Store as JSON string
                'status': 'created',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self.storage_service.create_entity('annotation_sessions', session_data)
            
            return {
                'success': True,
                'session_id': session_id,
                'total_pages': pdf_processing.get('total_pages', 0),
                'image_urls': eval(pdf_processing.get('image_urls', '[]'))
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def save_page_annotations(self, project_id: str, session_id: str, page: int, annotations: List[Dict]) -> Dict[str, Any]:
        """
        Save annotations for a specific page
        
        Args:
            project_id: Project identifier
            session_id: Annotation session identifier
            page: Page number (1-based)
            annotations: List of annotation objects with x, y, width, height, label
            
        Returns:
            Dict with save result
        """
        try:
            # Get current session
            session = self.storage_service.get_entity('annotation_sessions', project_id, session_id)
            if not session:
                return {'success': False, 'error': 'Annotation session not found'}
            
            # Parse existing annotations
            current_annotations = json.loads(session.get('annotations', '{}'))
            
            # Update annotations for this page
            current_annotations[str(page)] = annotations
            
            # Update session
            updated_session = {
                'PartitionKey': project_id,
                'RowKey': session_id,
                'processing_id': session.get('processing_id'),
                'total_pages': session.get('total_pages'),
                'current_page': page,
                'annotations': json.dumps(current_annotations),
                'status': 'in_progress',
                'created_at': session.get('created_at'),
                'updated_at': datetime.now().isoformat()
            }
            
            self.storage_service.update_entity('annotation_sessions', updated_session)
            
            return {
                'success': True,
                'page': page,
                'annotation_count': len(annotations),
                'total_annotations': sum(len(page_annotations) for page_annotations in current_annotations.values())
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_page_annotations(self, project_id: str, session_id: str, page: int) -> Dict[str, Any]:
        """Get annotations for a specific page"""
        try:
            session = self.storage_service.get_entity('annotation_sessions', project_id, session_id)
            if not session:
                return {'success': False, 'error': 'Annotation session not found'}
            
            annotations = json.loads(session.get('annotations', '{}'))
            page_annotations = annotations.get(str(page), [])
            
            return {
                'success': True,
                'page': page,
                'annotations': page_annotations
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def complete_annotation_session(self, project_id: str, session_id: str) -> Dict[str, Any]:
        """Mark annotation session as complete"""
        try:
            session = self.storage_service.get_entity('annotation_sessions', project_id, session_id)
            if not session:
                return {'success': False, 'error': 'Annotation session not found'}
            
            # Update session status
            updated_session = {
                'PartitionKey': project_id,
                'RowKey': session_id,
                'processing_id': session.get('processing_id'),
                'total_pages': session.get('total_pages'),
                'current_page': session.get('current_page'),
                'annotations': session.get('annotations'),
                'status': 'completed',
                'created_at': session.get('created_at'),
                'updated_at': datetime.now().isoformat(),
                'completed_at': datetime.now().isoformat()
            }
            
            self.storage_service.update_entity('annotation_sessions', updated_session)
            
            # Count total annotations
            annotations = json.loads(session.get('annotations', '{}'))
            total_annotations = sum(len(page_annotations) for page_annotations in annotations.values())
            
            return {
                'success': True,
                'status': 'completed',
                'total_pages': session.get('total_pages'),
                'total_annotations': total_annotations
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_annotation_session(self, project_id: str, session_id: str) -> Dict[str, Any]:
        """Get annotation session details"""
        try:
            session = self.storage_service.get_entity('annotation_sessions', project_id, session_id)
            if not session:
                return {'success': False, 'error': 'Annotation session not found'}
            
            annotations = json.loads(session.get('annotations', '{}'))
            total_annotations = sum(len(page_annotations) for page_annotations in annotations.values())
            
            return {
                'success': True,
                'session_id': session_id,
                'processing_id': session.get('processing_id'),
                'total_pages': session.get('total_pages'),
                'current_page': session.get('current_page'),
                'status': session.get('status'),
                'total_annotations': total_annotations,
                'created_at': session.get('created_at'),
                'updated_at': session.get('updated_at'),
                'completed_at': session.get('completed_at')
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def list_project_sessions(self, project_id: str) -> List[Dict[str, Any]]:
        """List all annotation sessions for a project"""
        try:
            entities = self.storage_service.query_entities(
                'annotation_sessions',
                f"PartitionKey eq '{project_id}'"
            )
            
            sessions = []
            for entity in entities:
                annotations = json.loads(entity.get('annotations', '{}'))
                total_annotations = sum(len(page_annotations) for page_annotations in annotations.values())
                
                sessions.append({
                    'session_id': entity.get('RowKey'),
                    'processing_id': entity.get('processing_id'),
                    'total_pages': entity.get('total_pages'),
                    'status': entity.get('status'),
                    'total_annotations': total_annotations,
                    'created_at': entity.get('created_at'),
                    'updated_at': entity.get('updated_at')
                })
            
            return sessions
            
        except Exception as e:
            print(f"Error listing annotation sessions: {e}")
            return []
