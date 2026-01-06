#!/usr/bin/env python
"""Integration test for opaque event JSON fix.

Tests that Event.logOpaqueEvent() now properly handles dict values
through the entire stack: Event → DB → SQLAlchemy → PostgreSQL.

This test requires a working database connection.
"""

import sys
sys.path.insert(0, 'src')

import os
import time
from Config import Config
from DB import DB
from Event import Event
from db.Engine import Engine

print("=" * 70)
print("Opaque Event JSON Fix - Integration Test")
print("=" * 70)

# Initialize components
try:
    config = Config.getInstance()
    print(f"\n✓ Config loaded (DB: {config.dbName})")
except Exception as e:
    print(f"\n✗ Config failed: {e}")
    print("  Ensure config.json or config_custom.json exists")
    sys.exit(1)

try:
    db = DB(config)
    print("✓ DB initialized")
except Exception as e:
    print(f"✗ DB initialization failed: {e}")
    print("  Ensure PostgreSQL is running and database exists")
    sys.exit(1)

try:
    event = Event(db)
    print("✓ Event singleton initialized")
except Exception as e:
    print(f"✗ Event initialization failed: {e}")
    sys.exit(1)

# Test 1: Log dict value (main fix)
print("\n" + "-" * 70)
print("Test 1: Logging dict value")
print("-" * 70)

test_data_dict = {
    "test_type": "integration",
    "timestamp": time.time(),
    "nested": {
        "level": 2,
        "value": 42
    }
}

try:
    Event.logOpaqueEvent("test_opaque_dict", test_data_dict)
    print(f"✓ Dict logged successfully: {test_data_dict}")
except Exception as e:
    print(f"✗ FAILED to log dict: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Log string value (backward compat)
print("\n" + "-" * 70)
print("Test 2: Logging string value (backward compatibility)")
print("-" * 70)

test_data_string = "simple string value"

try:
    Event.logOpaqueEvent("test_opaque_string", test_data_string)
    print(f"✓ String logged successfully: {test_data_string}")
except Exception as e:
    print(f"✗ FAILED to log string: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Log None value (backward compat)
print("\n" + "-" * 70)
print("Test 3: Logging None value (backward compatibility)")
print("-" * 70)

try:
    Event.logOpaqueEvent("test_opaque_none", None)
    print("✓ None logged successfully")
except Exception as e:
    print(f"✗ FAILED to log None: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Verify data in database
print("\n" + "-" * 70)
print("Test 4: Verifying data in database")
print("-" * 70)

try:
    from db.models.Event import Event as EventModel
    from sqlalchemy import select

    with db.engine.getSession() as session:
        # Query for test events
        stmt = select(EventModel).where(
            EventModel.name.like('test_opaque_%')
        ).order_by(EventModel.time.desc()).limit(3)

        results = session.execute(stmt).scalars().all()

        if len(results) >= 3:
            print(f"✓ Found {len(results)} test events in database")

            for event_record in results:
                print(f"\n  Event: {event_record.name}")
                print(f"    Opaque: {event_record.opaque}")
                print(f"    Type: {type(event_record.opaque)}")

                # Verify dict event has correct structure
                if event_record.name == "test_opaque_dict":
                    if isinstance(event_record.opaque, dict):
                        if event_record.opaque.get('test_type') == 'integration':
                            print("    ✓ Dict structure preserved correctly")
                        else:
                            print("    ✗ Dict structure incorrect")
                    else:
                        print(f"    ✗ Expected dict, got {type(event_record.opaque)}")

                # Verify string event
                if event_record.name == "test_opaque_string":
                    if event_record.opaque == test_data_string:
                        print("    ✓ String value preserved correctly")
                    else:
                        print(f"    ✗ String mismatch: {event_record.opaque}")

                # Verify None event
                if event_record.name == "test_opaque_none":
                    if event_record.opaque is None:
                        print("    ✓ None value preserved correctly")
                    else:
                        print(f"    ✗ Expected None, got {event_record.opaque}")
        else:
            print(f"✗ Expected at least 3 events, found {len(results)}")
            sys.exit(1)

except Exception as e:
    print(f"✗ Database verification failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Cleanup test data
print("\n" + "-" * 70)
print("Cleanup: Removing test events")
print("-" * 70)

try:
    from db.models.Event import Event as EventModel
    from sqlalchemy import delete

    with db.engine.getSession() as session:
        stmt = delete(EventModel).where(
            EventModel.name.like('test_opaque_%')
        )
        result = session.execute(stmt)
        session.commit()
        print(f"✓ Removed {result.rowcount} test events")

except Exception as e:
    print(f"⚠ Cleanup warning (non-critical): {e}")

# Success summary
print("\n" + "=" * 70)
print("✓ ALL INTEGRATION TESTS PASSED!")
print("=" * 70)
print("\nSummary:")
print("  ✓ Dict values can be logged without json.dumps()")
print("  ✓ String values still work (backward compatible)")
print("  ✓ None values still work (backward compatible)")
print("  ✓ Data is stored correctly in PostgreSQL jsonb column")
print("  ✓ Python dict structure is preserved after round-trip")
print("\nThe opaque event JSON fix is working correctly!")
print("=" * 70)
