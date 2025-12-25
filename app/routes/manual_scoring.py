from flask import request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models.project import Project
from services.manual_scoring_service import ManualScoringService
from services.storage_service import StorageService

def register_manual_scoring_routes(app):
    manual_service = ManualScoringService()
    storage_service = StorageService()
    
    @app.route('/project/<project_id>/manual-scoring/start/<ai_session_id>')
    @login_required
    def start_manual_scoring(project_id, ai_session_id):
        project = Project.get_by_id(project_id)
        if not project or project.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        result = manual_service.create_manual_session(project_id, ai_session_id)
        
        if result['success']:
            project.update_status('manual_scoring')
            return redirect(url_for('manual_scoring_interface', 
                                  project_id=project_id, 
                                  session_id=result['session_id']))
        else:
            flash(f"Failed to start manual scoring: {result['error']}")
            return redirect(url_for('project_detail', project_id=project_id))
    
    @app.route('/project/<project_id>/manual-scoring/<session_id>')
    @login_required
    def manual_scoring_interface(project_id, session_id):
        project = Project.get_by_id(project_id)
        if not project or project.user_id != current_user.id:
            flash('Project not found')
            return redirect(url_for('dashboard'))
        
        session = manual_service.get_manual_session(project_id, session_id)
        if not session['success']:
            flash('Manual scoring session not found')
            return redirect(url_for('project_detail', project_id=project_id))
        
        return render_template('project/manual_scoring.html',
                             project=project,
                             session=session)
    
    @app.route('/project/<project_id>/manual-scoring/<session_id>/update', methods=['POST'])
    @login_required
    def update_question_score(project_id, session_id):
        project = Project.get_by_id(project_id)
        if not project or project.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        question_id = request.json.get('question_id')
        new_score = request.json.get('score')
        
        result = manual_service.update_question_score(project_id, session_id, question_id, new_score)
        return jsonify(result)
    
    @app.route('/project/<project_id>/manual-scoring/<session_id>/complete', methods=['POST'])
    @login_required
    def complete_manual_scoring(project_id, session_id):
        project = Project.get_by_id(project_id)
        if not project or project.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        result = manual_service.complete_manual_scoring(project_id, session_id)
        
        if result['success']:
            project.update_status('manually_scored')
        
        return jsonify(result)
