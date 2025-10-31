# Windows Server 2025 Upgrade Automation

This repository provisions Azure networking and Windows Server virtual machines using Compute Gallery images. The configuration is decomposed into reusable modules for networking, OS image lookups, and VM deployment.

## Structure

- `modules/` contains reusable Terraform modules.
- `env/<environment>/terraform.tfvars` provides environment-specific overrides.
- `azure-pipelines.yml` defines Terraform validation automation.
- `pull_request_template.md` enforces PR hygiene.

## Usage

1. Populate the desired environment tfvars file with required variable values.
2. Export the appropriate Azure credentials.
3. Run Terraform commands referencing the environment overrides:

   ```bash
   terraform init
   terraform plan -var-file="env/dev/terraform.tfvars"
   terraform apply -var-file="env/dev/terraform.tfvars"
   ```

## Prerequisites

- Existing resource group and Key Vault containing the local admin password secret.
- Compute Gallery image ID for Windows Server 2025 supplied through `ws2025_image_id`.

## Documentation

Module documentation is generated with `terraform-docs` and must remain in sync with the module variable definitions. The automated pipeline will fail if generated documentation differs from the committed files.
