import json
import os
from threading import RLock
from typing import Any, Dict, List, Optional

import pandas as pd

try:
    from supabase import Client, create_client
except ImportError:  # pragma: no cover - optional dependency
    Client = None
    create_client = None

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

QUESTIONS_FILE = os.path.join(DATA_DIR, "questions.csv")
SCORES_FILE = os.path.join(DATA_DIR, "scores.csv")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

_CONFIG_DEFAULTS: Dict[str, Any] = {
    "show_explanations_for_correct": False,
    "module_time_limits": {},
    "module_availability": {},
}

_QUESTION_COLUMNS = [
    "id",
    "module",
    "question",
    "options",
    "answer",
    "correct_answers",
    "allow_multiple",
    "difficulty",
    "image",
    "explanation",
]
_SCORE_COLUMNS = [
    "name",
    "student_id",
    "module",
    "score",
    "total_questions",
    "timestamp",
    "time_limit_minutes",
]

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")
SUPABASE_QUESTIONS_TABLE = os.environ.get("SUPABASE_QUESTIONS_TABLE", "questions")
SUPABASE_SCORES_TABLE = os.environ.get("SUPABASE_SCORES_TABLE", "scores")

_USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_KEY and create_client)
_SUPABASE_CLIENT: Optional[Client] = None

_DATA_LOCK = RLock()
_QUESTIONS_CACHE: Optional[pd.DataFrame] = None
_SCORES_CACHE: Optional[pd.DataFrame] = None
_SUPABASE_INITIALISED = False


def _normalise_options(raw: Any) -> List[str]:
    if isinstance(raw, list):
        return [str(opt).strip() for opt in raw if str(opt).strip()]
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return []
        if text.startswith("["):
            try:
                data = json.loads(text)
                if isinstance(data, list):
                    return [str(opt).strip() for opt in data if str(opt).strip()]
            except json.JSONDecodeError:
                pass
        if "|" in text:
            return [part.strip() for part in text.split("|") if part.strip()]
        return [text]
    return []


# =============================================================================
# Ensure the data directory and CSV files exist
# =============================================================================
def _seed_questions_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "id": 1,
                "module": "Basics",
                "question": "What is the accounting equation?",
                "options": json.dumps(
                    [
                        "Assets = Liabilities + Equity",
                        "Assets = Revenue - Expenses",
                        "Equity = Assets + Liabilities",
                        "Liabilities = Assets + Equity",
                    ]
                ),
                "answer": "Assets = Liabilities + Equity",
                "correct_answers": json.dumps(["Assets = Liabilities + Equity"]),
                "allow_multiple": False,
                "difficulty": "Easy",
                "image": "",
                "explanation": "The accounting equation represents the relationship between assets, liabilities, and equity.",
            },
            {
                "id": 2,
                "module": "Basics",
                "question": "Which of these is an expense?",
                "options": json.dumps(["Sales", "Wages", "Loan", "Capital"]),
                "answer": "Wages",
                "correct_answers": json.dumps(["Wages"]),
                "allow_multiple": False,
                "difficulty": "Easy",
                "image": "",
                "explanation": "Wages are an expense because they represent a cost incurred in running the business.",
            },
            {
                "id": 3,
                "module": "Financial Statements",
                "question": "Which statement shows financial performance over a period?",
                "options": json.dumps(
                    [
                        "Balance Sheet",
                        "Income Statement",
                        "Cash Flow Statement",
                        "Trial Balance",
                    ]
                ),
                "answer": "Income Statement",
                "correct_answers": json.dumps(["Income Statement"]),
                "allow_multiple": False,
                "difficulty": "Easy",
                "image": "",
                "explanation": "The income statement shows revenue, expenses, and profit or loss for a period.",
            },
        ]
    )


def _empty_scores_df() -> pd.DataFrame:
    return pd.DataFrame(columns=_SCORE_COLUMNS)


def _get_supabase_client() -> Optional[Client]:
    global _SUPABASE_CLIENT
    if not _USE_SUPABASE:
        return None
    if _SUPABASE_CLIENT is None:
        _SUPABASE_CLIENT = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _SUPABASE_CLIENT


def _prepare_question_records(
    df: pd.DataFrame, include_id: bool = True
) -> List[Dict[str, Any]]:
    import math

    records: List[Dict[str, Any]] = []
    for row in df.to_dict("records"):
        record = {}

        # Handle each field with NaN checking
        for key, value in row.items():
            # Convert numpy types to Python natives and handle NaN
            if hasattr(value, 'item'):  # numpy scalar
                value = value.item()

            # Handle NaN values
            if pd.isna(value) or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
                # Set appropriate defaults based on field
                if key in ["image", "explanation", "module", "question", "answer", "difficulty"]:
                    record[key] = ""
                elif key in ["id"]:
                    record[key] = None
                elif key == "allow_multiple":
                    record[key] = False
                else:
                    record[key] = value if value is not None else ""
            else:
                record[key] = value

        # Parse JSON fields
        if isinstance(record.get("options"), str):
            try:
                record["options"] = json.loads(record["options"])
            except json.JSONDecodeError:
                record["options"] = []
        if isinstance(record.get("correct_answers"), str):
            try:
                record["correct_answers"] = json.loads(record["correct_answers"])
            except json.JSONDecodeError:
                record["correct_answers"] = []

        # Ensure boolean
        record["allow_multiple"] = bool(record.get("allow_multiple"))

        # Handle ID field
        if include_id:
            if record.get("id") is not None:
                record["id"] = int(record["id"])
        else:
            record.pop("id", None)

        # Final JSON serialization test with more aggressive cleaning
        try:
            json.dumps(record)
            records.append(record)
        except (ValueError, TypeError) as e:
            # Try one more time with aggressive cleaning
            print(f"⚠️ Warning: Question record failed serialization, attempting to fix: {e}")
            cleaned_record = {}
            for key, value in record.items():
                try:
                    # Test if this specific value is serializable
                    json.dumps(value)
                    cleaned_record[key] = value
                except:
                    # Replace problematic value with safe default
                    if key in ["id"]:
                        cleaned_record[key] = None
                    elif key == "allow_multiple":
                        cleaned_record[key] = False
                    elif key in ["options", "correct_answers"]:
                        cleaned_record[key] = []
                    else:
                        cleaned_record[key] = ""

            # Try again with cleaned record
            try:
                json.dumps(cleaned_record)
                records.append(cleaned_record)
                print(f"✅ Successfully recovered question record after cleaning")
            except:
                print(f"❌ Unable to recover question record, skipping")
                print(f"Problematic record: {record}")
                continue

    return records


def _prepare_score_records(
    df: pd.DataFrame, include_id: bool = True
) -> List[Dict[str, Any]]:
    import json
    import math

    records: List[Dict[str, Any]] = []

    # Define expected fields - filter out any Supabase auto-generated fields
    expected_fields = {
        "id",
        "name",
        "student_id",
        "module",
        "score",
        "total_questions",
        "timestamp",
        "time_limit_minutes",
    }

    for idx, row in enumerate(df.to_dict("records")):
        record = row.copy()

        # Remove Supabase auto-generated fields
        for key in list(record.keys()):
            if key not in expected_fields:
                record.pop(key, None)

        if not include_id:
            record.pop("id", None)

        # Validate and clean all fields
        for key, value in list(record.items()):
            if pd.isna(value):
                # Replace NaN with appropriate default
                if key == "score":
                    record[key] = 0.0
                elif key in ["total_questions", "time_limit_minutes"]:
                    record[key] = 0
                elif key == "timestamp":
                    # Provide current timestamp if missing
                    from datetime import datetime

                    record[key] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                else:
                    record[key] = ""
            elif isinstance(value, float):
                # Check for invalid float values
                if math.isinf(value) or math.isnan(value):
                    record[key] = 0.0
                else:
                    record[key] = float(value)
            elif key == "timestamp" and (not value or str(value).strip() == ""):
                # Fix empty timestamp
                from datetime import datetime

                record[key] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Specific field validation
        if "score" in record:
            try:
                score_val = float(record["score"])
                if math.isinf(score_val) or math.isnan(score_val):
                    record["score"] = 0.0
                else:
                    record["score"] = round(score_val, 4)
            except (TypeError, ValueError):
                record["score"] = 0.0

        if "total_questions" in record:
            try:
                record["total_questions"] = int(record["total_questions"])
            except (TypeError, ValueError):
                record["total_questions"] = 0

        if "time_limit_minutes" in record:
            try:
                time_val = record["time_limit_minutes"]
                if pd.isna(time_val):
                    record["time_limit_minutes"] = 0
                else:
                    record["time_limit_minutes"] = int(time_val)
            except (TypeError, ValueError):
                record["time_limit_minutes"] = 0

        # Final JSON validation - try to serialize
        try:
            json.dumps(record)
        except (ValueError, TypeError) as e:
            # If serialization fails, log and fix the problematic record
            print(f"⚠️ Warning: Record {idx} has invalid JSON values: {e}")
            print(f"Record: {record}")
            # Convert all numeric fields to safe values
            for key, value in list(record.items()):
                if isinstance(value, (int, float)):
                    try:
                        json.dumps(value)
                    except (ValueError, TypeError):
                        record[key] = 0 if isinstance(value, int) else 0.0

        records.append(record)
    return records


def _supabase_delete_all(client: Client, table: str, column: str, sentinel) -> None:
    client.table(table).delete().neq(column, sentinel).execute()


def _invalidate_questions_cache():
    global _QUESTIONS_CACHE
    _QUESTIONS_CACHE = None


def _invalidate_scores_cache():
    global _SCORES_CACHE
    _SCORES_CACHE = None


def ensure_data_files():
    if _USE_SUPABASE:
        global _SUPABASE_INITIALISED
        if _SUPABASE_INITIALISED:
            return
        client = _get_supabase_client()
        if client:
            resp = (
                client.table(SUPABASE_QUESTIONS_TABLE).select("id").limit(1).execute()
            )
            if not resp.data:
                seed_records = _prepare_question_records(
                    _seed_questions_df(), include_id=False
                )
                if seed_records:
                    client.table(SUPABASE_QUESTIONS_TABLE).insert(
                        seed_records
                    ).execute()
            client.table(SUPABASE_SCORES_TABLE).select("name").limit(1).execute()
        _SUPABASE_INITIALISED = True
        return

    with _DATA_LOCK:
        os.makedirs(DATA_DIR, exist_ok=True)

        if not os.path.exists(QUESTIONS_FILE):
            _seed_questions_df().to_csv(QUESTIONS_FILE, index=False)

        if not os.path.exists(SCORES_FILE):
            _empty_scores_df().to_csv(SCORES_FILE, index=False)

        if not os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(_CONFIG_DEFAULTS, f, indent=2)


# =============================================================================
# Load Questions
# =============================================================================
def load_questions() -> pd.DataFrame:
    ensure_data_files()

    global _QUESTIONS_CACHE
    if _QUESTIONS_CACHE is not None:
        return _QUESTIONS_CACHE.copy()

    if _USE_SUPABASE:
        client = _get_supabase_client()
        resp = client.table(SUPABASE_QUESTIONS_TABLE).select("*").execute()
        df = pd.DataFrame(resp.data or [])
    else:
        with _DATA_LOCK:
            df = pd.read_csv(QUESTIONS_FILE)

    if df.empty:
        return pd.DataFrame(columns=_QUESTION_COLUMNS)

    option_cols = [c for c in df.columns if c.lower().startswith("option")]
    if "options" in df.columns:
        df["options"] = df["options"].apply(_normalise_options)
    elif option_cols:

        def _collect_options(row):
            opts = []
            for col in sorted(
                option_cols, key=lambda x: int("".join(filter(str.isdigit, x)) or 0)
            ):
                val = row.get(col)
                if isinstance(val, str) and val.strip():
                    opts.append(val.strip())
            return opts

        df["options"] = df.apply(_collect_options, axis=1)
    else:
        df["options"] = [[] for _ in range(len(df))]

    # Ensure explanation column exists
    if "explanation" not in df.columns:
        df["explanation"] = ""

    if "allow_multiple" not in df.columns:
        df["allow_multiple"] = False

    if "correct_answers" not in df.columns:
        df["correct_answers"] = ""

    def _parse_answers(raw: Any) -> List[str]:
        if isinstance(raw, list):
            return [str(a).strip() for a in raw if str(a).strip()]
        if isinstance(raw, str) and raw.strip():
            text = raw.strip()
            if text.startswith("["):
                try:
                    data = json.loads(text)
                    if isinstance(data, list):
                        return [str(a).strip() for a in data if str(a).strip()]
                except json.JSONDecodeError:
                    pass
            if "|" in text:
                return [part.strip() for part in text.split("|") if part.strip()]
            return [text]
        return []

    df["correct_answers"] = df["correct_answers"].apply(_parse_answers)
    if "answer" in df.columns:
        df["answer"] = df["answer"].fillna("")
        df["correct_answers"] = df.apply(
            lambda row: row["correct_answers"]
            if row["correct_answers"]
            else ([row["answer"]] if str(row["answer"]).strip() else []),
            axis=1,
        )

    if "allow_multiple" not in df.columns:
        df["allow_multiple"] = False
    df["allow_multiple"] = df.apply(
        lambda row: (
            str(row.get("allow_multiple")).lower() in ("true", "1", "yes")
            if isinstance(row.get("allow_multiple"), str)
            else bool(row.get("allow_multiple"))
        )
        or len(row["correct_answers"]) > 1,
        axis=1,
    )

    _QUESTIONS_CACHE = df.copy()
    return df


# =============================================================================
# Save Questions
# =============================================================================
def save_questions(df: pd.DataFrame) -> None:
    ensure_data_files()
    df_to_save = df.copy()

    # Convert options list → JSON string
    if "options" in df_to_save.columns:
        df_to_save["options"] = df_to_save["options"].apply(json.dumps)

    if "correct_answers" in df_to_save.columns:
        df_to_save["correct_answers"] = df_to_save["correct_answers"].apply(
            lambda x: json.dumps(x if isinstance(x, list) else [])
        )

    if "allow_multiple" not in df_to_save.columns:
        df_to_save["allow_multiple"] = df_to_save["correct_answers"].apply(
            lambda ans: len(json.loads(ans)) > 1
        )

    if _USE_SUPABASE:
        client = _get_supabase_client()
        if client:
            records = _prepare_question_records(df, include_id=False)
            # IMPORTANT: Only delete if we have valid records to replace with
            # This prevents data loss if record preparation fails
            if records:
                _supabase_delete_all(client, SUPABASE_QUESTIONS_TABLE, "id", -1)
                client.table(SUPABASE_QUESTIONS_TABLE).insert(records).execute()
            else:
                print("⚠️ WARNING: No valid question records to save. Keeping existing data.")
        _invalidate_questions_cache()
        return

    with _DATA_LOCK:
        df_to_save.to_csv(QUESTIONS_FILE, index=False)
    _invalidate_questions_cache()


# =============================================================================
# Load Scores
# =============================================================================
def load_scores() -> pd.DataFrame:
    ensure_data_files()
    global _SCORES_CACHE
    if _SCORES_CACHE is not None:
        return _SCORES_CACHE.copy()

    if _USE_SUPABASE:
        client = _get_supabase_client()
        resp = client.table(SUPABASE_SCORES_TABLE).select("*").execute()
        df = pd.DataFrame(resp.data or [])
    else:
        with _DATA_LOCK:
            df = pd.read_csv(SCORES_FILE)

    if df.empty:
        df = pd.DataFrame(columns=_SCORE_COLUMNS)

    _SCORES_CACHE = df.copy()
    return df


# =============================================================================
# Save Scores
# =============================================================================
def save_scores(df: pd.DataFrame) -> None:
    ensure_data_files()
    df_to_save = df.copy()
    if _USE_SUPABASE:
        client = _get_supabase_client()
        if client:
            # Get existing scores count to determine if this is an append operation
            existing_resp = (
                client.table(SUPABASE_SCORES_TABLE).select("*", count="exact").execute()
            )
            existing_count = (
                existing_resp.count
                if hasattr(existing_resp, "count")
                else len(existing_resp.data or [])
            )

            records = _prepare_score_records(df, include_id=False)

            # Only delete all if we're replacing the entire dataset (used by admin clear function)
            # Otherwise, append new scores
            if len(records) < existing_count:
                # This is likely a clear operation - delete all first
                _supabase_delete_all(client, SUPABASE_SCORES_TABLE, "name", "__never__")
            elif existing_count == 0:
                # No existing scores, just insert
                pass
            else:
                # Appending new scores - only insert the new ones
                # Get the last N records (the new ones)
                new_record_count = len(records) - existing_count
                if new_record_count > 0:
                    records = records[-new_record_count:]

            if records:
                # Final safety check - convert all numpy/pandas types to Python natives
                import json
                from datetime import datetime

                safe_records = []
                for record in records:
                    safe_record = {}
                    for key, value in record.items():
                        # Convert numpy/pandas types to Python natives
                        if hasattr(value, "item"):  # numpy scalar
                            safe_record[key] = value.item()
                        elif pd.isna(value):
                            if key == "timestamp":
                                safe_record[key] = datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                )
                            elif key in [
                                "score",
                                "total_questions",
                                "time_limit_minutes",
                            ]:
                                safe_record[key] = 0
                            else:
                                safe_record[key] = ""
                        elif key == "timestamp" and (
                            not value or str(value).strip() == ""
                        ):
                            # Fix empty timestamp
                            safe_record[key] = datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                        else:
                            safe_record[key] = value

                    # Ensure timestamp is valid
                    if (
                        not safe_record.get("timestamp")
                        or str(safe_record.get("timestamp", "")).strip() == ""
                    ):
                        safe_record["timestamp"] = datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )

                    # Final JSON serialization test
                    try:
                        json.dumps(safe_record)
                        safe_records.append(safe_record)
                    except (ValueError, TypeError) as e:
                        print(f"⚠️ Skipping invalid record: {e}")
                        print(f"Record: {safe_record}")

                if safe_records:
                    client.table(SUPABASE_SCORES_TABLE).insert(safe_records).execute()
        _invalidate_scores_cache()
        return

    with _DATA_LOCK:
        df_to_save.to_csv(SCORES_FILE, index=False)
    _invalidate_scores_cache()


# =============================================================================
# Config helpers
# =============================================================================
def load_config() -> Dict[str, Any]:
    ensure_data_files()
    with _DATA_LOCK:
        if not os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(_CONFIG_DEFAULTS, f, indent=2)
            return _CONFIG_DEFAULTS.copy()
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
        if not isinstance(data, dict):
            data = {}

    merged = _CONFIG_DEFAULTS.copy()
    merged.update(data)
    return merged


def save_config(config: Dict[str, Any]) -> None:
    ensure_data_files()
    merged = _CONFIG_DEFAULTS.copy()
    merged.update(config or {})
    with _DATA_LOCK:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2)
