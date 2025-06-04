# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sqlalchemy as sa
from sqlalchemy.orm import Session
from datacommons.db.models.edge import EdgeModel
from sqlalchemy.types import Text, ARRAY, Float
import logging

logger = logging.getLogger(__name__)

class EdgeRepository:
  """
  Repository for managing edges in the database.
  """
  def __init__(self, session: Session):
    self.session = session

  def get_edge(self, subject_id: str, predicate: str, object_id: str) -> EdgeModel:
    return self.session.query(EdgeModel).filter(EdgeModel.subject_id == subject_id, EdgeModel.predicate == predicate, EdgeModel.object_id == object_id).first()

  def create_edge(self, edge: EdgeModel) -> EdgeModel:
    self.session.add(edge)
    self.session.commit()
    return edge
  
  def build_create_edge_with_embedding_statement(
    self,
    edge: EdgeModel
  ):
    """
    Builds a SQL statement for creating an Edge with an embedding.
    Returns a tuple of (sql_string, parameters) for execution.

    Uses the Google Cloud AI Platform to compute the embedding of the object value.
    """
    sql = f"""
    INSERT INTO {EdgeModel.__tablename__} (
      subject_id,
      predicate,
      object_id,
      object_value,
      object_hash,
      provenance,
      object_value_embedding
    )
    WITH Input AS (
      SELECT :object_value AS content
    ),
    Prediction AS (
      SELECT 
        t.content,
        e.embeddings.values as embeddings_values
      FROM
        ML.PREDICT(
          MODEL EmbeddingsModel,
          TABLE Input
        ) AS e,
        Input AS t
    )
    SELECT
      :subject_id,
      :predicate,
      Input.content,
      Input.content,
      TO_BASE64(SHA256(Input.content)),
      :provenance,
      embeddings_values
    FROM Prediction, Input
    """
    
    params = {
      'subject_id': edge.subject_id,
      'predicate': edge.predicate,
      'object_value': edge.object_value,
      'provenance': edge.provenance or ""
    }
    
    return sql, params