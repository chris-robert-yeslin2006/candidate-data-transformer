"""
Nested projection engine.

Filters and projects structured dictionaries based on a nested schema of boolean flags.
Supports granular field selection for custom client templates.
"""

from typing import Any


class NestedProjectionEngine:
    """
    Projects and filters structured data based on a nested schema of boolean flags.

    Example:
        data = {
            "id": "123",
            "details": {"email": "test@test.com", "phone": "999"},
            "tags": ["A", "B"],
            "metadata": {"source": "web"}
        }
        schema = {
            "details": {"email": True},
            "tags": True
        }
        output = {
            "details": {"email": "test@test.com"},
            "tags": ["A", "B"]
        }
    """

    def project(self, data: Any, schema: Any) -> Any:
        """
        Recursively filter data according to the schema.

        Args:
            data: The source data (dict, list, or primitive).
            schema: The projection schema (dict of booleans/sub-dicts, or boolean).

        Returns:
            The projected and filtered data.
        """
        # If schema is True, keep the entire data item
        if schema is True:
            return data

        # If schema is False or None, filter it out
        if not schema:
            return None

        # If schema is a dictionary
        if isinstance(schema, dict):
            # If data is also a dictionary, project its keys
            if isinstance(data, dict):
                result: dict[str, Any] = {}
                for key, sub_schema in schema.items():
                    if key in data:
                        val = self.project(data[key], sub_schema)
                        if val is not None:
                            result[key] = val
                return result

            # If data is a list, project each item inside the list
            elif isinstance(data, (list, tuple)):
                projected_list = []
                for item in data:
                    val = self.project(item, schema)
                    if val is not None:
                        projected_list.append(val)
                return projected_list

        # Return None if schema structure and data structure do not align
        return None
