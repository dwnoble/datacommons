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

import logging

from sqlalchemy import Engine, create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker

from datacommons_db.models.base import Base
from datacommons_db.models.edge import EDGE_TABLE_NAME
from datacommons_db.models.node import NODE_TABLE_NAME
from datacommons_db.models.observation import (
    OBSERVATION_ATTRIBUTE_TABLE_NAME,
    OBSERVATION_TABLE_NAME,
    TIMESERIES_ATTRIBUTE_TABLE_NAME,
    TIMESERIES_TABLE_NAME,
)

logger = logging.getLogger(__name__)

REQUIRED_TABLES = [
    NODE_TABLE_NAME,
    EDGE_TABLE_NAME,
    TIMESERIES_TABLE_NAME,
    TIMESERIES_ATTRIBUTE_TABLE_NAME,
    OBSERVATION_TABLE_NAME,
    OBSERVATION_ATTRIBUTE_TABLE_NAME,
]


# DDL for Creating Property Graph
DDL_PROPERTY_GRAPH = """
CREATE OR REPLACE PROPERTY GRAPH DCGraph
  NODE TABLES(
    Node
      KEY(subject_id)
      LABEL Node PROPERTIES(
        bytes,
        name,
        subject_id,
        types,
        value)
  )
  EDGE TABLES(
    Edge
      KEY(subject_id, predicate, object_id, provenance)
      SOURCE KEY(subject_id) REFERENCES Node(subject_id)
      DESTINATION KEY(object_id) REFERENCES Node(subject_id)
      LABEL Edge PROPERTIES(
        object_id,
        predicate,
        provenance,
        subject_id)
  );
"""


def get_engine(
    project_id: str = "",
    instance_id: str = "",
    database_name: str = "",
    db_backend: str = "spanner",
    postgres_host: str = "",
    postgres_port: int = 5432,
    postgres_database: str = "",
    postgres_user: str = "",
    postgres_password: str = "",
    postgres_sslmode: str = "disable",
) -> Engine:
    """Create and return a SQLAlchemy engine for the configured backend."""
    if db_backend == "spanner":
        return create_engine(
            f"spanner+spanner:///projects/{project_id}/instances/{instance_id}/databases/{database_name}",
        )

    if db_backend == "postgres":
        return create_engine(
            "postgresql+psycopg://"
            f"{postgres_user}:{postgres_password}"
            f"@{postgres_host}:{postgres_port}/{postgres_database}"
            f"?sslmode={postgres_sslmode}",
        )

    raise ValueError(f"Unsupported db_backend: {db_backend}")


def create_property_graph(engine: Engine):
    """Create the Property Graph schema in the database.

    Args:
      engine: SQLAlchemy engine connected to the database
    """
    from sqlalchemy import text

    with engine.begin() as connection:
        connection.execute(text(DDL_PROPERTY_GRAPH))


def enable_spanner_columnar_policy(engine: Engine):
    """Enable Spanner columnar policy for observation tables when available."""
    from sqlalchemy import text

    columnar_tables = [
        TIMESERIES_TABLE_NAME,
        TIMESERIES_ATTRIBUTE_TABLE_NAME,
        OBSERVATION_TABLE_NAME,
        OBSERVATION_ATTRIBUTE_TABLE_NAME,
    ]
    with engine.begin() as connection:
        for table_name in columnar_tables:
            try:
                connection.execute(
                    text(
                        f"ALTER TABLE {table_name} SET OPTIONS (columnar_policy = 'enabled')"
                    )
                )
            except Exception as e:
                logger.warning(
                    "Could not enable columnar policy for table %s: %s",
                    table_name,
                    e,
                )


def get_session(
    project_id: str = "",
    instance_id: str = "",
    database_name: str = "",
    db_backend: str = "spanner",
    postgres_host: str = "",
    postgres_port: int = 5432,
    postgres_database: str = "",
    postgres_user: str = "",
    postgres_password: str = "",
    postgres_sslmode: str = "disable",
) -> Session:
    """Create and return a SQLAlchemy session for the configured backend."""
    engine = get_engine(
        project_id=project_id,
        instance_id=instance_id,
        database_name=database_name,
        db_backend=db_backend,
        postgres_host=postgres_host,
        postgres_port=postgres_port,
        postgres_database=postgres_database,
        postgres_user=postgres_user,
        postgres_password=postgres_password,
        postgres_sslmode=postgres_sslmode,
    )
    session = sessionmaker(bind=engine)
    return session()


def initialize_db(
    project_id: str = "",
    instance_id: str = "",
    database_name: str = "",
    db_backend: str = "spanner",
    postgres_host: str = "",
    postgres_port: int = 5432,
    postgres_database: str = "",
    postgres_user: str = "",
    postgres_password: str = "",
    postgres_sslmode: str = "disable",
):
    """Initialize the configured database backend."""
    engine = get_engine(
        project_id=project_id,
        instance_id=instance_id,
        database_name=database_name,
        db_backend=db_backend,
        postgres_host=postgres_host,
        postgres_port=postgres_port,
        postgres_database=postgres_database,
        postgres_user=postgres_user,
        postgres_password=postgres_password,
        postgres_sslmode=postgres_sslmode,
    )

    # Check if database is empty by inspecting existing tables
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    # Check if all required tables exist
    missing_tables = [
        table for table in REQUIRED_TABLES if table not in existing_tables
    ]
    if missing_tables:
        logger.warning(
            "Missing required tables in database %s: %s", database_name, missing_tables
        )

    # Only create tables if database is completely empty
    if not existing_tables or missing_tables:
        # Import all models so they are properly initialized with the call to Base.metadata.create_all
        logger.info("Creating tables %s in database %s", REQUIRED_TABLES, database_name)
        Base.metadata.create_all(engine)
        if db_backend == "spanner":
            create_property_graph(engine)
            enable_spanner_columnar_policy(engine)
