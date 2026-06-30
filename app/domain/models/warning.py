"""
Warning model.

Represents a non-fatal issue encountered during candidate
data processing. Warnings are collected and propagated
through the pipeline without halting execution.
"""

from pydantic import BaseModel


class Warning(BaseModel):
    """
    A non-fatal processing warning.

    Captures issues such as missing fields, parse failures,
    normalization errors, or merge conflicts that do not
    prevent pipeline completion but indicate data quality
    concerns.

    Attributes:
        message: Human-readable warning description.
        source: Source identifier where the warning originated.
        code: Machine-readable warning code for categorization.
        field: The specific field or model the warning relates to.
    """

    message: str
    source: str = ""
    code: str = ""
    field: str = ""
