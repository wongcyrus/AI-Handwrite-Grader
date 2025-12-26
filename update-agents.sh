#!/bin/bash
# Update existing agents - redeploy with latest configurations

set -e

echo "🔄 Updating Connected Agents..."

# Activate environment
source venv/bin/activate

# Redeploy agents (will update existing ones)
echo "🤖 Redeploying agents with latest configurations..."
python deploy_agents_tf.py

echo "✅ Agent update complete!"
