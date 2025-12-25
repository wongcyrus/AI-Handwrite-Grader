"""Tests for Manual Scoring Service"""

import pytest
import json
from unittest.mock import Mock, patch
from services.manual_scoring_service import ManualScoringService


class TestManualScoringService:
    """Test manual scoring service"""
    
    @pytest.fixture
    def manual_service(self):
        """Create manual scoring service instance"""
        with patch('services.manual_scoring_service.StorageService') as mock_storage:
            service = ManualScoringService()
            service.storage_service = mock_storage.return_value
            return service
    
    def test_create_manual_session_success(self, manual_service):
        """Test successful manual session creation"""
        mock_ai_questions = [
            {'question_id': 'q1', 'ai_score': 85, 'label': 'Q1'},
            {'question_id': 'q2', 'ai_score': 70, 'label': 'Q2'}
        ]
        
        mock_ai_session = {
            'status': 'processed',
            'questions_data': json.dumps(mock_ai_questions)
        }
        
        manual_service.storage_service.get_entity.return_value = mock_ai_session
        manual_service.storage_service.create_entity.return_value = True
        
        result = manual_service.create_manual_session('test-project', 'ai-session-123')
        
        assert result['success'] is True
        assert 'session_id' in result
        assert result['total_questions'] == 2
        assert result['ai_scoring_session_id'] == 'ai-session-123'
        
        # Verify storage calls
        manual_service.storage_service.get_entity.assert_called_once()
        manual_service.storage_service.create_entity.assert_called_once()
    
    def test_create_manual_session_ai_not_processed(self, manual_service):
        """Test manual session creation with unprocessed AI session"""
        mock_ai_session = {
            'status': 'created',
            'questions_data': '[]'
        }
        
        manual_service.storage_service.get_entity.return_value = mock_ai_session
        
        result = manual_service.create_manual_session('test-project', 'ai-session-123')
        
        assert result['success'] is False
        assert 'not processed' in result['error']
    
    def test_update_question_score_success(self, manual_service):
        """Test successful question score update"""
        mock_questions = [
            {
                'question_id': 'q1',
                'ai_score': 85,
                'manual_score': 85,
                'score_source': 'ai',
                'reviewed': False
            },
            {
                'question_id': 'q2',
                'ai_score': 70,
                'manual_score': 70,
                'score_source': 'ai',
                'reviewed': False
            }
        ]
        
        mock_session = {
            'ai_scoring_session_id': 'ai-123',
            'questions_data': json.dumps(mock_questions),
            'created_at': '2023-01-01T00:00:00'
        }
        
        manual_service.storage_service.get_entity.return_value = mock_session
        manual_service.storage_service.update_entity.return_value = True
        
        result = manual_service.update_question_score('test-project', 'manual-123', 'q1', 90)
        
        assert result['success'] is True
        assert result['question_id'] == 'q1'
        assert result['new_score'] == 90
        assert result['reviewed_questions'] == 1
        assert result['manually_adjusted'] == 1
        
        # Verify update call
        manual_service.storage_service.update_entity.assert_called_once()
    
    def test_update_question_score_invalid_score(self, manual_service):
        """Test updating with invalid score"""
        result = manual_service.update_question_score('test-project', 'manual-123', 'q1', 150)
        
        assert result['success'] is False
        assert 'between 0 and 100' in result['error']
    
    def test_update_question_score_same_as_ai(self, manual_service):
        """Test updating score to same as AI score (should not count as manual adjustment)"""
        mock_questions = [
            {
                'question_id': 'q1',
                'ai_score': 85,
                'manual_score': 90,
                'score_source': 'manual',
                'reviewed': True
            }
        ]
        
        mock_session = {
            'ai_scoring_session_id': 'ai-123',
            'questions_data': json.dumps(mock_questions),
            'created_at': '2023-01-01T00:00:00'
        }
        
        manual_service.storage_service.get_entity.return_value = mock_session
        manual_service.storage_service.update_entity.return_value = True
        
        # Update back to AI score
        result = manual_service.update_question_score('test-project', 'manual-123', 'q1', 85)
        
        assert result['success'] is True
        assert result['manually_adjusted'] == 0  # Should not count as manual adjustment
    
    def test_batch_update_scores_success(self, manual_service):
        """Test batch score updates"""
        mock_questions = [
            {'question_id': 'q1', 'ai_score': 85, 'manual_score': 85, 'score_source': 'ai', 'reviewed': False},
            {'question_id': 'q2', 'ai_score': 70, 'manual_score': 70, 'score_source': 'ai', 'reviewed': False}
        ]
        
        mock_session = {
            'ai_scoring_session_id': 'ai-123',
            'questions_data': json.dumps(mock_questions),
            'created_at': '2023-01-01T00:00:00'
        }
        
        manual_service.storage_service.get_entity.return_value = mock_session
        manual_service.storage_service.update_entity.return_value = True
        
        updates = [
            {'question_id': 'q1', 'score': 90},
            {'question_id': 'q2', 'score': 75}
        ]
        
        result = manual_service.batch_update_scores('test-project', 'manual-123', updates)
        
        assert result['success'] is True
        assert result['updated_count'] == 2
        assert result['reviewed_questions'] == 2
        assert result['manually_adjusted'] == 2
    
    def test_get_manual_session_success(self, manual_service):
        """Test getting manual session details"""
        mock_questions = [
            {'question_id': 'q1', 'ai_score': 85, 'manual_score': 90, 'reviewed': True}
        ]
        
        mock_session = {
            'RowKey': 'manual-123',
            'ai_scoring_session_id': 'ai-123',
            'status': 'in_progress',
            'total_questions': 1,
            'reviewed_questions': 1,
            'manually_adjusted': 1,
            'questions_data': json.dumps(mock_questions),
            'created_at': '2023-01-01T00:00:00',
            'updated_at': '2023-01-01T01:00:00'
        }
        
        manual_service.storage_service.get_entity.return_value = mock_session
        
        result = manual_service.get_manual_session('test-project', 'manual-123')
        
        assert result['success'] is True
        assert result['session_id'] == 'manual-123'
        assert result['status'] == 'in_progress'
        assert result['total_questions'] == 1
        assert result['reviewed_questions'] == 1
        assert result['manually_adjusted'] == 1
        assert len(result['questions']) == 1
    
    def test_complete_manual_scoring_success(self, manual_service):
        """Test completing manual scoring session"""
        mock_session = {
            'ai_scoring_session_id': 'ai-123',
            'total_questions': 5,
            'reviewed_questions': 5,
            'manually_adjusted': 2,
            'questions_data': '[]',
            'created_at': '2023-01-01T00:00:00'
        }
        
        manual_service.storage_service.get_entity.return_value = mock_session
        manual_service.storage_service.update_entity.return_value = True
        
        result = manual_service.complete_manual_scoring('test-project', 'manual-123')
        
        assert result['success'] is True
        assert result['status'] == 'completed'
        assert result['total_questions'] == 5
        assert result['reviewed_questions'] == 5
        assert result['manually_adjusted'] == 2
        
        # Verify update call with completed status
        manual_service.storage_service.update_entity.assert_called_once()
        update_call = manual_service.storage_service.update_entity.call_args[0][1]
        assert update_call['status'] == 'completed'
        assert 'completed_at' in update_call
    
    def test_calculate_student_totals_success(self, manual_service):
        """Test calculating student totals"""
        mock_questions = [
            # Student 1 (page 1)
            {'question_id': 'q1', 'page': 1, 'label': 'Q1', 'manual_score': 85, 'ai_score': 80},
            {'question_id': 'q2', 'page': 1, 'label': 'Q2', 'manual_score': 90, 'ai_score': 85},
            # Student 2 (page 2)
            {'question_id': 'q3', 'page': 2, 'label': 'Q1', 'manual_score': 75, 'ai_score': 70},
            {'question_id': 'q4', 'page': 2, 'label': 'Q2', 'manual_score': 80, 'ai_score': 75},
            # Metadata (should be excluded)
            {'question_id': 'q5', 'page': 1, 'label': 'NAME', 'manual_score': 100, 'ai_score': 100}
        ]
        
        mock_session = {
            'questions_data': json.dumps(mock_questions)
        }
        
        manual_service.storage_service.get_entity.return_value = mock_session
        
        result = manual_service.calculate_student_totals('test-project', 'manual-123')
        
        assert result['success'] is True
        assert result['total_students'] == 2
        
        student_scores = result['student_scores']
        
        # Student 1 (page 1): 85 + 90 = 175/200 = 87.5%
        student1 = next(s for s in student_scores if s['student_page'] == 1)
        assert student1['total_score'] == 175
        assert student1['max_possible'] == 200
        assert student1['percentage'] == 87.5
        assert student1['question_count'] == 2
        
        # Student 2 (page 2): 75 + 80 = 155/200 = 77.5%
        student2 = next(s for s in student_scores if s['student_page'] == 2)
        assert student2['total_score'] == 155
        assert student2['max_possible'] == 200
        assert student2['percentage'] == 77.5
        assert student2['question_count'] == 2
