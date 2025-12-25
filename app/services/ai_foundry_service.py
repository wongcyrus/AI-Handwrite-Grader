import os
import asyncio
import json
from datetime import datetime
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ConnectedAgentTool, MessageRole
from azure.identity import DefaultAzureCredential

class AIFoundryService:
    def __init__(self):
        self.project_client = AIProjectClient(
            endpoint=os.environ.get("AI_FOUNDRY_ENDPOINT"),
            credential=DefaultAzureCredential(),
        )
        self.agents = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all connected agents"""
        try:
            # OCR Agent
            self.agents['ocr'] = self.project_client.agents.create_agent(
                model=os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4o-mini"),
                name="ocr_agent",
                instructions="Extract text from PDF images using OCR. Focus on handwritten text recognition and return structured text data with confidence scores."
            )
            
            # Layout Agent
            self.agents['layout'] = self.project_client.agents.create_agent(
                model=os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4o-mini"),
                name="layout_agent",
                instructions="Analyze page layout and structure. Identify headers, sections, question areas, and answer spaces. Return coordinate-based layout information."
            )
            
            # Question Detection Agent
            self.agents['question_detection'] = self.project_client.agents.create_agent(
                model=os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4o-mini"),
                name="question_detection_agent",
                instructions="Identify question boundaries and labels (Q1, Q2, etc.). Detect question types (multiple choice, short answer, essay). Return question metadata."
            )
            
            # Answer Extraction Agent
            self.agents['answer_extraction'] = self.project_client.agents.create_agent(
                model=os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4o-mini"),
                name="answer_extraction_agent",
                instructions="Extract student responses from identified answer areas. Handle handwritten text, drawings, and multiple choice selections."
            )
            
            # Validation Agent
            self.agents['validation'] = self.project_client.agents.create_agent(
                model=os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4o-mini"),
                name="validation_agent",
                instructions="Validate annotation quality and confidence scores. Check for missing or unclear annotations. Suggest improvements."
            )
            
            # Quality Control Agent
            self.agents['quality_control'] = self.project_client.agents.create_agent(
                model=os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4o-mini"),
                name="quality_control_agent",
                instructions="Final review of all annotations. Provide overall confidence score and recommendations for manual review."
            )
            
            # Main Orchestrator Agent with connected agents
            connected_agents = [
                ConnectedAgentTool(
                    id=self.agents['ocr'].id,
                    name="ocr_agent",
                    description="Extracts text from PDF images using OCR"
                ),
                ConnectedAgentTool(
                    id=self.agents['layout'].id,
                    name="layout_agent", 
                    description="Analyzes page layout and structure"
                ),
                ConnectedAgentTool(
                    id=self.agents['question_detection'].id,
                    name="question_detection_agent",
                    description="Identifies question boundaries and types"
                ),
                ConnectedAgentTool(
                    id=self.agents['answer_extraction'].id,
                    name="answer_extraction_agent",
                    description="Extracts student responses from answer areas"
                ),
                ConnectedAgentTool(
                    id=self.agents['validation'].id,
                    name="validation_agent",
                    description="Validates annotation quality and confidence"
                ),
                ConnectedAgentTool(
                    id=self.agents['quality_control'].id,
                    name="quality_control_agent",
                    description="Performs final quality control review"
                )
            ]
            
            self.main_agent = self.project_client.agents.create_agent(
                model=os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4o-mini"),
                name="grading_orchestrator",
                instructions="""You are a grading orchestrator that coordinates specialized agents to process student assignments.
                
                For each PDF document:
                1. Use OCR agent to extract text
                2. Use layout agent to analyze structure  
                3. Use question detection agent to identify questions
                4. Use answer extraction agent to get student responses
                5. Use validation agent to check quality
                6. Use quality control agent for final review
                
                Return structured JSON with all annotation data.""",
                tools=[agent.definitions for agent in connected_agents]
            )
            
        except Exception as e:
            print(f"Error initializing agents: {e}")
            raise e
    
    def start_annotation_job(self, project_id, pdf_url, excel_url):
        """Start annotation job for a project"""
        try:
            # Create thread for this job
            thread = self.project_client.agents.threads.create()
            
            # Create message with file URLs
            message = self.project_client.agents.messages.create(
                thread_id=thread.id,
                role=MessageRole.USER,
                content=f"""Process this student assignment:
                PDF URL: {pdf_url}
                Answer Template: {excel_url}
                
                Please coordinate all agents to:
                1. Extract text from the PDF
                2. Analyze the layout structure
                3. Identify all questions and their boundaries
                4. Extract student answers from each question area
                5. Validate the annotation quality
                6. Provide final quality control assessment
                
                Return structured JSON with all annotation data including coordinates, confidence scores, and extracted text."""
            )
            
            # Start the run (async processing)
            run = self.project_client.agents.runs.create(
                thread_id=thread.id,
                agent_id=self.main_agent.id
            )
            
            # Store job info
            job_id = f"{project_id}_{thread.id}_{run.id}"
            
            return job_id
            
        except Exception as e:
            print(f"Error starting annotation job: {e}")
            raise e
    
    def get_job_status(self, job_id):
        """Get status of annotation job"""
        try:
            # Parse job_id to get thread and run IDs
            parts = job_id.split('_')
            if len(parts) < 3:
                return {'status': 'error', 'message': 'Invalid job ID'}
            
            project_id, thread_id, run_id = parts[0], parts[1], parts[2]
            
            # Get run status
            run = self.project_client.agents.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            
            status_map = {
                'queued': {'status': 'queued', 'progress': 10},
                'in_progress': {'status': 'processing', 'progress': 50},
                'completed': {'status': 'completed', 'progress': 100},
                'failed': {'status': 'failed', 'progress': 0},
                'cancelled': {'status': 'cancelled', 'progress': 0}
            }
            
            result = status_map.get(run.status, {'status': 'unknown', 'progress': 0})
            
            if run.status == 'completed':
                # Get the results
                messages = self.project_client.agents.messages.list(thread_id=thread_id)
                last_message = messages.get_last_message_by_role(MessageRole.AGENT)
                
                if last_message:
                    result['data'] = last_message.text_messages[0].text.value
            
            return result
            
        except Exception as e:
            print(f"Error getting job status: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def cleanup_agents(self):
        """Cleanup agents when shutting down"""
        try:
            for agent in self.agents.values():
                self.project_client.agents.delete_agent(agent.id)
            
            if hasattr(self, 'main_agent'):
                self.project_client.agents.delete_agent(self.main_agent.id)
                
        except Exception as e:
            print(f"Error cleaning up agents: {e}")
