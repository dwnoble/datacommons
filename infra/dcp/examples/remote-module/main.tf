terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.11.0"
    }
  }
}

module "datacommons_dcp" {
  # Pin this to a tag/commit for reproducible deployments.
  source = "git::https://github.com/your-org/datacommons.git//infra/dcp?ref=main"

  # Required
  project_id = var.project_id
  namespace  = var.namespace

  # Typical DCP-only deployment defaults
  enable_dcp = true
  enable_cdc = true

  dcp_create_spanner_instance = true
  dcp_spanner_database_id     = var.dcp_spanner_database_id
}

variable "project_id" {
  description = "GCP project id"
  type        = string
}

variable "namespace" {
  description = "Prefix applied to provisioned resource names"
  type        = string
}

variable "dcp_spanner_database_id" {
  description = "Spanner database id for DCP"
  type        = string
  default     = "dcp-db"
}

output "dcp_service_url" {
  value = module.datacommons_dcp.dcp_service_url
}

output "dcp_spanner_instance_id" {
  value = module.datacommons_dcp.dcp_spanner_instance_id
}

output "dcp_spanner_database_id" {
  value = module.datacommons_dcp.dcp_spanner_database_id
}
