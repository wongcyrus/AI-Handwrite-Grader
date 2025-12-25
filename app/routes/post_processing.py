from flask import request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models.project import Project
from services.post_processing_service import PostProcessingService
from services.storage_service import StorageService

def register_post_processing_routes(app):
    post_service = PostProcessingService()
    storage_service = StorageService()
    
    @app.route('/project/<project_id>/post-processing/start/<manual_session_id>')
    @login_required
    def start_post_processing(project_id, manual_session_id):
        project = Project.get_by_id(project_id)
        if not project or project.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        result = post_service.create_post_processing_session(project_id, manual_session_id)
        
        if result['success']:
            project.update_status('post_processing')
            return redirect(url_for('post_processing_interface', 
                                  project_id=project_id, 
                                  session_id=result['session_id']))
        else:
            flash(f"Failed to start post-processing: {result['error']}")
            return redirect(url_for('project_detail', project_id=project_id))
    
    @app.route('/project/<project_id>/post-processing/<session_id>')
    @login_required
    def post_processing_interface(project_id, session_id):
        project = Project.get_by_id(project_id)
        if not project or project.user_id != current_user.id:
            flash('Project not found')
            return redirect(url_for('dashboard'))
        
        session = post_service.get_post_processing_session(project_id, session_id)
        if not session['success']:
            flash('Post-processing session not found')
            return redirect(url_for('project_detail', project_id=project_id))
        
        return render_template('project/post_processing.html',
                             project=project,
                             session=session)
    
    @app.route('/project/<project_id>/post-processing/<session_id>/generate-report', methods=['POST'])
    @login_required
    def generate_report(project_id, session_id):
        project = Project.get_by_id(project_id)
        if not project or project.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        result = post_service.generate_excel_report(project_id, session_id)
        return jsonify(result)
    
    @app.route('/project/<project_id>/post-processing/<session_id>/create-pdfs', methods=['POST'])
    @login_required
    def create_pdfs(project_id, session_id):
        project = Project.get_by_id(project_id)
        if not project or project.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        result = post_service.create_annotated_pdfs(project_id, session_id)
        return jsonify(result)
    
    @app.route('/project/<project_id>/post-processing/<session_id>/complete', methods=['POST'])
    @login_required
    def complete_post_processing(project_id, session_id):
        project = Project.get_by_id(project_id)
        if not project or project.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        result = post_service.complete_post_processing(project_id, session_id)
        
        if result['success']:
            project.update_status('reports_ready')
        
        return jsonify(result)
