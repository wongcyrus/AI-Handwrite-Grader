#!/bin/bash
# Delete and recreate all agents with fresh configurations

set -e

echo "🗑️  Recreating Connected Agents..."

# Check prerequisites
source venv/bin/activate

# Delete existing agents
python3 << 'EOF'
import os
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

load_dotenv('app/.env')

endpoint = os.getenv('AZURE_AI_PROJECT_ENDPOINT')
if not endpoint:
    print("❌ Missing Azure endpoint")
    exit(1)

client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())

# Delete all existing agents
agents = list(client.agents.list_agents())
for agent in agents:
    try:
        client.agents.delete_agent(agent.id)
        print(f"🗑️  Deleted {agent.name}")
    except Exception as e:
        print(f"⚠️  Could not delete {agent.name}: {e}")

print(f"✅ Cleanup complete")
EOF

# Deploy fresh agents
echo "🤖 Deploying fresh agents..."
python deploy_agents_tf.py

echo "🎉 Agent recreation complete!"
