from sqlalchemy import create_engine, inspect, Engine, text
from sqlalchemy.orm import sessionmaker, Session
from datacommons.db.models.base import Base
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

def get_engine(project_id: str, instance_id: str, database_name: str) -> Engine:
  """Create and return a SQLAlchemy engine for Cloud Spanner.
  
  Args:
    project_id: GCP project ID
    instance_id: Cloud Spanner instance ID 
    database_name: Cloud Spanner database name
    
  Returns:
    SQLAlchemy engine configured for Cloud Spanner
  """
  return create_engine(
    f"spanner+spanner:///projects/{project_id}/instances/{instance_id}/databases/{database_name}",
  )

def get_session(project_id: str, instance_id: str, database_name: str) -> Session:
  """Create and return a SQLAlchemy session for Cloud Spanner.
  
  Args:
    project_id: GCP project ID
    instance_id: Cloud Spanner instance ID
    database_name: Cloud Spanner database name
    
  Returns:
    SQLAlchemy session configured for Cloud Spanner
  """
  engine = get_engine(project_id, instance_id, database_name)
  Session = sessionmaker(bind=engine)
  return Session()

def initialize_db(project_id: str, instance_id: str, database_name: str):
  """Initialize the Spanner database.
  
  Args:
    project_id: GCP project ID
    instance_id: Cloud Spanner instance ID
    database_name: Cloud Spanner database name
  """
  engine = get_engine(project_id, instance_id, database_name)
  
  # Check if database is empty by inspecting existing tables
  inspector = inspect(engine)
  existing_tables = inspector.get_table_names()

  # Only create tables if database is completely empty
  if not existing_tables:
    # Import all models so they are properly initialized with the call to Base.metadata.create_all
    from datacommons.db.models.node import NodeModel
    from datacommons.db.models.edge import EdgeModel
    from datacommons.db.models.observation import ObservationModel
    logging.info(f"Creating tables in database {database_name}")
    Base.metadata.create_all(engine)


def initialize_vertex_ai_embedding_model(project_id: str, instance_id: str, database_name: str, model_name: str, model_endpoint: str):
  """Initialize the Vertex AI embedding model.
  
  Args:
    project_id: GCP project ID
    instance_id: Cloud Spanner instance ID
    database_name: Cloud Spanner database name
    model_name: Vertex AI embedding model name
    model_endpoint: Vertex AI embedding model endpoint
  """
  try:
    engine = get_engine(project_id, instance_id, database_name)
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
      # First, query to see if the model exists and what its current endpoint is.
      query_sql = text("""
        SELECT OPTION_VALUE
        FROM INFORMATION_SCHEMA.MODEL_OPTIONS
        WHERE MODEL_NAME = :model_name AND OPTION_NAME = 'endpoint'
      """)
      
      result = connection.execute(query_sql, {"model_name": model_name})
      current_endpoint = result.scalar_one_or_none()

      # If the current endpoint is the same as the desired one, do nothing.
      if current_endpoint == model_endpoint:
        logging.info(f"Model '{model_name}' is already up-to-date with the correct endpoint.")
        return

      # If the model doesn't exist or the endpoint is different, create or replace it.
      logging.info(f"Endpoint for model '{model_name}' is either missing or outdated. Updating...")

      ddl_statement = f"""
      CREATE OR REPLACE MODEL {model_name}
      INPUT(content STRING(MAX))
      OUTPUT(embeddings STRUCT<statistics STRUCT<truncated BOOL, token_count FLOAT64>, values ARRAY<FLOAT64>>)
      REMOTE OPTIONS (endpoint = '{model_endpoint}')
      """
      
      # Execute the DDL statement.
      connection.execute(text(ddl_statement))
      
      logging.info(f"Successfully created or updated model '{model_name}' with endpoint '{model_endpoint}'.")

  except SQLAlchemyError as e:
    logging.error(f"An error occurred while connecting or executing DDL: {e}")
  except ImportError:
    logging.error("Please install the required spanner-sqlalchemy library: pip install google-cloud-spanner-sqlalchemy")
