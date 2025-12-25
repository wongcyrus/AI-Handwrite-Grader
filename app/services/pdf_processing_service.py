"""PDF Processing Microservice for AI Handwriting Grader"""

import os
import uuid
from datetime import datetime
from typing import List, Dict, Any
from pdf2image import convert_from_path
from PIL import Image
import io
from .storage_service import StorageService


class PDFProcessingService:
    """Microservice for PDF processing and image conversion"""
    
    def __init__(self):
        self.storage_service = StorageService()
        self.container_name = "pdf-images"
    
    def process_pdf(self, pdf_path: str, project_id: str) -> Dict[str, Any]:
        """
        Convert PDF to images and store in blob storage
        
        Args:
            pdf_path: Path to PDF file
            project_id: Project identifier
            
        Returns:
            Dict with processing results and image URLs
        """
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=200)
            
            # Process each page
            image_urls = []
            processing_id = str(uuid.uuid4())
            
            for i, image in enumerate(images):
                # Convert PIL image to bytes
                img_bytes = io.BytesIO()
                image.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                
                # Generate blob name
                blob_name = f"{project_id}/{processing_id}/page_{i+1}.png"
                
                # Upload to blob storage
                blob_url = self.storage_service.upload_file(
                    self.container_name,
                    blob_name,
                    img_bytes.getvalue(),
                    content_type="image/png"
                )
                
                image_urls.append({
                    'page': i + 1,
                    'url': blob_url,
                    'blob_name': blob_name
                })
            
            # Store processing metadata
            metadata = {
                'PartitionKey': project_id,
                'RowKey': processing_id,
                'pdf_path': pdf_path,
                'total_pages': len(images),
                'image_urls': str(image_urls),  # Store as string for table storage
                'status': 'completed',
                'created_at': datetime.now().isoformat(),
                'container_name': self.container_name
            }
            
            self.storage_service.create_entity('pdf_processing', metadata)
            
            return {
                'success': True,
                'processing_id': processing_id,
                'total_pages': len(images),
                'image_urls': image_urls,
                'status': 'completed'
            }
            
        except Exception as e:
            # Log error and return failure status
            error_metadata = {
                'PartitionKey': project_id,
                'RowKey': str(uuid.uuid4()),
                'pdf_path': pdf_path,
                'status': 'failed',
                'error': str(e),
                'created_at': datetime.now().isoformat()
            }
            
            self.storage_service.create_entity('pdf_processing', error_metadata)
            
            return {
                'success': False,
                'error': str(e),
                'status': 'failed'
            }
    
    def get_processing_status(self, project_id: str, processing_id: str) -> Dict[str, Any]:
        """Get processing status and results"""
        try:
            entity = self.storage_service.get_entity('pdf_processing', project_id, processing_id)
            if entity:
                return {
                    'success': True,
                    'status': entity.get('status'),
                    'total_pages': entity.get('total_pages'),
                    'image_urls': eval(entity.get('image_urls', '[]')),  # Convert back from string
                    'created_at': entity.get('created_at'),
                    'error': entity.get('error')
                }
            else:
                return {'success': False, 'error': 'Processing record not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def list_project_processing(self, project_id: str) -> List[Dict[str, Any]]:
        """List all PDF processing records for a project"""
        try:
            entities = self.storage_service.query_entities(
                'pdf_processing',
                f"PartitionKey eq '{project_id}'"
            )
            
            results = []
            for entity in entities:
                results.append({
                    'processing_id': entity.get('RowKey'),
                    'status': entity.get('status'),
                    'total_pages': entity.get('total_pages'),
                    'created_at': entity.get('created_at'),
                    'error': entity.get('error')
                })
            
            return results
        except Exception as e:
            print(f"Error listing processing records: {e}")
            return []
