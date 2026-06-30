#!/usr/bin/env python
"""
Brief executable example demonstrating NestedProjectionEngine
processing the sample payload against the custom config schema.
"""

import json
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.projections.nested_projection import NestedProjectionEngine


def main() -> None:
    # 1. Instantiate the NestedProjectionEngine
    engine = NestedProjectionEngine()

    # 2. Define the source payload
    source_data = {
        "id": "123",
        "details": {
            "email": "test@test.com",
            "phone": "999"
        },
        "tags": ["A", "B"],
        "metadata": {
            "source": "web"
        }
    }

    # 3. Define the config schema (representing wants/templates)
    config_schema = {
        "details": {
            "email": True
        },
        "tags": True
    }

    # 4. Project and filter the data
    projected_output = engine.project(source_data, config_schema)

    # 5. Output results
    print("=== Source Data ===")
    print(json.dumps(source_data, indent=2))
    print("\n=== Config Schema ===")
    print(json.dumps(config_schema, indent=2))
    print("\n=== Expected Output ===")
    print(json.dumps({
        "details": {
            "email": "test@test.com"
        },
        "tags": ["A", "B"]
    }, indent=2))
    print("\n=== Actual Projected Output ===")
    print(json.dumps(projected_output, indent=2))


if __name__ == "__main__":
    main()
