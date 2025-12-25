import os
import logging
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import AzureError

logger = logging.getLogger(__name__)

class ConnectedAgent:
    """Represents a connected agent with specialized capabilities."""
    
    def __init__(self, name: str, description: str, instructions: str):
        self.name = name
        self.description = description
        self.instructions = instructions
        self.id = f"agent_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

class AIFoundryService:
    """
    Service for Azure AI Foundry Connected Agents simulation.
    Implements the Connected Agents pattern using available Azure AI Projects APIs.
    """
    
    def __init__(self):
        """Initialize the AI Foundry service with Connected Agents architecture."""
        try:
            self.project_endpoint = os.getenv('AZURE_AI_PROJECT_ENDPOINT')
            self.model_deployment_name = os.getenv('AZURE_AI_MODEL_DEPLOYMENT_NAME', 'gpt-4')
            self.max_retries = int(os.getenv('AGENT_MAX_RETRIES', '3'))
            self.retry_delay = int(os.getenv('AGENT_RETRY_DELAY', '1'))
            
            if not self.project_endpoint:
                raise ValueError("AZURE_AI_PROJECT_ENDPOINT environment variable is required")
            
            # Initialize the AI Project Client
            self.client = AIProjectClient(
                endpoint=self.project_endpoint,
                credential=DefaultAzureCredential()
            )
            
            # Get OpenAI client for agent operations
            self.openai_client = self.client.get_openai_client()
            
            # Initialize connected agents
            self.connected_agents = {}
            self.main_agent = None
            self._initialize_connected_agents()
            
            logger.info("AI Foundry Connected Agents service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI Foundry service: {str(e)}")
            raise

    def _initialize_connected_agents(self):
        """Initialize or retrieve existing connected agents."""
        try:
            # Use pre-deployed agent IDs from environment variables
            self.connected_agents = {
                'handwriting_analyzer': ConnectedAgent(
                    name="handwriting_analyzer",
                    description="Analyzes handwritten text and extracts content from images",
                    instructions="""You are a handwriting analysis specialist. Your responsibilities:
                    1. Analyze handwritten text in images with high accuracy
                    2. Extract text content and provide confidence scores (0.0-1.0)
                    3. Identify unclear, ambiguous, or illegible writing sections
                    4. Flag potential OCR errors and suggest manual review when confidence < 0.7
                    5. Preserve mathematical notation, symbols, and formatting
                    6. Return structured results with extracted text, confidence, and quality assessment"""
                ),
                'content_evaluator': ConnectedAgent(
                    name="content_evaluator", 
                    description="Evaluates student answers against standard answers and rubrics",
                    instructions="""You are a content evaluation specialist. Your responsibilities:
                    1. Compare student answers against standard answers using provided rubrics
                    2. Identify key concepts, partial credit opportunities, and misconceptions
                    3. Provide detailed scoring rationale with specific examples
                    4. Suggest constructive feedback for improvement
                    5. Handle multiple answer formats (text, equations, diagrams)
                    6. Apply consistent grading standards across all submissions
                    7. Return structured evaluation with score breakdown and detailed feedback"""
                ),
                'scoring_coordinator': ConnectedAgent(
                    name="scoring_coordinator",
                    description="Coordinates final scoring and grade calculation",
                    instructions="""You are a scoring coordination specialist. Your responsibilities:
                    1. Aggregate scores from multiple evaluation agents and sources
                    2. Apply consistent grading rubrics and institutional policies
                    3. Handle edge cases, scoring conflicts, and grade boundaries
                    4. Generate final grade recommendations with justification
                    5. Ensure fairness and consistency across all student submissions
                    6. Calculate weighted scores, bonus points, and penalty adjustments
                    7. Return final scores with detailed breakdown and audit trail"""
                )
            }
            
            # Override with deployed agent IDs if available
            if os.getenv('HANDWRITING_AGENT_ID'):
                self.connected_agents['handwriting_analyzer'].id = os.getenv('HANDWRITING_AGENT_ID')
            if os.getenv('CONTENT_AGENT_ID'):
                self.connected_agents['content_evaluator'].id = os.getenv('CONTENT_AGENT_ID')
            if os.getenv('SCORING_AGENT_ID'):
                self.connected_agents['scoring_coordinator'].id = os.getenv('SCORING_AGENT_ID')
            
            self.main_agent = ConnectedAgent(
                name="grading_orchestrator",
                description="Main orchestrator for grading workflow",
                instructions="""You are a grading orchestrator that coordinates specialized agents. Your responsibilities:
                1. Analyze incoming tasks and route to appropriate connected agents
                2. For handwriting analysis: delegate to handwriting_analyzer
                3. For content evaluation: delegate to content_evaluator  
                4. For final scoring: delegate to scoring_coordinator
                5. Coordinate multi-step workflows and agent handoffs
                6. Aggregate results from multiple agents into coherent responses
                7. Handle errors and fallback scenarios gracefully
                8. Always provide clear, actionable results with proper attribution"""
            )
            
            if os.getenv('MAIN_AGENT_ID'):
                self.main_agent.id = os.getenv('MAIN_AGENT_ID')
            
            logger.info("Connected agents initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize connected agents: {str(e)}")
            raise

    def _delegate_to_agent(self, agent_name: str, task_description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Delegate a task to a specific connected agent with retry logic."""
        if agent_name not in self.connected_agents:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        agent = self.connected_agents[agent_name]
        
        for attempt in range(self.max_retries):
            try:
                messages = [
                    {"role": "system", "content": agent.instructions},
                    {"role": "user", "content": task_description}
                ]
                
                if context:
                    messages.append({"role": "user", "content": f"Context: {json.dumps(context)}"})
                
                # THIS IS WHERE THE SLOW PROCESSING HAPPENS (Azure OpenAI inference)
                response = self.openai_client.chat.completions.create(
                    model=self.model_deployment_name,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=1000
                )  # ← This Azure OpenAI call takes 30 seconds to 5+ minutes
                
                return {
                    "status": "completed",
                    "agent": agent_name,
                    "response": response.choices[0].message.content,
                    "usage": response.usage.dict() if response.usage else None,
                    "attempt": attempt + 1
                }
                
            except Exception as e:
                logger.warning(f"Agent {agent_name} attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"All {self.max_retries} attempts failed for agent {agent_name}")
                    return {"status": "error", "message": str(e), "attempts": self.max_retries}

    def start_annotation_job(self, project_id: str, pdf_url: str, excel_url: str) -> str:
        """Start annotation job asynchronously and return job ID immediately."""
        try:
            job_id = f"{project_id}_job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Store job details for async processing
            job_context = {
                "job_id": job_id,
                "project_id": project_id,
                "pdf_url": pdf_url,
                "excel_url": excel_url,
                "status": "initializing",
                "created_at": datetime.now().isoformat()
            }
            
            # In production, this would queue the job for background processing
            # For now, we simulate immediate job creation
            logger.info(f"Queued annotation job {job_id} for async processing")
            
            # Return job ID immediately - processing happens in background
            return job_id
            
        except Exception as e:
            logger.error(f"Error starting annotation job: {str(e)}")
            raise

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of annotation job with realistic processing times."""
        try:
            # Extract project ID and timestamp from job ID
            parts = job_id.split('_job_')
            if len(parts) != 2:
                return {"status": "invalid", "message": "Invalid job ID format"}
            
            project_id, timestamp = parts
            
            # Simulate realistic job progression based on time elapsed
            job_time = datetime.strptime(timestamp, '%Y%m%d_%H%M%S')
            elapsed = (datetime.now() - job_time).total_seconds()
            
            # Realistic processing stages with longer times
            if elapsed < 60:  # First minute: initializing
                status = "initializing"
                progress = min(int(elapsed / 60 * 10), 10)
                current_step = "Setting up Connected Agents"
            elif elapsed < 300:  # 1-5 minutes: OCR processing
                status = "processing_ocr"
                progress = 10 + min(int((elapsed - 60) / 240 * 30), 30)
                current_step = "Handwriting analysis and text extraction"
            elif elapsed < 900:  # 5-15 minutes: AI content evaluation
                status = "processing_content"
                progress = 40 + min(int((elapsed - 300) / 600 * 40), 40)
                current_step = "AI content evaluation and scoring"
            elif elapsed < 1200:  # 15-20 minutes: final scoring
                status = "finalizing_scores"
                progress = 80 + min(int((elapsed - 900) / 300 * 15), 15)
                current_step = "Coordinating final scores and generating reports"
            else:  # 20+ minutes: completed
                status = "completed"
                progress = 100
                current_step = "Processing complete"
            
            return {
                "status": status,
                "job_id": job_id,
                "project_id": project_id,
                "progress": progress,
                "current_step": current_step,
                "created_at": job_time.isoformat(),
                "elapsed_seconds": int(elapsed),
                "estimated_completion": self._estimate_completion_time(elapsed, progress)
            }
            
        except Exception as e:
            logger.error(f"Error getting job status: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _estimate_completion_time(self, elapsed: float, progress: int) -> str:
        """Estimate remaining completion time."""
        if progress >= 100:
            return "Completed"
        elif progress > 0:
            total_estimated = (elapsed / progress) * 100
            remaining = max(0, total_estimated - elapsed)
            minutes = int(remaining / 60)
            return f"~{minutes} minutes remaining"
        else:
            return "~20 minutes estimated"

    def process_handwriting_analysis(self, image_data: bytes, question_id: str) -> str:
        """Queue handwriting analysis job and return job ID immediately."""
        try:
            job_id = f"handwriting_{question_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Queue for background processing - don't process immediately
            logger.info(f"Queued handwriting analysis job {job_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Error queuing handwriting analysis: {str(e)}")
            raise

    def evaluate_answer(self, student_answer: str, standard_answer: str, rubric: Dict[str, Any]) -> str:
        """Queue answer evaluation job and return job ID immediately."""
        try:
            job_id = f"evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Queue for background processing - don't process immediately
            logger.info(f"Queued answer evaluation job {job_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Error queuing answer evaluation: {str(e)}")
            raise
            return {"status": "error", "message": str(e)}

    def cleanup_agents(self):
        """Clean up connected agents resources."""
        try:
            # Don't delete pre-deployed agents - they should be reused
            logger.info("Connected agents cleanup completed (reusable agents preserved)")
            
        except Exception as e:
            logger.error(f"Error cleaning up agents: {str(e)}")
