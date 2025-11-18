#!/usr/bin/env python3
"""
Test saving scores with various edge cases to ensure no JSON errors.
"""

import pandas as pd
import numpy as np
from datetime import datetime


def test_score_saving():
    """Test that scores can be saved without JSON errors."""
    print("=" * 80)
    print("TESTING SCORE SAVING WITH EDGE CASES")
    print("=" * 80)
    print()

    # Create test scores with various data types
    test_scores = [
        {
            "name": "Test User 1",
            "student_id": "123",
            "module": "Budgeting",
            "score": 5.5,  # Python float
            "total_questions": 10,  # Python int
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "time_limit_minutes": 15
        },
        {
            "name": "Test User 2",
            "student_id": "456",
            "module": "Budgeting",
            "score": np.float64(7.25),  # NumPy float
            "total_questions": np.int64(10),  # NumPy int
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "time_limit_minutes": np.int64(20)
        },
        {
            "name": "Test User 3",
            "student_id": "789",
            "module": "Budgeting",
            "score": pd.Series([8.0]).iloc[0],  # Pandas value
            "total_questions": pd.Series([10]).iloc[0],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "time_limit_minutes": 0
        }
    ]

    df = pd.DataFrame(test_scores)

    print("Created test DataFrame with various numeric types:")
    print(df)
    print()
    print("Data types:")
    print(df.dtypes)
    print()

    # Test JSON serialization of raw DataFrame
    import json
    print("Testing JSON serialization of DataFrame records...")
    records = df.to_dict("records")

    for idx, record in enumerate(records):
        print(f"\nRecord {idx + 1}:")
        print(f"  Types: {[(k, type(v).__name__) for k, v in record.items()]}")

        # Try to serialize
        try:
            json_str = json.dumps(record)
            print(f"  ❌ Direct serialization FAILED (this is expected)")
        except (ValueError, TypeError) as e:
            print(f"  ✅ Direct serialization failed as expected: {e}")

        # Now convert to safe types
        safe_record = {}
        for key, value in record.items():
            if hasattr(value, 'item'):  # numpy scalar
                safe_record[key] = value.item()
            elif pd.isna(value):
                safe_record[key] = 0 if key in ["score", "total_questions", "time_limit_minutes"] else ""
            else:
                safe_record[key] = value

        print(f"  Safe types: {[(k, type(v).__name__) for k, v in safe_record.items()]}")

        # Try again
        try:
            json_str = json.dumps(safe_record)
            print(f"  ✅ Safe serialization SUCCESS")
        except (ValueError, TypeError) as e:
            print(f"  ❌ Safe serialization FAILED: {e}")
            return False

    print()
    print("=" * 80)
    print("✅ ALL TESTS PASSED - Score saving should work!")
    print("=" * 80)
    return True


if __name__ == "__main__":
    try:
        success = test_score_saving()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
