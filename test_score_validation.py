#!/usr/bin/env python3
"""
Test script to verify score validation handles edge cases correctly.
"""

import math
import pandas as pd
from utils.quiz_engine import calculate_score


def test_valid_scores():
    """Test that normal scores work correctly."""
    print("=" * 80)
    print("TEST 1: Valid Scores")
    print("=" * 80)

    quiz_df = pd.DataFrame([
        {
            "id": 1,
            "question": "What is 2+2?",
            "options": ["2", "3", "4", "5"],
            "answer": "4",
            "correct_answers": ["4"],
            "allow_multiple": False
        }
    ])

    answers = {1: "4"}
    score, details = calculate_score(quiz_df, answers)

    print(f"Score: {score}")
    print(f"Is valid float: {not math.isnan(score) and not math.isinf(score)}")
    assert score == 1.0, f"Expected score 1.0, got {score}"
    assert not math.isnan(score), "Score should not be NaN"
    assert not math.isinf(score), "Score should not be infinite"
    print("✅ Valid scores test passed\n")


def test_empty_correct_answers():
    """Test handling of questions with empty correct_answers."""
    print("=" * 80)
    print("TEST 2: Empty Correct Answers")
    print("=" * 80)

    quiz_df = pd.DataFrame([
        {
            "id": 1,
            "question": "Test question",
            "options": ["A", "B"],
            "answer": "",
            "correct_answers": [],
            "allow_multiple": True
        }
    ])

    answers = {1: ["A"]}
    score, details = calculate_score(quiz_df, answers)

    print(f"Score: {score}")
    print(f"Is valid float: {not math.isnan(score) and not math.isinf(score)}")
    assert score == 0.0, f"Expected score 0.0, got {score}"
    assert not math.isnan(score), "Score should not be NaN"
    assert not math.isinf(score), "Score should not be infinite"
    print("✅ Empty correct answers test passed\n")


def test_multiple_choice_partial_credit():
    """Test partial credit calculation for multiple choice."""
    print("=" * 80)
    print("TEST 3: Multiple Choice Partial Credit")
    print("=" * 80)

    quiz_df = pd.DataFrame([
        {
            "id": 1,
            "question": "Select all even numbers",
            "options": ["1", "2", "3", "4"],
            "answer": "2",
            "correct_answers": ["2", "4"],
            "allow_multiple": True
        }
    ])

    # User selects only 1 out of 2 correct answers
    answers = {1: ["2"]}
    score, details = calculate_score(quiz_df, answers)

    print(f"Score: {score}")
    print(f"Is valid float: {not math.isnan(score) and not math.isinf(score)}")
    assert 0.0 <= score <= 1.0, f"Score {score} should be between 0 and 1"
    assert not math.isnan(score), "Score should not be NaN"
    assert not math.isinf(score), "Score should not be infinite"
    print("✅ Multiple choice partial credit test passed\n")


def test_score_record_preparation():
    """Test that score records can be safely converted to JSON."""
    print("=" * 80)
    print("TEST 4: Score Record JSON Serialization")
    print("=" * 80)

    import json
    from utils.loader import _prepare_score_records

    # Create a score record with potential edge cases
    scores_df = pd.DataFrame([
        {
            "name": "Test User",
            "student_id": "123",
            "module": "Basics",
            "score": 5.5,
            "total_questions": 10,
            "timestamp": "2025-01-01 12:00:00",
            "time_limit_minutes": 15
        }
    ])

    records = _prepare_score_records(scores_df, include_id=False)

    # Try to serialize to JSON (this is what Supabase does)
    try:
        json_str = json.dumps(records)
        print(f"✅ Successfully serialized to JSON:")
        print(json.loads(json_str))
        print("✅ Score record JSON serialization test passed\n")
    except (ValueError, TypeError) as e:
        print(f"❌ Failed to serialize: {e}")
        raise


def test_invalid_float_handling():
    """Test handling of invalid float values (inf, nan)."""
    print("=" * 80)
    print("TEST 5: Invalid Float Handling")
    print("=" * 80)

    import json
    from utils.loader import _prepare_score_records

    # Create records with invalid float values
    scores_df = pd.DataFrame([
        {
            "name": "Test User",
            "student_id": "123",
            "module": "Basics",
            "score": float('inf'),  # Invalid: infinity
            "total_questions": 10,
            "timestamp": "2025-01-01 12:00:00",
            "time_limit_minutes": 15
        }
    ])

    records = _prepare_score_records(scores_df, include_id=False)

    # Check that inf was converted to 0.0
    assert records[0]["score"] == 0.0, "Infinity should be converted to 0.0"

    # Verify it can be serialized to JSON
    try:
        json_str = json.dumps(records)
        print(f"✅ Successfully converted inf to 0.0 and serialized:")
        print(json.loads(json_str))
        print("✅ Invalid float handling test passed\n")
    except (ValueError, TypeError) as e:
        print(f"❌ Failed to serialize: {e}")
        raise


if __name__ == "__main__":
    try:
        test_valid_scores()
        test_empty_correct_answers()
        test_multiple_choice_partial_credit()
        test_score_record_preparation()
        test_invalid_float_handling()

        print("=" * 80)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 80)
        print("\nThe score validation is working correctly.")
        print("You can now safely submit quizzes without JSON serialization errors.")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
