import os
import sqlite3
import json
import csv
import io

from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

from gail_model import RiskFactors, calculate_gail_risk
from chatbot.database import init_chat_tables
from chatbot.routes import chat_bp

app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("FLASK_SECRET_KEY is missing from .env")

DATABASE = "database.db"
app.config["DATABASE"] = DATABASE

app.config["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
app.config["GROQ_MODEL"] = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b"
)

if not app.config["GROQ_API_KEY"]:
    raise RuntimeError("GROQ_API_KEY is missing from .env")

app.register_blueprint(chat_bp)

# Create database and users table
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)


        # Add patient data consent column if it does not exist
        user_columns = [
            row[1] for row in
            conn.execute("PRAGMA table_info(users)")
        ]

        if "patient_data_consent" not in user_columns:
            conn.execute("""
                ALTER TABLE users
                ADD COLUMN patient_data_consent
                INTEGER NOT NULL DEFAULT 0
            """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS risk_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                answers TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'completed',

                FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS self_exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                exam_date TEXT NOT NULL,
                status TEXT NOT NULL,
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
            )
        """)

        init_chat_tables(conn)

                # Add observations column if it does not exist
        columns = [
            row[1] for row in
            conn.execute("PRAGMA table_info(self_exams)")
        ]

        if "observations" not in columns:
            conn.execute("""
                ALTER TABLE self_exams
                ADD COLUMN observations TEXT DEFAULT '{}'
            """)

# home page
@app.route("/")
def home():
    return render_template("login.html")

@app.route("/main")
def main():
    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]

    with sqlite3.connect(DATABASE) as conn:
        assessment = conn.execute("""
            SELECT id
            FROM risk_assessments
            WHERE user_id = ?
            AND status = 'completed'
            LIMIT 1
        """, (user_id,)).fetchone()

    has_completed_assessment = assessment is not None

    return render_template(
        "main.html",
        has_completed_assessment=has_completed_assessment
    )

@app.route("/self_examination")
def self_examination():
    if "user_id" not in session:
        return redirect("/")
    return render_template("self_examination.html")

@app.route("/reports")
def reports():

    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]

    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row

        # تقارير Gail
        assessment_rows = conn.execute("""
            SELECT id, answers, created_at, status
            FROM risk_assessments
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,)).fetchall()

        # سجلات الفحص الذاتي
        self_exam_rows = conn.execute("""
            SELECT id, exam_date, observations, notes, created_at, status
            FROM self_exams
            WHERE user_id = ?
            ORDER BY exam_date DESC
        """, (user_id,)).fetchall()

    assessments = []

    for row in assessment_rows:
        assessments.append({
            "id": row["id"],
            "answers": json.loads(row["answers"]),
            "created_at": row["created_at"],
            "status": row["status"]
        })

    self_exams = []

    for row in self_exam_rows:
        self_exams.append({
            "id": row["id"],
            "exam_date": row["exam_date"],
            "observations": json.loads(row["observations"] or "{}"),
            "notes": row["notes"] or "",
            "created_at": row["created_at"],
            "status": row["status"]
        })

    return render_template(
        "reports.html",
        assessments=assessments,
        self_exams=self_exams
    )


@app.route("/reports/<int:assessment_id>")
def report_details(assessment_id):
    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]

    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row

        report = conn.execute("""
            SELECT id, answers, created_at, status, gail_result
            FROM risk_assessments
            WHERE id = ? AND user_id = ?
        """, (assessment_id, user_id)).fetchone()

    if report is None:
        return redirect("/reports")

    report_data = {
        "id": report["id"],
        "answers": json.loads(report["answers"]),
        "created_at": report["created_at"],
        "status": report["status"],
        "gail_result": (
            json.loads(report["gail_result"])
            if report["gail_result"] else None
        )
    }

    return render_template(
        "report_details.html",
        report=report_data
    )  


@app.route("/self-exams/<int:exam_id>")
def self_exam_details(exam_id):

    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]

    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row

        exam = conn.execute("""
            SELECT id, exam_date, observations, notes, status
            FROM self_exams
            WHERE id = ? AND user_id = ?
        """, (exam_id, user_id)).fetchone()

    if exam is None:
        return redirect("/reports")

    exam_data = {
        "id": exam["id"],
        "exam_date": exam["exam_date"],
        "observations": json.loads(exam["observations"] or "{}"),
        "notes": exam["notes"] or "",
        "status": exam["status"]
    }

    return render_template(
        "report_details.html",
        report_type="self_exam",
        exam=exam_data
    )


@app.route("/risk-assessment")
def risk_assessment():
    if "user_id" not in session:
        return redirect("/")
    return render_template("risk_assessment.html") 

@app.route("/tracker")
def tracker():
    if "user_id" not in session:
        return redirect("/")

    return render_template("tracker.html")          


@app.route("/api/self-exams", methods=["POST"])
def save_self_exam():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please log in first."
        }), 401

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Invalid exam data."
        }), 400

    exam_date = data.get("exam_date")
    observations = data.get("observations", {})
    notes = data.get("notes", "")

    # Date is required, but the user chooses it manually
    if not isinstance(exam_date, str) or not exam_date.strip():
        return jsonify({
            "success": False,
            "message": "Please select the examination date."
        }), 400

    # Validate date format
    try:
        from datetime import date
        date.fromisoformat(exam_date)
    except ValueError:
        return jsonify({
            "success": False,
            "message": "Invalid examination date."
        }), 400

    if not isinstance(observations, dict):
        return jsonify({
            "success": False,
            "message": "Invalid observations."
        }), 400

    if not isinstance(notes, str):
        return jsonify({
            "success": False,
            "message": "Invalid notes."
        }), 400

    observations_json = json.dumps(
        observations,
        ensure_ascii=False
    )

    with sqlite3.connect(DATABASE) as conn:

        cursor = conn.execute("""
            INSERT INTO self_exams
            (user_id, exam_date, status, notes, observations)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            exam_date,
            "recorded",
            notes.strip(),
            observations_json
        ))

        exam_id = cursor.lastrowid

    return jsonify({
        "success": True,
        "message": "Self-examination saved successfully.",
        "exam_id": exam_id
    }), 201


@app.route("/api/self-exams", methods=["GET"])
def get_self_exams():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please log in first."
        }), 401

    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row

        exams = conn.execute("""
            SELECT id, exam_date, status
            FROM self_exams
            WHERE user_id = ?
            ORDER BY exam_date DESC, id DESC
        """, (session["user_id"],)).fetchall()

    exams_data = [
        {
            "id": exam["id"],
            "exam_date": exam["exam_date"],
            "status": exam["status"]
        }
        for exam in exams
    ]

    return jsonify({
        "success": True,
        "exams": exams_data
    }), 200

@app.route("/chatbot")
def chatbot():
    if "user_id" not in session:
        return redirect("/")
    return render_template("chatbot.html")

# Register new user
@app.route("/register", methods=["POST"])
def register():

    first_name = request.form.get("first name", "").strip()
    last_name = request.form.get("last name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    # Check empty fields
    if not all([first_name, last_name, email, password]):
        return jsonify({
            "success": False,
            "message": "Please fill in all fields."
        }), 400

    # Check password length
    if len(password) < 8:
        return jsonify({
            "success": False,
            "message": "Password must be at least 8 characters."
        }), 400

    # Encrypt password
    password_hash = generate_password_hash(password)

    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.execute("""
                INSERT INTO users
                (first_name, last_name, email, password_hash)
                VALUES (?, ?, ?, ?)
            """, (first_name, last_name, email, password_hash))

        return jsonify({
            "success": True,
            "message": "Account created successfully!"
        })

    except sqlite3.IntegrityError:
        return jsonify({
            "success": False,
            "message": "This email is already registered."
        }), 409

# Login existing user
@app.route("/login", methods=["POST"])
def login():

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Please enter your email and password."
        }), 400

    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

    if user is None:
        return jsonify({
            "success": False,
            "message": "Email not found."
        }), 404

    if not check_password_hash(user["password_hash"], password):
        return jsonify({
            "success": False,
            "message": "Incorrect password."
        }), 401

    session["user_id"] = user["id"]

    return jsonify({
        "success": True,
        "message": "Login successful!"
    })


def map_answers_to_gail(answers):
    """Convert Miria questionnaire answers into Gail model inputs."""

    age = int(answers["3"])

    # Gail model does not support ages below 20.
    if age < 20:
        return None

    # Previous benign biopsies
    biopsy_answer = answers["5"]

    if biopsy_answer == "نعم":
        biopsy_map = {
            "خزعة واحدة": 1,
            "خزعتان أو أكثر": 2
        }
        biopsies = biopsy_map[answers["6"]]

        atypical_map = {
            "لا": 0,
            "نعم": 1,
            "لا أعلم": 99
        }
        atypical = atypical_map[answers["7"]]

    elif biopsy_answer == "لا":
        biopsies = 0
        atypical = 99

    elif biopsy_answer == "لا أعلم":
        biopsies = 99
        atypical = 99

    else:
        raise ValueError("Invalid biopsy answer.")

    # Age at menarche
    menarche_map = {
        "7–11 سنة": 11,
        "12–13 سنة": 13,
        "14 سنة أو أكثر": 14
    }
    menarche = menarche_map[answers["8"]]

    # Age at first live birth
    birth_map = {
        "لم يسبق لي الإنجاب": 98,
        "أقل من 20 سنة": 19,
        "20–24 سنة": 20,
        "25–29 سنة": 25,
        "30 سنة أو أكثر": 30
    }
    first_birth = birth_map[answers["9"]]

    # First-degree relatives
    relatives_map = {
        "لا يوجد": 0,
        "واحدة": 1,
        "اثنتان أو أكثر": 2,
        "لا أعلم": 99
    }
    relatives = relatives_map[answers["10"]]

    return RiskFactors(
        current_age=age,
        projection_age=age + 5,
        biopsies=biopsies,
        atypical_hyperplasia=atypical,
        menarche_age=menarche,
        first_live_birth_age=first_birth,
        first_degree_relatives=relatives
    )


@app.route("/api/risk-assessment", methods=["POST"])
def save_risk_assessment():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please log in first."
        }), 401

    data = request.get_json(silent=True)

    if not data or not isinstance(data.get("answers"), dict):
        return jsonify({
            "success": False,
            "message": "Invalid assessment data."
        }), 400

    answers = data["answers"]

    if not answers:
        return jsonify({
            "success": False,
            "message": "No answers provided."
        }), 400

    # Calculate Gail risk
    try:
        gail_input = map_answers_to_gail(answers)

        gail_result = None

        if gail_input is not None:
            result = calculate_gail_risk(gail_input)

            gail_result = {
                "relative_risk_under_50": result.relative_risk_under_50,
                "relative_risk_50_plus": result.relative_risk_50_plus,
                "absolute_risk_percent": result.absolute_risk_percent,
                "projection_years": result.projection_years,
                "reference_population": result.reference_population
            }

    except (KeyError, ValueError, TypeError) as error:
        return jsonify({
            "success": False,
            "message": f"Invalid assessment answers: {error}"
        }), 400

    answers_json = json.dumps(answers, ensure_ascii=False)

    gail_json = (
        json.dumps(gail_result, ensure_ascii=False)
        if gail_result is not None else None
    )

    with sqlite3.connect(DATABASE) as conn:

        # Add the new column without deleting existing records
        columns = [
            row[1] for row in
            conn.execute("PRAGMA table_info(risk_assessments)")
        ]

        if "gail_result" not in columns:
            conn.execute("""
                ALTER TABLE risk_assessments
                ADD COLUMN gail_result TEXT
            """)

        cursor = conn.execute("""
            INSERT INTO risk_assessments
            (user_id, answers, gail_result)
            VALUES (?, ?, ?)
        """, (
            session["user_id"],
            answers_json,
            gail_json
        ))

        assessment_id = cursor.lastrowid

    return jsonify({
        "success": True,
        "message": "Assessment saved successfully!",
        "assessment_id": assessment_id,
        "gail_result": gail_result
    })


@app.route("/export-assessments")
def export_assessments():

    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]

    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
            SELECT
                users.id AS user_id,
                users.first_name,
                users.last_name,
                users.email,
                risk_assessments.id AS assessment_id,
                risk_assessments.answers,
                risk_assessments.created_at,
                risk_assessments.status

            FROM risk_assessments

            JOIN users
            ON users.id = risk_assessments.user_id

            WHERE users.id = ?

            ORDER BY risk_assessments.created_at DESC
        """, (user_id,)).fetchall()

    # Convert JSON answers into separate columns
    assessments = []
    answer_columns = set()

    for row in rows:
        answers = json.loads(row["answers"])

        answer_columns.update(answers.keys())

        assessment = {
            "user_id": row["user_id"],
            "first_name": row["first_name"],
            "last_name": row["last_name"],
            "email": row["email"],
            "assessment_id": row["assessment_id"],
            "created_at": row["created_at"],
            "status": row["status"]
        }

        assessment.update(answers)
        assessments.append(assessment)

    # Prepare CSV
    output = io.StringIO()
    output.write("\ufeff")

    columns = [
        "user_id",
        "first_name",
        "last_name",
        "email",
        "assessment_id",
        "created_at",
        "status"
    ] + sorted(answer_columns)

    writer = csv.DictWriter(
        output,
        fieldnames=columns,
        extrasaction="ignore"
    )

    writer.writeheader()
    writer.writerows(assessments)

    from flask import Response

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
                "attachment; filename=my_assessments.csv"
        }
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5001)