"""AI Scoring Microservice for AI Handwriting Grader"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from .storage_service import StorageService
from .ai_foundry_service import AIFoundryService


class AIScoringService:
    """Microservice for AI-powered answer extraction and scoring"""
    
    def __init__(self):
        self.storage_service = StorageService()
        self.ai_foundry_service = AIFoundryService()
        self.default_confidence_threshold = 0.8  # 80% default threshold
    
    def create_scoring_session(self, project_id: str, annotation_session_id: str, 
                             confidence_threshold: float = None) -> Dict[str, Any]:
        """
        Create a new AI scoring session
        
        Args:
            project_id: Project identifier
            annotation_session_id: Completed annotation session
            confidence_threshold: Custom confidence threshold (default 80%)
            
        Returns:
            Dict with session details
        """
        try:
            # Get annotation session
            annotation_session = self.storage_service.get_entity(
                'annotation_sessions', project_id, annotation_session_id
            )
            if not annotation_session or annotation_session.get('status') != 'completed':
                return {'success': False, 'error': 'Annotation session not found or not completed'}
            
            # Create scoring session
            session_id = str(uuid.uuid4())
            threshold = confidence_threshold or self.default_confidence_threshold
            
            session_data = {
                'PartitionKey': project_id,
                'RowKey': session_id,
                'annotation_session_id': annotation_session_id,
                'confidence_threshold': threshold,
                'status': 'created',
                'total_questions': 0,
                'processed_questions': 0,
                'low_confidence_count': 0,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self.storage_service.create_entity('scoring_sessions', session_data)
            
            return {
                'success': True,
                'session_id': session_id,
                'confidence_threshold': threshold,
                'status': 'created'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def extract_and_score_questions(self, project_id: str, session_id: str) -> Dict[str, Any]:
        """
        Extract answers from annotated questions and generate AI scores
        
        Args:
            project_id: Project identifier
            session_id: Scoring session identifier
            
        Returns:
            Dict with extraction and scoring results
        """
        try:
            # Get scoring session
            session = self.storage_service.get_entity('scoring_sessions', project_id, session_id)
            if not session:
                return {'success': False, 'error': 'Scoring session not found'}
            
            # Get annotation data
            annotation_session = self.storage_service.get_entity(
                'annotation_sessions', project_id, session['annotation_session_id']
            )
            
            annotations = json.loads(annotation_session.get('annotations', '{}'))
            confidence_threshold = session.get('confidence_threshold', self.default_confidence_threshold)
            
            # Process each page and extract questions
            all_questions = []
            low_confidence_count = 0
            
            for page_num, page_annotations in annotations.items():
                for annotation in page_annotations:
                    # Simulate AI extraction and scoring
                    # In real implementation, this would call AI Foundry agents
                    question_result = self._process_question_annotation(
                        project_id, page_num, annotation, confidence_threshold
                    )
                    
                    all_questions.append(question_result)
                    
                    if question_result['confidence'] < confidence_threshold:
                        low_confidence_count += 1
            
            # Update session with results
            updated_session = {
                'PartitionKey': project_id,
                'RowKey': session_id,
                'annotation_session_id': session['annotation_session_id'],
                'confidence_threshold': confidence_threshold,
                'status': 'processed',
                'total_questions': len(all_questions),
                'processed_questions': len(all_questions),
                'low_confidence_count': low_confidence_count,
                'questions_data': json.dumps(all_questions),
                'created_at': session.get('created_at'),
                'updated_at': datetime.now().isoformat(),
                'processed_at': datetime.now().isoformat()
            }
            
            self.storage_service.update_entity('scoring_sessions', updated_session)
            
            return {
                'success': True,
                'total_questions': len(all_questions),
                'low_confidence_count': low_confidence_count,
                'confidence_threshold': confidence_threshold,
                'questions': all_questions
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _process_question_annotation(self, project_id: str, page_num: str, 
                                   annotation: Dict, confidence_threshold: float) -> Dict[str, Any]:
        """
        Process a single question annotation with AI extraction and scoring
        
        This is a simplified implementation. In production, this would:
        1. Extract the question region from the image
        2. Use OCR to extract text
        3. Use AI to understand and score the answer
        4. Return confidence scores
        """
        # Simulate AI processing with realistic confidence scores
        import random
        
        # Generate realistic confidence based on question type
        if annotation['label'] in ['NAME', 'ID', 'CLASS']:
            # Metadata fields typically have higher confidence
            base_confidence = 0.9 + random.uniform(-0.1, 0.05)
        else:
            # Question answers have more variable confidence
            base_confidence = 0.7 + random.uniform(-0.2, 0.25)
        
        confidence = max(0.1, min(0.99, base_confidence))
        
        # Simulate extracted answer text
        if annotation['label'] == 'NAME':
            extracted_text = "John Smith"
        elif annotation['label'] == 'ID':
            extracted_text = "12345678"
        elif annotation['label'] == 'CLASS':
            extracted_text = "CS101"
        else:
            extracted_text = f"Sample answer for {annotation['label']}"
        
        # Simulate AI scoring (0-100 scale)
        if confidence > 0.8:
            ai_score = random.randint(75, 100)
        elif confidence > 0.6:
            ai_score = random.randint(50, 85)
        else:
            ai_score = random.randint(20, 70)
        
        return {
            'question_id': str(uuid.uuid4()),
            'page': int(page_num),
            'label': annotation['label'],
            'bbox': {
                'x': annotation['x'],
                'y': annotation['y'],
                'width': annotation['width'],
                'height': annotation['height']
            },
            'extracted_text': extracted_text,
            'ai_score': ai_score,
            'confidence': round(confidence, 3),
            'needs_review': confidence < confidence_threshold,
            'processed_at': datetime.now().isoformat()
        }
    
    def get_scoring_results(self, project_id: str, session_id: str) -> Dict[str, Any]:
        """Get scoring session results"""
        try:
            session = self.storage_service.get_entity('scoring_sessions', project_id, session_id)
            if not session:
                return {'success': False, 'error': 'Scoring session not found'}
            
            questions = json.loads(session.get('questions_data', '[]'))
            
            return {
                'success': True,
                'session_id': session_id,
                'status': session.get('status'),
                'total_questions': session.get('total_questions', 0),
                'low_confidence_count': session.get('low_confidence_count', 0),
                'confidence_threshold': session.get('confidence_threshold'),
                'questions': questions,
                'created_at': session.get('created_at'),
                'processed_at': session.get('processed_at')
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def update_confidence_threshold(self, project_id: str, session_id: str, 
                                  new_threshold: float) -> Dict[str, Any]:
        """Update confidence threshold and recalculate warnings"""
        try:
            session = self.storage_service.get_entity('scoring_sessions', project_id, session_id)
            if not session:
                return {'success': False, 'error': 'Scoring session not found'}
            
            # Validate threshold
            if not 0.1 <= new_threshold <= 0.99:
                return {'success': False, 'error': 'Threshold must be between 0.1 and 0.99'}
            
            # Recalculate low confidence count
            questions = json.loads(session.get('questions_data', '[]'))
            low_confidence_count = sum(1 for q in questions if q['confidence'] < new_threshold)
            
            # Update needs_review flags
            for question in questions:
                question['needs_review'] = question['confidence'] < new_threshold
            
            # Update session
            updated_session = {
                'PartitionKey': project_id,
                'RowKey': session_id,
                'annotation_session_id': session['annotation_session_id'],
                'confidence_threshold': new_threshold,
                'status': session.get('status'),
                'total_questions': session.get('total_questions'),
                'processed_questions': session.get('processed_questions'),
                'low_confidence_count': low_confidence_count,
                'questions_data': json.dumps(questions),
                'created_at': session.get('created_at'),
                'updated_at': datetime.now().isoformat(),
                'processed_at': session.get('processed_at')
            }
            
            self.storage_service.update_entity('scoring_sessions', updated_session)
            
            return {
                'success': True,
                'new_threshold': new_threshold,
                'low_confidence_count': low_confidence_count,
                'total_questions': len(questions)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def list_project_scoring_sessions(self, project_id: str) -> List[Dict[str, Any]]:
        """List all scoring sessions for a project"""
        try:
            entities = self.storage_service.query_entities(
                'scoring_sessions',
                f"PartitionKey eq '{project_id}'"
            )
            
            sessions = []
            for entity in entities:
                sessions.append({
                    'session_id': entity.get('RowKey'),
                    'annotation_session_id': entity.get('annotation_session_id'),
                    'status': entity.get('status'),
                    'total_questions': entity.get('total_questions', 0),
                    'low_confidence_count': entity.get('low_confidence_count', 0),
                    'confidence_threshold': entity.get('confidence_threshold'),
                    'created_at': entity.get('created_at'),
                    'processed_at': entity.get('processed_at')
                })
            
            return sessions
            
        except Exception as e:
            print(f"Error listing scoring sessions: {e}")
            return []
