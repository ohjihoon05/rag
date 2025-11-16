#!/usr/bin/env python3
"""Test Infinity table creation directly"""

from infinity import connect

# Connect to Infinity
conn = connect("http://infinity:23820")

# Create database
db = conn.get_database("test_ragflow")

# Try to create a simple table with vector
schema = {
    "id": {"type": "varchar"},
    "content": {"type": "varchar"},
    "q_768_vec": {"type": "vector,768,float"}
}

try:
    table = db.create_table("test_table", schema)
    print("✅ Table created successfully!")
    print(f"Table: {table}")
except Exception as e:
    print(f"❌ Error creating table: {e}")
    print(f"Error type: {type(e)}")

    # Try alternative vector type syntax
    print("\nTrying alternative syntax...")
    schema2 = {
        "id": {"type": "varchar"},
        "content": {"type": "varchar"},
        "q_768_vec": {"type": "vector", "dimension": 768, "element_type": "float"}
    }

    try:
        table = db.create_table("test_table2", schema2)
        print("✅ Alternative syntax worked!")
    except Exception as e2:
        print(f"❌ Alternative syntax also failed: {e2}")
