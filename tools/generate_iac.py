import os
import re
import json
from pathlib import Path

ISSUE_NUMBER = os.getenv("ISSUE_NUMBER", "").strip()
ISSUE_TITLE = os.getenv("ISSUE_TITLE", "").strip()
ISSUE_BODY = os.getenv("ISSUE_BODY", "")
REPO = os.getenv("REPO", "").strip()

def find_field(body, label):
    pattern = rf"###\s+{re.escape(label)}\s*\n([\s\S]*?)(?=\n###\s+|\Z)"
    m = re.search(pattern, body)
    if not m:
        return None
    value = m.group(1).strip()
    return value if value else None

def main():
    environment = (find_field(ISSUE_BODY, "Environment") or "dev").lower().strip()
    location = (find_field(ISSUE_BODY, "Azure Region") or "eastus").strip()
    rg_name = (find_field(ISSUE_BODY, "Resource Group Name") or "rg-default").strip()
    sa_name = (find_field(ISSUE_BODY, "Resource Name") or "stdefault001").strip()
    sku = (find_field(ISSUE_BODY, "SKU / Tier") or "Standard_LRS").strip()
    tags_raw = find_field(ISSUE_BODY, "Tags (JSON)") or "{}"

    try:
        tags = json.loads(tags_raw)
    except:
        tags = {"owner": "unknown"}

    replication = sku.split("_")[-1] if "_" in sku else "LRS"

    out_dir = Path("infra") / environment / "azure-storage"
    out_dir.mkdir(parents=True, exist_ok=True)

    main_tf = f'''terraform {{
  required_version = ">= 1.5.0"
  required_providers {{
    azurerm = {{
      source  = "hashicorp/azurerm"
      version = ">= 3.0.0"
    }}
  }}
}}

provider "azurerm" {{
  features {{}}
}}

resource "azurerm_resource_group" "rg" {{
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}}

resource "azurerm_storage_account" "sa" {{
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = var.replication_type
  tags                     = var.tags
}}
'''

    variables_tf = f'''variable "resource_group_name" {{
  description = "Name of the resource group"
  type        = string
  default     = "{rg_name}"
}}

variable "location" {{
  description = "Azure region"
  type        = string
  default     = "{location}"
}}

variable "storage_account_name" {{
  description = "Name of the storage account"
  type        = string
  default     = "{sa_name}"
}}

variable "replication_type" {{
  description = "Storage replication type"
  type        = string
  default     = "{replication}"
}}

variable "tags" {{
  description = "Resource tags"
  type        = map(string)
  default     = {json.dumps(tags, indent=2)}
}}
'''

    outputs_tf = '''output "resource_group_id" {
  description = "ID of the resource group"
  value       = azurerm_resource_group.rg.id
}

output "storage_account_id" {
  description = "ID of the storage account"
  value       = azurerm_storage_account.sa.id
}

output "storage_account_primary_endpoint" {
  description = "Primary blob endpoint"
  value       = azurerm_storage_account.sa.primary_blob_endpoint
}
'''

    readme = f"""# Auto-generated IaC

- **Repo:** {REPO}
- **Issue:** #{ISSUE_NUMBER}
- **Title:** {ISSUE_TITLE}
- **Environment:** {environment}
- **Region:** {location}

This folder was auto-generated from a GitHub Issue.
Review before merging.
"""

    (out_dir / "main.tf").write_text(main_tf)
    (out_dir / "variables.tf").write_text(variables_tf)
    (out_dir / "outputs.tf").write_text(outputs_tf)
    (out_dir / "README.md").write_text(readme)

    print(f"Generated Terraform in: {out_dir}")

if __name__ == "__main__":
    main()
