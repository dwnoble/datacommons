import os

class Config:
  """Base configuration."""
  # Database settings
  GCP_PROJECT_ID: str = os.getenv('GCP_PROJECT_ID', '')
  GCP_SPANNER_INSTANCE_ID: str = os.getenv('GCP_SPANNER_INSTANCE_ID', '')
  GCP_SPANNER_DATABASE_NAME: str = os.getenv('GCP_SPANNER_DATABASE_NAME', '')
  GCP_REGION: str = os.getenv('GCP_REGION', 'us-central1')
  GCP_SPANNER_EMBEDDING_MODEL_NAME: str = os.getenv('GCP_SPANNER_EMBEDDING_MODEL_NAME', 'EmbeddingsModel')
  GCP_VERTEX_AI_EMBEDDING_MODEL_NAME: str = os.getenv('GCP_VERTEX_AI_EMBEDDING_MODEL_NAME', 'text-embedding-004')
  GCP_VERTEX_AI_EMBEDDING_MODEL_ENDPOINT: str = os.getenv('GCP_VERTEX_AI_EMBEDDING_MODEL_ENDPOINT', f'//aiplatform.googleapis.com/projects/{GCP_PROJECT_ID}/locations/{GCP_REGION}/publishers/google/models/{GCP_VERTEX_AI_EMBEDDING_MODEL_NAME}')
class DevelopmentConfig(Config):
  """Development configuration."""
  DEBUG = True

class ProductionConfig(Config):
  """Production configuration."""
  DEBUG = False

# Configuration dictionary
config = {
  'development': DevelopmentConfig,
  'production': ProductionConfig,
  'default': DevelopmentConfig
}

def get_config() -> Config:
  """Get the appropriate configuration object based on environment."""
  env = os.getenv('APP_ENV', 'default')
  return config[env]()  # Instantiate the config class