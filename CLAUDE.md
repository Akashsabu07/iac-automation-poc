# Project: IaC Automation POC

## Purpose
This repo generates Infrastructure-as-Code (Terraform) from GitHub Issues.

## Rules
- All Terraform code goes in `infra/<environment>/<resource-type>/`
- Environments allowed: dev, test, prod
- Always include tags on every resource
- Use azurerm provider >= 3.0.0
- Follow Terraform naming conventions
- Always include a README.md in each generated folder
- Branch naming: `issue-<number>`

## Code Standards
- terraform fmt must pass
- terraform validate must pass
- No hardcoded secrets
- Use variables for reusable values

## Folder Structure
