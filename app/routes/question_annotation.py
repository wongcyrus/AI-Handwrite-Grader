from flask import request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models.project import Project
from services.question_annotation_service import QuestionAnnotationService
from services.pdf_processing_service import PDFProcessingService

def register_annotation_routes(app):
    annotation_service = QuestionAnnotationService()
    pdf_service = PDFProcessingService()
    
    @app.route('/project/<project_id>/annotation/start/<processing_id>')
    @login_required
    def start_annotation(project_id, processing_id):
        project = Project.get_by_id(project_id)
        if not project or project.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        result = annotation_service.create_annotation_session(project_id, processing_id)
        
        if result['success']:
            project.update_status('annotating')
            return redirect(url_for('annotation_wizard', 
                                  project_id=project_id, 
                                  session_id=result['session_id']))
        else:
            flash(f"Failed to start annotation: {result['error']}")
            return redirect(url_for('project_detail', project_id=project_id))
    
    @app.route('/project/<project_id>/annotation/<session_id>')
    @login_required
    def annotation_wizard(project_id, session_id):
        project = Project.get_by_id(project_id)
        if not project or project.user_id != current_user.id:
            flash('Project not found')
            return redirect(url_for('dashboard'))
        
        session = annotation_service.get_annotation_session(project_id, session_id)
        if not session['success']:
            flash('Annotation session not found')
            return redirect(url_for('project_detail', project_id=project_id))
        
        pdf_processing = pdf_service.get_processing_status(project_id, session['processing_id'])
        
        return render_template('project/annotation_wizard.html',
                             project=project,
                             session=session,
                             image_urls=pdf_processing.get('image_urls', []))
    
    @app.route('/project/<project_id>/annotation/<session_id>/page/<int:page>', methods=['POST'])
    @login_required
    def save_page_annotations(project_id, session_id, page):
        project = Project.get_by_id(project_id)
        if not project or project.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        annotations = request.json.get('annotations', [])
        result = annotation_service.save_page_annotations(project_id, session_id, page, annotations)
        return jsonify(result)
    
    @app.route('/project/<project_id>/annotation/<session_id>/complete', methods=['POST'])
    @login_required
    def complete_annotation(project_id, session_id):
        project = Project.get_by_id(project_id)
        if not project or project.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        result = annotation_service.complete_annotation_session(project_id, session_id)
        
        if result['success']:
            project.update_status('annotated')
        
        return jsonify(result)
