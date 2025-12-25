#!/bin/bash

# Clean test runner - restarts Azurite with fresh data for each test run

set -e

echo "🧹 Starting clean test environment..."

# Stop any existing test containers
docker compose -f docker-compose.test.yml down 2>/dev/null || true

# Start fresh Azurite instance (no persistent volumes)
docker compose -f docker-compose.test.yml up -d azurite-test

# Wait for Azurite to be ready
echo "⏳ Waiting for Azurite..."
sleep 5

# Test connection (expect 400 but connection working)
if curl -s http://localhost:11002/devstoreaccount1 >/dev/null 2>&1; then
    echo "✅ Clean Azurite instance ready"
else
    echo "❌ Azurite failed to start"
    exit 1
fi

# Set up test environment
cd app
source test_env/bin/activate 2>/dev/null || {
    echo "Creating test environment..."
    python -m venv test_env
    source test_env/bin/activate
    pip install -r requirements.txt
    pip install -r requirements-test.txt
}

# Set test environment variables
export FLASK_ENV=testing
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://localhost:11000/devstoreaccount1;QueueEndpoint=http://localhost:11001/devstoreaccount1;TableEndpoint=http://localhost:11002/devstoreaccount1;"
export AI_FOUNDRY_ENDPOINT="https://test.cognitiveservices.azure.com/"
export MODEL_DEPLOYMENT_NAME="gpt-4o-mini"
export SECRET_KEY="test-secret-key"

echo "✅ Running tests with clean storage..."

# Run tests
python -m pytest "$@"

# Cleanup
echo "🧹 Cleaning up..."
docker compose -f ../docker-compose.test.yml down
