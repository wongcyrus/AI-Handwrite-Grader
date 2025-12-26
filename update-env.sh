#!/bin/bash
# Auto-update .env files with Terraform outputs after deployment

set -e

echo "🔄 Updating .env files with Terraform outputs..."

# Get Terraform outputs
cd terraform
AI_ENDPOINT=$(terraform output -raw ai_foundry_endpoint 2>/dev/null || echo "")
AI_KEY=$(terraform output -raw ai_foundry_key 2>/dev/null || echo "")
STORAGE_CONNECTION=$(terraform output -raw storage_connection_string 2>/dev/null || echo "")

cd ..

# Check if outputs exist
if [[ -z "$AI_ENDPOINT" || -z "$AI_KEY" || -z "$STORAGE_CONNECTION" ]]; then
    echo "❌ Missing Terraform outputs. Run 'terraform apply' first."
    exit 1
fi

# Update app/.env
cat > app/.env << EOF
# Azure AI Configuration
AZURE_AI_PROJECT_ENDPOINT=$AI_ENDPOINT
AZURE_AI_PROJECT_KEY=$AI_KEY
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-5-chat
OPENAI_API_VERSION=2024-10-21

# Storage Configuration  
AZURE_STORAGE_CONNECTION_STRING=$STORAGE_CONNECTION

# Agent IDs (will be populated after agent deployment)
HANDWRITING_AGENT_ID=
CONTENT_AGENT_ID=
SCORING_AGENT_ID=
MAIN_AGENT_ID=

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)
EOF

echo "✅ Updated app/.env with Terraform outputs"

# Update test environment
cp app/.env app/.env.test
sed -i 's/FLASK_ENV=production/FLASK_ENV=testing/' app/.env.test

echo "✅ Updated app/.env.test"
echo "⚠️  Run deploy_agents_tf.py to populate agent IDs"
