#!/usr/bin/env python3
"""
Test that the leaderboard persists scores correctly.
"""

import os
import pandas as pd
from datetime import datetime

# Set environment variables
os.environ["SUPABASE_URL"] = "https://rlsfvjfjkuylahnhzxrg.supabase.co"
os.environ["SUPABASE_ANON_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJsc2Z2amZqa3V5bGFobmh6eHJnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzM5MjYwNCwiZXhwIjoyMDc4OTY4NjA0fQ.jlqG2MMgbxIb8N1DOsH51ZvS63FLuvANU1_RvJSMXj0"
os.environ["SUPABASE_SCORES_TABLE"] = "scores"

from utils.loader import load_scores, save_scores


def test_persistence():
    """Test that scores are appended, not replaced."""
    print("=" * 80)
    print("TESTING LEADERBOARD PERSISTENCE")
    print("=" * 80)
    print()

    # Load existing scores
    existing_scores = load_scores()
    print(f"📊 Current scores in database: {len(existing_scores)}")
    print()

    # Add a test score
    print("Adding test score 1...")
    new_score_1 = pd.DataFrame([{
        "name": "Test User 1",
        "student_id": "TEST001",
        "module": "Budgeting",
        "score": 8.5,
        "total_questions": 10,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "time_limit_minutes": 15
    }])

    combined = pd.concat([existing_scores, new_score_1], ignore_index=True)
    save_scores(combined)
    print("✅ Saved score 1")

    # Load again to verify
    after_first = load_scores()
    print(f"📊 Scores after first save: {len(after_first)}")
    assert len(after_first) == len(existing_scores) + 1, "First score not saved!"
    print()

    # Add another score
    print("Adding test score 2...")
    new_score_2 = pd.DataFrame([{
        "name": "Test User 2",
        "student_id": "TEST002",
        "module": "Budgeting",
        "score": 9.0,
        "total_questions": 10,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "time_limit_minutes": 15
    }])

    combined = pd.concat([after_first, new_score_2], ignore_index=True)
    save_scores(combined)
    print("✅ Saved score 2")

    # Load final state
    final_scores = load_scores()
    print(f"📊 Scores after second save: {len(final_scores)}")
    assert len(final_scores) == len(existing_scores) + 2, "Second score not saved!"

    print()
    print("=" * 80)
    print("✅ PERSISTENCE TEST PASSED!")
    print("=" * 80)
    print()
    print("Leaderboard now contains:")
    print(final_scores[["name", "score", "module", "timestamp"]].tail(10))


if __name__ == "__main__":
    try:
        test_persistence()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
