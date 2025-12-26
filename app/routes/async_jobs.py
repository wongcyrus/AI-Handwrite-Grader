from flask import jsonify, request
from flask_login import login_required
import asyncio

def register_async_job_routes(app, job_processor):
    """Register async job routes with the Flask app."""
    
    @app.route('/api/jobs/<job_id>/status')
    @login_required
    def get_job_status(job_id):
        """Get job status for polling (avoids timeout issues)."""
        try:
            status = job_processor.get_job_status(job_id)
            return jsonify(status)
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route('/api/jobs/start', methods=['POST'])
    @login_required
    def start_async_job():
        """Start a job asynchronously and return job ID immediately."""
        try:
            data = request.get_json()
            job_type = data.get('job_type', 'annotation')
            
            if job_type == 'annotation':
                project_id = data.get('project_id')
                pdf_url = data.get('pdf_url')
                excel_url = data.get('excel_url')
                
                if not all([project_id, pdf_url, excel_url]):
                    return jsonify({"error": "Missing required parameters"}), 400
                
                from services.ai_foundry_service import AIFoundryService
                ai_foundry_service = AIFoundryService()
                job_id = ai_foundry_service.start_annotation_job(project_id, pdf_url, excel_url)
                
            elif job_type == 'handwriting':
                question_id = data.get('question_id')
                image_data = data.get('image_data', b'')
                
                if not question_id:
                    return jsonify({"error": "Missing question_id"}), 400
                
                from services.ai_foundry_service import AIFoundryService
                ai_foundry_service = AIFoundryService()
                job_id = ai_foundry_service.process_handwriting_analysis(image_data, question_id)
                
            elif job_type == 'evaluation':
                student_answer = data.get('student_answer')
                standard_answer = data.get('standard_answer')
                rubric = data.get('rubric', {})
                
                if not all([student_answer, standard_answer]):
                    return jsonify({"error": "Missing student_answer or standard_answer"}), 400
                
                from services.ai_foundry_service import AIFoundryService
                ai_foundry_service = AIFoundryService()
                job_id = ai_foundry_service.evaluate_answer(student_answer, standard_answer, rubric)
                
            else:
                return jsonify({"error": f"Unknown job type: {job_type}"}), 400
            
            return jsonify({
                "job_id": job_id,
                "job_type": job_type,
                "status": "queued",
                "message": f"{job_type.title()} job started successfully. Use /api/jobs/{job_id}/status to track progress."
            })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
