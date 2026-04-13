# Copyright 2025 Google LLC.
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

import os
import sys
from dotenv import load_dotenv

from datacommons_api.core.logging import get_logger

# Load environment variables from .env file
load_dotenv()

logger = get_logger(__name__)

class Config:
    """Base configuration."""

    # Database settings
    DB_BACKEND: str = os.getenv("DB_BACKEND", "spanner")
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "")
    GCP_SPANNER_INSTANCE_ID: str = os.getenv("GCP_SPANNER_INSTANCE_ID", "")
    GCP_SPANNER_DATABASE_NAME: str = os.getenv("GCP_SPANNER_DATABASE_NAME", "")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DATABASE: str = os.getenv("POSTGRES_DATABASE", "")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_SSLMODE: str = os.getenv("POSTGRES_SSLMODE", "disable")


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False


# Configuration dictionary
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


# Default configuration
app_config = config[os.getenv("APP_ENV", "default")]()


def validate_config_or_exit(config: Config) -> None:
    """Ensure the configuration is valid"""
    if config.DB_BACKEND == "spanner":
        required_env_vars = [
            "GCP_PROJECT_ID",
            "GCP_SPANNER_INSTANCE_ID",
            "GCP_SPANNER_DATABASE_NAME",
        ]
        for var in required_env_vars:
            if not getattr(config, var):
                logger.error("Config variable %s must be set for spanner backend", var)
                sys.exit(1)
        return

    if config.DB_BACKEND == "postgres":
        required_env_vars = [
            "POSTGRES_HOST",
            "POSTGRES_DATABASE",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
        ]
        for var in required_env_vars:
            if not getattr(config, var):
                logger.error(
                    "Config variable %s must be set for postgres backend", var
                )
                sys.exit(1)
        return

    logger.error(
        "Unsupported DB_BACKEND '%s'. Supported values: spanner, postgres",
        config.DB_BACKEND,
    )
    sys.exit(1)


def initialize_config(
    db_backend: str = "",
    gcp_project_id: str = "",
    gcp_spanner_instance_id: str = "",
    gcp_spanner_database_name: str = "",
    postgres_host: str = "",
    postgres_port: int | None = None,
    postgres_database: str = "",
    postgres_user: str = "",
    postgres_password: str = "",
    postgres_sslmode: str = "",
) -> Config:
    """
    Initialize the configuration object based on environment or command line arguments.

    Args:
        db_backend: Database backend ("spanner" or "postgres").
        gcp_project_id: Optional GCP project id.
        gcp_spanner_instance_id: Optional GCP Spanner instance id.
        gcp_spanner_database_name: Optional GCP Spanner database name.
        postgres_host: Optional PostgreSQL host.
        postgres_port: Optional PostgreSQL port.
        postgres_database: Optional PostgreSQL database name.
        postgres_user: Optional PostgreSQL user.
        postgres_password: Optional PostgreSQL password.
        postgres_sslmode: Optional PostgreSQL SSL mode.

    Returns:
        Config: The configuration object.
    """
    app_config.DB_BACKEND = (db_backend or app_config.DB_BACKEND).lower()
    app_config.GCP_PROJECT_ID = gcp_project_id or app_config.GCP_PROJECT_ID
    app_config.GCP_SPANNER_INSTANCE_ID = (
        gcp_spanner_instance_id or app_config.GCP_SPANNER_INSTANCE_ID
    )
    app_config.GCP_SPANNER_DATABASE_NAME = (
        gcp_spanner_database_name or app_config.GCP_SPANNER_DATABASE_NAME
    )
    app_config.POSTGRES_HOST = postgres_host or app_config.POSTGRES_HOST
    app_config.POSTGRES_PORT = postgres_port or app_config.POSTGRES_PORT
    app_config.POSTGRES_DATABASE = postgres_database or app_config.POSTGRES_DATABASE
    app_config.POSTGRES_USER = postgres_user or app_config.POSTGRES_USER
    app_config.POSTGRES_PASSWORD = postgres_password or app_config.POSTGRES_PASSWORD
    app_config.POSTGRES_SSLMODE = postgres_sslmode or app_config.POSTGRES_SSLMODE
    validate_config_or_exit(app_config)
    return app_config


def get_config() -> Config:
    """
    Get the configuration object.

    Returns:
        Config: The configuration object.
    """
    return app_config
