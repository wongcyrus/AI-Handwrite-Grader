#!/bin/bash

# Test script for AI Handwriting Grader

set -e

echo "🧪 Running AI Handwriting Grader Test Suite"
echo "============================================"

# Check if we're in the app directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: Please run this script from the app directory"
    exit 1
fi

# Install test dependencies
echo "📦 Installing test dependencies..."
pip install -r requirements-test.txt

# Set test environment variables
export FLASK_ENV=testing
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=test;AccountKey=test;EndpointSuffix=core.windows.net"
export AI_FOUNDRY_ENDPOINT="https://test.cognitiveservices.azure.com/"
export MODEL_DEPLOYMENT_NAME="gpt-4o-mini"
export SECRET_KEY="test-secret-key"

# Run linting (if flake8 is available)
if command -v flake8 &> /dev/null; then
    echo "🔍 Running code linting..."
    flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || true
fi

# Run tests with coverage
echo "🧪 Running tests with coverage..."
pytest tests/ \
    --verbose \
    --tb=short \
    --cov=. \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-exclude=tests/* \
    --cov-exclude=venv/*

# Display coverage summary
echo ""
echo "📊 Coverage Summary:"
echo "==================="
coverage report --show-missing

# Check coverage threshold
COVERAGE=$(coverage report --format=total)
THRESHOLD=80

if [ "$COVERAGE" -lt "$THRESHOLD" ]; then
    echo "❌ Coverage $COVERAGE% is below threshold $THRESHOLD%"
    exit 1
else
    echo "✅ Coverage $COVERAGE% meets threshold $THRESHOLD%"
fi

echo ""
echo "🎉 All tests completed successfully!"
echo "📁 Detailed coverage report available in htmlcov/index.html"
