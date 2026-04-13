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

import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.types import String

from datacommons_db.models.base import Base
from datacommons_db.models.node import NodeRecord

TIMESERIES_TABLE_NAME = "TimeSeries"
TIMESERIES_ATTRIBUTE_TABLE_NAME = "TimeSeriesAttribute"
OBSERVATION_TABLE_NAME = "Observation"
OBSERVATION_ATTRIBUTE_TABLE_NAME = "ObservationAttribute"


class TimeSeriesRecord(Base):
    """Series-level key row for observations."""

    __tablename__ = TIMESERIES_TABLE_NAME

    id = sa.Column(String(1024), primary_key=True, autoincrement=False)
    variable_measured = sa.Column(String(1024), sa.ForeignKey("Node.subject_id"))
    facet_id = sa.Column(String(1024), sa.ForeignKey("Node.subject_id"))
    import_name = sa.Column(String(1024))

    variable_node = relationship("NodeRecord", foreign_keys=[variable_measured], lazy="joined")
    facet_node = relationship("NodeRecord", foreign_keys=[facet_id], lazy="joined")

    attributes = relationship(
        "TimeSeriesAttributeRecord",
        back_populates="timeseries",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    observations = relationship(
        "ObservationRecord",
        back_populates="timeseries",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self):
        return (
            "<TimeSeriesRecord("
            f"id='{self.id}', variable_measured='{self.variable_measured}', "
            f"facet_id='{self.facet_id}', import_name='{self.import_name}')>"
        )


class TimeSeriesAttributeRecord(Base):
    """Arbitrary key/value pair attached to a series."""

    __tablename__ = TIMESERIES_ATTRIBUTE_TABLE_NAME

    id = sa.Column(String(1024), sa.ForeignKey("TimeSeries.id"), primary_key=True)
    property = sa.Column(String(1024), primary_key=True)
    value = sa.Column(String(1024), primary_key=True)

    timeseries = relationship("TimeSeriesRecord", back_populates="attributes", lazy="joined")

    __table_args__ = {
        "spanner_interleave_in": "TimeSeries",
        "spanner_interleave_on_delete_cascade": True,
    }


class ObservationRecord(Base):
    """Single observation point within a series."""

    __tablename__ = OBSERVATION_TABLE_NAME

    id = sa.Column(String(1024), sa.ForeignKey("TimeSeries.id"), primary_key=True)
    date = sa.Column(String(1024), primary_key=True)
    value = sa.Column(String(1024), nullable=False)

    timeseries = relationship("TimeSeriesRecord", back_populates="observations", lazy="joined")
    attributes = relationship(
        "ObservationAttributeRecord",
        back_populates="observation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = {
        "spanner_interleave_in": "TimeSeries",
        "spanner_interleave_on_delete_cascade": True,
    }

    def __repr__(self):
        return (
            "<ObservationRecord("
            f"id='{self.id}', date='{self.date}', value='{self.value}')>"
        )


class ObservationAttributeRecord(Base):
    """Arbitrary key/value pair attached to an observation row."""

    __tablename__ = OBSERVATION_ATTRIBUTE_TABLE_NAME

    id = sa.Column(String(1024), primary_key=True)
    date = sa.Column(String(1024), primary_key=True)
    property = sa.Column(String(1024), primary_key=True)
    value = sa.Column(String(1024), primary_key=True)

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["id", "date"],
            ["Observation.id", "Observation.date"],
            name="fk_observation_attribute_observation",
        ),
        {
            "spanner_interleave_in": "Observation",
            "spanner_interleave_on_delete_cascade": True,
        },
    )

    observation = relationship("ObservationRecord", back_populates="attributes", lazy="joined")


TimeSeriesAttributeRecord.__table__.add_is_dependent_on(TimeSeriesRecord.__table__)
ObservationRecord.__table__.add_is_dependent_on(TimeSeriesRecord.__table__)
ObservationAttributeRecord.__table__.add_is_dependent_on(ObservationRecord.__table__)
TimeSeriesRecord.__table__.add_is_dependent_on(NodeRecord.__table__)
