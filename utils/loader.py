import json
import os
from threading import RLock
from typing import Any, Dict, List, Optional

import pandas as pd

try:
    from . import sheets_bridge
except ImportError:  # pragma: no cover - optional dependency
    sheets_bridge = None

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

GOOGLE_SHEETS_CREDS = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
GOOGLE_SHEETS_SPREADSHEET_ID = os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID")
GOOGLE_SHEETS_QUESTIONS_WS = os.environ.get("GOOGLE_SHEETS_QUESTIONS_WS", "questions")
GOOGLE_SHEETS_SCORES_WS = os.environ.get("GOOGLE_SHEETS_SCORES_WS", "scores")

_USE_SHEETS = bool(
    GOOGLE_SHEETS_CREDS and GOOGLE_SHEETS_SPREADSHEET_ID and sheets_bridge
)

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


def _read_sheet(worksheet: str) -> List[List[str]]:
    if not _USE_SHEETS:
        return []
    try:
        return sheets_bridge.read_sheet(worksheet)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Invalid GOOGLE_SHEETS_CREDENTIALS JSON") from exc


def _write_sheet(worksheet: str, columns: List[str], rows: List[List[str]]) -> None:
    if not _USE_SHEETS:
        return
    sheets_bridge.write_sheet(worksheet, columns, rows)


def _invalidate_questions_cache():
    global _QUESTIONS_CACHE
    _QUESTIONS_CACHE = None


def _invalidate_scores_cache():
    global _SCORES_CACHE
    _SCORES_CACHE = None


def _write_sheet(ws, df: pd.DataFrame, columns: List[str]) -> None:
    df_out = df.copy()
    for col in columns:
        if col not in df_out.columns:
            df_out[col] = ""
    df_out = df_out.reindex(columns=columns)
    df_out = df_out.fillna("")
    data = [columns] + df_out.values.tolist()
    ws.clear()
    ws.update(data)


def ensure_data_files():
    if _USE_SHEETS:
        for ws_name, columns, seed_df in [
            (GOOGLE_SHEETS_QUESTIONS_WS, _QUESTION_COLUMNS, _seed_questions_df()),
            (GOOGLE_SHEETS_SCORES_WS, _SCORE_COLUMNS, _empty_scores_df()),
        ]:
            values = _read_sheet(ws_name)
            if len(values) <= 1:
                rows = seed_df.reindex(columns=columns).fillna("").values.tolist()
                _write_sheet(ws_name, columns, rows)
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

    if _USE_SHEETS:
        raw_values = _read_sheet(GOOGLE_SHEETS_QUESTIONS_WS)
        if not raw_values:
            df = pd.DataFrame(columns=_QUESTION_COLUMNS)
        else:
            header = raw_values[0]
            rows = raw_values[1:]
            normalized = []
            for row in rows:
                record = {
                    header[idx]: row[idx] if idx < len(row) else ""
                    for idx in range(len(header))
                }
                normalized.append(record)
            df = pd.DataFrame(normalized)
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

    if _USE_SHEETS:
        rows = df_to_save.reindex(columns=_QUESTION_COLUMNS).fillna("").values.tolist()
        _write_sheet(GOOGLE_SHEETS_QUESTIONS_WS, _QUESTION_COLUMNS, rows)
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

    if _USE_SHEETS:
        raw_values = _read_sheet(GOOGLE_SHEETS_SCORES_WS)
        if not raw_values:
            df = pd.DataFrame(columns=_SCORE_COLUMNS)
        else:
            header = raw_values[0]
            rows = raw_values[1:]
            normalized = []
            for row in rows:
                record = {
                    header[idx]: row[idx] if idx < len(row) else ""
                    for idx in range(len(header))
                }
                normalized.append(record)
            df = pd.DataFrame(normalized)
    else:
        with _DATA_LOCK:
            df = pd.read_csv(SCORES_FILE)

    _SCORES_CACHE = df.copy()
    return df


# =============================================================================
# Save Scores
# =============================================================================
def save_scores(df: pd.DataFrame) -> None:
    ensure_data_files()
    df_to_save = df.copy()
    if _USE_SHEETS:
        rows = df_to_save.reindex(columns=_SCORE_COLUMNS).fillna("").values.tolist()
        _write_sheet(GOOGLE_SHEETS_SCORES_WS, _SCORE_COLUMNS, rows)
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
