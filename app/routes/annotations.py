# Additional routes for annotation functionality

@app.route('/project/<project_id>/annotations')
@login_required
def review_annotations(project_id):
    project = Project.get_by_id(project_id)
    if not project or project.user_id != current_user.id:
        flash('Project not found')
        return redirect(url_for('dashboard'))
    
    if project.status != 'annotated':
        flash('Project annotations not ready for review')
        return redirect(url_for('project_detail', project_id=project_id))
    
    # Get annotation data from storage
    annotations = get_project_annotations(project_id)
    
    return render_template('project/annotations.html', 
                         project=project, 
                         annotations=annotations)

@app.route('/project/<project_id>/annotations', methods=['POST'])
@login_required
def save_annotations(project_id):
    project = Project.get_by_id(project_id)
    if not project or project.user_id != current_user.id:
        return jsonify({'error': 'Project not found'}), 404
    
    try:
        annotations_data = request.get_json()
        
        # Save annotations to Table Storage
        save_project_annotations(project_id, annotations_data)
        
        # Update project status
        project.update_status('scored')
        
        # Log audit trail
        storage_service.log_audit(
            current_user.id, 
            'annotations_saved', 
            project_id,
            {'annotation_count': len(annotations_data.get('annotations', []))}
        )
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/project/<project_id>/page/<page_num>/image')
@login_required
def get_page_image(project_id, page_num):
    """Serve page images for annotation review"""
    project = Project.get_by_id(project_id)
    if not project or project.user_id != current_user.id:
        return jsonify({'error': 'Project not found'}), 404
    
    try:
        # Get image from blob storage
        blob_name = f"{project_id}/images/page_{page_num}.jpg"
        image_data = storage_service.download_file('images', blob_name)
        
        if image_data:
            return image_data, 200, {'Content-Type': 'image/jpeg'}
        else:
            # Return placeholder image if not found
            return redirect('/static/placeholder-page.jpg')
            
    except Exception as e:
        print(f"Error serving page image: {e}")
        return jsonify({'error': 'Image not found'}), 404

def get_project_annotations(project_id):
    """Get annotations for a project from Table Storage"""
    try:
        entities = storage_service.query_entities('annotations', f"PartitionKey eq '{project_id}'")
        
        annotations = []
        for entity in entities:
            annotation_data = json.loads(entity.get('annotation_data', '{}'))
            annotations.append({
                'page': entity['RowKey'],
                'data': annotation_data,
                'confidence': entity.get('confidence', 0.0),
                'created_at': entity.get('created_at', '')
            })
        
        # If no annotations exist, create sample data for demo
        if not annotations:
            annotations = create_sample_annotations(project_id)
        
        return sorted(annotations, key=lambda x: int(x['page']))
        
    except Exception as e:
        print(f"Error getting annotations: {e}")
        return create_sample_annotations(project_id)

def save_project_annotations(project_id, annotations_data):
    """Save annotations for a project to Table Storage"""
    try:
        for page_num, page_data in annotations_data.items():
            entity = {
                'PartitionKey': project_id,
                'RowKey': str(page_num),
                'annotation_data': json.dumps(page_data),
                'confidence': page_data.get('confidence', 0.0),
                'updated_at': datetime.now().isoformat(),
                'updated_by': current_user.id
            }
            
            storage_service.create_entity('annotations', entity)
            
    except Exception as e:
        print(f"Error saving annotations: {e}")
        raise e

def create_sample_annotations(project_id):
    """Create sample annotations for demo purposes"""
    return [
        {
            'page': '1',
            'data': {
                'questions': [
                    {
                        'id': 'Q1',
                        'type': 'short_answer',
                        'bbox': [100, 150, 400, 200],
                        'confidence': 0.95,
                        'extracted_text': 'What is the capital of France?'
                    },
                    {
                        'id': 'Q2', 
                        'type': 'multiple_choice',
                        'bbox': [100, 250, 400, 350],
                        'confidence': 0.87,
                        'extracted_text': 'Which of the following is correct? A) Paris B) London C) Berlin'
                    }
                ]
            },
            'confidence': 0.91,
            'created_at': datetime.now().isoformat()
        },
        {
            'page': '2',
            'data': {
                'questions': [
                    {
                        'id': 'Q3',
                        'type': 'essay',
                        'bbox': [100, 100, 500, 400],
                        'confidence': 0.78,
                        'extracted_text': 'Explain the process of photosynthesis...'
                    }
                ]
            },
            'confidence': 0.78,
            'created_at': datetime.now().isoformat()
        }
    ]
