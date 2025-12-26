# Deployment and Local Development Guide

## Testing

### Test Structure
- `tests/test_agents.py` - Unit tests for AI Foundry service (fast, mocked)
- `tests/test_agent_integration.py` - Integration tests with real Azure agents
- `pytest.ini` - Test configuration with markers

### Running Tests
```bash
# Interactive test runner
./run-tests.sh

# Unit tests only (fast)
python -m pytest tests/test_agents.py -v

# All tests including integration
python -m pytest tests/ -v

# Skip integration tests
python -m pytest -m "not integration"
```

### Test Categories
- **Unit Tests** (`@pytest.mark.unit`) - Service logic with mocks
- **Integration Tests** (`@pytest.mark.integration`) - Real deployed agents

## Local Development

### Prerequisites
- Python 3.9+
- Docker (for Azurite storage emulator)
- Azure AI Foundry project with deployed model

### Quick Start
```bash
# 1. Clone and setup
git clone <repository-url>
cd AI-Handwrite-Grader

# 2. Setup development environment
./setup-dev.sh

# 3. Configure environment
cp app/.env.template app/.env
# Edit app/.env with your Azure credentials

# 4. Deploy Connected Agents (one-time)
python deploy_agents.py

# 5. Start development server
cd app
python app.py
```

### Environment Configuration
```bash
# app/.env
AZURE_AI_PROJECT_ENDPOINT=https://your-project.services.ai.azure.com/api/projects/your-project
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4
HANDWRITING_AGENT_ID=handwriting_agent_abc123
CONTENT_AGENT_ID=content_agent_def456
SCORING_AGENT_ID=scoring_agent_ghi789
MAIN_AGENT_ID=main_agent_jkl012

# Storage (local development uses Azurite)
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;
```

### Development Workflow
```bash
# Start storage emulator
docker-compose up azurite -d

# Run tests
./run-clean-tests.sh

# Start Flask app
cd app && python app.py

# Access at http://localhost:5000
```

## Production Deployment

### Azure App Service Deployment

#### 1. Azure Resources Setup
```bash
# Create resource group
az group create --name ai-grader-rg --location eastus

# Create App Service plan
az appservice plan create --name ai-grader-plan --resource-group ai-grader-rg --sku B1 --is-linux

# Create web app
az webapp create --resource-group ai-grader-rg --plan ai-grader-plan --name ai-handwrite-grader --runtime "PYTHON|3.9"
```

#### 2. Configure App Settings
```bash
# Set environment variables
az webapp config appsettings set --resource-group ai-grader-rg --name ai-handwrite-grader --settings \
  AZURE_AI_PROJECT_ENDPOINT="https://your-project.services.ai.azure.com/api/projects/your-project" \
  AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-4" \
  HANDWRITING_AGENT_ID="your-handwriting-agent-id" \
  CONTENT_AGENT_ID="your-content-agent-id" \
  SCORING_AGENT_ID="your-scoring-agent-id" \
  MAIN_AGENT_ID="your-main-agent-id"
```

#### 3. Deploy Code
```bash
# Using Azure CLI
az webapp deployment source config --resource-group ai-grader-rg --name ai-handwrite-grader --repo-url https://github.com/your-repo --branch main --manual-integration

# Or using GitHub Actions (see .github/workflows/deploy.yml)
```

### Docker Deployment

#### Build and Run
```bash
# Build image
docker build -t ai-handwrite-grader .

# Run container
docker run -p 5000:5000 --env-file app/.env ai-handwrite-grader
```

#### Docker Compose (Production)
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - AZURE_AI_PROJECT_ENDPOINT=${AZURE_AI_PROJECT_ENDPOINT}
      - AZURE_AI_MODEL_DEPLOYMENT_NAME=${AZURE_AI_MODEL_DEPLOYMENT_NAME}
      - HANDWRITING_AGENT_ID=${HANDWRITING_AGENT_ID}
      - CONTENT_AGENT_ID=${CONTENT_AGENT_ID}
      - SCORING_AGENT_ID=${SCORING_AGENT_ID}
      - MAIN_AGENT_ID=${MAIN_AGENT_ID}
    restart: unless-stopped
```

### Terraform Deployment (Infrastructure as Code)

```bash
# Initialize Terraform
cd terraform
terraform init

# Plan deployment
terraform plan -var="project_name=ai-grader" -var="location=eastus"

# Deploy infrastructure and agents (one command)
terraform apply
```

## Configuration Management

### Required Azure Resources
1. **Azure AI Foundry Project** with deployed GPT-4 model
2. **Storage Account** for file uploads and data
3. **App Service** or **Container Instance** for hosting
4. **Connected Agents** deployed via `deploy_agents.py`

### Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_AI_PROJECT_ENDPOINT` | AI Foundry project endpoint | Yes |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | Model deployment name | Yes |
| `HANDWRITING_AGENT_ID` | Deployed handwriting agent ID | Yes |
| `CONTENT_AGENT_ID` | Deployed content evaluator agent ID | Yes |
| `SCORING_AGENT_ID` | Deployed scoring coordinator agent ID | Yes |
| `MAIN_AGENT_ID` | Deployed main orchestrator agent ID | Yes |
| `AZURE_STORAGE_CONNECTION_STRING` | Storage account connection | Yes |
| `AGENT_MAX_RETRIES` | Max retry attempts for agents | No (default: 3) |
| `AGENT_RETRY_DELAY` | Retry delay in seconds | No (default: 1) |

## Monitoring and Maintenance

### Health Checks
```bash
# Check app health
curl http://your-app-url/health

# Check agent status
curl http://your-app-url/api/agents/status
```

### Logs and Debugging
```bash
# Azure App Service logs
az webapp log tail --resource-group ai-grader-rg --name ai-handwrite-grader

# Docker logs
docker logs ai-handwrite-grader

# Local development logs
tail -f app/logs/app.log
```

### Scaling Considerations
- **App Service**: Scale up/out based on concurrent users
- **Storage**: Monitor blob storage usage and costs
- **AI Foundry**: Monitor token usage and rate limits
- **Connected Agents**: Consider agent deployment costs

## Troubleshooting

### Common Issues
1. **Agent deployment fails**: Check Azure credentials and permissions
2. **Storage connection errors**: Verify connection string and firewall rules
3. **AI processing timeouts**: Check Azure AI Foundry quotas and limits
4. **Job status not updating**: Verify background processor is running

### Debug Commands
```bash
# Test Azure connection
python -c "from services.ai_foundry_service import AIFoundryService; AIFoundryService()"

# Test storage connection
python -c "from services.storage_service import StorageService; StorageService().test_connection()"

# Check deployed agents
python deploy_agents.py --list
```
