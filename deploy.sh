#!/bin/bash
set -e

echo "🚀 Starting complete AI Handwrite Grader deployment..."

# Check prerequisites
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Please install it first."
    exit 1
fi

if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform not found. Please install it first."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install it first."
    exit 1
fi

# Check Azure login
if ! az account show &> /dev/null; then
    echo "❌ Not logged into Azure. Please run 'az login' first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Setup Python environment
echo "🐍 Setting up Python environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r app/requirements.txt

# Deploy infrastructure
echo "🏗️ Deploying infrastructure..."
cd terraform
terraform init
terraform apply -auto-approve

# Get outputs
echo "📋 Getting deployment outputs..."
RESOURCE_GROUP=$(terraform output -raw resource_group_name)
STORAGE_ACCOUNT=$(terraform output -raw storage_account_name)
CONTAINER_FQDN=$(terraform output -raw container_instance_fqdn)
AI_ENDPOINT=$(terraform output -raw ai_foundry_endpoint)

cd ..

# Update .env files with Terraform outputs
echo "🔄 Updating environment files..."
./update-env.sh

# Deploy agents
echo "🤖 Deploying Connected Agents..."
source venv/bin/activate
python deploy_agents_tf.py

echo "✅ Deployment complete!"
echo ""
echo "📊 Deployment Summary:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Storage Account: $STORAGE_ACCOUNT"
echo "  Web App URL: http://$CONTAINER_FQDN"
echo "  AI Endpoint: $AI_ENDPOINT"
echo "  Region: East US 2"
echo "  GPT-5 Model: Deployed with GlobalStandard SKU"
echo "  Connected Agents: 4 agents deployed"
echo "  Environment Files: Auto-updated with credentials"
echo ""
echo "🎯 Next steps:"
echo "  1. Visit http://$CONTAINER_FQDN to access the application"
echo "  2. Environment files (.env) are auto-configured"
echo "  3. Upload test documents to start grading"
