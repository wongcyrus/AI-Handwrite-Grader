#!/bin/bash
# cleanup-nested-resources.sh
# Cleans up nested Azure resources before terraform destroy

set -e

RESOURCE_GROUP="ai-handwrite-grader-dev-rg"

echo "🧹 Cleaning up nested resources in $RESOURCE_GROUP..."

# Delete AI Foundry projects (nested under AI services)
echo "Deleting AI Foundry projects..."
az resource list \
  --resource-group "$RESOURCE_GROUP" \
  --resource-type "Microsoft.CognitiveServices/accounts/projects" \
  --query "[].id" -o tsv | while read project_id; do
  if [ ! -z "$project_id" ]; then
    echo "  Deleting: $project_id"
    az resource delete --ids "$project_id" || echo "  Failed to delete $project_id"
  fi
done

# Delete model deployments (nested under AI services)  
echo "Deleting model deployments..."
az resource list \
  --resource-group "$RESOURCE_GROUP" \
  --resource-type "Microsoft.CognitiveServices/accounts/deployments" \
  --query "[].id" -o tsv | while read deployment_id; do
  if [ ! -z "$deployment_id" ]; then
    echo "  Deleting: $deployment_id"
    az resource delete --ids "$deployment_id" || echo "  Failed to delete $deployment_id"
  fi
done

echo "✅ Cleanup complete!"
