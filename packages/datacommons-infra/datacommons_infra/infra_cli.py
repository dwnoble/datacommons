# Copyright 2026 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path

import click

MAIN_TF_TEMPLATE = """terraform {{
  required_version = ">= 1.5.0"

  required_providers {{
    google = {{
      source  = "hashicorp/google"
      version = ">= 5.11.0"
    }}
  }}
}}

module "datacommons_dcp" {{
  # Pin this to a tag/commit for reproducible deployments.
  source = "git::https://github.com/datacommonsorg/datacommons.git//infra/dcp?ref={ref}"

  project_id = var.project_id
  namespace  = var.namespace
  cdc_dc_api_key = var.dc_api_key

  enable_dcp = true
  enable_cdc = true

  dcp_create_spanner_instance = true
  dcp_spanner_database_id     = var.dcp_spanner_database_id
}}

variable "project_id" {{
  description = "GCP project id"
  type        = string
}}

variable "namespace" {{
  description = "Prefix applied to provisioned resource names"
  type        = string
}}

variable "dc_api_key" {{
  description = "Data Commons API key"
  type        = string
  default     = ""
}}

variable "dcp_spanner_database_id" {{
  description = "Spanner database id for DCP"
  type        = string
  default     = "dcp-db"
}}

output "dcp_service_url" {{
  value = module.datacommons_dcp.dcp_service_url
}}

output "dcp_spanner_instance_id" {{
  value = module.datacommons_dcp.dcp_spanner_instance_id
}}

output "dcp_spanner_database_id" {{
  value = module.datacommons_dcp.dcp_spanner_database_id
}}
"""

TFVARS_TEMPLATE = """project_id = "{project_id}"
namespace  = "{namespace}"
dc_api_key = "{dc_api_key}"

# Optional (defaults to dcp-db)
dcp_spanner_database_id = "dcp-db"
"""

README_TEMPLATE = """# Data Commons Platform Terraform Setup

This directory contains Terraform configuration for a new Data Commons Platform instance.

Data Commons is an open knowledge graph for integrating and querying structured data across domains.
The Data Commons Platform is the deployable infrastructure stack that runs Data Commons services in your GCP project.

## What This Terraform Creates

This setup deploys core Data Commons Platform infrastructure on GCP using the `infra/dcp` module, including Cloud Run services, Cloud Spanner resources, IAM bindings, and supporting service configuration.

## Configure Variables

Set environment-specific values in `terraform.tfvars` (for example `project_id`, `namespace`, and `dc_api_key`), and update module arguments in `main.tf` if you want to enable or tune additional features.

## Learn More About Variables

For the full list of supported module inputs and defaults, see:
- https://github.com/datacommonsorg/datacommons/blob/main/infra/dcp/variables.tf
- https://github.com/datacommonsorg/datacommons/blob/main/infra/dcp/terraform.tfvars.example
- https://github.com/datacommonsorg/datacommons/blob/main/infra/dcp/README.md

## Next Steps

1. Review `terraform.tfvars` and update values if needed.
2. Initialize Terraform:
   ```bash
   terraform init
   ```
3. Preview infrastructure changes:
   ```bash
   terraform plan
   ```
4. Deploy infrastructure:
   ```bash
   terraform apply
   ```

Generated using the Data Commons CLI tool:
https://github.com/datacommonsorg/datacommons
"""


@click.group()
def infra() -> None:
    """Infrastructure commands."""


@infra.command()
@click.option("--project-id", default="", help="GCP project id to initialize into tfvars.")
@click.option("--namespace", default="", help="Namespace prefix for provisioned resources.")
@click.option("--dc-api-key", default="", help="Data Commons API key.")
@click.option("--ref", default="main", show_default=True, help="Git ref for module source.")
@click.option("--force", is_flag=True, help="Overwrite existing generated files if present.")
def init(
    project_id: str,
    namespace: str,
    dc_api_key: str,
    ref: str,
    force: bool,
) -> None:
    """Initialize Terraform scaffolding for Data Commons infrastructure."""
    click.secho("Datacommons Infra Init", fg="cyan", bold=True)
    click.secho("Generating Terraform starter files...", fg="bright_black")

    resolved_project_id = project_id.strip() or click.prompt(
        "GCP project id", type=str, prompt_suffix=": "
    ).strip()
    if not resolved_project_id:
        raise click.ClickException("GCP project id must not be empty.")

    resolved_namespace = namespace.strip() or click.prompt(
        "Namespace", type=str, prompt_suffix=": "
    ).strip()
    if not resolved_namespace:
        raise click.ClickException("Namespace must not be empty.")

    resolved_dc_api_key = dc_api_key.strip() or click.prompt(
        "Data Commons API key (get one at apikeys.datacommons.org)",
        type=str,
        default="",
        show_default=False,
        prompt_suffix=": ",
    ).strip()

    target_dir = Path.cwd() / resolved_namespace
    main_tf_path = target_dir / "main.tf"
    tfvars_path = target_dir / "terraform.tfvars"
    readme_path = target_dir / "README.md"
    existing_paths = [
        path for path in (main_tf_path, tfvars_path, readme_path) if path.exists()
    ]
    if existing_paths and not force:
        existing_labels = ", ".join(str(path) for path in existing_paths)
        raise click.ClickException(
            f"Refusing to overwrite existing file(s): {existing_labels}. "
            "Use --force to overwrite."
        )

    target_dir.mkdir(parents=True, exist_ok=True)
    main_tf_path.write_text(MAIN_TF_TEMPLATE.format(ref=ref), encoding="utf-8")
    tfvars_path.write_text(
        TFVARS_TEMPLATE.format(
            project_id=resolved_project_id,
            namespace=resolved_namespace,
            dc_api_key=resolved_dc_api_key,
        ),
        encoding="utf-8",
    )
    readme_path.write_text(README_TEMPLATE, encoding="utf-8")

    click.secho(f"Initialized Terraform scaffold in {target_dir}", fg="green")
    click.secho(f"- Wrote {main_tf_path}", fg="bright_black")
    click.secho(f"- Wrote {tfvars_path}", fg="bright_black")
    click.secho(f"- Wrote {readme_path}", fg="bright_black")
    click.secho(
        f"Generated new folder '{resolved_namespace}'. See {resolved_namespace}/README.md for next steps.",
        fg="cyan",
    )
