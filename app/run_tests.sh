#!/bin/bash

# Test script for AI Handwriting Grader with Azurite

set -e

echo "🧪 Running AI Handwriting Grader Test Suite with Azurite"
echo "======================================================="

# Check if we're in the app directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: Please run this script from the app directory"
    exit 1
fi

# Check if Azurite is running
if ! curl -f http://localhost:10002/devstoreaccount1 > /dev/null 2>&1; then
    echo "⚠️  Azurite not detected. Starting it..."
    cd ..
    docker-compose up -d azurite
    sleep 5
    cd app
    
    if ! curl -f http://localhost:10002/devstoreaccount1 > /dev/null 2>&1; then
        echo "❌ Failed to start Azurite. Please run: docker-compose up -d azurite"
        exit 1
    fi
fi

echo "✅ Azurite is running"

# Install test dependencies
echo "📦 Installing test dependencies..."
pip install -r requirements-test.txt > /dev/null 2>&1

# Set test environment variables with Azurite
export FLASK_ENV=testing
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://localhost:10000/devstoreaccount1;QueueEndpoint=http://localhost:10001/devstoreaccount1;TableEndpoint=http://localhost:10002/devstoreaccount1;"
export AI_FOUNDRY_ENDPOINT="https://test.cognitiveservices.azure.com/"
export MODEL_DEPLOYMENT_NAME="gpt-4o-mini"
export SECRET_KEY="test-secret-key"

# Initialize storage for tests
echo "🗄️  Initializing test storage..."
python3 -c "
from services.storage_service import StorageService
try:
    storage = StorageService()
    # Create test containers
    containers = ['pdfs', 'images', 'results']
    for container in containers:
        try:
            storage.blob_client.create_container(container)
        except:
            pass  # Container might already exist
    print('✅ Test storage ready')
except Exception as e:
    print(f'⚠️  Storage setup warning: {e}')
"

# Run linting (if flake8 is available)
if command -v flake8 &> /dev/null; then
    echo "🔍 Running code linting..."
    flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || true
fi

# Run tests with coverage
echo "🧪 Running tests with Azurite backend..."
pytest tests/ \
    --verbose \
    --tb=short \
    --cov=. \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-exclude=tests/* \
    --cov-exclude=venv/* \
    --cov-exclude=test_env/*

# Display coverage summary
echo ""
echo "📊 Coverage Summary:"
echo "==================="
coverage report --show-missing

# Check coverage threshold
COVERAGE=$(coverage report --format=total 2>/dev/null || echo "0")
THRESHOLD=70

if [ "$COVERAGE" -lt "$THRESHOLD" ]; then
    echo "⚠️  Coverage $COVERAGE% is below threshold $THRESHOLD%"
else
    echo "✅ Coverage $COVERAGE% meets threshold $THRESHOLD%"
fi

echo ""
echo "🎉 Tests completed with Azurite backend!"
echo "📁 Detailed coverage report available in htmlcov/index.html"
echo "🔧 Azurite data persisted in Docker volume for next run"
