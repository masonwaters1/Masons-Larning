# The Reading Room — A Personal E-Learning Platform

A local Django app for working through four long-form humanities courses, one lesson at a time, in an **interleaved** reading order. You read Lesson 1 of every course, then Lesson 2 of every course, and so on — so all four courses advance together rather than finishing one before starting the next.

The four courses:

1. **The Architecture of Meaning** — depth psychology, mythology, and the thought of Jordan Peterson (148 lessons)
2. **The Free-Market Tradition** — economic thought from Adam Smith to Thomas Sowell (113 lessons)
3. **The Water We Swim In** — how Christianity made the modern world (189 lessons)
4. **The American Story** — a deep history of a providential and imperfect nation (137 lessons)

The full structure of all 587 lessons is seeded and navigable. Four lessons are written in full so far (the first lesson of each course); the rest show a clean "coming soon" state until their text is written.

---

## Running it in VS Code

You need **Python 3.10+** installed. From a terminal in VS Code (`` Ctrl+` ``):

### 1. Create and activate a virtual environment

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up the database and load the courses
```bash
python manage.py migrate
python manage.py seed_courses
```

`seed_courses` builds all four courses, their units, and all 587 lessons from the outline files in `courses/data/`, then loads the full lesson text for any written lessons found in `courses/data/lessons/`.

### 4. Run the server
```bash
python manage.py runserver
```

Open **http://127.0.0.1:8000/** in your browser. That's the dashboard. Click **Continue** to jump to your next unread lesson.

> Tip: In VS Code, select the `.venv` interpreter via the Command Palette → *Python: Select Interpreter* so the editor resolves Django imports.

---

## How to use it

- **Dashboard** (`/`) — overall progress, a card that jumps to your next unread lesson, and a preview of the upcoming interleaved rounds.
- **Reading a lesson** — full text with footnotes, a per-lesson table of contents in the left rail, and a navigation rail across all four courses. When you finish, click **Mark as read** and it auto-advances to the next lesson in the interleaved sequence.
- **Course pages** — see every unit and lesson in one course, with read-checkmarks and a badge marking which lessons have full text.
- **Admin** (`/admin/`) — optional. Create a login with `python manage.py createsuperuser` to browse/edit content in Django's admin.

Your read-progress is stored in the local SQLite database (`db.sqlite3`). It is personal to this machine.

---

## Writing more lessons

Lessons are plain Markdown files in `courses/data/lessons/`, named by course and lesson number:

```
c{course_number}_l{lesson_number}.md
```

So `c2_l5.md` is Course 2 ("The Free-Market Tradition"), Lesson 5. Use `##` headings inside the file — the reader builds the in-page table of contents from them automatically. Footnotes use standard Markdown footnote syntax:

```markdown
Some claim in the text.[^1]

[^1]: The source and note for that claim.
```

After adding or editing a lesson file, re-run:
```bash
python manage.py seed_courses
```
This reloads lesson text without disturbing your read-progress.

---

## Project layout

```
elearning/
├── manage.py
├── requirements.txt
├── config/                 # Django project settings + root URLs
└── courses/
    ├── models.py           # Course, Unit, Lesson, Progress (+ interleaving logic)
    ├── views.py            # dashboard, course, lesson, mark-as-read
    ├── urls.py
    ├── admin.py
    ├── templatetags/
    │   └── lesson_extras.py  # markdown + reading-time filters
    ├── management/commands/
    │   └── seed_courses.py   # builds courses and loads lesson text
    ├── templates/courses/
    ├── static/courses/css/
    └── data/
        ├── c1.txt … c4.txt   # course/unit/lesson outlines
        └── lessons/          # full lesson markdown files
```

The interleaved order lives in the `Lesson` model: lessons are ordered by `course_lesson_number` first, then by course, so the global sequence naturally rotates through the four courses. When a shorter course runs out of lessons, the remaining courses simply continue.
