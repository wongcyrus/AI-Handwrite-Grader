#!/usr/bin/env python3
"""
Deploy Azure AI Foundry Connected Agents.
Can be run standalone or from Terraform.
"""

import os
import sys
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

def deploy_agents():
    """Deploy all agents to Azure AI Foundry."""
    
    try:
        # Use correct AI Foundry project endpoint format
        client = AIProjectClient(
            endpoint="https://aihandwritegraderdevai.services.ai.azure.com/api/projects/ai-handwrite-grader-dev-proj",
            credential=DefaultAzureCredential()
        )
        
        agents_config = [
            {
                'name': 'Handwriting Analyzer',
                'description': 'Analyzes handwritten text quality and legibility',
                'instructions': 'You are a handwriting analysis expert. Analyze handwritten text for legibility, structure, and quality. Provide detailed feedback on writing clarity and areas for improvement.',
                'env_var': 'HANDWRITING_AGENT_ID'
            },
            {
                'name': 'Content Evaluator', 
                'description': 'Evaluates content accuracy and completeness',
                'instructions': 'You are an academic content evaluator. Compare student answers against standard answers and rubrics. Assess accuracy, completeness, and understanding demonstrated in responses.',
                'env_var': 'CONTENT_AGENT_ID'
            },
            {
                'name': 'Scoring Coordinator',
                'description': 'Coordinates scoring and generates final grades',
                'instructions': 'You are a grading coordinator. Combine handwriting analysis and content evaluation to generate fair, consistent scores. Apply rubrics systematically and provide constructive feedback.',
                'env_var': 'SCORING_AGENT_ID'
            },
            {
                'name': 'Main Orchestrator',
                'description': 'Main orchestrator for the grading workflow',
                'instructions': 'You are the main grading orchestrator. Coordinate the entire grading process by delegating tasks to specialized agents and synthesizing their results into comprehensive evaluations.',
                'env_var': 'MAIN_AGENT_ID'
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
                deployed_agents[config['env_var']] = agent_id
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
                
                deployed_agents[config['env_var']] = agent.id
                print(f"✅ Created {config['name']}: {agent.id}")
        
        # Write agent IDs to .env file
        env_file = os.path.join(os.path.dirname(__file__), 'app', '.env')
        
        # Read existing .env or create new
        env_lines = []
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                env_lines = f.readlines()
        
        # Update agent IDs
        agent_vars = set(deployed_agents.keys())
        updated_lines = []
        
        for line in env_lines:
            var_name = line.split('=')[0] if '=' in line else ''
            if var_name not in agent_vars:
                updated_lines.append(line)
        
        # Add agent IDs and deployment name
        for env_var, agent_id in deployed_agents.items():
            updated_lines.append(f"{env_var}={agent_id}\n")
        
        # Add deployment name if not present
        has_deployment_name = any('AZURE_AI_MODEL_DEPLOYMENT_NAME' in line for line in updated_lines)
        if not has_deployment_name:
            updated_lines.append("AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-5-chat\n")
        
        # Write updated .env
        with open(env_file, 'w') as f:
            f.writelines(updated_lines)
        
        print(f"\n✅ All agents ready!")
        print(f"✅ Configuration written to {env_file}")
        
        return deployed_agents
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    deploy_agents()
