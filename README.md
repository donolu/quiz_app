# Accounting Quiz Game (Streamlit)

This is a multipurpose accounting quiz app built with **Streamlit**.

## Features

- 🎮 Quiz page for students
- 🏆 Leaderboard
- 🔐 Admin dashboard with:
  - Add / delete questions via UI
  - Import question bank from Excel
  - Export questions as CSV
  - Support for modules/topics
  - Difficulty levels
  - Optional image URL per question
- ⏳ Optional quiz time limit
- 🎲 Randomised question and option order
- CSV-based storage (no external DB)

## Running Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Default admin password is `change_me` (set in `app.py`).
