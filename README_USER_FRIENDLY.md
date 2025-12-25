# AI Handwriting Grader - User Friendly Mode

## Quick Start

### Prerequisites
- Azure CLI installed and logged in
- Terraform installed
- Docker installed
- Python 3.11+

### 1. Infrastructure Setup

```bash
# Navigate to Terraform directory
cd terraform/environments/dev

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var-file="terraform.tfvars"

# Deploy infrastructure
terraform apply -var-file="terraform.tfvars"
```

### 2. Local Development

```bash
# Navigate to app directory
cd app

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export AZURE_STORAGE_CONNECTION_STRING="your_connection_string"
export AI_FOUNDRY_ENDPOINT="your_ai_foundry_endpoint"
export MODEL_DEPLOYMENT_NAME="gpt-4o-mini"
export SECRET_KEY="your_secret_key"

# Run application
python app.py
```

### 3. Docker Deployment

```bash
# Build image
docker build -t ai-grader-app ./app

# Run container
docker run -p 5000:5000 \
  -e AZURE_STORAGE_CONNECTION_STRING="your_connection_string" \
  -e AI_FOUNDRY_ENDPOINT="your_ai_foundry_endpoint" \
  ai-grader-app
```

## Architecture

### Azure AI Foundry Connected Agents
- **Main Agent**: Grading Orchestrator
- **OCR Agent**: Text extraction from images
- **Layout Agent**: Page structure analysis
- **Question Detection Agent**: Identify question boundaries
- **Answer Extraction Agent**: Extract student responses
- **Validation Agent**: Quality control
- **Quality Control Agent**: Final review

### Cost-Effective Azure Services
- **Container Instances**: Pay-per-second compute
- **Table Storage**: Ultra-low cost NoSQL database
- **Blob Storage**: File storage for PDFs and images
- **AI Foundry**: Pay-per-use AI services

### Estimated Monthly Costs
- Container Instances: $10-30
- Storage Account: $5-10
- AI Foundry: $10-20
- **Total: ~$25-60/month**

## Features

### ✅ Implemented
- [x] Terraform infrastructure setup
- [x] Flask web application with authentication
- [x] Azure Table Storage integration
- [x] Azure AI Foundry Connected Agents
- [x] Project management dashboard
- [x] File upload to Blob Storage
- [x] Real-time processing status
- [x] Docker containerization
- [x] CI/CD pipeline

### 🚧 In Progress
- [ ] Annotation review interface
- [ ] Scoring interface integration
- [ ] Results export system
- [ ] Email distribution

### 📋 Planned
- [ ] Advanced analytics dashboard
- [ ] Batch processing
- [ ] API endpoints
- [ ] Mobile responsive design

## Usage

1. **Register/Login**: Create account or sign in
2. **Create Project**: Set up new grading project
3. **Upload Files**: Upload PDF assignments and Excel answer key
4. **AI Processing**: Connected agents automatically process files
5. **Review Annotations**: Manual refinement of AI results
6. **Grade Assignments**: Score student responses
7. **Export Results**: Generate reports and send to students

## Development

### Project Structure
```
app/
├── app.py                 # Main Flask application
├── models/               # Data models
├── services/             # Business logic services
├── templates/            # HTML templates
├── static/              # CSS, JS, images
├── Dockerfile           # Container configuration
└── requirements.txt     # Python dependencies

terraform/
├── environments/        # Environment-specific configs
└── modules/            # Reusable Terraform modules
```

### Environment Variables
```bash
AZURE_STORAGE_CONNECTION_STRING=  # Azure Storage connection
AI_FOUNDRY_ENDPOINT=             # AI Foundry project endpoint
MODEL_DEPLOYMENT_NAME=           # AI model deployment name
SECRET_KEY=                      # Flask secret key
```

## Deployment

### Manual Deployment
```bash
# Deploy infrastructure
terraform apply -var-file="terraform.tfvars"

# Build and push image
docker build -t ai-grader-app ./app
docker tag ai-grader-app your-registry.azurecr.io/ai-grader-app:latest
docker push your-registry.azurecr.io/ai-grader-app:latest
```

### Automated Deployment
Push to `user-friendly-mode` branch triggers automatic deployment via GitHub Actions.

## Monitoring

- **Azure Monitor**: Application insights and metrics
- **Container Logs**: Real-time application logs
- **Cost Alerts**: Automated cost monitoring
- **Health Checks**: Container health monitoring

## Support

For issues and questions:
1. Check the logs in Azure Container Instances
2. Review Terraform state for infrastructure issues
3. Monitor AI Foundry agent performance
4. Check Azure Storage connectivity
