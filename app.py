from flask import Flask, render_template, request, redirect, session
from db import Base, engine, SessionLocal
from ai import analyze_resume
import models
import PyPDF2
import docx
import json

app = Flask(__name__)
app.secret_key = "1234msd1234"

Base.metadata.create_all(bind=engine)


# HOME

@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")

    return redirect("/login")


# SIGNUP

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if "user" in session:
        return redirect("/dashboard")

    db = SessionLocal()

    try:

        if request.method == "POST":

            email = request.form.get("email")
            password = request.form.get("password")

            existing_user = (
                db.query(models.User)
                .filter_by(email=email)
                .first()
            )

            if existing_user:
                return "User already exists"

            user = models.User(
                email=email,
                password=password
            )

            db.add(user)
            db.commit()

            return redirect("/login")

        return render_template("signup.html")

    finally:
        db.close()


# LOGIN

@app.route("/login", methods=["GET", "POST"])
def login():

    if "user" in session:
        return redirect("/dashboard")

    db = SessionLocal()

    try:

        if request.method == "POST":

            email = request.form.get("email")
            password = request.form.get("password")

            user = (
                db.query(models.User)
                .filter_by(
                    email=email,
                    password=password
                )
                .first()
            )

            if user:

                session["user"] = user.email

                return redirect("/dashboard")

            return "Invalid credentials"

        return render_template("login.html")

    finally:
        db.close()


# DASHBOARD

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():

    if "user" not in session:
        return redirect("/login")

    result = None

    if request.method == "POST":

        user_goal = request.form.get("role")
        resume_text = request.form.get("resume")

        file = request.files.get("file")


        # FILE HANDLING

        if file and file.filename != "":

            if file.filename.lower().endswith(".pdf"):

                try:

                    pdf_reader = PyPDF2.PdfReader(file)

                    text = ""

                    for page in pdf_reader.pages:
                        text += page.extract_text() or ""

                    resume_text = text

                except Exception as e:

                    result = {
                        "error": f"PDF error: {str(e)}"
                    }


            elif file.filename.lower().endswith(".docx"):

                try:

                    doc = docx.Document(file)

                    text = ""

                    for para in doc.paragraphs:
                        text += para.text + "\n"

                    resume_text = text

                except Exception as e:

                    result = {
                        "error": f"DOCX error: {str(e)}"
                    }


        # AI ANALYSIS

        if resume_text and user_goal:

            try:

                result = analyze_resume(
                    resume_text,
                    user_goal
                )


                # SAVE REPORT

                db = SessionLocal()

                try:

                    user = (
                        db.query(models.User)
                        .filter_by(email=session["user"])
                        .first()
                    )


                    report = models.Report(
                        user_id=user.id,
                        resume_text=resume_text,
                        result=json.dumps(result)
                    )


                    db.add(report)
                    db.commit()


                finally:

                    db.close()


            except Exception as e:

                result = {
                    "error": f"AI error: {str(e)}"
                }


    return render_template(
        "dashboard.html",
        user=session["user"],
        result=result
    )


# HISTORY

@app.route("/history")
def history():

    if "user" not in session:
        return redirect("/login")

    db = SessionLocal()

    try:

        user = (
            db.query(models.User)
            .filter_by(email=session["user"])
            .first()
        )


        reports = (
            db.query(models.Report)
            .filter_by(user_id=user.id)
            .all()
        )


        parsed_reports = []

        for r in reports:

            try:

                result = json.loads(r.result)

            except Exception:

                result = {}


            parsed_reports.append({
                "resume": r.resume_text,
                "result": result
            })


        return render_template(
            "history.html",
            reports=parsed_reports
        )

    finally:

        db.close()


# LOGOUT

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# MAIN

if __name__ == "__main__":
    app.run(debug=True)