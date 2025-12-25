"""Email Distribution Service for AI Handwriting Grader"""

import json
import uuid
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import requests
from typing import List, Dict, Any, Optional
from .storage_service import StorageService


class EmailDistributionService:
    """Service for email distribution with SMTP integration"""
    
    def __init__(self):
        self.storage_service = StorageService()
    
    def create_email_session(self, project_id: str, post_processing_session_id: str, 
                           smtp_config: Dict[str, str]) -> Dict[str, Any]:
        """Create email distribution session"""
        try:
            # Get post-processing session
            post_session = self.storage_service.get_entity(
                'post_processing_sessions', project_id, post_processing_session_id
            )
            if not post_session or post_session.get('status') != 'completed':
                return {'success': False, 'error': 'Post-processing session not found or not completed'}
            
            # Validate SMTP configuration
            required_fields = ['email', 'password', 'smtp_server', 'smtp_port']
            for field in required_fields:
                if not smtp_config.get(field):
                    return {'success': False, 'error': f'Missing SMTP configuration: {field}'}
            
            # Create email session
            session_id = str(uuid.uuid4())
            
            session_data = {
                'PartitionKey': project_id,
                'RowKey': session_id,
                'post_processing_session_id': post_processing_session_id,
                'smtp_config': json.dumps(smtp_config),
                'status': 'created',
                'emails_sent': 0,
                'emails_failed': 0,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self.storage_service.create_entity('email_sessions', session_data)
            
            return {
                'success': True,
                'session_id': session_id,
                'post_processing_session_id': post_processing_session_id
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_student_emails(self, project_id: str, session_id: str, 
                          email_template: Dict[str, str]) -> Dict[str, Any]:
        """Send personalized emails to students with their results"""
        try:
            # Get email session
            email_session = self.storage_service.get_entity('email_sessions', project_id, session_id)
            if not email_session:
                return {'success': False, 'error': 'Email session not found'}
            
            # Get post-processing data
            post_session = self.storage_service.get_entity(
                'post_processing_sessions', project_id, email_session['post_processing_session_id']
            )
            
            smtp_config = json.loads(email_session.get('smtp_config', '{}'))
            pdf_urls = json.loads(post_session.get('pdf_urls', '[]'))
            
            # Send emails to each student
            emails_sent = 0
            emails_failed = 0
            email_results = []
            
            for student_pdf in pdf_urls:
                try:
                    result = self._send_individual_email(
                        student_pdf, smtp_config, email_template
                    )
                    
                    if result['success']:
                        emails_sent += 1
                    else:
                        emails_failed += 1
                    
                    email_results.append(result)
                    
                except Exception as e:
                    emails_failed += 1
                    email_results.append({
                        'success': False,
                        'student_name': student_pdf.get('student_name', 'Unknown'),
                        'error': str(e)
                    })
            
            # Update session
            updated_session = {
                'PartitionKey': project_id,
                'RowKey': session_id,
                'post_processing_session_id': email_session['post_processing_session_id'],
                'smtp_config': email_session.get('smtp_config'),
                'status': 'completed' if emails_failed == 0 else 'partial',
                'emails_sent': emails_sent,
                'emails_failed': emails_failed,
                'email_results': json.dumps(email_results),
                'created_at': email_session.get('created_at'),
                'updated_at': datetime.now().isoformat(),
                'completed_at': datetime.now().isoformat()
            }
            
            self.storage_service.update_entity('email_sessions', updated_session)
            
            return {
                'success': True,
                'emails_sent': emails_sent,
                'emails_failed': emails_failed,
                'total_students': len(pdf_urls),
                'email_results': email_results
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_individual_email(self, student_data: Dict, smtp_config: Dict, 
                             email_template: Dict) -> Dict[str, Any]:
        """Send email to individual student"""
        try:
            # For demo purposes, simulate email sending
            # In production, this would use actual SMTP
            
            student_name = student_data.get('student_name', 'Student')
            student_email = self._get_student_email(student_name)  # Would get from database
            total_score = student_data.get('total_score', 0)
            percentage = student_data.get('percentage', 0)
            
            # Simulate email composition
            subject = email_template.get('subject', 'Your Assignment Results').replace(
                '{student_name}', student_name
            )
            
            body = email_template.get('body', 'Dear {student_name}, your score is {percentage}%.').replace(
                '{student_name}', student_name
            ).replace(
                '{total_score}', str(total_score)
            ).replace(
                '{percentage}', str(percentage)
            )
            
            # Simulate SMTP sending (in production, would use real SMTP)
            if self._simulate_smtp_send(student_email, subject, body, student_data.get('pdf_url')):
                return {
                    'success': True,
                    'student_name': student_name,
                    'student_email': student_email,
                    'subject': subject
                }
            else:
                return {
                    'success': False,
                    'student_name': student_name,
                    'error': 'SMTP send failed'
                }
                
        except Exception as e:
            return {
                'success': False,
                'student_name': student_data.get('student_name', 'Unknown'),
                'error': str(e)
            }
    
    def _get_student_email(self, student_name: str) -> str:
        """Get student email (placeholder implementation)"""
        # In production, this would query the student database
        # For demo, generate a placeholder email
        name_parts = student_name.lower().replace(' ', '.')
        return f"{name_parts}@student.edu"
    
    def _simulate_smtp_send(self, to_email: str, subject: str, body: str, pdf_url: str) -> bool:
        """Simulate SMTP email sending (placeholder implementation)"""
        # In production, this would:
        # 1. Create SMTP connection
        # 2. Download PDF from blob storage
        # 3. Attach PDF to email
        # 4. Send email via SMTP
        # 5. Handle SMTP errors
        
        # For demo, simulate success/failure
        import random
        return random.random() > 0.1  # 90% success rate
    
    def get_email_session(self, project_id: str, session_id: str) -> Dict[str, Any]:
        """Get email session details"""
        try:
            session = self.storage_service.get_entity('email_sessions', project_id, session_id)
            if not session:
                return {'success': False, 'error': 'Email session not found'}
            
            email_results = json.loads(session.get('email_results', '[]'))
            
            return {
                'success': True,
                'session_id': session_id,
                'post_processing_session_id': session.get('post_processing_session_id'),
                'status': session.get('status'),
                'emails_sent': session.get('emails_sent', 0),
                'emails_failed': session.get('emails_failed', 0),
                'email_results': email_results,
                'created_at': session.get('created_at'),
                'updated_at': session.get('updated_at'),
                'completed_at': session.get('completed_at')
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_smtp_connection(self, smtp_config: Dict[str, str]) -> Dict[str, Any]:
        """Test SMTP connection configuration"""
        try:
            # Validate configuration
            required_fields = ['email', 'password', 'smtp_server', 'smtp_port']
            for field in required_fields:
                if not smtp_config.get(field):
                    return {'success': False, 'error': f'Missing SMTP configuration: {field}'}
            
            # For demo purposes, simulate connection test
            # In production, this would test actual SMTP connection
            
            server = smtp_config['smtp_server']
            port = int(smtp_config['smtp_port'])
            email = smtp_config['email']
            
            # Simulate connection test
            if server and port and email:
                return {
                    'success': True,
                    'message': f'SMTP connection test successful to {server}:{port}',
                    'server': server,
                    'port': port,
                    'email': email
                }
            else:
                return {'success': False, 'error': 'Invalid SMTP configuration'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
