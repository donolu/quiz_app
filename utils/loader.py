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
    records: List[Dict[str, Any]] = []
    for row in df.to_dict("records"):
        record = row.copy()
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
        record["allow_multiple"] = bool(record.get("allow_multiple"))
        if include_id:
            if record.get("id") is not None:
                record["id"] = int(record["id"])
        else:
            record.pop("id", None)
        records.append(record)
    return records


def _prepare_score_records(
    df: pd.DataFrame, include_id: bool = True
) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for row in df.to_dict("records"):
        record = row.copy()
        if not include_id:
            record.pop("id", None)
        if "score" in record:
            try:
                record["score"] = float(record["score"])
            except (TypeError, ValueError):
                record["score"] = 0.0
        if "total_questions" in record:
            try:
                record["total_questions"] = int(record["total_questions"])
            except (TypeError, ValueError):
                record["total_questions"] = 0
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
            # Scores table can remain empty; ensure table exists by touching it
            client.table(SUPABASE_SCORES_TABLE).select("name").limit(1).execute()
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

    # Convert JSON string in options → list
    if "options" in df.columns:
        df["options"] = df["options"].apply(
            lambda x: json.loads(x) if isinstance(x, str) and x.strip() else []
        )

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
            _supabase_delete_all(client, SUPABASE_QUESTIONS_TABLE, "id", -1)
            if records:
                client.table(SUPABASE_QUESTIONS_TABLE).insert(records).execute()
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
            records = _prepare_score_records(df, include_id=False)
            _supabase_delete_all(client, SUPABASE_SCORES_TABLE, "name", "__never__")
            if records:
                client.table(SUPABASE_SCORES_TABLE).insert(records).execute()
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
