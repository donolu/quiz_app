# Repository Guidelines

## Project Structure & Module Organization
- `app.py` is the active Streamlit entry point that wires the quiz UI, leaderboard, and admin dashboard; `app_old.py` is historic reference only.
- Shared logic lives in `utils/loader.py` (CSV persistence) and `utils/quiz_engine.py` (randomisation and scoring). Keep new helpers modular inside `utils/` to ease testing.
- Persistent data resides in `data/questions.csv` and `data/scores.csv`; `ensure_data_files()` seeds missing files, so keep headers consistent when editing data manually.
- Assets such as question banks should be versioned as CSV under `data/` and never committed with personally identifiable information.

## Build, Test, and Development Commands
- `pip install -r requirements.txt` installs Streamlit, pandas, and runtime helpers; run it inside a virtualenv (`python -m venv venv && source venv/bin/activate`).
- `streamlit run app.py` launches the interactive quiz; use the sidebar to hop between quiz, leaderboard, and admin views while iterating locally.
- `python -m streamlit.cli --server.headless true app.py` is handy for CI smoke checks without opening a browser.

## Coding Style & Naming Conventions
- Follow the existing 4-space indentation, snake_case for functions (`load_scores`), and ALL_CAPS for config constants (`APP_TITLE`).
- Mirror the current docstring and section-divider style when adding modules; Streamlit callbacks should stay small and delegate work to `utils/` functions.
- Run `ruff` or `black` locally if you introduce them; keep imports grouped (`stdlib`, `third_party`, `local`).

## Testing Guidelines
- There is no dedicated `tests/` package yet; when adding logic under `utils/`, create lightweight unit tests (pytest recommended) and run `pytest -q` before submitting.
- For UI flows, manually verify via `streamlit run app.py`, exercising quiz creation, timer expiry, and admin CRUD against a throwaway CSV copy (`cp data/questions.csv data/questions.backup.csv`).

## Commit & Pull Request Guidelines
- Git history is not bundled with this checkout; adopt Conventional Commit messages (`feat: add timed quiz toggle`) so logs stay searchable when pushed.
- PRs should describe the user impact, list test evidence (`streamlit run app.py ✔️`, `pytest ✔️`), link any tracking issue, and include screenshots/GIFs for UI changes (quiz, leaderboard, admin tabs).
- Highlight how you handled CSV migrations (schema changes, seed data) and mention any secrets you rotated (e.g., `ADMIN_PASSWORD`).

## Data & Security Notes
- Default admin password in `app.py` is `change_me`; override via environment variable or secrets manager before deploying.
- Treat CSV exports as sensitive: strip student identifiers before sharing, and avoid committing real production data.
