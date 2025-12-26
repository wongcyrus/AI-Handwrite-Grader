#!/bin/bash
set -e

echo "🗑️ Starting complete AI Handwrite Grader cleanup..."

# Check prerequisites
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Please install it first."
    exit 1
fi

if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform not found. Please install it first."
    exit 1
fi

# Check Azure login
if ! az account show &> /dev/null; then
    echo "❌ Not logged into Azure. Please run 'az login' first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Destroy infrastructure
echo "💥 Destroying infrastructure..."
cd terraform
terraform destroy -auto-approve

# Clean up soft-deleted resources
echo "🧹 Cleaning up soft-deleted resources..."
echo "Checking for soft-deleted AI Services..."
DELETED_SERVICES=$(az cognitiveservices account list-deleted --query "[].{name:name,location:location}" -o tsv 2>/dev/null || true)

if [ ! -z "$DELETED_SERVICES" ]; then
    echo "Found soft-deleted services, purging..."
    while IFS=$'\t' read -r name location; do
        if [[ $name == *"ai-handwrite-grader"* ]]; then
            echo "Purging $name in $location..."
            az cognitiveservices account purge --name "$name" --resource-group "ai-handwrite-grader-dev-rg" --location "$location" 2>/dev/null || true
        fi
    done <<< "$DELETED_SERVICES"
fi

# Clean up terraform state
echo "🧽 Cleaning up Terraform state..."
rm -f terraform.tfstate terraform.tfstate.backup .terraform.lock.hcl
rm -rf .terraform

cd ..

echo "✅ Cleanup complete!"
echo ""
echo "🎯 All resources have been removed:"
echo "  ✅ Infrastructure destroyed"
echo "  ✅ Soft-deleted resources purged"
echo "  ✅ Terraform state cleaned"
