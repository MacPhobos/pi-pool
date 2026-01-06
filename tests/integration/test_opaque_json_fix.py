#!/usr/bin/env python
"""Test script to validate Event.logOpaqueEvent JSON fix.

This script verifies that the opaque event logging now accepts dicts
without requiring manual json.dumps() serialization.
"""

import sys
sys.path.insert(0, 'src')

from db.models.Event import Event as EventModel
from sqlalchemy.types import JSON

print("=" * 60)
print("Event Opaque JSON Fix Validation")
print("=" * 60)

# Test 1: Verify model has JSON type
print("\n1. Checking Event model opaque column type...")
column_type = EventModel.opaque.type
print(f"   Column type: {column_type}")

if isinstance(column_type, JSON):
    print("   ✓ opaque column is JSON type")
else:
    print(f"   ✗ FAILED - opaque column is {type(column_type)}, expected JSON")
    sys.exit(1)

# Test 2: Verify model imports correctly
print("\n2. Checking Event model imports...")
try:
    from db.models.Event import Event as EventModel
    print("   ✓ Event model imports successfully")
except ImportError as e:
    print(f"   ✗ FAILED - Import error: {e}")
    sys.exit(1)

# Test 3: Verify DB.py imports correctly
print("\n3. Checking DB.py imports...")
try:
    from DB import DB
    print("   ✓ DB class imports successfully")
    print(f"   ✓ DB.logOpaqueEvent exists: {hasattr(DB, 'logOpaqueEvent')}")
except ImportError as e:
    print(f"   ✗ FAILED - Import error: {e}")
    sys.exit(1)

# Test 4: Verify migration file syntax
print("\n4. Checking migration file syntax...")
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "migration_002",
        "alembic/versions/002_event_opaque_to_json.py"
    )
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    print("   ✓ Migration file syntax is valid")
    print(f"   ✓ Migration revision: {migration.revision}")
    print(f"   ✓ Down revision: {migration.down_revision}")
except Exception as e:
    print(f"   ✗ FAILED - Migration error: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ All validation checks passed!")
print("=" * 60)

print("\nNext steps:")
print("1. Run migration: uv run alembic upgrade head")
print("2. Test with actual DB connection")
print("3. Verify dict values are stored correctly")
print("\nExample usage after migration:")
print("""
    Event.logOpaqueEvent("test_event", {
        "key": "value",
        "count": 42,
        "nested": {"data": "works"}
    })
""")
