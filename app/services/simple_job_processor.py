import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class AsyncJobProcessor:
    """Simple job processor that avoids event loop conflicts."""
    
    def __init__(self):
        self.jobs = {}
        self.running = False
    
    async def start_processor(self):
        """Start the background job processor."""
        self.running = True
        logger.info("Simple job processor started")
    
    def queue_job(self, job_id: str, job_type: str, **kwargs) -> str:
        """Queue a job for processing (synchronous interface)."""
        try:
            # Initialize job status
            self.jobs[job_id] = {
                'id': job_id,
                'type': job_type,
                'status': 'queued',
                'progress': 0,
                'created_at': datetime.utcnow().isoformat(),
                'kwargs': kwargs
            }
            
            # Immediately mark as processing for demo
            self.jobs[job_id]['status'] = 'processing'
            self.jobs[job_id]['progress'] = 50
            
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to queue job {job_id}: {e}")
            return job_id
            
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status."""
        if job_id not in self.jobs:
            return {"status": "not_found", "message": "Job not found"}
            
        # Simulate progress for demo
        job = self.jobs[job_id]
        if job['status'] == 'processing' and job['progress'] < 100:
            job['progress'] = min(100, job['progress'] + 10)
            if job['progress'] >= 100:
                job['status'] = 'completed'
                job['result'] = f"Mock result for {job['type']} job"
            
        return job
        
    def stop_processor(self):
        """Stop the job processor."""
        self.running = False
        logger.info("Job processor stopped")
