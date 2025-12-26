#!/bin/bash
# Test runner script for AI Handwrite Grader

set -e

echo "🧪 AI Handwrite Grader Test Suite"
echo "=================================="

# Activate virtual environment
source venv/bin/activate

# Run unit tests only (fast)
echo "📋 Running Unit Tests..."
python -m pytest tests/test_agents.py -v -m "not integration"

# Ask if user wants to run integration tests
echo ""
read -p "🔗 Run integration tests? (requires Azure credentials) [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔗 Running Integration Tests..."
    python -m pytest tests/test_agent_integration.py -v -m integration
else
    echo "⏭️  Skipping integration tests"
fi

echo ""
echo "✅ Test run complete!"
