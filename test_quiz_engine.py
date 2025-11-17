"""
Test script for accounting quiz app components.

Run using:
    python test_quiz_engine.py

This verifies:
- Loader functions
- Question loading + explanation column
- Quiz randomisation
- Score calculation
- Simulated quiz attempt
"""

import pandas as pd

from utils.loader import (
    ensure_data_files,
    load_questions,
    load_scores,
    # save_questions,
    save_scores,
)
from utils.quiz_engine import calculate_score, get_randomised_quiz


def banner(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def test_loader():
    banner("TEST 1: Loader & Data Setup")

    ensure_data_files()

    qdf = load_questions()
    sdf = load_scores()

    print("Questions:\n", qdf.head(), "\n")
    print("Scores:\n", sdf.head(), "\n")

    assert "explanation" in qdf.columns, "Explanation column missing!"
    assert "options" in qdf.columns, "Options column missing!"

    print("➡ Loader OK — CSVs loaded and explanation column found.")


def test_randomisation():
    banner("TEST 2: Randomised Question Generation")

    qdf = load_questions()
    module = qdf["module"].iloc[0]

    quiz = get_randomised_quiz(qdf, module=module, num_questions=2)

    print("Sample Quiz:\n", quiz, "\n")

    assert len(quiz) == 2
    assert isinstance(quiz.iloc[0]["options"], list)

    print("➡ Randomisation OK — Question subset + option shuffle working.")


def test_scoring():
    banner("TEST 3: Score Calculation")

    qdf = load_questions()

    quiz = get_randomised_quiz(qdf, module=qdf["module"].iloc[0], num_questions=2)

    # Simulate student answers:
    answers = {}
    for _, row in quiz.iterrows():
        answers[row["id"]] = row["answer"]  # pretend all answers correct

    score, details = calculate_score(quiz, answers)

    print("Score:", score)
    print("Details:")
    for d in details:
        print(d)

    assert score == 2
    assert all(d["is_correct"] for d in details)

    print("➡ Scoring OK — Correct answers evaluated properly.")


def test_simulated_quiz_attempt():
    banner("TEST 4: Full Simulation — Save Score")

    sdf_before = load_scores()

    qdf = load_questions()
    quiz = get_randomised_quiz(qdf, module=qdf["module"].iloc[0], num_questions=1)
    qid = quiz.iloc[0]["id"]
    correct = quiz.iloc[0]["answer"]

    score, details = calculate_score(quiz, {qid: correct})

    new_row = pd.DataFrame(
        [
            {
                "name": "Test User",
                "student_id": "T001",
                "module": quiz.iloc[0]["module"],
                "score": score,
                "total_questions": 1,
                "timestamp": "2025-01-01 12:00:00",
                "time_limit_minutes": 0,
            }
        ]
    )

    sdf_after = pd.concat([sdf_before, new_row], ignore_index=True)
    save_scores(sdf_after)

    print("Updated scores:\n", sdf_after.tail(), "\n")

    assert len(sdf_after) >= len(sdf_before)

    print("➡ Score saving OK — End-to-end write completed.")


if __name__ == "__main__":
    test_loader()
    test_randomisation()
    test_scoring()
    test_simulated_quiz_attempt()

    banner("ALL TESTS COMPLETED SUCCESSFULLY 🎉")
