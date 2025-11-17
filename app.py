import json
import os
from datetime import datetime

import pandas as pd
import streamlit as st

from utils.loader import (
    ensure_data_files,
    load_config,
    load_questions,
    load_scores,
    save_config,
    save_questions,
    save_scores,
)
from utils.quiz_engine import calculate_score, get_randomised_quiz

APP_TITLE = "📘 Accounting Quiz Game"
PAGE_SLUGS = {
    "Home": "home",
    "Take Quiz": "take_quiz",
    "Leaderboard": "leaderboard",
    "Admin": "admin",
}


def get_admin_password() -> str:
    """Retrieve the admin password from env vars or Streamlit secrets."""
    env_secret = os.environ.get("ADMIN_PASSWORD", "").strip()
    secrets_secret = ""
    secrets_obj = getattr(st, "secrets", None)
    if secrets_obj is not None:
        try:
            secret_val = secrets_obj.get("ADMIN_PASSWORD")
        except Exception:
            secret_val = None
        if secret_val:
            secrets_secret = str(secret_val).strip()
    return env_secret or secrets_secret


ADMIN_PASSWORD = get_admin_password()


def reset_quiz_state() -> None:
    """Clear quiz-related session state keys."""
    st.session_state.quiz_started = False
    st.session_state.quiz_question_ids = []
    st.session_state.quiz_answers = {}
    st.session_state.quiz_start_time = None
    st.session_state.quiz_option_orders = {}
    st.session_state.quiz_run_id = None


# =============================================================================
# INITIALISATION
# =============================================================================
def init_app():
    st.set_page_config(
        page_title="Accounting Quiz Game",
        page_icon="📘",
        layout="centered",
    )

    ensure_data_files()

    defaults = {
        "quiz_started": False,
        "quiz_answers": {},
        "quiz_question_ids": [],
        "quiz_start_time": None,
        "quiz_module": None,
        "quiz_option_orders": {},
        "quiz_run_id": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Refresh shared config-driven flags on every run
    config = load_config()
    st.session_state.show_explanations_for_correct = config.get(
        "show_explanations_for_correct", False
    )


# =============================================================================
# HOME PAGE
# =============================================================================
def home_page():
    st.title(APP_TITLE)
    st.markdown(
        """
        Welcome to the **Accounting Quiz Game** for non-accounting students! 🎮

        Use the sidebar to:
        - 🎓 Take a quiz
        - 🏆 View the leaderboard
        - 🔐 Manage the question bank (Admin)
        """
    )


# =============================================================================
# QUIZ PAGE
# =============================================================================
def quiz_page():
    st.title("🎮 Take the Quiz")

    questions_df = load_questions()
    config = load_config()
    module_time_limits = config.get("module_time_limits", {}) or {}
    module_availability = config.get("module_availability", {}) or {}
    if questions_df.empty:
        st.info("No questions available. Please ask the admin to add some.")
        return

    name = st.text_input("Enter your name:")
    student_id = st.text_input("Enter your student ID (optional):")

    modules = sorted(questions_df["module"].dropna().unique().tolist()) or ["General"]
    enabled_modules = [
        module for module in modules if module_availability.get(module, True)
    ]
    if not enabled_modules:
        st.warning(
            "No modules are currently enabled by the admin. Please check back later."
        )
        return

    disabled_modules = [
        module for module in modules if not module_availability.get(module, True)
    ]
    if disabled_modules:
        st.caption(
            "The following modules are currently disabled by the admin: "
            + ", ".join(disabled_modules)
        )

    selected_module = st.selectbox("Choose module / topic:", enabled_modules)

    # How many questions are available for this module?
    available_q = len(questions_df[questions_df["module"] == selected_module])
    if available_q < 1:
        st.error(
            "This module has no questions yet. Please choose another or ask admin to add some."
        )
        return

    module_time_limit_minutes = module_time_limits.get(selected_module)
    col1, col2 = st.columns(2)
    with col1:
        num_questions = st.number_input(
            "Number of questions",
            min_value=1,
            max_value=available_q,
            value=available_q,
            step=1,
        )
    with col2:
        time_limit_options = [0, 3, 5, 10, 15, 20, 30]
        default_time_limit = module_time_limit_minutes or 0
        if module_time_limit_minutes is not None:
            if module_time_limit_minutes not in time_limit_options:
                time_limit_options = sorted(
                    set(time_limit_options + [module_time_limit_minutes])
                )
            time_limit = st.selectbox(
                "Time limit (minutes)",
                time_limit_options,
                index=time_limit_options.index(module_time_limit_minutes),
                help="Admin-defined limit for this module.",
                disabled=True,
            )
        else:
            time_limit = st.selectbox(
                "Time limit (minutes)",
                time_limit_options,
                index=time_limit_options.index(default_time_limit),
                help="0 = no time limit",
            )

    if st.button("Start Quiz"):
        if not name:
            st.warning("Please enter your name before starting.")
            return

        st.session_state.quiz_started = True
        st.session_state.quiz_answers = {}
        st.session_state.quiz_start_time = datetime.now()
        st.session_state.quiz_module = selected_module
        st.session_state.quiz_run_id = (
            f"run_{st.session_state.quiz_start_time.timestamp()}"
        )

        quiz_q = get_randomised_quiz(
            questions_df, module=selected_module, num_questions=int(num_questions)
        )
        st.session_state.quiz_question_ids = quiz_q["id"].tolist()
        st.session_state.quiz_option_orders = {
            row["id"]: list(row["options"]) if isinstance(row["options"], list) else []
            for _, row in quiz_q.iterrows()
        }

    if not st.session_state.quiz_started:
        return

    # Reconstruct quiz questions in the stored order while guarding against deletions
    quiz_q = questions_df.set_index("id").reindex(
        st.session_state.quiz_question_ids, copy=False
    )
    missing_mask = quiz_q.isna().all(axis=1)
    if missing_mask.any():
        missing_ids = quiz_q[missing_mask].index.tolist()
        st.warning(
            "One or more quiz questions were removed or replaced by an admin "
            "while you were answering (IDs: "
            + ", ".join(map(str, missing_ids))
            + "). Please start a new quiz."
        )
        reset_quiz_state()
        return
    quiz_q = quiz_q.reset_index().rename(columns={"index": "id"})

    # Timer display
    if time_limit > 0 and st.session_state.quiz_start_time:
        elapsed = (datetime.now() - st.session_state.quiz_start_time).total_seconds()
        remaining = time_limit * 60 - elapsed
        if remaining <= 0:
            st.error(
                "⏰ Time is up! You can still submit, but your time limit has passed."
            )
        else:
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            st.info(f"⏳ Time remaining: {minutes:02d}:{seconds:02d}")

    st.markdown(f"### Module: **{st.session_state.quiz_module}**")

    # Render questions
    for idx, row in quiz_q.iterrows():
        qid = row["id"]
        st.markdown(f"#### Q{idx + 1}. {row['question']}")

        # Optional image
        if isinstance(row.get("image"), str) and row["image"].strip():
            st.image(row["image"], use_container_width=True)

        allow_multiple = bool(row.get("allow_multiple"))
        options = st.session_state.quiz_option_orders.get(qid) or row["options"]
        options = list(options)
        stored_answer = st.session_state.quiz_answers.get(qid)

        widget_key = f"{st.session_state.get('quiz_run_id', 'quiz')}_q_{qid}"
        if allow_multiple:
            prev_answers = stored_answer if isinstance(stored_answer, list) else []
            selected_options = []
            for opt in options:
                checkbox_key = f"{widget_key}_{opt}"
                checked = opt in prev_answers
                checked = st.checkbox(opt, value=checked, key=checkbox_key)
                if checked:
                    selected_options.append(opt)
            st.session_state.quiz_answers[qid] = selected_options
        else:
            default_index = (
                options.index(stored_answer) if stored_answer in options else None
            )
            ans = st.radio(
                "Select the correct answer:",
                options,
                index=default_index,
                label_visibility="collapsed",
                key=widget_key,
            )
            st.session_state.quiz_answers[qid] = ans
        st.write("---")

    if st.button("Submit Quiz"):
        # Calculate score
        score, detailed = calculate_score(quiz_q, st.session_state.quiz_answers)
        st.success(f"🎉 {name}, your score is **{score:.2f}/{len(quiz_q)}**!")

        # Feedback with explanations
        with st.expander("Detailed feedback"):
            for item in detailed:
                # item: {id, question, correct_answers, user_answer, is_correct, awarded}
                qrow = quiz_q[quiz_q["id"] == item["id"]].iloc[0]
                qtext = qrow["question"]
                explanation = str(qrow.get("explanation", "") or "").strip()
                correct_display = ", ".join(item["correct_answers"])
                if item["allow_multiple"]:
                    user_display = (
                        ", ".join(item["user_answer"])
                        if item["user_answer"]
                        else "No answer selected"
                    )
                else:
                    user_value = item["user_answer"] or "No answer selected"
                    user_display = user_value

                status_icon = "✅" if item["is_correct"] else "ℹ️"
                st.markdown(
                    f"{status_icon} **{qtext}**  \n"
                    f"Your answer: **{user_display}**  \n"
                    f"Correct answer(s): **{correct_display or '—'}**  \n"
                    f"Score: **{item['awarded']:.2f}/{item['max_points']}**"
                )
                if explanation:
                    if item["is_correct"]:
                        if st.session_state.show_explanations_for_correct:
                            st.info(f"💡 Explanation: {explanation}")
                    else:
                        st.warning(f"💡 Explanation: {explanation}")

        # Save score
        scores_df = load_scores()
        final_score = round(score, 4)
        new_row = pd.DataFrame(
            [
                {
                    "name": name,
                    "student_id": student_id,
                    "module": st.session_state.quiz_module,
                    "score": final_score,
                    "total_questions": len(quiz_q),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "time_limit_minutes": time_limit,
                }
            ]
        )
        scores_df = pd.concat([scores_df, new_row], ignore_index=True)
        save_scores(scores_df)

        # Reset quiz state
        reset_quiz_state()


# =============================================================================
# LEADERBOARD PAGE
# =============================================================================
def leaderboard_page():
    st.title("🏆 Leaderboard")

    df = load_scores()
    if df.empty:
        st.info("No quiz results yet.")
        return

    module_filter = st.selectbox(
        "Filter by module (optional):",
        ["All"] + sorted(df["module"].dropna().unique().tolist()),
    )

    if module_filter != "All":
        df = df[df["module"] == module_filter]

    if df.empty:
        st.info("No results for this module yet.")
        return

    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df["total_questions"] = pd.to_numeric(df["total_questions"], errors="coerce")
    df = df.dropna(subset=["score", "total_questions"])
    if df.empty:
        st.info("No quiz results yet.")
        return

    df["percentage"] = (df["score"] / df["total_questions"] * 100).round(1)
    df_sorted = df.sort_values(by=["percentage", "timestamp"], ascending=[False, True])

    st.subheader("Top scores")
    st.dataframe(
        df_sorted[
            [
                "name",
                "student_id",
                "module",
                "score",
                "total_questions",
                "percentage",
                "timestamp",
            ]
        ],
        width="stretch",
    )


# =============================================================================
# ADMIN PAGE
# =============================================================================
def admin_page():
    st.title("🔐 Admin Dashboard")

    admin_secret = get_admin_password()
    if not admin_secret:
        st.error(
            "Admin password is not configured. Set the `ADMIN_PASSWORD` "
            "environment variable or Streamlit secret and restart the app."
        )
        return

    pwd = st.text_input("Enter admin password:", type="password")
    if pwd != admin_secret:
        st.warning("Enter the correct admin password to manage questions.")
        return

    st.success("Admin access granted ✅")

    config = load_config()
    current_flag = config.get("show_explanations_for_correct", False)
    module_time_limits = config.get("module_time_limits", {})
    module_availability = config.get("module_availability", {})

    with st.expander("Global settings", expanded=True):
        show_flag = st.checkbox(
            "Show explanations even when the student's answer is correct",
            value=current_flag,
            key="show_explanations_for_correct_admin_toggle",
        )
        if show_flag != current_flag:
            config["show_explanations_for_correct"] = show_flag
            save_config(config)
            st.session_state.show_explanations_for_correct = show_flag
            st.info("Explanation preference updated for all future quizzes.")
        else:
            st.session_state.show_explanations_for_correct = current_flag

        st.markdown("### Module-specific settings")
        questions_df = load_questions()
        module_names = sorted(questions_df["module"].dropna().unique().tolist())
        if module_names:
            for module in module_names:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{module}**")
                with col2:
                    enabled = st.checkbox(
                        "Enabled",
                        value=module_availability.get(module, True),
                        key=f"module_enabled_{module}",
                    )
                    module_availability[module] = bool(enabled)
                with col3:
                    current_limit = module_time_limits.get(module)
                    time_limit = st.number_input(
                        "Time limit (minutes)",
                        min_value=0,
                        max_value=120,
                        value=current_limit or 0,
                        key=f"time_limit_{module}",
                    )
                    if time_limit <= 0:
                        module_time_limits.pop(module, None)
                    else:
                        module_time_limits[module] = time_limit
            config["module_time_limits"] = module_time_limits
            config["module_availability"] = module_availability
            save_config(config)
        else:
            st.info("No modules available yet. Add questions to configure limits.")

    st.markdown("---")
    st.subheader("Current question bank")
    st.dataframe(questions_df, width="stretch")

    # ---------------------------
    # Add question
    # ---------------------------
    st.markdown("---")
    st.subheader("➕ Add a new question (Explanation REQUIRED)")

    with st.form("add_question_form"):
        module = st.text_input("Module / Topic", value="Basics")
        question_text = st.text_area("Question text")

        col1, col2 = st.columns(2)
        with col1:
            opt1 = st.text_input("Option 1")
            opt2 = st.text_input("Option 2")
        with col2:
            opt3 = st.text_input("Option 3")
            opt4 = st.text_input("Option 4")

        options = [o for o in [opt1, opt2, opt3, opt4] if o and o.strip()]

        allow_multi = st.checkbox("Allow multiple correct answers")
        correct_choices = (
            st.multiselect("Select correct answer(s)", options) if options else []
        )
        difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
        image = st.text_input("Image URL (optional)")
        explanation = st.text_area("Explanation (REQUIRED)")

        submitted = st.form_submit_button("Add question")

    if submitted:
        missing_fields = (
            not module.strip()
            or not question_text.strip()
            or not options
            or not correct_choices
            or not explanation.strip()
        )
        multi_invalid = allow_multi and len(correct_choices) < 2
        single_invalid = not allow_multi and len(correct_choices) != 1
        if missing_fields or multi_invalid or single_invalid:
            st.error(
                "Provide module, question, at least two options, select valid answer(s), "
                "and include an explanation."
            )
        else:
            new_id = int(questions_df["id"].max() + 1) if not questions_df.empty else 1
            correct_answers = [c.strip() for c in correct_choices]
            new_row = pd.DataFrame(
                [
                    {
                        "id": new_id,
                        "module": module.strip(),
                        "question": question_text.strip(),
                        "options": options,
                        "answer": correct_answers[0],
                        "correct_answers": correct_answers,
                        "allow_multiple": allow_multi,
                        "difficulty": difficulty,
                        "image": image.strip(),
                        "explanation": explanation.strip(),
                    }
                ]
            )
            questions_df = pd.concat([questions_df, new_row], ignore_index=True)
            save_questions(questions_df)
            st.success(f"Question added with ID {new_id}.")

    # ---------------------------
    # Edit question
    # ---------------------------
    st.markdown("---")
    st.subheader("✏️ Edit an existing question")
    if not questions_df.empty:
        q_ids = questions_df["id"].astype(int).tolist()
        edit_id = st.selectbox(
            "Select question ID to edit", q_ids, key="edit_question_select"
        )
        edit_row = questions_df[questions_df["id"] == edit_id].iloc[0]
        row_options = (
            edit_row["options"] if isinstance(edit_row["options"], list) else []
        )
        max_opts = max(6, len(row_options))
        with st.form(f"edit_question_form_{edit_id}"):
            module_edit = st.text_input("Module / Topic", value=edit_row["module"])
            question_edit = st.text_area("Question text", value=edit_row["question"])
            allow_multi_edit = st.checkbox(
                "Allow multiple correct answers",
                value=bool(edit_row.get("allow_multiple")),
                key=f"edit_allow_multi_{edit_id}",
            )
            option_inputs = []
            for i in range(max_opts):
                default_val = row_options[i] if i < len(row_options) else ""
                option_inputs.append(
                    st.text_input(
                        f"Option {i + 1}",
                        value=default_val,
                        key=f"edit_option_{edit_id}_{i}",
                    )
                )
            options_updated = [
                opt.strip() for opt in option_inputs if opt and opt.strip()
            ]
            if allow_multi_edit:
                correct_defaults = edit_row.get("correct_answers", [])
                correct_edit = st.multiselect(
                    "Select correct answer(s)",
                    options_updated,
                    default=[c for c in correct_defaults if c in options_updated],
                    key=f"edit_correct_multi_{edit_id}",
                )
            else:
                single_default = edit_row.get("correct_answers", [])
                default_value = single_default[0] if single_default else None
                correct_choice = st.selectbox(
                    "Select the correct answer",
                    options_updated,
                    index=options_updated.index(default_value)
                    if default_value in options_updated
                    else 0,
                    key=f"edit_correct_single_{edit_id}",
                )
                correct_edit = [correct_choice]
            difficulty_edit = st.selectbox(
                "Difficulty",
                ["Easy", "Medium", "Hard"],
                index=["Easy", "Medium", "Hard"].index(
                    edit_row.get("difficulty", "Easy")
                ),
                key=f"edit_difficulty_{edit_id}",
            )
            image_edit = st.text_input(
                "Image URL (optional)", value=edit_row.get("image", "")
            )
            explanation_edit = st.text_area(
                "Explanation", value=edit_row.get("explanation", "")
            )
            submitted_edit = st.form_submit_button("Save changes")
        if submitted_edit:
            if (
                not module_edit.strip()
                or not question_edit.strip()
                or not options_updated
                or not explanation_edit.strip()
            ):
                st.error("Please complete all required fields before saving.")
            else:
                if allow_multi_edit and len(correct_edit) < 2:
                    st.error(
                        "Select at least two correct answers for multi-answer questions."
                    )
                elif not allow_multi_edit and len(correct_edit) != 1:
                    st.error("Select exactly one correct answer.")
                elif any(ans not in options_updated for ans in correct_edit):
                    st.error("All correct answers must match the available options.")
                else:
                    updated_row = {
                        "id": edit_id,
                        "module": module_edit.strip(),
                        "question": question_edit.strip(),
                        "options": options_updated,
                        "answer": correct_edit[0],
                        "correct_answers": correct_edit,
                        "allow_multiple": allow_multi_edit,
                        "difficulty": difficulty_edit,
                        "image": image_edit.strip(),
                        "explanation": explanation_edit.strip(),
                    }
                    questions_df = questions_df[questions_df["id"] != edit_id]
                    questions_df = pd.concat(
                        [questions_df, pd.DataFrame([updated_row])], ignore_index=True
                    )
                    questions_df = questions_df.sort_values("id").reset_index(drop=True)
                    save_questions(questions_df)
                    st.success(f"Question {edit_id} updated.")
                    st.rerun()
    else:
        st.info("No questions available to edit.")

    # ---------------------------
    # Delete question
    # ---------------------------
    st.markdown("---")
    st.subheader("🗑 Delete a question")

    if not questions_df.empty:
        delete_ids = questions_df["id"].astype(int).tolist()
        del_id = st.selectbox(
            "Select question ID to delete", delete_ids, key="delete_question_select"
        )
        if st.button("Delete selected question"):
            questions_df = questions_df[questions_df["id"] != del_id]
            save_questions(questions_df)
            st.success(f"Question with ID {del_id} deleted.")
            st.rerun()
    else:
        st.info("No questions to delete.")

    # ---------------------------
    # Clear entire question bank
    # ---------------------------
    st.markdown("---")
    st.subheader("🧹 Clear entire question bank")
    st.warning(
        "This will permanently remove all questions. This action cannot be undone."
    )
    if st.button("Delete ALL questions", type="secondary"):
        empty_df = pd.DataFrame(columns=questions_df.columns)
        save_questions(empty_df)
        st.success("All questions deleted.")
        st.experimental_rerun()

    # ---------------------------
    # Export questions
    # ---------------------------
    st.markdown("---")
    st.subheader("📤 Export questions as CSV")

    if st.button("Prepare CSV for download"):
        csv_data = questions_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download questions.csv",
            data=csv_data,
            file_name="questions_export.csv",
            mime="text/csv",
        )

    # ---------------------------
    # Import questions from Excel
    # ---------------------------
    st.markdown("---")
    st.subheader("📥 Import / replace question bank from Excel")

    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])
    st.caption(
        "Expected columns (min): module, question, option1, option2, answer. "
        "Optional: option3, option4, difficulty, image, explanation, "
        "allow_multiple, correct_answers (JSON array or pipe-delimited)."
    )

    if uploaded_file is not None:
        try:
            df_excel = pd.read_excel(uploaded_file)
            required_cols = {
                "module",
                "question",
                "option1",
                "option2",
                "answer",
                "explanation",
            }
            if not required_cols.issubset(set(df_excel.columns)):
                st.error(
                    "Missing required columns. Required at minimum: "
                    + ", ".join(sorted(required_cols))
                )
            else:
                new_rows = []
                skipped_no_options = 0
                skipped_missing_explanation = 0
                skipped_answer_mismatch = 0
                skipped_invalid_multiselect = 0

                def parse_answers(value):
                    if isinstance(value, list):
                        return [str(v).strip() for v in value if str(v).strip()]
                    if isinstance(value, str) and value.strip():
                        text = value.strip()
                        if text.startswith("["):
                            try:
                                data = json.loads(text)
                                if isinstance(data, list):
                                    return [
                                        str(v).strip() for v in data if str(v).strip()
                                    ]
                            except json.JSONDecodeError:
                                pass
                        if "|" in text:
                            return [
                                part.strip() for part in text.split("|") if part.strip()
                            ]
                        return [text]
                    return []

                for _, row in df_excel.iterrows():
                    opts = [
                        row.get("option1"),
                        row.get("option2"),
                        row.get("option3"),
                        row.get("option4"),
                    ]
                    opts = [o for o in opts if isinstance(o, str) and o.strip()]
                    if not opts:
                        skipped_no_options += 1
                        continue

                    explanation = str(row.get("explanation", "") or "").strip()
                    if not explanation:
                        # Enforce explanation requirement even on import
                        skipped_missing_explanation += 1
                        continue

                    raw_correct = row.get("correct_answers")
                    parsed_answers = parse_answers(raw_correct)
                    fallback_answer = str(row.get("answer", "") or "").strip()
                    if not parsed_answers and fallback_answer:
                        parsed_answers = [fallback_answer]

                    if not parsed_answers:
                        skipped_answer_mismatch += 1
                        continue

                    if any(ans not in opts for ans in parsed_answers):
                        skipped_answer_mismatch += 1
                        continue

                    allow_multiple_flag = row.get("allow_multiple")
                    allow_multiple = (
                        bool(allow_multiple_flag)
                        if pd.notna(allow_multiple_flag)
                        else len(parsed_answers) > 1
                    )

                    if allow_multiple and len(parsed_answers) < 2:
                        skipped_invalid_multiselect += 1
                        continue
                    if not allow_multiple and len(parsed_answers) != 1:
                        # fall back to first answer
                        parsed_answers = [parsed_answers[0]]

                    new_rows.append(
                        {
                            "module": row.get("module", "General"),
                            "question": row["question"],
                            "options": opts,
                            "answer": parsed_answers[0],
                            "correct_answers": parsed_answers,
                            "allow_multiple": allow_multiple,
                            "difficulty": row.get("difficulty", "Easy"),
                            "image": row.get("image", ""),
                            "explanation": explanation,
                        }
                    )

                if new_rows:
                    new_df = pd.DataFrame(new_rows)
                    new_df.insert(0, "id", range(1, len(new_df) + 1))
                    save_questions(new_df)
                    st.success(f"Imported {len(new_rows)} questions from Excel.")
                else:
                    st.warning("No valid rows found in the uploaded file.")
                if skipped_no_options:
                    st.warning(
                        f"Skipped {skipped_no_options} row(s) without at least two options."
                    )
                if skipped_missing_explanation:
                    st.warning(
                        f"Skipped {skipped_missing_explanation} row(s) without explanations."
                    )
                if skipped_answer_mismatch:
                    st.warning(
                        f"Skipped {skipped_answer_mismatch} row(s) where the answer was blank or "
                        "did not match any provided option."
                    )
                if skipped_invalid_multiselect:
                    st.warning(
                        f"Skipped {skipped_invalid_multiselect} row(s) with invalid multi-answer settings "
                        "(need at least two correct answers when allow_multiple is true)."
                    )
        except Exception as e:
            st.error(f"Error reading Excel file: {e}")

    # ---------------------------
    # Clear leaderboard
    # ---------------------------
    st.markdown("---")
    st.subheader("🧹 Clear leaderboard data")
    st.warning("This permanently deletes all recorded quiz results.")
    if st.button("Clear leaderboard", type="secondary"):
        empty_scores = pd.DataFrame(
            columns=[
                "name",
                "student_id",
                "module",
                "score",
                "total_questions",
                "timestamp",
                "time_limit_minutes",
            ]
        )
        save_scores(empty_scores)
        st.success("Leaderboard cleared.")


# =============================================================================
# MAIN
# =============================================================================
def main():
    init_app()

    st.sidebar.title("Navigation")
    pages = ["Home", "Take Quiz", "Leaderboard", "Admin"]
    slug_to_page = {slug: name for name, slug in PAGE_SLUGS.items()}
    params = st.query_params
    requested_slug = params.get("page")
    if isinstance(requested_slug, list):
        requested_slug = requested_slug[0] if requested_slug else None
    default_page = slug_to_page.get(requested_slug, "Home")
    default_index = pages.index(default_page)

    page = st.sidebar.radio(
        "Go to:",
        pages,
        index=default_index,
        key="nav_radio",
    )

    st.query_params["page"] = PAGE_SLUGS.get(page, "home")

    if page == "Home":
        home_page()
    elif page == "Take Quiz":
        quiz_page()
    elif page == "Leaderboard":
        leaderboard_page()
    elif page == "Admin":
        admin_page()


if __name__ == "__main__":
    main()
