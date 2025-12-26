# Azure AI Foundry Connected Agents Implementation

## Agent Management

### Single Source Configuration
All agent configurations (prompts, descriptions, instructions) are managed in one file:
- **File**: `deploy_agents_tf.py` (lines 25-45)
- **Configuration**: `agents_config` array

### Update Agent Prompts
1. **Edit** `deploy_agents_tf.py`:
```python
{
    'name': 'Handwriting Analyzer',
    'description': 'Your updated description',
    'instructions': '''Your new prompt instructions here...''',
    'env_var': 'HANDWRITING_AGENT_ID'
}
```

2. **Apply updates**:
```bash
./update-agents.sh     # Quick update (recommended)
./recreate-agents.sh   # Full recreation for major changes
```

### Environment Auto-Update
- `.env` files auto-generated from Terraform outputs
- Agent IDs automatically populated after deployment
- No manual credential management required
- Fresh checkout + `./deploy.sh` = fully configured system

## Deployed Agents (Live Production)
All agents successfully deployed and tested:

- ✅ **Handwriting Analyzer** (`asst_7dPN3cHaAxjl5712Xm0EwaNI`) - Live and functional
- ✅ **Content Evaluator** (`asst_XnSPMfZv0vXcrA0svhBfgVrk`) - Live and functional  
- ✅ **Scoring Coordinator** (`asst_kqD4ic5Cq3HZeDuFtClOQGcL`) - Live and functional
- ✅ **Main Orchestrator** (`asst_wA5KIyptGvd59gzAgRxurQlS`) - Live and functional

### Test Coverage
- ✅ **Unit Tests** - Service initialization, agent creation, job handling
- ✅ **Integration Tests** - Agent existence verification, basic connectivity
- ✅ **PyTest Integration** - Proper test structure with markers and configuration

## Overview

The AI Foundry service has been updated to implement the **Connected Agents** architecture pattern using Azure AI Foundry and the Azure AI Projects SDK. This implementation follows Microsoft's Connected Agents design principles for multi-agent orchestration.

## Architecture

### Connected Agents Pattern

The implementation uses a **main orchestrator agent** that delegates specialized tasks to **connected agents**:

```
Main Agent (Grading Orchestrator)
├── Handwriting Analyzer Agent
├── Content Evaluator Agent  
└── Scoring Coordinator Agent
```

### Agent Specialization

1. **Handwriting Analyzer Agent**
   - Analyzes handwritten text in images
   - Extracts text content with confidence scores
   - Identifies unclear or ambiguous writing
   - Flags potential OCR errors for manual review

2. **Content Evaluator Agent**
   - Compares student answers against standard answers
   - Identifies key concepts and partial credit opportunities
   - Provides detailed scoring rationale
   - Suggests areas for improvement

3. **Scoring Coordinator Agent**
   - Aggregates scores from multiple evaluation agents
   - Applies consistent grading rubrics
   - Handles edge cases and scoring conflicts
   - Generates final grade recommendations

4. **Main Orchestrator Agent**
   - Routes tasks to appropriate connected agents
   - Coordinates the overall grading workflow
   - Provides unified interface for the application

## Implementation Details

### Technology Stack

- **Azure AI Projects SDK**: `azure-ai-projects>=1.0.0b1`
- **Azure Identity**: For authentication with DefaultAzureCredential
- **OpenAI Client**: Accessed through AIProjectClient for agent interactions

### Key Components

#### ConnectedAgent Class
```python
class ConnectedAgent:
    def __init__(self, name: str, description: str, instructions: str):
        self.name = name
        self.description = description
        self.instructions = instructions
        self.id = f"agent_{name}_{timestamp}"
```

#### AIFoundryService Class
- Initializes connected agents with specialized roles
- Provides delegation mechanism via `_delegate_to_agent()`
- Implements workflow methods for grading tasks
- Uses OpenAI client for agent communication

### Core Methods

1. **start_annotation_job()**: Initiates grading workflow using handwriting analyzer
2. **process_handwriting_analysis()**: Delegates handwriting analysis to specialized agent
3. **evaluate_answer()**: Uses content evaluator and scoring coordinator in sequence
4. **get_job_status()**: Tracks job progress and status

## Benefits of Connected Agents

### Modularity
- Each agent has a focused, specialized responsibility
- Easy to add new agents without modifying existing ones
- Clear separation of concerns

### Scalability
- Agents can be scaled independently based on workload
- Parallel processing capabilities for different tasks
- Efficient resource utilization

### Maintainability
- Easier debugging with focused agent responsibilities
- Better traceability of decision-making process
- Simplified testing of individual agent capabilities

### Reliability
- Fault isolation - failure in one agent doesn't affect others
- Consistent behavior through specialized instructions
- Better error handling and recovery

## Configuration

### Agent Deployment (One-Time Setup)
```bash
# Deploy agents once
python deploy_agents.py
```

### Environment Variables
```bash
# Azure AI Foundry Configuration
AZURE_AI_PROJECT_ENDPOINT=https://your-project.services.ai.azure.com/api/projects/your-project
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4

# Pre-deployed Agent IDs (from deploy_agents.py output)
HANDWRITING_AGENT_ID=handwriting_agent_abc123
CONTENT_AGENT_ID=content_agent_def456
SCORING_AGENT_ID=scoring_agent_ghi789
MAIN_AGENT_ID=main_agent_jkl012
```

### Azure Setup Requirements
1. Azure AI Foundry project
2. Deployed language model (GPT-4 recommended)
3. Proper RBAC permissions for the service principal

## Usage Example

```python
# Initialize the service
service = AIFoundryService()

# Start annotation job
job_id = service.start_annotation_job(
    project_id='proj-123',
    pdf_url='https://storage.com/exam.pdf',
    excel_url='https://storage.com/answers.xlsx'
)

# Process handwriting analysis
result = service.process_handwriting_analysis(
    image_data=image_bytes,
    question_id='q1'
)

# Evaluate student answer
evaluation = service.evaluate_answer(
    student_answer="Student response",
    standard_answer="Expected answer",
    rubric={"total_points": 10}
)
```

## Testing

The implementation includes comprehensive tests covering:
- Agent initialization and configuration
- Task delegation and routing
- Error handling and recovery
- Integration with Azure services
- Mock-based testing for reliable CI/CD

## Enhancements

### Detailed Agent Instructions
Each agent now has comprehensive, specific instructions:
- **Handwriting Analyzer**: OCR accuracy, confidence scoring, error detection
- **Content Evaluator**: Rubric-based evaluation, partial credit, feedback generation  
- **Scoring Coordinator**: Grade aggregation, consistency, audit trails
- **Main Orchestrator**: Task routing, workflow coordination, error handling

### Retry Logic
Automatic retry mechanism for agent communication failures:
- Configurable max retries (default: 3)
- Configurable retry delay (default: 1 second)
- Exponential backoff for resilience
- Detailed error reporting with attempt counts

### Environment Template
`.env.template` file provided with all required configuration variables and optional retry settings.

When Azure AI Foundry Connected Agents become generally available:
1. Replace simulation with actual Connected Agents API
2. Add support for agent-to-agent communication
3. Implement advanced orchestration patterns
4. Add support for custom tools and functions

## Implementation Status
✅ **COMPLETE** - All agents deployed and configured

### Current Deployment
- **Model**: GPT-5.2-chat (version 2025-12-11)
- **SKU**: GlobalStandard with 50 TPM capacity
- **Endpoint**: https://aihandwritegraderdevai.cognitiveservices.azure.com/

### Agent IDs
```
HANDWRITING_AGENT_ID=handwriting_agent_e857f7fd
CONTENT_AGENT_ID=content_agent_63eee7fd
SCORING_AGENT_ID=scoring_agent_f814058e
MAIN_AGENT_ID=main_agent_8ca33088
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-52-chat
```

### Infrastructure Status
- AI Foundry Hub: `ai-handwrite-grader-dev-hub` ✅
- AI Foundry Project: `ai-handwrite-grader-dev-proj` ✅
- Container Instance: `http://52.149.246.0` (HTTP 200 OK) ✅
- Local Development: Environment configured in `app/.env` ✅

Both container and local environments are configured with all required environment variables.
