#!/bin/bash

# Test script for AI Handwriting Grader with Live Azure Services

set -e

echo "🧪 Running AI Handwriting Grader Test Suite with Live Azure"
echo "=========================================================="

# Check if we're in the app directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: Please run this script from the app directory"
    exit 1
fi

# Check if .env exists with live credentials
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found. Run ./deploy.sh first to create it."
    exit 1
fi

# Load environment variables
source .env

# Verify Azure credentials are present
if [ -z "$AZURE_STORAGE_CONNECTION_STRING" ] || [ -z "$AZURE_AI_PROJECT_ENDPOINT" ]; then
    echo "❌ Error: Missing Azure credentials in .env file"
    echo "Run ./update-env.sh to refresh from Terraform outputs"
    exit 1
fi

echo "✅ Live Azure credentials loaded"

# Install test dependencies
echo "📦 Installing test dependencies..."
pip install -r requirements-test.txt > /dev/null 2>&1

# Set additional test environment variables
export FLASK_ENV=testing
export SECRET_KEY="test-secret-key-$(date +%s)"
export PYTHONPATH="/home/developer/Documents/data-disk/AI-Handwrite-Grader/app"

# Run tests that work with live services
echo "🧪 Running tests with Live Azure backend..."
pytest tests/test_pdf_processing_service.py \
       tests/test_post_processing_service.py \
       tests/test_manual_scoring_service.py \
       tests/test_question_annotation_service.py \
       tests/test_email_distribution_service.py \
       tests/test_ai_scoring_service.py \
       tests/test_workflow_integration.py \
       --verbose \
       --tb=short \
       -W ignore::DeprecationWarning

# Run live service integration tests
echo ""
echo "🔗 Running Live Service Integration Tests..."
cd ..
python test_live_services.py
python test_services.py
cd app

# Display test summary
echo ""
echo "📊 Test Summary:"
echo "================"
echo "✅ Core business logic tests completed"

echo ""
echo "🎉 Tests completed with Live Azure backend!"
echo "🔧 Live Azure services tested and working"
