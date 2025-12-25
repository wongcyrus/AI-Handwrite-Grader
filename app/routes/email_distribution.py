from flask import request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models.project import Project
from services.email_distribution_service import EmailDistributionService
from services.storage_service import StorageService

def register_email_routes(app):
    email_service = EmailDistributionService()
    storage_service = StorageService()
    
    @app.route('/project/<project_id>/email/start/<post_session_id>')
    @login_required
    def start_email_distribution(project_id, post_session_id):
        project = Project.get_by_id(project_id)
        if not project or project.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        return render_template('project/email_setup.html',
                             project=project,
                             post_session_id=post_session_id)
    
    @app.route('/project/<project_id>/email/create', methods=['POST'])
    @login_required
    def create_email_session(project_id):
        project = Project.get_by_id(project_id)
        if not project or project.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        post_session_id = request.json.get('post_session_id')
        smtp_config = request.json.get('smtp_config', {})
        
        result = email_service.create_email_session(project_id, post_session_id, smtp_config)
        
        if result['success']:
            project.update_status('email_ready')
        
        return jsonify(result)
    
    @app.route('/project/<project_id>/email/<session_id>')
    @login_required
    def email_interface(project_id, session_id):
        project = Project.get_by_id(project_id)
        if not project or project.user_id != current_user.id:
            flash('Project not found')
            return redirect(url_for('dashboard'))
        
        session = email_service.get_email_session(project_id, session_id)
        if not session['success']:
            flash('Email session not found')
            return redirect(url_for('project_detail', project_id=project_id))
        
        return render_template('project/email_distribution.html',
                             project=project,
                             session=session)
    
    @app.route('/project/<project_id>/email/<session_id>/send', methods=['POST'])
    @login_required
    def send_emails(project_id, session_id):
        project = Project.get_by_id(project_id)
        if not project or project.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        email_template = request.json.get('email_template', {})
        
        result = email_service.send_student_emails(project_id, session_id, email_template)
        
        if result['success']:
            project.update_status('emails_sent')
            storage_service.log_audit(
                current_user.id,
                'emails_sent',
                f"Sent {result['emails_sent']} emails for project {project_id}"
            )
        
        return jsonify(result)
    
    @app.route('/project/<project_id>/email/test-smtp', methods=['POST'])
    @login_required
    def test_smtp(project_id):
        project = Project.get_by_id(project_id)
        if not project or project.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        smtp_config = request.json.get('smtp_config', {})
        result = email_service.test_smtp_connection(smtp_config)
        
        return jsonify(result)
