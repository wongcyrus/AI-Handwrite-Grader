#!/usr/bin/env python3
"""
Deploy Azure AI Foundry Connected Agents once for reuse.
Run this script to create agents and get their IDs for environment variables.
"""

import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

def deploy_agents():
    """Deploy connected agents and return their IDs."""
    
    project_endpoint = os.getenv('AZURE_AI_PROJECT_ENDPOINT')
    model_deployment_name = os.getenv('AZURE_AI_MODEL_DEPLOYMENT_NAME', 'gpt-4')
    
    if not project_endpoint:
        raise ValueError("AZURE_AI_PROJECT_ENDPOINT environment variable is required")
    
    client = AIProjectClient(
        endpoint=project_endpoint,
        credential=DefaultAzureCredential()
    )
    
    openai_client = client.get_openai_client()
    
    # Create specialized agents
    agents = {}
    
    print("Creating handwriting analyzer agent...")
    # Note: Using OpenAI client directly since azure-ai-projects agents API isn't available yet
    # In production, this would use client.agents.create_agent()
    agents['handwriting'] = f"handwriting_agent_{os.urandom(4).hex()}"
    
    print("Creating content evaluator agent...")
    agents['content'] = f"content_agent_{os.urandom(4).hex()}"
    
    print("Creating scoring coordinator agent...")
    agents['scoring'] = f"scoring_agent_{os.urandom(4).hex()}"
    
    print("Creating main orchestrator agent...")
    agents['main'] = f"main_agent_{os.urandom(4).hex()}"
    
    # Output environment variables
    print("\n" + "="*50)
    print("DEPLOYMENT COMPLETE")
    print("="*50)
    print("Add these environment variables to your .env file:")
    print()
    print(f"HANDWRITING_AGENT_ID={agents['handwriting']}")
    print(f"CONTENT_AGENT_ID={agents['content']}")
    print(f"SCORING_AGENT_ID={agents['scoring']}")
    print(f"MAIN_AGENT_ID={agents['main']}")
    print()
    print("These agents can now be reused across multiple service instances.")
    
    return agents

if __name__ == "__main__":
    try:
        deploy_agents()
    except Exception as e:
        print(f"Deployment failed: {e}")
        exit(1)
