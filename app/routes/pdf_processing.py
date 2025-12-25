"""PDF Processing Routes for AI Handwriting Grader"""

from flask import request, jsonify, flash, redirect, url_for, render_template
from flask_login import login_required, current_user
import os
import tempfile
from werkzeug.utils import secure_filename
from models.project import Project
from services.pdf_processing_service import PDFProcessingService
from services.storage_service import StorageService


def register_pdf_routes(app):
    """Register PDF processing routes"""
    
    pdf_service = PDFProcessingService()
    storage_service = StorageService()
    
    @app.route('/project/<project_id>/process-pdf', methods=['POST'])
    @login_required
    def process_pdf(project_id):
        """Process uploaded PDF and convert to images"""
        project = Project.get_by_id(project_id)
        if not project or project.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        if 'pdf_file' not in request.files:
            return jsonify({'success': False, 'error': 'No PDF file provided'}), 400
        
        pdf_file = request.files['pdf_file']
        if pdf_file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not pdf_file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'error': 'File must be a PDF'}), 400
        
        try:
            # Save uploaded file temporarily
            filename = secure_filename(pdf_file.filename)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                pdf_file.save(temp_file.name)
                temp_path = temp_file.name
            
            # Process PDF
            result = pdf_service.process_pdf(temp_path, project_id)
            
            # Clean up temporary file
            os.unlink(temp_path)
            
            if result['success']:
                # Update project status
                project.update_status('pdf_processed')
                
                # Log audit trail
                storage_service.log_audit(
                    current_user.id,
                    'pdf_processed',
                    f"PDF processed for project {project_id}: {result['total_pages']} pages"
                )
                
                return jsonify(result)
            else:
                return jsonify(result), 500
                
        except Exception as e:
            # Clean up temporary file if it exists
            if 'temp_path' in locals():
                try:
                    os.unlink(temp_path)
                except:
                    pass
            
            return jsonify({
                'success': False,
                'error': f'Processing failed: {str(e)}'
            }), 500
    
    @app.route('/project/<project_id>/pdf-status/<processing_id>')
    @login_required
    def get_pdf_status(project_id, processing_id):
        """Get PDF processing status"""
        project = Project.get_by_id(project_id)
        if not project or project.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        result = pdf_service.get_processing_status(project_id, processing_id)
        return jsonify(result)
    
    @app.route('/project/<project_id>/pdf-processing')
    @login_required
    def list_pdf_processing(project_id):
        """List all PDF processing records for project"""
        project = Project.get_by_id(project_id)
        if not project or project.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        results = pdf_service.list_project_processing(project_id)
        return jsonify({'success': True, 'processing_records': results})
    
    @app.route('/project/<project_id>/pdf-upload')
    @login_required
    def pdf_upload_page(project_id):
        """PDF upload page"""
        project = Project.get_by_id(project_id)
        if not project or project.user_id != current_user.id:
            flash('Project not found')
            return redirect(url_for('dashboard'))
        
        # Get existing processing records
        processing_records = pdf_service.list_project_processing(project_id)
        
        return render_template('project/pdf_upload.html', 
                             project=project, 
                             processing_records=processing_records)
