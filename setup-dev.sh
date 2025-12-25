#!/bin/bash

# Development setup script with Azurite

set -e

echo "🚀 Setting up AI Handwriting Grader Development Environment"
echo "=========================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start Azurite storage emulator
echo "📦 Starting Azurite storage emulator..."
docker-compose up -d azurite

# Wait for Azurite to be ready
echo "⏳ Waiting for Azurite to be ready..."
sleep 5

# Check if Azurite is responding
if curl -f http://localhost:10002/devstoreaccount1 > /dev/null 2>&1; then
    echo "✅ Azurite is running and ready"
else
    echo "❌ Azurite failed to start properly"
    exit 1
fi

# Set up Python environment
echo "🐍 Setting up Python environment..."
cd app

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-test.txt

# Set environment variables for local development
export FLASK_ENV=development
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://localhost:10000/devstoreaccount1;QueueEndpoint=http://localhost:10001/devstoreaccount1;TableEndpoint=http://localhost:10002/devstoreaccount1;"
export AI_FOUNDRY_ENDPOINT="https://test.cognitiveservices.azure.com/"
export MODEL_DEPLOYMENT_NAME="gpt-4o-mini"
export SECRET_KEY="dev-secret-key"

# Initialize storage tables and containers
echo "🗄️  Initializing storage containers and tables..."
python3 -c "
from services.storage_service import StorageService
import time

# Wait a bit more for Azurite
time.sleep(2)

try:
    storage = StorageService()
    print('✅ Connected to Azurite successfully')
    
    # Create containers
    containers = ['pdfs', 'images', 'results']
    for container in containers:
        try:
            storage.blob_client.create_container(container)
            print(f'✅ Created container: {container}')
        except Exception as e:
            if 'already exists' in str(e).lower():
                print(f'ℹ️  Container {container} already exists')
            else:
                print(f'❌ Error creating container {container}: {e}')
    
    # Tables are created automatically when first accessed
    print('✅ Storage initialization complete')
    
except Exception as e:
    print(f'❌ Storage initialization failed: {e}')
    exit(1)
"

# Run tests to verify everything works
echo "🧪 Running tests with Azurite..."
python -m pytest tests/test_storage_service.py::TestStorageService::test_create_entity_success -v

if [ $? -eq 0 ]; then
    echo "✅ Tests passed with Azurite!"
else
    echo "⚠️  Some tests failed, but setup is complete"
fi

echo ""
echo "🎉 Development environment ready!"
echo ""
echo "📋 Next steps:"
echo "  1. Start the Flask app: python app.py"
echo "  2. Open browser: http://localhost:5000"
echo "  3. Run tests: python -m pytest"
echo ""
echo "🔧 Azurite endpoints:"
echo "  - Blob: http://localhost:10000"
echo "  - Queue: http://localhost:10001" 
echo "  - Table: http://localhost:10002"
echo ""
echo "🛑 To stop: docker-compose down"
