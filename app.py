import os
import sqlite3
import traceback
import pickle
import re
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session

# --- config ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "db")
DB_PATH = os.path.join(DB_DIR, "companies.db")
MODEL_DIR = os.path.join(BASE_DIR, "model")
VECT_PATH = os.path.join(MODEL_DIR, "vectorizer.pkl")
MODEL_PATH = os.path.join(MODEL_DIR, "internship_model.pkl")

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret-key-change-me")

# --- DB helpers ---
def get_db_conn():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def execute(query, params=()):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    lastrowid = cur.lastrowid
    conn.close()
    return lastrowid

def query_one(query, params=()):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(query, params)
    row = cur.fetchone()
    conn.close()
    return row

def query_all(query, params=()):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows

# --- ensure tables exist (safe migration friendly) ---
def ensure_tables():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_db_conn()
    cur = conn.cursor()
    # users
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT,
        full_name TEXT,
        email TEXT,
        skills TEXT,
        created_at TEXT
    )""")
    # internships
    cur.execute("""
    CREATE TABLE IF NOT EXISTS internships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER,
        title TEXT,
        description TEXT,
        location TEXT,
        stipend TEXT,
        skills_required TEXT,
        category TEXT,
        created_at TEXT
    )""")
    # applications
    cur.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        internship_id INTEGER,
        student_id INTEGER,
        resume_text TEXT,
        status TEXT,
        applied_at TEXT
    )""")
    # reports (note: user_feedback column name used)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        posting_id TEXT,
        user_feedback TEXT,
        reason TEXT,
        reporter_id INTEGER,
        created_at TEXT
    )""")
    conn.commit()
    conn.close()

ensure_tables()

# --- Auth helpers ---
def login_user(user_id):
    session['user_id'] = user_id

def logout_user():
    session.pop('user_id', None)

def get_current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    row = query_one("SELECT * FROM users WHERE id = ?", (uid,))
    return dict(row) if row else None

@app.context_processor
def inject_user():
    return dict(user=get_current_user())

# --- Simple recommender placeholder (no external dependency needed) ---
recommend_for_text = None
try:
    # optional: if user added a real recommender module
    from model.recommender import recommend_for_text as _r
    recommend_for_text = _r
except Exception:
    recommend_for_text = None

# --- Heuristic red flags and model loader (works without model) ---
RED_FLAG_PATTERNS = {
    "fee": [r"\b(pay|fee|paid|charge|payment|registration fee|processing fee|₹)\b"],
    "whatsapp": [r"\b(whatsapp|telegram|snapchat)\b"],
    "personal_contact": [r"\b(gmail\.com|yahoo\.com|hotmail\.com|outlook\.com)\b"],
    "vague": [r"\b(urgent hiring|no experience required|any graduate|no qualification|max 2 days)\b"],
    "high_pay": [r"\b(\d{3,} per month|\d+k|\bunrealistic pay\b|\binternship stipend:?\b)\b"]
}

_model = None
_vectorizer = None
def load_vectorizer_if_needed():
    global _vectorizer
    if _vectorizer is None:
        try:
            with open(VECT_PATH, "rb") as f:
                _vectorizer = pickle.load(f)
        except Exception:
            _vectorizer = None
    return _vectorizer

def load_model_if_needed():
    global _model
    if _model is None:
        try:
            with open(MODEL_PATH, "rb") as f:
                _model = pickle.load(f)
        except Exception:
            _model = None
    return _model

def heuristic_score_and_reasons(text):
    txt = (text or "").lower()
    found = []
    rf_count = 0
    for key, pats in RED_FLAG_PATTERNS.items():
        for p in pats:
            if re.search(p, txt):
                found.append(key)
                rf_count += 1
                break
    # basic scoring: each red flag reduces score
    score = max(0.0, 1.0 - min(1.0, rf_count * 0.25))
    reasons = []
    if "fee" in found:
        reasons.append("Mentions fees/payments (red flag).")
    if "whatsapp" in found:
        reasons.append("Contact via messaging apps detected (WhatsApp/Telegram).")
    if "personal_contact" in found:
        reasons.append("Personal email domains present instead of corporate.")
    if "vague" in found:
        reasons.append("Role description is vague or unrealistic.")
    if "high_pay" in found:
        reasons.append("Promised high pay or vague stipend phrase.")
    if not reasons:
        reasons.append("No obvious red flags detected; use judgment.")
    return score, "; ".join(reasons)

def predict_flag_and_prob(text):
    text = (text or "").strip()
    if not text:
        return "suspect", 0.0, "Empty text submitted."
    model = load_model_if_needed()
    vec = load_vectorizer_if_needed()
    if model is not None and vec is not None:
        try:
            X = vec.transform([text])
            if hasattr(model, "predict_proba"):
                probs = model.predict_proba(X)[0]
                # attempt to find 'genuine' class
                if hasattr(model, "classes_"):
                    classes = list(model.classes_)
                    if "genuine" in classes:
                        idx = classes.index("genuine")
                    else:
                        idx = int(__import__("numpy").argmax(probs))
                    prob = float(probs[idx])
                else:
                    prob = float(max(probs))
            else:
                pred = model.predict(X)[0]
                prob = 1.0 if pred else 0.0
            flag = "genuine" if prob >= 0.70 else ("fake" if prob <= 0.40 else "suspect")
            return flag, prob, "Model-based prediction"
        except Exception:
            traceback.print_exc()
    # fallback to heuristics
    score, reason = heuristic_score_and_reasons(text)
    flag = "genuine" if score >= 0.70 else ("fake" if score <= 0.40 else "suspect")
    return flag, float(score), reason

# --- Routes ---

@app.route("/")
def index():
    recent_rows = query_all("SELECT i.*, u.full_name as company_name FROM internships i LEFT JOIN users u ON i.company_id = u.id ORDER BY created_at DESC LIMIT 8")
    recent = [dict(r) for r in recent_rows] if recent_rows else []
    return render_template("index.html", recent=recent)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","").strip()
        role = request.form.get("role","student").strip()
        full_name = request.form.get("full_name","").strip()
        email = request.form.get("email","").strip()
        skills = request.form.get("skills","").strip()
        if not username or not password:
            flash("Username and password required.")
            return redirect(url_for("register"))
        # simple save (no password hashing needed for demo; you can add generate_password_hash)
        try:
            execute("INSERT INTO users (username, password, role, full_name, email, skills, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (username, password, role, full_name, email, skills, datetime.utcnow().isoformat()))
            flash("Registered successfully. Please login.")
            return redirect(url_for("login"))
        except Exception as e:
            traceback.print_exc()
            flash("Registration failed or username taken.")
            return redirect(url_for("register"))
    return render_template("register.html")


@app.route("/reports")
def reports():
    # Internship / application statistics for dashboard-style reports page

    # Top skills
    rows = query_all(
        "SELECT skills_required FROM internships "
        "WHERE skills_required IS NOT NULL AND trim(skills_required) != ''"
    )
    skills = {}
    for r in rows:
        txt = r["skills_required"] or ""
        for s in re.split(r"[,\n;]+", txt):
            s = s.strip().lower()
            if not s:
                continue
            skills[s] = skills.get(s, 0) + 1
    top_skills = sorted(skills.items(), key=lambda x: -x[1])[:10]

    # Top companies by number of internships
    top_companies = query_all(
        "SELECT u.full_name, COUNT(i.id) AS cnt "
        "FROM internships i "
        "LEFT JOIN users u ON i.company_id = u.id "
        "GROUP BY i.company_id "
        "ORDER BY cnt DESC LIMIT 10"
    )

    # Total number of applications
    total_apps_row = query_one("SELECT COUNT(*) AS cnt FROM applications")
    total_apps = total_apps_row["cnt"] if total_apps_row else 0

    return render_template(
        "reports.html",
        top_skills=top_skills,
        top_companies=top_companies,
        total_apps=total_apps,
    )


@app.route("/recommend", methods=["GET", "POST"])
def recommend():
    user = get_current_user()
    input_text = ""
    recs = []

    # GET default: pre‑fill with user skills if present
    if request.method == "GET":
        if user and user.get("skills"):
            input_text = user.get("skills", "")
    else:
        # POST: user submitted text from form
        input_text = request.form.get("resume_text", "").strip()

    try:
        if recommend_for_text and input_text:
            # your existing recommender function from model/recommender.py
            recs = recommend_for_text(input_text, topn=7)
        else:
            recs = []
    except Exception:
        traceback.print_exc()
        recs = []

    return render_template(
        "recommend.html",
        recs=recs,
        input_text=input_text,
    )







@app.route("/report", methods=["POST"])
def report():
    # ensure posting_id never becomes NULL (some DB schemas require NOT NULL)
    posting_id = request.form.get("posting_id")
    # if posting_id is None or empty, store empty string (or a generated token)
    if not posting_id:
        posting_id = ""  # or: posting_id = "manual-" + datetime.utcnow().strftime("%Y%m%d%H%M%S")

    user_feedback = request.form.get("user_feedback") or ""
    reason_text = request.form.get("reason") or ""

    try:
        reporter_id = None
        user = get_current_user()
        if user:
            reporter_id = user.get("id")

        execute(
            "INSERT INTO reports (posting_id, user_feedback, reason, reporter_id, created_at) VALUES (?, ?, ?, ?, ?)",
            (posting_id, user_feedback, reason_text, reporter_id, datetime.utcnow().isoformat())
        )

        flash("Thank you — your report has been submitted.")
    except Exception:
        traceback.print_exc()
        flash("Report received but not stored.")
    return redirect(url_for("index"))



@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","").strip()
        row = query_one("SELECT * FROM users WHERE username = ?", (username,))
        if row and row["password"] == password:
            login_user(row["id"])
            flash("Logged in successfully.")
            return redirect(url_for("index"))
        else:
            flash("Invalid credentials.")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    logout_user()
    flash("Logged out.")
    return redirect(url_for("index"))

@app.route("/post_internship", methods=["GET","POST"])
def post_internship():
    user = get_current_user()
    if not user or user.get("role") != "company":
        flash("Only company users can post internships.")
        return redirect(url_for("login"))
    if request.method == "POST":
        title = request.form.get("title","").strip()
        description = request.form.get("description","").strip()
        location = request.form.get("location","").strip()
        stipend = request.form.get("stipend","").strip()
        skills_required = request.form.get("skills_required","").strip()
        category = request.form.get("category","").strip()
        execute("INSERT INTO internships (company_id, title, description, location, stipend, skills_required, category, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (user["id"], title, description, location, stipend, skills_required, category, datetime.utcnow().isoformat()))
        flash("Internship posted.")
        return redirect(url_for("manage"))
    return render_template("post_internship.html")

@app.route("/internships")
def internships():
    try:
        rows = query_all("""SELECT i.id, i.title, i.description, i.location, i.stipend, i.skills_required, i.category, i.created_at,
                             u.full_name as company_name, u.username as company_username
                             FROM internships i LEFT JOIN users u ON i.company_id = u.id
                             ORDER BY i.created_at DESC""")
        internships_list = [dict(r) for r in rows] if rows else []
    except Exception:
        traceback.print_exc()
        flash("Could not load internships.")
        internships_list = []
    return render_template("internships.html", internships=internships_list)

@app.route("/apply/<int:internship_id>", methods=["GET","POST"])
def apply(internship_id):
    user = get_current_user()
    if not user or user.get("role") != "student":
        flash("Please login as a student to apply.")
        return redirect(url_for("login"))
    row = query_one("SELECT i.*, u.full_name as company_name FROM internships i LEFT JOIN users u ON i.company_id = u.id WHERE i.id = ?", (internship_id,))
    if not row:
        flash("Internship not found.")
        return redirect(url_for("internships"))
    internship = dict(row)
    if request.method == "POST":
        resume_text = request.form.get("resume_text","").strip()
        execute("INSERT INTO applications (internship_id, student_id, resume_text, status, applied_at) VALUES (?, ?, ?, ?, ?)",
                (internship_id, user["id"], resume_text, "applied", datetime.utcnow().isoformat()))
        flash("Application submitted.")
        return redirect(url_for("manage"))
    return render_template("apply.html", internship=internship)

@app.route("/manage")
def manage():
    user = get_current_user()
    if not user:
        flash("Please login.")
        return redirect(url_for("login"))
    if user.get("role") == "company":
        rows = query_all("SELECT * FROM internships WHERE company_id = ? ORDER BY created_at DESC", (user["id"],))
        internships_list = [dict(r) for r in rows] if rows else []
        return render_template("manage.html", internships=internships_list, applications=[])
    elif user.get("role") == "admin":
        internships_rows = query_all("SELECT i.*, u.full_name as company_name FROM internships i LEFT JOIN users u ON i.company_id = u.id ORDER BY i.created_at DESC")
        internships_list = [dict(r) for r in internships_rows] if internships_rows else []
        apps_rows = query_all("""SELECT a.id, a.internship_id, a.student_id, a.resume_text, a.status,
                                 i.title as internship_title, u.username as student_username, u.full_name as student_name
                                 FROM applications a
                                 LEFT JOIN internships i ON a.internship_id = i.id
                                 LEFT JOIN users u ON a.student_id = u.id
                                 ORDER BY a.applied_at DESC""")
        applications = [dict(r) for r in apps_rows] if apps_rows else []
        return render_template("manage.html", internships=internships_list, applications=applications)
    else:
        apps_rows = query_all("""SELECT a.*, i.title as internship_title, u.full_name as company_name
                                FROM applications a
                                LEFT JOIN internships i ON a.internship_id = i.id
                                LEFT JOIN users u ON i.company_id = u.id
                                WHERE a.student_id = ?
                                ORDER BY a.applied_at DESC""", (user["id"],))
        applications = [dict(r) for r in apps_rows] if apps_rows else []
        return render_template("manage.html", internships=[], applications=applications)

@app.route("/update_application/<int:app_id>", methods=["POST"])
def update_application(app_id):
    user = get_current_user()
    if not user or user.get("role") not in ("company","admin"):
        flash("Not authorized.")
        return redirect(url_for("manage"))
    status = request.form.get("status","applied")
    execute("UPDATE applications SET status = ? WHERE id = ?", (status, app_id))
    flash("Application updated.")
    return redirect(url_for("manage"))

@app.route("/predict", methods=["POST"])
def predict():
    description = request.form.get("description", "").strip()
    if not description:
        flash("Please paste the internship description before checking.")
        return redirect(url_for("index"))

    flag, prob_raw, reason = predict_flag_and_prob(description)

    # produce integer percent safely
    try:
        prob_pct = int(round(float(prob_raw) * 100))
    except Exception:
        try:
            prob_pct = int(round(float(prob_raw)))
        except Exception:
            prob_pct = 0

    recent_rows = query_all("SELECT i.*, u.full_name as company_name FROM internships i LEFT JOIN users u ON i.company_id = u.id ORDER BY created_at DESC LIMIT 8")
    recent = [dict(r) for r in recent_rows] if recent_rows else []
    return render_template("index.html", recent=recent, description=description, flag=flag, prob=prob_pct, prob_raw=prob_raw, reason=reason, posting_id=None)



# @app.route("/reports")
# def reports():
#     reports = Reports.query.all() 
#     rows = query_all("SELECT skills_required FROM internships WHERE skills_required IS NOT NULL AND trim(skills_required) != ''")
#     skills = {}
#     for r in rows:
#         txt = r["skills_required"] or ""
#         for s in re.split(r"[,\n;]+", txt):
#             s = s.strip().lower()
#             if not s:
#                 continue
#             skills[s] = skills.get(s, 0) + 1
#     top_skills = sorted(skills.items(), key=lambda x: -x[1])[:10]
#     top_companies = query_all("SELECT u.full_name, COUNT(i.id) as cnt FROM internships i LEFT JOIN users u ON i.company_id = u.id GROUP BY i.company_id ORDER BY cnt DESC LIMIT 10")
#     total_apps_row = query_one("SELECT COUNT(*) as cnt FROM applications")
#     total_apps = total_apps_row["cnt"] if total_apps_row else 0
#     return render_template("reports.html", top_skills=top_skills, top_companies=top_companies, total_apps=total_apps)

# @app.route("/recommend", methods=["GET","POST"])
# def recommend():
#     user = get_current_user()
#     input_text = ""
#     recs = []
#     if request.method == "POST":
#         input_text = request.form.get("resume_text","").strip()
#     else:
#         if user and user.get("skills"):
#             input_text = user.get("skills","")
#     try:
#         if recommend_for_text and input_text:
#             recs = recommend_for_text(input_text, topn=7)
#         else:
#             recs = []
#     except Exception:
#         traceback.print_exc()
#         recs = []
#     return render_template("recommend.html", recs=recs, input_text=input_text)

@app.route("/admin/reports")
def admin_reports():
    user = get_current_user()
    if not user or user.get("role") != "admin":
        flash("Admin access required.")
        return redirect(url_for("login"))
    rows = query_all("""SELECT r.id, r.posting_id, r.user_feedback AS feedback, r.reason, r.reporter_id, r.created_at,
                               u.username as reporter_username, i.title as internship_title
                        FROM reports r
                        LEFT JOIN users u ON r.reporter_id = u.id
                        LEFT JOIN internships i ON r.posting_id = i.id
                        ORDER BY r.created_at DESC""")
    reports = [dict(r) for r in rows] if rows else []
    return render_template("admin_reports.html", reports=reports)


@app.route("/ping")
def ping():
    return "pong"

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.route("/_debug_reports")
def _debug_reports():
    rows = query_all("SELECT id, posting_id, user_feedback, reason, reporter_id, created_at FROM reports ORDER BY id DESC LIMIT 50")
    return {"reports":[dict(r) for r in rows]}


if __name__ == "__main__":
    # ensure DB file exists
    os.makedirs(DB_DIR, exist_ok=True)
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        conn.close()
    app.run(debug=True, host="127.0.0.1", port=5000)







# from flask import Flask, render_template, request, redirect, url_for, flash
# from flask_sqlalchemy import SQLAlchemy
# from datetime import datetime
# import os

# app = Flask(__name__)
# app.config['SECRET_KEY'] = 'change-this-secret-key'

# # ---- DATABASE CONFIG ----
# basedir = os.path.abspath(os.path.dirname(__file__))
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'interncheck.db')
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# db = SQLAlchemy(app)


# # ---- DATABASE MODELS ----
# class Report(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     company = db.Column(db.String(200), nullable=False)
#     title = db.Column(db.String(200), nullable=False)
#     description = db.Column(db.Text, nullable=False)
#     reporter_email = db.Column(db.String(200))
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#     score = db.Column(db.Float)           # optional: ML score
#     is_fake = db.Column(db.Boolean)       # optional: label

#     def __repr__(self):
#         return f'<Report {self.id} - {self.company}>'


# # ---- ROUTES ----

# @app.route('/')
# def home():
#     return render_template('index.html')


# @app.route('/report', methods=['GET', 'POST'])
# def report():
#     """Page where user submits a fake internship report."""
#     if request.method == 'POST':
#         company = request.form.get('company', '').strip()
#         title = request.form.get('title', '').strip()
#         description = request.form.get('description', '').strip()
#         reporter_email = request.form.get('email', '').strip()

#         if not company or not title or not description:
#             flash('Please fill all required fields.', 'danger')
#             return redirect(url_for('report'))

#         new_report = Report(
#             company=company,
#             title=title,
#             description=description,
#             reporter_email=reporter_email or None
#         )

#         # TODO: call your ML model here to predict score / fake / genuine
#         # new_report.score = predicted_score
#         # new_report.is_fake = is_fake_bool

#         db.session.add(new_report)
#         db.session.commit()
#         flash('Thank you! Your report has been submitted.', 'success')
#         return redirect(url_for('reports'))

#     return render_template('report.html')


# @app.route('/reports')
# def reports():
#     """
#     Show all reports that are stored in the database.
#     This was the part causing trouble: make sure we query
#     and pass `reports` into the template.
#     """
#     all_reports = Report.query.order_by(Report.created_at.desc()).all()
#     return render_template('reports.html', reports=all_reports)


# @app.route('/internships')
# def internships():
#     """Dummy page – you can later fetch real internships here."""
#     return render_template('internships.html')

# @app.route('/recommend')
# def recommend():
#     # Later you will put your ML prediction logic here
#     return render_template('recommend.html')


# @app.route('/post-internship', methods=['GET', 'POST'])
# def post_internship():
#     """Company can post internships – implement DB model later."""
#     if request.method == 'POST':
#         flash('Internship posting feature coming soon.', 'info')
#         return redirect(url_for('post_internship'))
#     return render_template('post_internship.html')


# # ---- MAIN ----
# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all()
#     app.run(debug=True)
