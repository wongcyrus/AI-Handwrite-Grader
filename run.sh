#!/bin/bash

# Get values from Terraform outputs
STORAGE_CONNECTION=$(cd terraform && terraform output -raw storage_connection_string)
AI_ENDPOINT=$(cd terraform && terraform output -raw ai_foundry_endpoint)
AI_KEY=$(cd terraform && terraform output -raw ai_foundry_key)

# Update .env file with dynamic values
sed -i "s|AZURE_STORAGE_CONNECTION_STRING=.*|AZURE_STORAGE_CONNECTION_STRING=$STORAGE_CONNECTION|" app/.env
sed -i "s|AZURE_AI_PROJECT_KEY=.*|AZURE_AI_PROJECT_KEY=$AI_KEY|" app/.env

echo "Environment variables updated in app/.env"

# Stop and remove existing container
docker stop ai-handwrite-grader-local 2>/dev/null
docker rm ai-handwrite-grader-local 2>/dev/null

# Run container with all environment variables
docker run -p 3000:80 --name ai-handwrite-grader-local \
  --env FLASK_ENV=production \
  --env AZURE_STORAGE_CONNECTION_STRING="$STORAGE_CONNECTION" \
  --env AZURE_AI_PROJECT_ENDPOINT="$AI_ENDPOINT" \
  --env AZURE_AI_PROJECT_KEY="$AI_KEY" \
  --env AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-52-chat" \
  --env HANDWRITING_AGENT_ID="asst_Av3aip2JnvJTo7fklAgOuI7U" \
  --env CONTENT_AGENT_ID="asst_mt3BGFH65bgLKwbriRac3p4a" \
  --env SCORING_AGENT_ID="asst_Q33fOG1BIaW5IgBsYRmsx4H2" \
  --env MAIN_AGENT_ID="asst_8ssQtzn01xVd6GqJV0XX79Iu" \
  ai-handwrite-grader-local
