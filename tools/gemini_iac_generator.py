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
    # Try to find ```hcl or ```terraform blocks
    pattern = r"```(?:hcl|terraform)?\s*\n([\s\S]*?)```"
    matches = re.findall(pattern, text)
    if matches:
        return "\n\n".join(matches)
    # If no code blocks, return the full text
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
    # GEMINI AI: Generate main.tf
    # ============================================
    main_tf_prompt = f"""You are a Terraform expert. Generate production-ready Terraform code for Azure.

Requirements:
- Create a Resource Group named "{rg_name}" in "{location}"
- Create a Storage Account named "{resource_name}" in the same resource group
- SKU: {sku}
- Tags: {json.dumps(tags)}

Rules:
- Use azurerm provider >= 3.0.0
- Include terraform block with required_version >= 1.5.0
- Include provider "azurerm" block with features {{}}
- Use variables for all configurable values (resource_group_name, location, storage_account_name, replication_type, tags)
- Reference variables using var.variable_name
- Output ONLY valid Terraform HCL code
- Do NOT include any explanations, comments, or markdown formatting
- Do NOT wrap in code blocks"""

    print("\nCalling Gemini AI for main.tf...")
    main_tf_raw = call_gemini(main_tf_prompt)
    main_tf = extract_code_block(main_tf_raw)
    print("main.tf generated successfully!")

    # ============================================
    # GEMINI AI: Generate variables.tf
    # ============================================
    variables_prompt = f"""You are a Terraform expert. Generate a variables.tf file for Azure infrastructure.

The variables must match this main.tf usage:
- var.resource_group_name (default: "{rg_name}")
- var.location (default: "{location}")
- var.storage_account_name (default: "{resource_name}")
- var.replication_type (default: "{sku.split('_')[-1] if '_' in sku else 'LRS'}")
- var.tags (type: map(string), default: {json.dumps(tags)})

Rules:
- Include description for each variable
- Include type for each variable
- Include default values
- Output ONLY valid Terraform HCL code
- Do NOT include any explanations or markdown formatting
- Do NOT wrap in code blocks"""

    print("Calling Gemini AI for variables.tf...")
    variables_tf_raw = call_gemini(variables_prompt)
    variables_tf = extract_code_block(variables_tf_raw)
    print("variables.tf generated successfully!")

    # ============================================
    # GEMINI AI: Generate outputs.tf
    # ============================================
    outputs_prompt = """You are a Terraform expert. Generate an outputs.tf file for Azure infrastructure.

The resources are:
- azurerm_resource_group.rg
- azurerm_storage_account.sa

Generate outputs for:
- resource_group_id
- storage_account_id
- storage_account_primary_blob_endpoint

Rules:
- Include description for each output
- Output ONLY valid Terraform HCL code
- Do NOT include any explanations or markdown formatting
- Do NOT wrap in code blocks"""

    print("Calling Gemini AI for outputs.tf...")
    outputs_tf_raw = call_gemini(outputs_prompt)
    outputs_tf = extract_code_block(outputs_tf_raw)
    print("outputs.tf generated successfully!")

    # ============================================
    # README (no AI needed)
    # ============================================
    readme = f"""# AI-Generated IaC (Infrastructure as Code)

- **Repo:** {REPO}
- **Issue:** #{ISSUE_NUMBER}
- **Title:** {ISSUE_TITLE}
- **Environment:** {environment}
- **Region:** {location}
- **Generated by:** Google Gemini AI

> This code was automatically generated from a GitHub Issue using AI.
> Please review carefully before merging.
"""

    # Write all files
    (out_dir / "main.tf").write_text(main_tf)
    (out_dir / "variables.tf").write_text(variables_tf)
    (out_dir / "outputs.tf").write_text(outputs_tf)
    (out_dir / "README.md").write_text(readme)

    print(f"\nAll files generated in: {out_dir}")
    print("Files: main.tf, variables.tf, outputs.tf, README.md")


if __name__ == "__main__":
    main()
