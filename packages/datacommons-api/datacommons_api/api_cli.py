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

import click
import uvicorn

from datacommons_api.app import app
from datacommons_api.core.config import get_config, initialize_config
from datacommons_api.core.logging import get_logger, setup_logging
from datacommons_db.session import get_session, initialize_db
from datacommons_api.services.graph_service import GraphService

setup_logging()
logger = get_logger(__name__)


@click.group()
def api():
    """Data Commons API CLI suite"""
    pass


@api.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to.")
@click.option("--port", default=5000, help="Port to listen on.")
@click.option("--reload", is_flag=True, help="Enable auto-reload.")
@click.option(
    "--db-backend",
    type=click.Choice(["spanner", "postgres"], case_sensitive=False),
    default="spanner",
    show_default=True,
    help="Database backend to use.",
)
@click.option("--gcp-project-id", default="", help="GCP project id.")
@click.option("--gcp-spanner-instance-id", default="", help="GCP Spanner instance id.")
@click.option(
    "--gcp-spanner-database-name", default="", help="GCP Spanner database name."
)
@click.option("--postgres-host", default="", help="PostgreSQL host.")
@click.option("--postgres-port", default=5432, help="PostgreSQL port.")
@click.option("--postgres-database", default="", help="PostgreSQL database name.")
@click.option("--postgres-user", default="", help="PostgreSQL user.")
@click.option("--postgres-password", default="", help="PostgreSQL password.")
@click.option(
    "--postgres-sslmode",
    default="disable",
    show_default=True,
    help="PostgreSQL SSL mode.",
)
def start(
    host: str,
    port: int,
    reload: bool,
    db_backend: str,
    gcp_project_id: str,
    gcp_spanner_instance_id: str,
    gcp_spanner_database_name: str,
    postgres_host: str,
    postgres_port: int,
    postgres_database: str,
    postgres_user: str,
    postgres_password: str,
    postgres_sslmode: str,
):
    """Start the FastAPI app with Uvicorn."""
    logger.info("Starting Data Commons...")
    config = initialize_config(
        db_backend=db_backend,
        gcp_project_id=gcp_project_id,
        gcp_spanner_instance_id=gcp_spanner_instance_id,
        gcp_spanner_database_name=gcp_spanner_database_name,
        postgres_host=postgres_host,
        postgres_port=postgres_port,
        postgres_database=postgres_database,
        postgres_user=postgres_user,
        postgres_password=postgres_password,
        postgres_sslmode=postgres_sslmode,
    )

    # Initialize the database
    logger.info("Initializing database...")
    logger.info("Database backend: %s", config.DB_BACKEND)
    if config.DB_BACKEND == "spanner":
        logger.info("GCP Project ID: %s", config.GCP_PROJECT_ID)
        logger.info("GCP Spanner Instance ID: %s", config.GCP_SPANNER_INSTANCE_ID)
        logger.info("GCP Spanner Database Name: %s", config.GCP_SPANNER_DATABASE_NAME)
    else:
        logger.info("PostgreSQL Host: %s", config.POSTGRES_HOST)
        logger.info("PostgreSQL Port: %s", config.POSTGRES_PORT)
        logger.info("PostgreSQL Database: %s", config.POSTGRES_DATABASE)
        logger.info("PostgreSQL User: %s", config.POSTGRES_USER)

    initialize_db(
        project_id=config.GCP_PROJECT_ID,
        instance_id=config.GCP_SPANNER_INSTANCE_ID,
        database_name=config.GCP_SPANNER_DATABASE_NAME,
        db_backend=config.DB_BACKEND,
        postgres_host=config.POSTGRES_HOST,
        postgres_port=config.POSTGRES_PORT,
        postgres_database=config.POSTGRES_DATABASE,
        postgres_user=config.POSTGRES_USER,
        postgres_password=config.POSTGRES_PASSWORD,
        postgres_sslmode=config.POSTGRES_SSLMODE,
    )
    logger.info("Starting API server...")
    uvicorn.run(
        "datacommons_api.app:app",
        host=host,
        port=port,
        reload=reload,
    )


@api.command()
@click.option(
    "--db-backend",
    type=click.Choice(["spanner", "postgres"], case_sensitive=False),
    default="spanner",
    show_default=True,
    help="Database backend to use.",
)
@click.option("--gcp-project-id", help="GCP project id.", default="")
@click.option(
    "--gcp-spanner-instance-id", help="GCP Spanner instance id.", default=""
)
@click.option(
    "--gcp-spanner-database-name", help="GCP Spanner database name.", default=""
)
@click.option("--postgres-host", default="", help="PostgreSQL host.")
@click.option("--postgres-port", default=5432, help="PostgreSQL port.")
@click.option("--postgres-database", default="", help="PostgreSQL database name.")
@click.option("--postgres-user", default="", help="PostgreSQL user.")
@click.option("--postgres-password", default="", help="PostgreSQL password.")
@click.option(
    "--postgres-sslmode",
    default="disable",
    show_default=True,
    help="PostgreSQL SSL mode.",
)
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
def drop_tables(
    db_backend: str,
    gcp_project_id: str,
    gcp_spanner_instance_id: str,
    gcp_spanner_database_name: str,
    postgres_host: str,
    postgres_port: int,
    postgres_database: str,
    postgres_user: str,
    postgres_password: str,
    postgres_sslmode: str,
    yes: bool,
):
    """Drop Node and Edge tables from the graph database."""
    # TODO: Refactor this method to only drop the data from the tables, not the tables themselves.
    if not yes:
        click.confirm(
            "Are you sure you want to drop the Node and Edge tables?", abort=True
        )

    logger.info("Dropping Node and Edge tables from the graph database")
    initialize_config(
        db_backend=db_backend,
        gcp_project_id=gcp_project_id,
        gcp_spanner_instance_id=gcp_spanner_instance_id,
        gcp_spanner_database_name=gcp_spanner_database_name,
        postgres_host=postgres_host,
        postgres_port=postgres_port,
        postgres_database=postgres_database,
        postgres_user=postgres_user,
        postgres_password=postgres_password,
        postgres_sslmode=postgres_sslmode,
    )
    config = get_config()
    db = get_session(
        project_id=config.GCP_PROJECT_ID,
        instance_id=config.GCP_SPANNER_INSTANCE_ID,
        database_name=config.GCP_SPANNER_DATABASE_NAME,
        db_backend=config.DB_BACKEND,
        postgres_host=config.POSTGRES_HOST,
        postgres_port=config.POSTGRES_PORT,
        postgres_database=config.POSTGRES_DATABASE,
        postgres_user=config.POSTGRES_USER,
        postgres_password=config.POSTGRES_PASSWORD,
        postgres_sslmode=config.POSTGRES_SSLMODE,
    )
    graph_service = GraphService(db)
    graph_service.drop_tables()
    logger.info("Successfully dropped Node and Edge tables")
