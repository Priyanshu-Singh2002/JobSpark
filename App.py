import os
from urllib.parse import urlparse

from dotenv import load_dotenv
from search_nlp import Extract_filter

load_dotenv()

import config

from flask import (
    Flask,
    render_template,
    request,
    session,
    send_file,
    redirect,
    url_for,
    flash,
    jsonify,
)

from DB import (
    init_db,
    load_jobs_from_db,
    load_job_from_db,
    Add_Applicant,
    get_admin_user,
    get_applicant_user,
    get_company_data,
    add_user_to_db,
    add_company_to_db,
    add_job_to_db,
    get_applicants_count,
    get_user_count,
    get_company_job_count,
    get_Unverified_companies,
    get_weekly_applications_by_company,
    load_filter_jobs_from_db,
    verify_company,
    save_job,
    get_saved_jobs,
    remove_saved_job,
    get_all_user_emails,
    get_all_company_emails,
    get_all_applicant_emails,
)

from Validation import generate_captcha_code, generate_captcha_image
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from email_utils import send_bulk_email_smtp

app = Flask(__name__)

# Load config properly (ONLY this, no override later)
app.config.from_object(config.Config)

# Debug (remove later)
# print("ENV DATABASE_URI:", os.getenv("DATABASE_URI"))
# print("FINAL CONFIG DB URI:", app.config.get("SQLALCHEMY_DATABASE_URI"))

# Security
Talisman(app, content_security_policy=None)

# Rate Limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "150 per hour"],
)

# Initialize DB
init_db(app)

# ---------------- ROUTES ----------------#


@app.route("/captcha_image")
def captcha_image():
    captcha_code = session["captcha"]
    img_buf = generate_captcha_image(captcha_code)
    return send_file(img_buf, mimetype="image/png")


@app.route("/")
def Start():
    return render_template("Start_App.html")


@app.route("/login/jobseeker", methods=["GET", "POST"])
@limiter.limit("50 per minute")
def Login_user():
    if request.method == "POST":
        if (
            "captcha" in session
            and request.form["captcha"].upper() == session["captcha"]
        ):
            username = request.form["username"]
            password = request.form["password"]

            user_applicant = get_applicant_user(username, password)

            if user_applicant:
                session.clear()
                session["user_id"] = user_applicant["id"]
                session["username"] = username
                session["role"] = user_applicant["role"]
                session["name"] = user_applicant["name"]
                session["profile_pic"] = user_applicant["profile_pic"]

                if user_applicant["role"] == "applicant":
                    return redirect(url_for("applicant_dashboard"))

            flash("Username or Password is incorrect!")
            return redirect(url_for("Login_user"))
        else:
            flash("Captcha is incorrect!")
            return redirect(url_for("Login_user"))
    else:
        captcha_code = generate_captcha_code()
        session["captcha"] = captcha_code
        return render_template("User_Login.html")


@app.route("/user_sign_up", methods=["GET", "POST"])
@limiter.limit("3 per minute")
def user_sign_up():
    data = request.form.to_dict()
    if data:
        add_user_to_db(data)
        flash("User Created Successfully!")
        return redirect(url_for("Login_user"))
    return render_template("sign_up_user.html")


@app.route("/login/company", methods=["GET", "POST"])
@limiter.limit("30 per minute")
def Login_company():
    if request.method == "POST":
        if (
            "captcha" in session
            and request.form["captcha"].upper() == session["captcha"]
        ):
            company = request.form["company_name"]
            password = request.form["password"]

            company_data = get_company_data(company, password)

            if company_data:
                if company_data["status"] == "verified":
                    session["comp_name"] = company
                    session["role"] = company_data["role"]
                    session["Comp_id"] = company_data["company_id"]
                    return redirect(url_for("company_dashboard"))
                else:
                    flash("Your company is not verified yet!")
                    return redirect(url_for("Login_company"))
            else:
                flash("Company not found!")
                return redirect(url_for("Login_company"))
        else:
            flash("Captcha is incorrect!")
            return redirect(url_for("Login_company"))
    else:
        captcha_code = generate_captcha_code()
        session["captcha"] = captcha_code
        return render_template("Company_Login.html")


@app.route("/comp_sign_up", methods=["GET", "POST"])
def comp_sign_up():
    data = request.form.to_dict()
    if data:
        add_company_to_db(data)
        flash("Company details sent for verification!")
        return redirect(url_for("Login_company"))
    return render_template("sign_up_comp.html")


@app.route("/login/admin", methods=["GET", "POST"])
@limiter.limit("100 per hour")
def Login_admin():
    if request.method == "POST":
        if (
            "captcha" in session
            and request.form["captcha"].upper() == session["captcha"]
        ):
            admin_name = request.form["username"]
            password = request.form["password"]

            user_admin = get_admin_user(admin_name, password)

            if user_admin:
                session["adm_name"] = admin_name
                session["role"] = user_admin["role"]

                if user_admin["role"] == "admin":
                    return redirect(url_for("admin_dashboard"))

            flash("Invalid admin credentials!")
            return redirect(url_for("Login_admin"))
        else:
            flash("Captcha is incorrect!")
            return redirect(url_for("Login_admin"))
    else:
        captcha_code = generate_captcha_code()
        session["captcha"] = captcha_code
        return render_template("admin_login.html")


@app.route("/Applicant/dashboard")
def applicant_dashboard():
    if "username" in session and session["role"] == "applicant":
        session.pop("job_filter_form", None)
        jobs = load_jobs_from_db()
        return render_template("applicant_dash.html", jobs=jobs, form_values=None)
    return redirect(url_for("Login_user"))


@app.route("/Admin/dashboard")
def admin_dashboard():
    if "adm_name" in session and session["role"] == "admin":
        per_job = list(get_applicants_count())
        # Disambiguate duplicate titles (multiple postings) for chart labels
        job_titles = [
            f'{j["title"]} · #{j["job_id"]}' for j in per_job
        ]
        apl_count_per_job = [j["Applicant_count"] for j in per_job]

        return render_template(
            "admin_dash.html",
            job_titles=job_titles,
            applicants_count=apl_count_per_job,
            total_jobs=len(load_jobs_from_db()),
            total_applicants=sum(apl_count_per_job),
            total_user=get_user_count(),
            unverified_comp=get_Unverified_companies(),
        )
    return redirect(url_for("Login_admin"))


@app.route("/bulk-email", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def bulk_email():
    if "adm_name" not in session or session.get("role") != "admin":
        return redirect(url_for("Login_admin"))

    if request.method == "GET":
        required = ["SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "MAIL_FROM"]
        missing = [k for k in required if not app.config.get(k)]
        return render_template(
            "bulk_email.html",
            smtp_missing=missing,
            mail_from=app.config.get("MAIL_FROM") or "",
        )

    audience = (request.form.get("audience") or "").strip()
    subject = (request.form.get("subject") or "").strip()
    body = (request.form.get("body") or "").strip()

    if not subject or not body:
        flash("Subject and message are required.", "error")
        return redirect(url_for("bulk_email"))

    if audience == "users":
        recipients = get_all_user_emails()
    elif audience == "applicants":
        recipients = get_all_applicant_emails()
    elif audience == "companies_verified":
        recipients = get_all_company_emails(include_unverified=False)
    elif audience == "companies_all":
        recipients = get_all_company_emails(include_unverified=True)
    else:
        flash("Invalid audience selected.", "error")
        return redirect(url_for("bulk_email"))

    try:
        sent, failed = send_bulk_email_smtp(
            smtp_host=app.config.get("SMTP_HOST"),
            smtp_port=app.config.get("SMTP_PORT"),
            smtp_username=app.config.get("SMTP_USERNAME"),
            smtp_password=app.config.get("SMTP_PASSWORD"),
            smtp_use_tls=app.config.get("SMTP_USE_TLS", True),
            mail_from=app.config.get("MAIL_FROM"),
            recipients=recipients,
            subject=subject,
            body=body,
        )
    except Exception as e:
        flash(f"Email sending failed: {e}", "error")
        return redirect(url_for("bulk_email"))

    flash(f"Bulk email complete. Sent: {sent}, Failed: {failed}", "success")
    return redirect(url_for("bulk_email"))


@app.route("/admin/company_verification/<int:company_id>", methods=["POST"])
def company_verification(company_id):
    return jsonify(verify_company(company_id))


@app.route("/Company/dashboard", methods=["GET"])
def company_dashboard():
    if "comp_name" in session and session["role"] == "company" and "Comp_id" in session:
        total_jobs, Appl_Detail = get_company_job_count(session["Comp_id"])
        total_appl = sum([job["Appl_C"] for job in Appl_Detail])
        Appl_Detail.append({"title": "Total_Application", "T_ApplCount": total_appl})
        AWD = get_weekly_applications_by_company(session["Comp_id"])  # <== new logic
        return render_template(
            "company_dash.html", jobs=total_jobs, AWD=AWD, APL=total_appl
        )
    return redirect(url_for("Login_company"))


@app.route("/Company/postings", methods=["GET", "POST"])
def company_postings():
    if "comp_name" in session and session["role"] == "company":
        id = session.get("Comp_id")
        if request.method == "POST":
            data = request.form.to_dict()
            if id is not None:
                add_job_to_db(data, id)  # job is listed in database
                flash("Job Posted Successfully!")
                return redirect(url_for("company_postings"))
        else:
            return render_template("company_posting.html")
    return redirect(url_for("Login_company"))


@app.route("/jobs/<id>")
def job(id):
    job = load_job_from_db(id)
    if job:
        return render_template("job_desc.html", job=job)
    return "<h1>Job Not Found!</h1>", 404


# This is used when data is sent over a URL
""" @app.route('/jobs/<id>/apply')
def apply_job(id):
    data = request.args
    return jsonify(data) """


# This is used when data is sent over a form using POST method
@app.route("/jobs/<job_id>/apply", methods=["POST", "GET"])
def apply_job(job_id):
    data = request.form.to_dict()  # data comes from the application form
    job = load_job_from_db(job_id)
    Applicant = Add_Applicant(job_id, data)  # New Applicant Data is added to Database
    return render_template("Form_submission.html", job=job, Applicant=Applicant)


def _merge_job_filters(form_dict, search_text):
    """Form fields win over NLP when both are set; search supplements empty fields."""
    merged = dict(form_dict)
    merged.pop("search", None)
    q = (search_text or "").strip()
    if not q:
        return merged
    nlp = Extract_filter(q)
    for key, val in nlp.items():
        if val in (None, "", False):
            continue
        cur = merged.get(key)
        empty = cur in (None, "") or (
            isinstance(cur, str) and not str(cur).strip()
        )
        if empty:
            merged[key] = val
    return merged


# this route is for filter the job (POST/Redirect/GET so GET /filter is safe — no 405 on refresh)
@app.route("/filter", methods=["GET", "POST"])
def filter_job():
    if request.method == "POST":
        form = request.form.to_dict()
        search_q = (form.get("search") or "").strip()
        filter_list = _merge_job_filters(form, search_q)
        session["job_filter_form"] = form
        return redirect(url_for("filter_job"))

    form = session.get("job_filter_form")
    if not form:
        return redirect(url_for("applicant_dashboard"))
    search_q = (form.get("search") or "").strip()
    filter_list = _merge_job_filters(form, search_q)
    jobs = load_filter_jobs_from_db(**filter_list)
    if not jobs:
        jobs = []
    return render_template("applicant_dash.html", jobs=jobs, form_values=form)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("Start"))


# ---------------- API ---------------- #


@app.route("/api/jobs")
def api_jobs():
    return jsonify(load_jobs_from_db())


@app.route("/api/jobs/<int:id>")
def api_job(id):
    job = load_job_from_db(id)
    if job:
        return jsonify(job)
    return jsonify({"error": "Job not found"}), 404


def _redirect_after_bookmark():
    """POST-only routes (e.g. /filter) cannot be reopened via GET — avoid 405 on redirect."""
    ref = request.referrer
    if not ref:
        return redirect(url_for("applicant_dashboard"))
    path = urlparse(ref).path.rstrip("/") or "/"
    if path == "/filter":
        return redirect(url_for("saved_jobs"))
    return redirect(ref)


# Save Jobs or Book-Mark
@app.route("/save-job/<int:job_id>", methods=["GET"])
def save_job_route(job_id):

    if "username" not in session and "user_id" not in session:
        flash("Please login first", "warning")
        return redirect("/login/jobseeker")

    save_job(session["user_id"], job_id)

    flash("Job Saved Successfully", "success")

    return _redirect_after_bookmark()


@app.route("/saved-jobs")
def saved_jobs():

    if "username" not in session and "user_id" not in session:
        return redirect("/login/jobseeker")

    jobs = get_saved_jobs(session["user_id"])

    return render_template("saved_jobs.html", jobs=jobs)


@app.route("/remove-saved/<int:job_id>", methods=["GET"])
def remove_saved(job_id):

    remove_saved_job(session["user_id"], job_id)

    flash("Removed from Saved Jobs", "info")

    return _redirect_after_bookmark()

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)


