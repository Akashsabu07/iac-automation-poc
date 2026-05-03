import os
import re
import json
import urllib.request
from pathlib import Path

# Environment variables from GitHub Actions
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ISSUE_NUMBER = os.getenv("ISSUE_NUMBER", "").strip()
ISSUE_TITLE = os.getenv("ISSUE_TITLE", "").strip()
ISSUE_BODY = os.getenv("ISSUE_BODY", "")
REPO = os.getenv("REPO", "").strip()

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"


def find_field(body, label):
    """Extract a field value from GitHub Issue Form markdown."""
    pattern = rf"###\s+{re.escape(label)}\s*\n([\s\S]*?)(?=\n###\s+|\Z)"
    m = re.search(pattern, body)
    if not m:
        return None
    value = m.group(1).strip()
    return value if value else None


def call_gemini(prompt):
    """Call Google Gemini API and return the generated text."""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 4096
        }
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        GEMINI_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    text = result["candidates"][0]["content"]["parts"][0]["text"]
    return text


def extract_code_block(text):
    """Extract code from markdown code blocks if present."""
    pattern = r"```(?:hcl|terraform)?\s*\n([\s\S]*?)```"
    matches = re.findall(pattern, text)
    if matches:
        return "\n\n".join(matches)
    return text.strip()


def main():
    # Parse issue fields
    environment = (find_field(ISSUE_BODY, "Environment") or "dev").lower().strip()
    location = (find_field(ISSUE_BODY, "Azure Region") or "eastus").strip()
    rg_name = (find_field(ISSUE_BODY, "Resource Group Name") or "rg-default").strip()
    resource_name = (find_field(ISSUE_BODY, "Resource Name") or "stdefault001").strip()
    sku = (find_field(ISSUE_BODY, "SKU / Tier") or "Standard_LRS").strip()
    tags_raw = find_field(ISSUE_BODY, "Tags (JSON)") or '{"owner":"team"}'

    try:
        tags = json.loads(tags_raw)
    except Exception:
        tags = {"owner": "unknown"}

    replication = sku.split("_")[-1] if "_" in sku else "LRS"

    print(f"Parsed issue fields:")
    print(f"  Environment: {environment}")
    print(f"  Location: {location}")
    print(f"  Resource Group: {rg_name}")
    print(f"  Resource Name: {resource_name}")
    print(f"  SKU: {sku}")
    print(f"  Tags: {tags}")

    # Create output directory
    out_dir = Path("infra") / environment / "azure-storage"
    out_dir.mkdir(parents=True, exist_ok=True)

    # ============================================
    # GEMINI AI: Generate main.tf (SECURITY HARDENED)
    # ============================================
    main_tf_prompt = f"""You are a senior Terraform engineer specializing in Azure cloud security.
Generate production-ready, security-hardened Terraform code.

Requirements:
- Create a Resource Group named "{rg_name}" in "{location}"
- Create a Storage Account named "{resource_name}" in the same resource group
- SKU: {sku}
- Tags: {json.dumps(tags)}

MANDATORY SECURITY RULES (DO NOT SKIP ANY):
- MUST include: min_tls_version = "TLS1_2"
- MUST include: enable_https_traffic_only = true
- MUST include: public_network_access_enabled = false
- MUST include: account_kind = "StorageV2"
- MUST include: blob_properties block with versioning_enabled = true
- MUST include: infrastructure_encryption_enabled = true

TERRAFORM RULES:
- Use azurerm provider version "~> 3.80"
- Include terraform block with required_version >= 1.5.0
- Include provider "azurerm" block with features {{}}
- Use variables for all configurable values:
  - var.resource_group_name
  - var.location
  - var.storage_account_name
  - var.replication_type
  - var.tags
- Apply tags to ALL resources
- Reference resources properly (azurerm_resource_group.rg.name, etc.)

OUTPUT RULES:
- Output ONLY valid Terraform HCL code
- Do NOT include any explanations, comments, or markdown formatting
- Do NOT wrap in code blocks
- Do NOT add any text before or after the code"""

    print("\nCalling Gemini AI for main.tf (security-hardened)...")
    main_tf_raw = call_gemini(main_tf_prompt)
    main_tf = extract_code_block(main_tf_raw)
    print("main.tf generated successfully!")

    # ============================================
    # GEMINI AI: Generate variables.tf (WITH VALIDATION)
    # ============================================
    variables_prompt = f"""You are a senior Terraform engineer. Generate a variables.tf file with input validation.

The variables must match this usage:
- var.resource_group_name (default: "{rg_name}")
- var.location (default: "{location}")
- var.storage_account_name (default: "{resource_name}")
- var.replication_type (default: "{replication}")
- var.tags (type: map(string), default: {json.dumps(tags)})

MANDATORY RULES:
- Include description for each variable
- Include type for each variable
- Include default values for each variable
- Add validation block for resource_group_name: must start with "rg-"
- Add validation block for storage_account_name: must be 3-24 lowercase letters and digits only
- Add validation block for location: must be one of ["eastus", "eastus2", "westus", "westus2", "centralus", "westeurope", "northeurope"]
- Add validation block for replication_type: must be one of ["LRS", "GRS", "ZRS", "RAGRS"]

OUTPUT RULES:
- Output ONLY valid Terraform HCL code
- Do NOT include any explanations or markdown formatting
- Do NOT wrap in code blocks
- Do NOT add any text before or after the code"""

    print("Calling Gemini AI for variables.tf (with validation)...")
    variables_tf_raw = call_gemini(variables_prompt)
    variables_tf = extract_code_block(variables_tf_raw)
    print("variables.tf generated successfully!")

    # ============================================
    # GEMINI AI: Generate outputs.tf (WITH SENSITIVE)
    # ============================================
    outputs_prompt = """You are a senior Terraform engineer. Generate an outputs.tf file for Azure infrastructure.

The resources are:
- azurerm_resource_group.rg
- azurerm_storage_account.sa

Generate outputs for:
- resource_group_id (description: "ID of the resource group")
- resource_group_name (description: "Name of the resource group")
- storage_account_id (description: "ID of the storage account")
- storage_account_name (description: "Name of the storage account")
- storage_account_primary_blob_endpoint (description: "Primary blob endpoint")
- storage_account_primary_connection_string (description: "Primary connection string", MUST mark as sensitive = true)

MANDATORY RULES:
- Include description for each output
- Mark connection string output as sensitive = true

OUTPUT RULES:
- Output ONLY valid Terraform HCL code
- Do NOT include any explanations or markdown formatting
- Do NOT wrap in code blocks
- Do NOT add any text before or after the code"""

    print("Calling Gemini AI for outputs.tf (with sensitive outputs)...")
    outputs_tf_raw = call_gemini(outputs_prompt)
    outputs_tf = extract_code_block(outputs_tf_raw)
    print("outputs.tf generated successfully!")

    # ============================================
    # README (no AI needed)
    # ============================================
readme_lines = [
        f"# AI-Generated IaC (Infrastructure as Code)",
        f"",
        f"- **Repo:** {REPO}",
        f"- **Issue:** #{ISSUE_NUMBER}",
        f"- **Title:** {ISSUE_TITLE}",
        f"- **Environment:** {environment}",
        f"- **Region:** {location}",
        f"- **Generated by:** Google Gemini AI (Security-Hardened)",
        f"",
        f"## Security Features Included",
        f"- TLS 1.2 enforced",
        f"- HTTPS only traffic",
        f"- Public network access disabled",
        f"- Infrastructure encryption enabled",
        f"- Blob versioning enabled",
        f"- StorageV2 account kind",
        f"",
        f"## Usage",
        f"    terraform init",
        f"    terraform plan",
        f"    terraform apply",
        f"",
        f"> This code was automatically generated from a GitHub Issue using AI.",
        f"> Please review carefully before merging.",
    ]
    readme = "\n".join(readme_lines)
# Write all files
    (out_dir / "main.tf").write_text(main_tf)
