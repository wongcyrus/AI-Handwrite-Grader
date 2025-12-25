from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
import uuid

from services.storage_service import StorageService
from services.ai_foundry_service import AIFoundryService
from models.user import User
from models.project import Project

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Initialize services
storage_service = StorageService()
ai_foundry_service = AIFoundryService()

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.get_by_email(email)
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid email or password')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'teacher')
        
        if User.get_by_email(email):
            flash('Email already registered')
            return render_template('auth/register.html')
        
        user = User.create(email, password, role)
        login_user(user)
        return redirect(url_for('dashboard'))
    
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    projects = Project.get_by_user(current_user.id)
    return render_template('dashboard.html', projects=projects)

@app.route('/project/create', methods=['GET', 'POST'])
@login_required
def create_project():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        
        project = Project.create(
            name=name,
            description=description,
            user_id=current_user.id
        )
        
        flash('Project created successfully')
        return redirect(url_for('project_detail', project_id=project.id))
    
    return render_template('project/create.html')

@app.route('/project/<project_id>')
@login_required
def project_detail(project_id):
    project = Project.get_by_id(project_id)
    if not project or project.user_id != current_user.id:
        flash('Project not found')
        return redirect(url_for('dashboard'))
    
    return render_template('project/detail.html', project=project)

@app.route('/project/<project_id>/upload', methods=['POST'])
@login_required
def upload_files(project_id):
    project = Project.get_by_id(project_id)
    if not project or project.user_id != current_user.id:
        return jsonify({'error': 'Project not found'}), 404
    
    if 'pdf_file' not in request.files or 'excel_file' not in request.files:
        return jsonify({'error': 'Both PDF and Excel files required'}), 400
    
    pdf_file = request.files['pdf_file']
    excel_file = request.files['excel_file']
    
    if pdf_file.filename == '' or excel_file.filename == '':
        return jsonify({'error': 'No files selected'}), 400
    
    try:
        # Upload files to blob storage
        pdf_url = storage_service.upload_file(pdf_file, 'pdfs', project_id)
        excel_url = storage_service.upload_file(excel_file, 'pdfs', project_id)
        
        # Update project with file URLs
        project.update_files(pdf_url, excel_url)
        
        # Start AI annotation process
        job_id = ai_foundry_service.start_annotation_job(project_id, pdf_url, excel_url)
        project.update_status('processing', job_id)
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Files uploaded and processing started'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/project/<project_id>/status')
@login_required
def project_status(project_id):
    project = Project.get_by_id(project_id)
    if not project or project.user_id != current_user.id:
        return jsonify({'error': 'Project not found'}), 404
    
    if project.job_id:
        status = ai_foundry_service.get_job_status(project.job_id)
        return jsonify({
            'status': status['status'],
            'progress': status.get('progress', 0),
            'message': status.get('message', '')
        })
    
    return jsonify({'status': project.status})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
