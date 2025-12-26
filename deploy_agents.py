#!/usr/bin/env python3
"""
Deploy Azure AI Foundry Connected Agents.
Standalone version with existing agent detection.
"""

import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

def deploy_agents():
    """Deploy all agents to Azure AI Foundry."""
    
    project_endpoint = "https://aihandwritegraderdevai.services.ai.azure.com/api/projects/ai-handwrite-grader-dev-project"
    
    client = AIProjectClient(
        endpoint=project_endpoint,
        credential=DefaultAzureCredential()
    )
    
    agents_config = [
        {
            'name': 'Handwriting Analyzer',
            'description': 'Analyzes handwritten text quality and legibility',
            'instructions': 'You are a handwriting analysis expert. Analyze handwritten text for legibility, structure, and quality. Provide detailed feedback on writing clarity and areas for improvement.'
        },
        {
            'name': 'Content Evaluator', 
            'description': 'Evaluates content accuracy and completeness',
            'instructions': 'You are an academic content evaluator. Compare student answers against standard answers and rubrics. Assess accuracy, completeness, and understanding demonstrated in responses.'
        },
        {
            'name': 'Scoring Coordinator',
            'description': 'Coordinates scoring and generates final grades',
            'instructions': 'You are a grading coordinator. Combine handwriting analysis and content evaluation to generate fair, consistent scores. Apply rubrics systematically and provide constructive feedback.'
        },
        {
            'name': 'Main Orchestrator',
            'description': 'Main orchestrator for the grading workflow',
            'instructions': 'You are the main grading orchestrator. Coordinate the entire grading process by delegating tasks to specialized agents and synthesizing their results into comprehensive evaluations.'
        }
    ]
    
    # Check existing agents first
    existing_agents = {}
    try:
        agents_list = client.agents.list_agents()
        for agent in agents_list:
            existing_agents[agent.name] = agent.id
            print(f"Found existing agent: {agent.name} ({agent.id})")
    except Exception as e:
        print(f"Could not list existing agents: {e}")
    
    deployed_agents = {}
    
    for config in agents_config:
        if config['name'] in existing_agents:
            # Use existing agent
            agent_id = existing_agents[config['name']]
            deployed_agents[config['name']] = agent_id
            print(f"✅ Using existing {config['name']}: {agent_id}")
        else:
            # Create new agent
            print(f"Creating {config['name']}...")
            
            agent = client.agents.create_agent(
                model="gpt-5-chat",
                name=config['name'],
                description=config['description'],
                instructions=config['instructions']
            )
            
            deployed_agents[config['name']] = agent.id
            print(f"✅ Created {config['name']}: {agent.id}")
    
    print(f"\n✅ All agents ready!")
    print("\nAgent IDs:")
    for name, agent_id in deployed_agents.items():
        print(f"{name}: {agent_id}")
    
    # Write to .env file
    env_content = f"""# Azure AI Foundry Agent IDs
HANDWRITING_AGENT_ID={deployed_agents['Handwriting Analyzer']}
CONTENT_AGENT_ID={deployed_agents['Content Evaluator']}
SCORING_AGENT_ID={deployed_agents['Scoring Coordinator']}
MAIN_AGENT_ID={deployed_agents['Main Orchestrator']}

# Azure AI Configuration
AZURE_AI_PROJECT_ENDPOINT={project_endpoint}
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-5-chat
OPENAI_API_VERSION=2024-05-13
"""
    
    with open('app/.env', 'w') as f:
        f.write(env_content)
    
    print(f"✅ Agent IDs written to app/.env")
    
    return deployed_agents

if __name__ == "__main__":
    deploy_agents()
