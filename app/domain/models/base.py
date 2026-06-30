"""
Base classes for domain entities and value objects.

Provides a consistent foundation: entities get a stable UUID
identity and lifecycle timestamps; value objects are compared
by their attributes.
"""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class BaseValueObject(BaseModel):
    """
    Marker base for all domain value objects.

    Value objects have no identity — two instances with the same
    attributes are considered equal. They should be immutable and
    self-validating.
    """


class BaseEntity(BaseModel):
    """
    Base for all domain entities.

    Entities have a stable UUID identity that persists across
    merges and updates. Lifecycle timestamps are set on creation
    and updated on modification.

    Attributes:
        id: Stable unique identifier (immutable after creation).
        created_at: When this entity was first created.
        updated_at: When this entity was last modified.
    """

    id: UUID = Field(default_factory=uuid4, frozen=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
