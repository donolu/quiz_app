import random
from typing import Any, Dict, List, Tuple

import pandas as pd


# =============================================================================
# Randomise Quiz Questions
# =============================================================================
def get_randomised_quiz(
    questions_df: pd.DataFrame,
    module: str,
    num_questions: int,
) -> pd.DataFrame:
    """
    Selects a random subset of questions filtered by module, and randomises
    the option order for each question.
    """

    # Filter by module
    df = questions_df.copy()
    if module in df["module"].values:
        df = df[df["module"] == module]

    # Safety: if empty, return empty
    if df.empty:
        return df

    # Random sample of questions
    if num_questions < len(df):
        df = df.sample(n=num_questions, random_state=None)
    else:
        df = df.sample(frac=1, random_state=None)

    # Randomise options per question
    df = df.copy()
    df["options"] = df["options"].apply(
        lambda opts: random.sample(opts, len(opts)) if isinstance(opts, list) else opts
    )

    return df.reset_index(drop=True)


# =============================================================================
# Score Calculation
# =============================================================================
def calculate_score(
    quiz_questions: pd.DataFrame,
    answers: Dict[int, Any],
) -> Tuple[float, List[Dict]]:
    """
    Returns:
        score (float)
        detailed_results (List[Dict]) → for feedback panel
    """

    score = 0.0
    detailed_results: List[Dict] = []

    for _, row in quiz_questions.iterrows():
        qid = row["id"]
        correct_answers = row.get("correct_answers") or []
        if not correct_answers and isinstance(row.get("answer"), str):
            correct_answers = [row["answer"]]
        allow_multiple = bool(row.get("allow_multiple")) or len(correct_answers) > 1
        max_points = 1.0

        user_response = answers.get(qid)
        awarded = 0.0
        is_correct = False

        if allow_multiple:
            user_selection = (
                user_response if isinstance(user_response, list) else []
            )
            correct_set = set(correct_answers)
            user_set = set(user_selection)
            true_pos = len(user_set & correct_set)
            false_pos = len(user_set - correct_set)
            if true_pos == len(correct_set) and false_pos == 0:
                awarded = max_points
                is_correct = True
            else:
                awarded = max((true_pos - false_pos) / max(len(correct_set), 1), 0)
                awarded = round(awarded, 4)
        else:
            user_value = user_response if isinstance(user_response, str) else ""
            is_correct = user_value == (correct_answers[0] if correct_answers else "")
            awarded = max_points if is_correct else 0.0

        score += awarded

        detailed_results.append(
            {
                "id": qid,
                "question": row["question"],
                "correct_answers": correct_answers,
                "user_answer": user_response,
                "is_correct": is_correct,
                "awarded": awarded,
                "max_points": max_points,
                "allow_multiple": allow_multiple,
            }
        )

    return score, detailed_results
