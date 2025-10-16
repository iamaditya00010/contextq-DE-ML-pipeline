# Azure Infrastructure as Code
**Author:** Aditya Padhi

This directory contains Terraform configuration for deploying the DE Log Processing & ML Pipeline infrastructure to Azure.

## Files

- `main.tf` - Main Terraform configuration
- `variables.tf` - Variable definitions
- `outputs.tf` - Output values
- `terraform.tfvars.example` - Example variables file

## Prerequisites

1. **Azure Subscription** with appropriate permissions
2. **Service Principal** with Contributor role
3. **Terraform** installed locally (optional for GitHub Actions)

## Quick Start

### Option 1: GitHub Actions (Recommended)
The infrastructure is automatically deployed via GitHub Actions when you push to the main branch.

### Option 2: Local Deployment
```bash
# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your values
# Add your Service Principal credentials

# Initialize Terraform
terraform init

# Plan deployment
terraform plan

# Apply infrastructure
terraform apply
```

## Resources Created

- Resource Group: `de-log-processing-rg`
- Storage Account (ADLS Gen2): `delogprocessingdatalake[random]`
- Databricks Workspace: `de-log-processing-databricks[random]`
- AKS Cluster: `de-log-processing-aks[random]`
- Data Factory: `de-log-processing-adf[random]`
- Container Registry: `delogprocessingacr[random]`
- Key Vault: `de-log-processing-kv[random]`
- Application Insights: `de-log-processing-insights[random]`
- Log Analytics Workspace: `de-log-processing-logs[random]`

## State Management

Currently using local state for initial deployment. Remote backend can be configured later:

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "de-log-processing-tfstate-rg"
    storage_account_name = "delogprocessingtfstate"
    container_name       = "tfstate"
    key                  = "terraform.tfstate"
  }
}
```

## Variables

See `terraform.tfvars.example` for all available variables.

## Outputs

After successful deployment, Terraform outputs:
- Resource group name
- Storage account name
- Databricks workspace URL
- AKS cluster name
- Container registry name
- Key vault name
- Application Insights key
- Log Analytics workspace ID

## Troubleshooting

### Common Issues:

1. **Authentication Error**: Ensure Service Principal has Contributor role
2. **Resource Name Conflicts**: Add random numbers to resource names
3. **Quota Limits**: Check Azure subscription quotas
4. **Permission Issues**: Verify Service Principal permissions

### Useful Commands:

```bash
# Check current state
terraform show

# List resources
terraform state list

# Import existing resource
terraform import azurerm_resource_group.main /subscriptions/.../resourceGroups/de-log-processing-rg

# Destroy infrastructure
terraform destroy
```

## Security Notes

- Service Principal credentials are stored in GitHub Secrets
- All resources use least privilege access
- Key Vault stores sensitive configuration
- Network security groups restrict access

## Cost Optimization

- AKS uses spot instances where possible
- Storage uses cool tier for archived data
- Auto-scaling enabled for compute resources
- Resource tagging for cost tracking

---

**Last Updated:** October 16, 2025  
**Author:** Aditya Padhi  
**Version:** 1.0
