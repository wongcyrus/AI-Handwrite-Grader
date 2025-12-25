"""Post-Processing Microservice for AI Handwriting Grader"""

import json
import uuid
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
from io import BytesIO
from .storage_service import StorageService


class PostProcessingService:
    """Microservice for result compilation and report generation"""
    
    def __init__(self):
        self.storage_service = StorageService()
    
    def create_post_processing_session(self, project_id: str, manual_scoring_session_id: str) -> Dict[str, Any]:
        """Create post-processing session from manual scoring results"""
        try:
            # Get manual scoring session
            manual_session = self.storage_service.get_entity(
                'manual_scoring_sessions', project_id, manual_scoring_session_id
            )
            if not manual_session or manual_session.get('status') != 'completed':
                return {'success': False, 'error': 'Manual scoring session not found or not completed'}
            
            # Create post-processing session
            session_id = str(uuid.uuid4())
            
            session_data = {
                'PartitionKey': project_id,
                'RowKey': session_id,
                'manual_scoring_session_id': manual_scoring_session_id,
                'status': 'created',
                'reports_generated': 0,
                'pdfs_created': 0,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self.storage_service.create_entity('post_processing_sessions', session_data)
            
            return {
                'success': True,
                'session_id': session_id,
                'manual_scoring_session_id': manual_scoring_session_id
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_excel_report(self, project_id: str, session_id: str) -> Dict[str, Any]:
        """Generate Excel score report from manual scoring results"""
        try:
            # Get post-processing session
            session = self.storage_service.get_entity('post_processing_sessions', project_id, session_id)
            if not session:
                return {'success': False, 'error': 'Post-processing session not found'}
            
            # Get manual scoring data
            manual_session = self.storage_service.get_entity(
                'manual_scoring_sessions', project_id, session['manual_scoring_session_id']
            )
            
            questions = json.loads(manual_session.get('questions_data', '[]'))
            
            # Group questions by student (page)
            student_data = {}
            for q in questions:
                page = q['page']
                if page not in student_data:
                    student_data[page] = {
                        'student_page': page,
                        'name': '',
                        'id': '',
                        'class': '',
                        'questions': {},
                        'total_score': 0,
                        'max_possible': 0
                    }
                
                if q['label'] == 'NAME':
                    student_data[page]['name'] = q.get('extracted_text', '')
                elif q['label'] == 'ID':
                    student_data[page]['id'] = q.get('extracted_text', '')
                elif q['label'] == 'CLASS':
                    student_data[page]['class'] = q.get('extracted_text', '')
                elif q['label'].startswith('Q'):
                    student_data[page]['questions'][q['label']] = {
                        'manual_score': q['manual_score'],
                        'ai_score': q['ai_score'],
                        'max_score': 100
                    }
                    student_data[page]['total_score'] += q['manual_score']
                    student_data[page]['max_possible'] += 100
            
            # Create Excel report
            report_data = []
            for student in student_data.values():
                row = {
                    'Student_Page': student['student_page'],
                    'Name': student['name'],
                    'ID': student['id'],
                    'Class': student['class'],
                    'Total_Score': student['total_score'],
                    'Max_Possible': student['max_possible'],
                    'Percentage': round((student['total_score'] / student['max_possible']) * 100, 1) if student['max_possible'] > 0 else 0
                }
                
                # Add individual question scores
                for q_label, q_data in student['questions'].items():
                    row[f'{q_label}_Score'] = q_data['manual_score']
                    row[f'{q_label}_AI_Score'] = q_data['ai_score']
                
                report_data.append(row)
            
            # Convert to DataFrame and Excel
            df = pd.DataFrame(report_data)
            excel_buffer = BytesIO()
            df.to_excel(excel_buffer, index=False, sheet_name='Score_Report')
            excel_buffer.seek(0)
            
            # Upload to blob storage
            blob_name = f"{project_id}/{session_id}/score_report.xlsx"
            report_url = self.storage_service.upload_file(
                'reports',
                blob_name,
                excel_buffer.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
            # Update session
            updated_session = {
                'PartitionKey': project_id,
                'RowKey': session_id,
                'manual_scoring_session_id': session['manual_scoring_session_id'],
                'status': 'reports_generated',
                'reports_generated': 1,
                'pdfs_created': session.get('pdfs_created', 0),
                'report_url': report_url,
                'report_data': json.dumps(report_data),
                'created_at': session.get('created_at'),
                'updated_at': datetime.now().isoformat()
            }
            
            self.storage_service.update_entity('post_processing_sessions', updated_session)
            
            return {
                'success': True,
                'report_url': report_url,
                'total_students': len(report_data),
                'report_data': report_data
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_annotated_pdfs(self, project_id: str, session_id: str) -> Dict[str, Any]:
        """Create individual annotated PDFs for students"""
        try:
            # Get post-processing session
            session = self.storage_service.get_entity('post_processing_sessions', project_id, session_id)
            if not session:
                return {'success': False, 'error': 'Post-processing session not found'}
            
            # For now, create placeholder PDF URLs (in production, would generate actual PDFs)
            report_data = json.loads(session.get('report_data', '[]'))
            pdf_urls = []
            
            for student in report_data:
                # Simulate PDF creation
                pdf_blob_name = f"{project_id}/{session_id}/annotated_pdfs/student_{student['Student_Page']}.pdf"
                
                # In production, this would:
                # 1. Get original PDF pages for this student
                # 2. Overlay scores and annotations
                # 3. Generate annotated PDF
                # 4. Upload to blob storage
                
                # For now, create a placeholder
                pdf_url = f"https://placeholder.blob.core.windows.net/reports/{pdf_blob_name}"
                
                pdf_urls.append({
                    'student_page': student['Student_Page'],
                    'student_name': student['Name'],
                    'student_id': student['ID'],
                    'pdf_url': pdf_url,
                    'total_score': student['Total_Score'],
                    'percentage': student['Percentage']
                })
            
            # Update session
            updated_session = {
                'PartitionKey': project_id,
                'RowKey': session_id,
                'manual_scoring_session_id': session['manual_scoring_session_id'],
                'status': 'pdfs_created',
                'reports_generated': session.get('reports_generated', 0),
                'pdfs_created': len(pdf_urls),
                'report_url': session.get('report_url'),
                'report_data': session.get('report_data'),
                'pdf_urls': json.dumps(pdf_urls),
                'created_at': session.get('created_at'),
                'updated_at': datetime.now().isoformat()
            }
            
            self.storage_service.update_entity('post_processing_sessions', updated_session)
            
            return {
                'success': True,
                'pdfs_created': len(pdf_urls),
                'pdf_urls': pdf_urls
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def complete_post_processing(self, project_id: str, session_id: str) -> Dict[str, Any]:
        """Complete post-processing session"""
        try:
            session = self.storage_service.get_entity('post_processing_sessions', project_id, session_id)
            if not session:
                return {'success': False, 'error': 'Post-processing session not found'}
            
            # Update session status
            updated_session = {
                'PartitionKey': project_id,
                'RowKey': session_id,
                'manual_scoring_session_id': session['manual_scoring_session_id'],
                'status': 'completed',
                'reports_generated': session.get('reports_generated', 0),
                'pdfs_created': session.get('pdfs_created', 0),
                'report_url': session.get('report_url'),
                'report_data': session.get('report_data'),
                'pdf_urls': session.get('pdf_urls'),
                'created_at': session.get('created_at'),
                'updated_at': datetime.now().isoformat(),
                'completed_at': datetime.now().isoformat()
            }
            
            self.storage_service.update_entity('post_processing_sessions', updated_session)
            
            return {
                'success': True,
                'status': 'completed',
                'reports_generated': session.get('reports_generated', 0),
                'pdfs_created': session.get('pdfs_created', 0)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_post_processing_session(self, project_id: str, session_id: str) -> Dict[str, Any]:
        """Get post-processing session details"""
        try:
            session = self.storage_service.get_entity('post_processing_sessions', project_id, session_id)
            if not session:
                return {'success': False, 'error': 'Post-processing session not found'}
            
            pdf_urls = json.loads(session.get('pdf_urls', '[]'))
            report_data = json.loads(session.get('report_data', '[]'))
            
            return {
                'success': True,
                'session_id': session_id,
                'manual_scoring_session_id': session.get('manual_scoring_session_id'),
                'status': session.get('status'),
                'reports_generated': session.get('reports_generated', 0),
                'pdfs_created': session.get('pdfs_created', 0),
                'report_url': session.get('report_url'),
                'report_data': report_data,
                'pdf_urls': pdf_urls,
                'created_at': session.get('created_at'),
                'updated_at': session.get('updated_at'),
                'completed_at': session.get('completed_at')
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
