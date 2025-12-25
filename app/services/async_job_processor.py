import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
from .ai_foundry_service import AIFoundryService

logger = logging.getLogger(__name__)

class AsyncJobProcessor:
    """Background processor for long-running AI jobs to avoid web request timeouts."""
    
    def __init__(self, ai_service: AIFoundryService):
        self.ai_service = ai_service
        self.job_queue = asyncio.Queue()
        self.job_status = {}
        self.running = False
    
    async def start_processor(self):
        """Start the background job processor."""
        self.running = True
        while self.running:
            try:
                job_data = await asyncio.wait_for(self.job_queue.get(), timeout=1.0)
                await self.process_job(job_data)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in job processor: {str(e)}")
    
    async def queue_job(self, job_id: str, job_type: str, **job_data):
        """Queue a job for background processing."""
        job_data_full = {
            "job_id": job_id,
            "job_type": job_type,
            "queued_at": datetime.now().isoformat(),
            **job_data
        }
        
        # Initialize job status
        self.job_status[job_id] = {
            "status": "queued",
            "progress": 0,
            "current_step": f"{job_type.title()} job queued for processing",
            "created_at": job_data_full["queued_at"]
        }
        
        await self.job_queue.put(job_data_full)
        logger.info(f"Queued {job_type} job {job_id} for background processing")
    
    async def process_job(self, job_data: Dict[str, Any]):
        """Process a job asynchronously based on job type."""
        job_id = job_data["job_id"]
        job_type = job_data["job_type"]
        
        try:
            if job_type == "annotation":
                await self.process_annotation_job(job_data)
            elif job_type == "handwriting":
                await self.process_handwriting_job(job_data)
            elif job_type == "evaluation":
                await self.process_evaluation_job(job_data)
            else:
                raise ValueError(f"Unknown job type: {job_type}")
                
        except Exception as e:
            logger.error(f"Job {job_id} failed: {str(e)}")
            self.update_job_status(job_id, "error", 0, f"Error: {str(e)}")

    async def process_annotation_job(self, job_data: Dict[str, Any]):
        """Process full annotation job (original workflow)."""
        job_id = job_data["job_id"]
        
        # Stage 1: Initialization
        self.update_job_status(job_id, "initializing", 5, "Setting up Connected Agents")
        await asyncio.sleep(2)
        
        # Stage 2: OCR Processing
        self.update_job_status(job_id, "processing_ocr", 20, "Handwriting analysis and text extraction")
        await self.process_ocr(job_data)
        
        # Stage 3: Content Evaluation
        self.update_job_status(job_id, "processing_content", 60, "AI content evaluation and scoring")
        await self.process_content(job_data)
        
        # Stage 4: Final Scoring
        self.update_job_status(job_id, "finalizing_scores", 90, "Coordinating final scores")
        await self.finalize_scores(job_data)
        
        # Stage 5: Completion
        self.update_job_status(job_id, "completed", 100, "Processing complete")
        logger.info(f"Annotation job {job_id} completed successfully")

    async def process_handwriting_job(self, job_data: Dict[str, Any]):
        """Process handwriting analysis job."""
        job_id = job_data["job_id"]
        
        self.update_job_status(job_id, "processing", 20, "Analyzing handwriting")
        await asyncio.sleep(3)  # Simulate OCR processing
        
        self.update_job_status(job_id, "extracting", 60, "Extracting text content")
        result = self.ai_service._delegate_to_agent(
            "handwriting_analyzer",
            f"Process handwriting for {job_data.get('question_id', 'unknown')}",
            job_data
        )
        
        if result["status"] == "error":
            raise Exception(f"Handwriting analysis failed: {result['message']}")
        
        self.update_job_status(job_id, "completed", 100, "Handwriting analysis complete")
        logger.info(f"Handwriting job {job_id} completed successfully")

    async def process_evaluation_job(self, job_data: Dict[str, Any]):
        """Process answer evaluation job."""
        job_id = job_data["job_id"]
        
        self.update_job_status(job_id, "evaluating", 30, "Evaluating student answer")
        await asyncio.sleep(4)  # Simulate evaluation time
        
        # Content evaluation
        eval_result = self.ai_service._delegate_to_agent(
            "content_evaluator",
            f"Evaluate answer for job {job_id}",
            job_data
        )
        
        if eval_result["status"] == "error":
            raise Exception(f"Content evaluation failed: {eval_result['message']}")
        
        self.update_job_status(job_id, "scoring", 70, "Calculating final score")
        await asyncio.sleep(2)
        
        # Final scoring
        score_result = self.ai_service._delegate_to_agent(
            "scoring_coordinator",
            f"Calculate score for job {job_id}",
            job_data
        )
        
        if score_result["status"] == "error":
            raise Exception(f"Scoring failed: {score_result['message']}")
        
        self.update_job_status(job_id, "completed", 100, "Answer evaluation complete")
        logger.info(f"Evaluation job {job_id} completed successfully")
    
    async def process_ocr(self, job_data: Dict[str, Any]):
        """Simulate OCR processing stage."""
        # In production, this would call the handwriting analyzer agent
        await asyncio.sleep(3)  # Simulate OCR processing time
        
        # Simulate calling the agent
        result = self.ai_service._delegate_to_agent(
            "handwriting_analyzer",
            f"Process OCR for job {job_data['job_id']}",
            job_data
        )
        
        if result["status"] == "error":
            raise Exception(f"OCR processing failed: {result['message']}")
    
    async def process_content(self, job_data: Dict[str, Any]):
        """Simulate content evaluation stage."""
        # In production, this would call the content evaluator agent
        await asyncio.sleep(5)  # Simulate content processing time
        
        result = self.ai_service._delegate_to_agent(
            "content_evaluator",
            f"Evaluate content for job {job_data['job_id']}",
            job_data
        )
        
        if result["status"] == "error":
            raise Exception(f"Content evaluation failed: {result['message']}")
    
    async def finalize_scores(self, job_data: Dict[str, Any]):
        """Simulate final scoring stage."""
        # In production, this would call the scoring coordinator agent
        await asyncio.sleep(2)  # Simulate scoring time
        
        result = self.ai_service._delegate_to_agent(
            "scoring_coordinator",
            f"Finalize scores for job {job_data['job_id']}",
            job_data
        )
        
        if result["status"] == "error":
            raise Exception(f"Score finalization failed: {result['message']}")
    
    def update_job_status(self, job_id: str, status: str, progress: int, current_step: str):
        """Update job status for polling."""
        if job_id not in self.job_status:
            self.job_status[job_id] = {"created_at": datetime.now().isoformat()}
        
        self.job_status[job_id].update({
            "status": status,
            "progress": progress,
            "current_step": current_step,
            "updated_at": datetime.now().isoformat()
        })
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get current job status for polling."""
        if job_id not in self.job_status:
            return {"status": "not_found", "message": "Job not found"}
        
        status = self.job_status[job_id].copy()
        
        # Calculate elapsed time
        created_at = datetime.fromisoformat(status["created_at"])
        elapsed = (datetime.now() - created_at).total_seconds()
        status["elapsed_seconds"] = int(elapsed)
        
        # Add estimated completion
        if status["progress"] > 0 and status["status"] not in ["completed", "error"]:
            total_estimated = (elapsed / status["progress"]) * 100
            remaining = max(0, total_estimated - elapsed)
            minutes = int(remaining / 60)
            status["estimated_completion"] = f"~{minutes} minutes remaining"
        elif status["status"] == "completed":
            status["estimated_completion"] = "Completed"
        else:
            status["estimated_completion"] = "Calculating..."
        
        return status
    
    def stop_processor(self):
        """Stop the background processor."""
        self.running = False
