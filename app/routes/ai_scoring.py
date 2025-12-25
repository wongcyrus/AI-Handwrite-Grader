from flask import request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models.project import Project
from services.ai_scoring_service import AIScoringService
from services.storage_service import StorageService

def register_scoring_routes(app):
    scoring_service = AIScoringService()
    storage_service = StorageService()
    
    @app.route('/project/<project_id>/scoring/start/<annotation_session_id>')
    @login_required
    def start_scoring(project_id, annotation_session_id):
        project = Project.get_by_id(project_id)
        if not project or project.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Get confidence threshold from request
        confidence_threshold = request.args.get('threshold', type=float)
        
        result = scoring_service.create_scoring_session(
            project_id, annotation_session_id, confidence_threshold
        )
        
        if result['success']:
            project.update_status('scoring')
            return redirect(url_for('scoring_interface', 
                                  project_id=project_id, 
                                  session_id=result['session_id']))
        else:
            flash(f"Failed to start scoring: {result['error']}")
            return redirect(url_for('project_detail', project_id=project_id))
    
    @app.route('/project/<project_id>/scoring/<session_id>')
    @login_required
    def scoring_interface(project_id, session_id):
        project = Project.get_by_id(project_id)
        if not project or project.user_id != current_user.id:
            flash('Project not found')
            return redirect(url_for('dashboard'))
        
        # Get or create scoring results
        results = scoring_service.get_scoring_results(project_id, session_id)
        
        if not results['success']:
            # Try to process if not yet done
            process_result = scoring_service.extract_and_score_questions(project_id, session_id)
            if process_result['success']:
                results = scoring_service.get_scoring_results(project_id, session_id)
            else:
                flash('Error processing scoring session')
                return redirect(url_for('project_detail', project_id=project_id))
        
        return render_template('project/scoring_interface.html',
                             project=project,
                             session=results)
    
    @app.route('/project/<project_id>/scoring/<session_id>/threshold', methods=['POST'])
    @login_required
    def update_threshold(project_id, session_id):
        project = Project.get_by_id(project_id)
        if not project or project.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        new_threshold = request.json.get('threshold')
        if not new_threshold:
            return jsonify({'success': False, 'error': 'Threshold required'}), 400
        
        result = scoring_service.update_confidence_threshold(project_id, session_id, new_threshold)
        return jsonify(result)
    
    @app.route('/project/<project_id>/scoring/<session_id>/complete', methods=['POST'])
    @login_required
    def complete_scoring(project_id, session_id):
        project = Project.get_by_id(project_id)
        if not project or project.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Update project status
        project.update_status('scored')
        
        storage_service.log_audit(
            current_user.id,
            'scoring_completed',
            f"Completed AI scoring for project {project_id}"
        )
        
        return jsonify({'success': True, 'status': 'scored'})
