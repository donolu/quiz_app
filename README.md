# Accounting Quiz Application

A comprehensive Streamlit-based quiz platform for non-accounting students to practice accounting concepts. Features include quiz-taking, persistent leaderboards, multi-select questions with partial credit, and a full admin dashboard.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip or conda
- (Optional) Supabase account for cloud storage

### Installation

```bash
# Navigate to the project directory
cd quiz_app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the App

**Option 1: Using the startup script (Recommended)**
```bash
# Edit run_app.sh to set your credentials
./run_app.sh
```

**Option 2: Manual setup**
```bash
# Set environment variables
export ADMIN_PASSWORD="your_secure_password"
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your_supabase_key"

# Run the app
streamlit run app.py
```

The app will be available at `http://localhost:8501`

## ✨ Features

### For Students
- **Interactive Quizzes** - Multiple choice and multi-select questions
- **Partial Credit** - Multi-select questions award partial credit
- **Timed Quizzes** - Optional time limits per module
- **Instant Feedback** - See results immediately after submission
- **Detailed Explanations** - Learn from mistakes with comprehensive explanations
- **Persistent Leaderboard** - Track your progress and compete with peers

### For Administrators
- **Question Management** - Add, edit, and delete questions via UI
- **Bulk Import** - Upload questions from Excel/CSV files
- **Module Control** - Enable/disable modules and set time limits
- **Export Data** - Download question bank as CSV
- **Score Tracking** - View all student submissions
- **Live Preview** - See options as you type when adding questions

## 📊 Storage Modes

### CSV Mode (Default)
- Stores data locally in `data/` directory
- No external dependencies
- Perfect for development and testing

### Supabase Mode (Recommended for Production)
- Cloud-based storage with PostgreSQL
- Persistent across deployments
- Automatic backups
- Multi-user support

**To enable Supabase mode:**
Set these environment variables in `run_app.sh`:
```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your_supabase_key"
export SUPABASE_QUESTIONS_TABLE="questions"  # optional, default: "questions"
export SUPABASE_SCORES_TABLE="scores"        # optional, default: "scores"
```

## 📝 Question Format

### Adding Questions via Admin UI
1. Go to Admin page
2. Fill in the "Add a new question" form:
   - **Module/Topic:** e.g., "Budgeting"
   - **Question text:** Your question
   - **Options 1-4:** Answer choices
   - **Correct answer(s):** Copy exact text from options, use `|` for multiple answers
   - **Explanation:** Why the answer is correct (required)
   - **Difficulty:** Easy, Medium, or Hard
3. Click "Add question" - form clears automatically

### CSV/Excel Format
```csv
module,question,option1,option2,option3,option4,answer,explanation,difficulty
Budgeting,What is the accounting equation?,Assets = Liabilities + Equity,Assets = Revenue - Expenses,Equity = Assets + Liabilities,Liabilities = Assets + Equity,Assets = Liabilities + Equity,The accounting equation represents the relationship between assets liabilities and equity.,Medium
```

### Multi-Select Questions
Use pipe (`|`) separator for multiple correct answers:
```csv
module,question,option1,option2,option3,option4,correct_answers,allow_multiple,explanation,difficulty
Budgeting,Select all expense types,Rent,Sales,Wages,Capital,Rent|Wages,True,Rent and wages are expenses while sales is revenue and capital is equity.,Medium
```

### Template Files
Use the provided templates to get started:
- `questions_template.xlsx` - Excel template
- `questions_template.csv` - CSV template (recommended - no corruption issues)

## 🛠️ Complete Admin Guide

### Getting Started with Admin

#### 1. Access the Admin Panel
```bash
# Make sure ADMIN_PASSWORD is set in run_app.sh
./run_app.sh
```
- Click **"Admin"** in the sidebar
- Enter your admin password
- You'll see the full question bank displayed

#### 2. View Current Questions
The admin dashboard shows:
- All questions in a searchable table
- Total number of questions
- Questions organized by module
- All question details (options, answers, explanations)

### Adding Questions Manually

**Step-by-Step Process:**

1. **Scroll to "Add a new question" section**

2. **Fill in the form fields:**

   **Module/Topic** (e.g., "Budgeting", "Financial Statements")
   - Groups related questions together
   - Students can select modules when taking quizzes

   **Question Text**
   - Write your question clearly
   - Can be as long as needed

   **Options 1-4**
   - Enter answer choices
   - Minimum 2 options required
   - Options 3 and 4 are optional
   - **As you type, you'll see a live preview below!**

   **Correct Answer(s)**
   - **Single answer:** Copy ONE option exactly (including capitalization)
   - **Multiple answers:** Copy multiple options separated by `|`
   - Example single: `Assets = Liabilities + Equity`
   - Example multiple: `Cash|Accounts Receivable|Equipment`

   **Allow Multiple Correct Answers** (checkbox)
   - Check this for multi-select questions
   - Students can select multiple options
   - Partial credit awarded automatically

   **Difficulty** (dropdown)
   - Easy, Medium, or Hard
   - Helps organize questions by complexity

   **Image URL** (optional)
   - Add a link to an image
   - Useful for diagrams, charts, screenshots

   **Explanation** (REQUIRED)
   - Explain why the answer is correct
   - Students see this after completing the quiz
   - Be detailed - this helps students learn!

3. **Click "Add question"**
   - Form automatically clears after success
   - New question appears in the question bank above
   - You'll see a success message

**Pro Tips:**
- Use the live preview to verify your options before submitting
- Copy-paste answers from the preview to avoid typos
- If you see an error, read the message carefully - it tells you exactly what's wrong

### Bulk Import from Files

**Quick Start:**
1. Use the provided `tutorial_8_budgeting_questions.csv` to test
2. Go to Admin → "Import / replace question bank"
3. Upload the file
4. Click "Process uploaded file"
5. ✅ 10 questions imported instantly!

**Creating Your Own Import File:**

**Option A: Start from Template (Easiest)**
```bash
# Open the template
open questions_template.csv

# Add your questions following the format
# Save the file
# Upload via Admin panel
```

**Option B: Create from Scratch**

CSV structure:
```csv
module,question,option1,option2,option3,option4,answer,explanation,difficulty
Budgeting,What is revenue?,Money earned,Money spent,Money borrowed,Money invested,Money earned,Revenue is income earned from business operations,Easy
```

For multi-select questions:
```csv
module,question,option1,option2,option3,option4,correct_answers,allow_multiple,explanation,difficulty
Budgeting,Select all assets,Cash,Loan,Equipment,Rent,Cash|Equipment,True,Cash and equipment are assets; loan is liability; rent is expense,Medium
```

**Import Process:**

1. **Prepare your file**
   - Use template as starting point
   - Ensure all required columns are present
   - Check answer text matches options exactly

2. **Upload via Admin**
   - Click "Browse files"
   - Select your .csv or .xlsx file
   - You'll see file details (name, size, type)

3. **Click "Process uploaded file"**
   - Processing starts immediately
   - You'll see:
     - ✅ Success message with count
     - ⚠️ Warnings for skipped rows (with reasons)
     - Detailed feedback for any errors

4. **Review the results**
   - Check the question bank table
   - Verify all questions imported correctly
   - Fix any issues and re-upload if needed

**Supported Formats:**
- **CSV (.csv)** - Recommended! No corruption, easy to edit
- **Excel (.xlsx, .xls)** - Works but can have issues

**Common Import Issues:**

| Issue | Solution |
|-------|----------|
| "0 worksheets found" | File is empty/corrupted - use CSV instead |
| "Missing required columns" | Add: module, question, option1, option2, answer, explanation |
| "Answer doesn't match options" | Copy answer text exactly from one of your options |
| "No valid rows found" | Check that explanations are filled in (required!) |

### Managing the Question Bank

**Export Questions**
- Click "Download questions as CSV"
- Opens in Excel or save to file
- Useful for backup or editing offline

**Clear Question Bank**
- Scroll to "Clear question bank" section
- Click "Yes, clear all questions"
- **Warning:** This deletes ALL questions permanently!
- Use for starting fresh or replacing entire bank

**Edit Questions**
- Find the question in the "Edit question" section
- Select question ID from dropdown
- Modify any fields
- Save changes

**Delete Questions**
- Select question ID from dropdown
- Click "Delete selected question"
- Question removed immediately

### Module Management

**Configure Module Availability:**
- Enable/disable specific modules for students
- Disabled modules won't appear in quiz selection
- Useful for rolling out content gradually

**Set Time Limits:**
- Add time limits per module (in minutes)
- Students see a countdown timer
- Quiz auto-submits when time expires

**Explanation Settings:**
- Toggle whether students see explanations for CORRECT answers
- Wrong answers always show explanations
- Helps balance learning vs assessment

## 🧪 Testing

### Run Test Suite
```bash
# Activate virtual environment
source venv/bin/activate

# Test score validation (checks for inf/NaN handling)
python test_score_validation.py

# Test score persistence to database
python test_leaderboard_persistence.py

# Test score saving with various data types
python test_score_save.py

# Test quiz engine (randomization, scoring)
python test_quiz_engine.py
```

All tests should pass ✅

### Utilities
```bash
# Clean up invalid scores in database
python cleanup_scores.py

# Convert Excel to CSV (if having upload issues)
python convert_excel_to_csv.py your_file.xlsx

# Check Supabase scores for issues
python test_supabase_scores.py
```

## 🐛 Troubleshooting

### Quiz Submission Fails
**Error:** "Out of range float values are not JSON compliant"

**Solution:**
- ✅ This has been fixed in the latest version
- If you still see it, run: `python cleanup_scores.py`
- All numpy/pandas types are now converted to Python natives

### Excel Upload Fails
**Error:** "Worksheet index 0 is invalid, 0 worksheets found"

**Solutions:**
1. File might be corrupted - try opening in Excel/Google Sheets
2. **Use CSV format instead** (more reliable)
3. Use provided template: `questions_template.csv`
4. See `EXCEL_UPLOAD_GUIDE.md` for detailed help

### Leaderboard Empty
**Issue:** Scores not persisting

**Solutions:**
1. ✅ This has been fixed - scores now properly append
2. Verify Supabase environment variables in `run_app.sh`
3. Check Supabase tables exist and are accessible
4. Run: `python test_leaderboard_persistence.py` to verify

### Admin Password Not Working
**Solutions:**
1. Ensure `ADMIN_PASSWORD` is set in `run_app.sh`
2. Restart the app after changing the password
3. Check the variable: `echo $ADMIN_PASSWORD`

### Form Not Clearing After Adding Question
**Solution:**
- ✅ This has been fixed
- Form now clears automatically with `clear_on_submit=True`

## 📂 Helper Files & Templates

### Ready-to-Use Question Files
The app includes sample question files you can use immediately:

**tutorial_8_budgeting_questions.csv** - 10 budgeting questions ready to import
- Includes single and multi-select questions
- All questions have detailed explanations
- Covers key budgeting concepts
- Perfect for testing or as a starting point

### Template Files
Use these templates to create your own questions:

**questions_template.csv** (Recommended)
- Simple text format - edit in any text editor or Excel
- No corruption issues
- Easy to version control
- 2 sample questions included

**questions_template.xlsx**
- Excel format for familiar interface
- Same structure as CSV
- Use if you prefer Excel

### How to Use Templates

1. **Open the template file**
   ```bash
   # CSV (opens in Excel, Google Sheets, or text editor)
   open questions_template.csv

   # OR Excel
   open questions_template.xlsx
   ```

2. **Add your questions** - Follow the format:
   - One question per row
   - Fill all required columns: module, question, option1-4, answer, explanation
   - For multi-select: use `|` to separate correct answers, set `allow_multiple` to `True`

3. **Save the file**

4. **Import via Admin panel**
   - Go to Admin → Import section
   - Upload your file
   - Click "Process uploaded file"
   - ✅ Done!

## 📚 Additional Documentation

- **CLAUDE.md** - Complete technical documentation for developers
- **EXCEL_UPLOAD_GUIDE.md** - Detailed troubleshooting for file uploads
- **TUTORIAL_8_README.md** - Guide to the sample budgeting questions
- **.env.example** - Environment variable template

## 📋 Requirements

See `requirements.txt` for full dependencies. Key packages:
```
streamlit
pandas>=2.0.0
numpy>=1.22.4,<2.0.0
openpyxl
supabase
```

## 🎓 Usage Examples

### Example 1: Taking a Quiz
1. Go to "Take Quiz" page
2. Enter your name and student ID
3. Select module: "Budgeting"
4. Choose number of questions: 10
5. (Optional) Set time limit: 15 minutes
6. Click "Start Quiz"
7. Answer all questions
8. Click "Submit Quiz"
9. View your score, detailed feedback, and explanations
10. Check the leaderboard to see your ranking

### Example 2: Adding a Simple Question
Via Admin UI:
```
Module: Budgeting
Question: What is an asset?
Option 1: Resource owned by a business
Option 2: Money owed to suppliers
Option 3: Owner's investment
Option 4: Business expenses
Correct Answer: Resource owned by a business
Explanation: An asset is an economic resource owned or controlled by a business.
Difficulty: Easy
```

### Example 3: Multi-Select Question (CSV)
```csv
module,question,option1,option2,option3,option4,correct_answers,allow_multiple,explanation,difficulty
Budgeting,"Select all assets",Cash,Loan,Equipment,Salary,Cash|Equipment,True,"Cash and equipment are assets. Loan is a liability and salary is an expense.",Medium
```

### Example 4: Importing 10 Questions
1. Download `tutorial_8_budgeting_questions.csv`
2. Go to Admin → "Import / replace question bank"
3. Upload the CSV file
4. Click "Process uploaded file"
5. ✅ All 10 budgeting questions imported successfully

## 🔐 Security Notes

- **Admin Password:** Store securely in `run_app.sh`, never commit to version control
- **Supabase Keys:** Use service role key for full access, anon key for read-only
- **Environment Variables:** Stored in `run_app.sh` (gitignored)
- **.env.example:** Template provided - copy and customize as needed

## 📊 Architecture

```
quiz_app/
├── app.py                          # Main Streamlit application
├── run_app.sh                      # Startup script with env vars
├── utils/
│   ├── loader.py                   # Data persistence layer
│   └── quiz_engine.py              # Quiz logic and scoring
├── data/
│   ├── questions.csv               # Question bank (CSV mode)
│   ├── scores.csv                  # Student scores (CSV mode)
│   └── config.json                 # App configuration
├── scripts/
│   ├── generate_questions.py       # Question generation utility
│   └── read_doc.py                 # Document reader
├── Test files:
│   ├── test_quiz_engine.py         # Core tests
│   ├── test_score_validation.py    # Score validation tests
│   ├── test_leaderboard_persistence.py  # Persistence tests
│   └── test_score_save.py          # Type conversion tests
├── Templates:
│   ├── questions_template.xlsx     # Excel template
│   ├── questions_template.csv      # CSV template (recommended)
│   └── tutorial_8_budgeting_questions.csv  # Sample questions
└── Documentation:
    ├── README.md                   # This file
    ├── CLAUDE.md                   # Developer documentation
    ├── BUGFIX_SUMMARY.md           # All bug fixes
    ├── EXCEL_UPLOAD_GUIDE.md       # Upload troubleshooting
    └── .env.example                # Environment template
```

## 🆘 Support

For issues, questions, or feature requests:
1. Check this README and the documentation files
2. Run the relevant test scripts to diagnose issues
3. Check Streamlit terminal output for detailed errors
4. Review `BUGFIX_SUMMARY.md` for known issues and solutions

## 📈 Version History

- **v1.1.0** (Current) - Fixed persistence, JSON errors, admin UX
- **v1.0.0** - Initial release with basic quiz functionality

---

**Version:** 1.1.0
**Last Updated:** November 2025
**Status:** Production Ready ✅
**All Tests Passing:** ✅
