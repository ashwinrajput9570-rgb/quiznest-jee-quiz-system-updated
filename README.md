# QuizNest — JEE Preparation Quiz System (Flask)

A JEE Main preparation quiz platform: Physics, Chemistry & Mathematics
question bank, topic-wise quizzes, full mock tests, timed attempts with
auto-grading, and a complete admin panel — built on Flask + SQLite.

## Features

- **Student side**: register/login, browse JEE Prep by subject → topic →
  quiz, take timed quizzes (countdown timer, question palette, navigate
  freely, single submit), auto-graded results with per-question
  correct/incorrect review and explanations, personal results history.
- **Admin side**: separate admin login, manage subjects/topics, full
  question CRUD (4 options, correct answer, explanation, difficulty,
  marks), create/edit/delete quizzes, add/remove questions from a quiz via
  a builder screen, view every student's attempts and scores.
- **Security**: student and admin sessions are independent; every
  `/admin/*` route requires an admin session; every quiz attempt is
  ownership-checked so students can only see their own results.
- Original homepage, register/login/logout, and Bootstrap 5 blue/white
  theme are unchanged and reused throughout the new pages.

## Project structure

```
quiznest/
├── app.py                      # Flask app, DB schema (init_db), all routes
├── seed_jee_data.py             # loads JEE subjects/topics/sample questions/quizzes
├── create_admin.py              # CLI script to create/promote an admin account
├── requirements.txt
├── quiz_system.db                # created automatically on first run
├── templates/
│   ├── base.html                 # shared navbar + footer (now session-aware for admin too)
│   ├── index.html, login.html, register.html, dashboard.html
│   ├── admin_login.html, admin_dashboard.html
│   ├── admin_content.html        # manage subjects & topics
│   ├── admin_questions.html, admin_question_form.html
│   ├── admin_quizzes.html, admin_quiz_form.html, admin_quiz_builder.html
│   ├── admin_results.html, admin_attempt_detail.html
│   ├── jee_home.html, jee_subject.html, jee_topic.html, jee_mock_tests.html
│   ├── quiz_attempt.html, quiz_result.html, my_results.html
└── static/
    ├── css/style.css             # original theme + new quiz-taking/result styles appended
    ├── js/main.js
    └── js/quiz-mock.js           # hero animation, now shows JEE sample questions
```

## Setup & run

```bash
# 1. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create the database + load the JEE question bank
python -c "from app import init_db; init_db()"
python seed_jee_data.py

# 4. Create an admin account
python create_admin.py

# 5. Run the app
python app.py
```

Then open **http://127.0.0.1:5000**.

`seed_jee_data.py` creates all 9 topics under Physics, Chemistry and
Mathematics, inserts ~48 verified sample MCQs spread across them, and
creates a handful of ready-to-take quizzes: one "Full Practice Set" per
subject, one featured topic test per subject (Mechanics, Organic
Chemistry, Calculus), and one mixed "JEE Main Mock Test 1". It's safe to
re-run — it skips seeding if subjects/questions/quizzes already exist.

## Admin login & testing instructions

1. Run `python create_admin.py` and follow the prompts (name, email,
   password). There's no public admin sign-up page on purpose.
2. Log in at **http://127.0.0.1:5000/admin/login**.
3. From the Admin Dashboard you can jump to:
   - **Manage Content** — add/edit/delete subjects & topics
   - **Question Bank** — add/edit/delete questions, filter by subject/topic
   - **Quizzes** — create a quiz, then use the "builder" screen (list icon)
     to add/remove questions from the bank into that quiz
   - **Results** — every submitted student attempt, with a detail view
     showing each question, the student's answer, and the correct answer
4. To test the student side: register a normal account at `/register`,
   log in, go to **JEE Prep** in the navbar, pick a subject → topic (or a
   mock test), start a quiz, answer, and submit. Your score and
   explanations appear immediately, and also show up under **My Results**
   and in the admin's **Results** page.

## Notes

- Before deploying anywhere public, replace `app.secret_key` in `app.py`
  with a securely generated random value (e.g.
  `python -c "import secrets; print(secrets.token_hex(32))"`) and load it
  from an environment variable instead of hardcoding it.
- The question bank is intentionally a *starting* set — use the admin
  Question Bank and Quiz pages to keep adding more JEE questions and
  quizzes; no code changes are needed for that.
