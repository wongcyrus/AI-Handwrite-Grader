"""Manual Scoring Service for AI Handwriting Grader"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from .storage_service import StorageService


class ManualScoringService:
    """Service for manual scoring interface with AI suggestions"""
    
    def __init__(self):
        self.storage_service = StorageService()
    
    def create_manual_session(self, project_id: str, ai_scoring_session_id: str) -> Dict[str, Any]:
        """Create manual scoring session from AI scoring results"""
        try:
            # Get AI scoring session
            ai_session = self.storage_service.get_entity('scoring_sessions', project_id, ai_scoring_session_id)
            if not ai_session or ai_session.get('status') != 'processed':
                return {'success': False, 'error': 'AI scoring session not found or not processed'}
            
            # Create manual scoring session
            session_id = str(uuid.uuid4())
            ai_questions = json.loads(ai_session.get('questions_data', '[]'))
            
            # Initialize manual scores with AI suggestions
            manual_questions = []
            for q in ai_questions:
                manual_q = q.copy()
                manual_q['manual_score'] = q['ai_score']  # Start with AI score
                manual_q['score_source'] = 'ai'  # Track if manually adjusted
                manual_q['reviewed'] = False
                manual_questions.append(manual_q)
            
            session_data = {
                'PartitionKey': project_id,
                'RowKey': session_id,
                'ai_scoring_session_id': ai_scoring_session_id,
                'status': 'created',
                'total_questions': len(manual_questions),
                'reviewed_questions': 0,
                'manually_adjusted': 0,
                'questions_data': json.dumps(manual_questions),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self.storage_service.create_entity('manual_scoring_sessions', session_data)
            
            return {
                'success': True,
                'session_id': session_id,
                'total_questions': len(manual_questions),
                'ai_scoring_session_id': ai_scoring_session_id
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def update_question_score(self, project_id: str, session_id: str, 
                            question_id: str, new_score: int, max_score: int = 100) -> Dict[str, Any]:
        """Update manual score for a specific question"""
        try:
            # Validate score
            if not 0 <= new_score <= max_score:
                return {'success': False, 'error': f'Score must be between 0 and {max_score}'}
            
            # Get session
            session = self.storage_service.get_entity('manual_scoring_sessions', project_id, session_id)
            if not session:
                return {'success': False, 'error': 'Manual scoring session not found'}
            
            # Update question score
            questions = json.loads(session.get('questions_data', '[]'))
            question_found = False
            manually_adjusted_count = 0
            reviewed_count = 0
            
            for q in questions:
                if q['question_id'] == question_id:
                    old_score = q['manual_score']
                    q['manual_score'] = new_score
                    q['reviewed'] = True
                    
                    # Track if manually adjusted from AI score
                    if new_score != q['ai_score']:
                        q['score_source'] = 'manual'
                    else:
                        q['score_source'] = 'ai'
                    
                    question_found = True
                
                # Count totals
                if q.get('reviewed', False):
                    reviewed_count += 1
                if q.get('score_source') == 'manual':
                    manually_adjusted_count += 1
            
            if not question_found:
                return {'success': False, 'error': 'Question not found'}
            
            # Update session
            updated_session = {
                'PartitionKey': project_id,
                'RowKey': session_id,
                'ai_scoring_session_id': session['ai_scoring_session_id'],
                'status': 'in_progress',
                'total_questions': len(questions),
                'reviewed_questions': reviewed_count,
                'manually_adjusted': manually_adjusted_count,
                'questions_data': json.dumps(questions),
                'created_at': session.get('created_at'),
                'updated_at': datetime.now().isoformat()
            }
            
            self.storage_service.update_entity('manual_scoring_sessions', updated_session)
            
            return {
                'success': True,
                'question_id': question_id,
                'new_score': new_score,
                'reviewed_questions': reviewed_count,
                'manually_adjusted': manually_adjusted_count
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def batch_update_scores(self, project_id: str, session_id: str, 
                          score_updates: List[Dict]) -> Dict[str, Any]:
        """Update multiple question scores in batch"""
        try:
            session = self.storage_service.get_entity('manual_scoring_sessions', project_id, session_id)
            if not session:
                return {'success': False, 'error': 'Manual scoring session not found'}
            
            questions = json.loads(session.get('questions_data', '[]'))
            updated_count = 0
            manually_adjusted_count = 0
            reviewed_count = 0
            
            # Create lookup for faster updates
            question_lookup = {q['question_id']: q for q in questions}
            
            for update in score_updates:
                question_id = update.get('question_id')
                new_score = update.get('score')
                max_score = update.get('max_score', 100)
                
                if question_id in question_lookup and 0 <= new_score <= max_score:
                    q = question_lookup[question_id]
                    q['manual_score'] = new_score
                    q['reviewed'] = True
                    
                    if new_score != q['ai_score']:
                        q['score_source'] = 'manual'
                    else:
                        q['score_source'] = 'ai'
                    
                    updated_count += 1
            
            # Count totals
            for q in questions:
                if q.get('reviewed', False):
                    reviewed_count += 1
                if q.get('score_source') == 'manual':
                    manually_adjusted_count += 1
            
            # Update session
            updated_session = {
                'PartitionKey': project_id,
                'RowKey': session_id,
                'ai_scoring_session_id': session['ai_scoring_session_id'],
                'status': 'in_progress',
                'total_questions': len(questions),
                'reviewed_questions': reviewed_count,
                'manually_adjusted': manually_adjusted_count,
                'questions_data': json.dumps(questions),
                'created_at': session.get('created_at'),
                'updated_at': datetime.now().isoformat()
            }
            
            self.storage_service.update_entity('manual_scoring_sessions', updated_session)
            
            return {
                'success': True,
                'updated_count': updated_count,
                'reviewed_questions': reviewed_count,
                'manually_adjusted': manually_adjusted_count
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_manual_session(self, project_id: str, session_id: str) -> Dict[str, Any]:
        """Get manual scoring session details"""
        try:
            session = self.storage_service.get_entity('manual_scoring_sessions', project_id, session_id)
            if not session:
                return {'success': False, 'error': 'Manual scoring session not found'}
            
            questions = json.loads(session.get('questions_data', '[]'))
            
            return {
                'success': True,
                'session_id': session_id,
                'ai_scoring_session_id': session.get('ai_scoring_session_id'),
                'status': session.get('status'),
                'total_questions': session.get('total_questions', 0),
                'reviewed_questions': session.get('reviewed_questions', 0),
                'manually_adjusted': session.get('manually_adjusted', 0),
                'questions': questions,
                'created_at': session.get('created_at'),
                'updated_at': session.get('updated_at')
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def complete_manual_scoring(self, project_id: str, session_id: str) -> Dict[str, Any]:
        """Complete manual scoring session"""
        try:
            session = self.storage_service.get_entity('manual_scoring_sessions', project_id, session_id)
            if not session:
                return {'success': False, 'error': 'Manual scoring session not found'}
            
            # Update session status
            updated_session = {
                'PartitionKey': project_id,
                'RowKey': session_id,
                'ai_scoring_session_id': session['ai_scoring_session_id'],
                'status': 'completed',
                'total_questions': session.get('total_questions'),
                'reviewed_questions': session.get('reviewed_questions'),
                'manually_adjusted': session.get('manually_adjusted'),
                'questions_data': session.get('questions_data'),
                'created_at': session.get('created_at'),
                'updated_at': datetime.now().isoformat(),
                'completed_at': datetime.now().isoformat()
            }
            
            self.storage_service.update_entity('manual_scoring_sessions', updated_session)
            
            return {
                'success': True,
                'status': 'completed',
                'total_questions': session.get('total_questions', 0),
                'reviewed_questions': session.get('reviewed_questions', 0),
                'manually_adjusted': session.get('manually_adjusted', 0)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def calculate_student_totals(self, project_id: str, session_id: str) -> Dict[str, Any]:
        """Calculate total scores per student from manual scoring"""
        try:
            session = self.storage_service.get_entity('manual_scoring_sessions', project_id, session_id)
            if not session:
                return {'success': False, 'error': 'Manual scoring session not found'}
            
            questions = json.loads(session.get('questions_data', '[]'))
            
            # Group questions by student (assuming page represents student)
            student_scores = {}
            for q in questions:
                if q['label'] not in ['NAME', 'ID', 'CLASS']:  # Only count actual questions
                    page = q['page']
                    if page not in student_scores:
                        student_scores[page] = {
                            'student_page': page,
                            'questions': [],
                            'total_score': 0,
                            'max_possible': 0,
                            'question_count': 0
                        }
                    
                    student_scores[page]['questions'].append({
                        'label': q['label'],
                        'manual_score': q['manual_score'],
                        'ai_score': q['ai_score'],
                        'score_source': q.get('score_source', 'ai')
                    })
                    
                    student_scores[page]['total_score'] += q['manual_score']
                    student_scores[page]['max_possible'] += 100  # Assuming 100 max per question
                    student_scores[page]['question_count'] += 1
            
            # Calculate percentages
            for student in student_scores.values():
                if student['max_possible'] > 0:
                    student['percentage'] = round((student['total_score'] / student['max_possible']) * 100, 1)
                else:
                    student['percentage'] = 0
            
            return {
                'success': True,
                'student_scores': list(student_scores.values()),
                'total_students': len(student_scores)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
