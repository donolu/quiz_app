#!/usr/bin/env python3
"""
Script to clean up any invalid scores in the database.
Run this if you're getting JSON serialization errors.
"""

import math

from utils.loader import load_scores, save_scores


def cleanup_scores():
    """Clean up invalid float values in scores database."""
    print("=" * 80)
    print("CLEANING UP SCORES DATABASE")
    print("=" * 80)
    print()

    # Load scores
    scores_df = load_scores()
    print(f"📊 Loaded {len(scores_df)} score records")

    if scores_df.empty:
        print("✅ No scores to clean up")
        return

    # Check for invalid values
    issues_found = 0

    # Check score column
    if "score" in scores_df.columns:
        invalid_scores = scores_df["score"].apply(
            lambda x: math.isnan(x) if isinstance(x, float) else False
        )
        if invalid_scores.any():
            count = invalid_scores.sum()
            print(f"⚠️  Found {count} NaN values in score column")
            scores_df.loc[invalid_scores, "score"] = 0.0
            issues_found += count

        inf_scores = scores_df["score"].apply(
            lambda x: math.isinf(x) if isinstance(x, float) else False
        )
        if inf_scores.any():
            count = inf_scores.sum()
            print(f"⚠️  Found {count} infinity values in score column")
            scores_df.loc[inf_scores, "score"] = 0.0
            issues_found += count

    # Check total_questions column
    if "total_questions" in scores_df.columns:
        invalid_total = scores_df["total_questions"].isna()
        if invalid_total.any():
            count = invalid_total.sum()
            print(f"⚠️  Found {count} NaN values in total_questions column")
            scores_df.loc[invalid_total, "total_questions"] = 1
            issues_found += count

    # Check time_limit_minutes column
    if "time_limit_minutes" in scores_df.columns:
        invalid_time = scores_df["time_limit_minutes"].isna()
        if invalid_time.any():
            count = invalid_time.sum()
            print(f"⚠️  Found {count} NaN values in time_limit_minutes column")
            scores_df.loc[invalid_time, "time_limit_minutes"] = 0
            issues_found += count

    if issues_found > 0:
        print()
        print(f"🔧 Fixed {issues_found} invalid values")
        print("💾 Saving cleaned scores...")
        save_scores(scores_df)
        print("✅ Scores cleaned and saved successfully!")
    else:
        print("✅ No invalid values found - database is clean!")

    print()
    print("=" * 80)
    print("CLEANUP COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    try:
        cleanup_scores()
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
