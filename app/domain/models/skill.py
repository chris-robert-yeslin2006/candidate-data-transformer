"""
Skill entity.

Represents a single skill with categorization, proficiency, and
identity. Skills have aliases to support deduplication across
sources (e.g., "JS", "JavaScript", "Javascript").
"""

from pydantic import Field

from app.domain.models.base import BaseEntity


class Skill(BaseEntity):
    """
    A single skill with identity, categorization, and aliases.

    Entity — each skill has a unique identity for cross-referencing.
    The ``normalized_name`` provides a canonical form for deduplication,
    while ``aliases`` captures alternative names from different sources.

    Attributes:
        name: Skill name as extracted from the source
              (e.g. "Python", "Project Management").
        normalized_name: Canonical form for deduplication
                         (e.g. "JavaScript" for "JS", "Javascript").
        aliases: Alternative names for this skill from different sources.
        category: Skill category (programming_language, framework,
                  tool, soft_skill, etc.).
        proficiency: Proficiency level (beginner, intermediate,
                     advanced, expert).
    """

    name: str
    normalized_name: str = Field(
        default="",
        description="Canonical form for deduplication",
    )
    aliases: list[str] = Field(
        default=[],
        description="Alternative names from different sources",
    )
    category: str = ""
    proficiency: str = ""
