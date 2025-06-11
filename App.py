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
    get_applicant_user,
    get_admin_user,
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
)

# from flask_sqlalchemy import SQLAlchemy
from Validation import generate_captcha_code, generate_captcha_image
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import config
from search_nlp import Extract_filter
# from dotenv import load_dotenv
import os

app = Flask(__name__)
#initializing the limiter
limiter = Limiter(
    app = app,
    key_func=get_remote_address,
    default_limits=["200 per day","50 per hour"]
)

app.secret_key = os.getenv("SECRET_KEY")
app.config.from_object(config)

Talisman(app, content_security_policy=None)  # Basic protection

# db = SQLAlchemy(app)   # This is used to initialize just after creating the app
init_db(app)  # To explicitly intialize the database


@app.route("/")
def Start():
    return render_template("Start_App.html")


@app.route("/login/jobseeker", methods=["GET", "POST"])
@limiter.limit("50 per minute") 
def Login_user():
    # now i will check username and login Credentials
    if request.method == "POST":
        if (
            "captcha" in session
            and request.form["captcha"].upper() == session["captcha"]
        ):
            username = request.form["username"]
            password = request.form["password"]

            user_applicant = get_applicant_user(username, password)

            if user_applicant:
                session.clear()    # Clear any previous session data
                session["username"] = username    # Store new username in session
                session["role"] = user_applicant["role"]
                if user_applicant["role"] == "applicant":
                    return redirect(url_for("applicant_dashboard"))

            # if user_applicant is not present in database
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
@limiter.limit("3 per minute") 
def Login_company():
    # now i will check Company_name and login Credentials
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
                    flash("your company is not verified yet!")
                    return redirect(url_for("Login_company"))
            else:
                # if company data is not present in database
                flash("Your company, not contracted yet!")
                return redirect(url_for("Login_company"))
        else:
            flash("Captcha is incorrect!")
            return redirect(url_for("Login_company"))
    else:
        captcha_code = generate_captcha_code()
        session["captcha"] = captcha_code
        return render_template("Company_Login.html")


@app.route("/comp_sign_up", methods=["GET", "POST"])
@limiter.limit("1 per minute") 
def comp_sign_up():
    data = request.form.to_dict()
    if data:
        add_company_to_db(data)
        flash("Company detail's sent for verification!")
        return redirect(url_for("Login_company"))
    return render_template("sign_up_comp.html")


@app.route("/login/admin", methods=["GET", "POST"])
@limiter.limit("10 per hour") 
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

            # if admin data is not present in database
            flash("Admin data in-correct!")
            return redirect(url_for("Login_admin"))
        else:
            flash("Captcha is incorrect!")
            return redirect(url_for("Login_admin"))
    else:
        captcha_code = generate_captcha_code()
        session["captcha"] = captcha_code
        return render_template("admin_login.html")


@app.route("/captcha_image")
def captcha_image():
    captcha_code = session["captcha"]
    img_buf = generate_captcha_image(captcha_code)
    return send_file(img_buf, mimetype="image/png")


@app.route("/Applicant/dashboard", methods=["GET"])
def applicant_dashboard():
    if "username" in session and session["role"] == "applicant":
        jobs = load_jobs_from_db()
        return render_template("applicant_dash.html", jobs=jobs)
    return redirect(url_for("Login_user"))


@app.route("/Admin/dashboard", methods=["GET"])
def admin_dashboard():
    if "adm_name" in session and session["role"] == "admin":
        job_titles = [job["title"] for job in get_applicants_count()]
        apl_count_per_job = [job["Applicant_count"] for job in get_applicants_count()]
        total_applicants = sum(apl_count_per_job)
        total_jobs = len(load_jobs_from_db())
        total_user = get_user_count()
        unverified_comp = get_Unverified_companies()
        return render_template(
            "admin_dash.html",
            job_titles=job_titles,
            applicants_count=apl_count_per_job,
            total_jobs=total_jobs,
            total_applicants=total_applicants,
            total_user=total_user,
            unverified_comp=unverified_comp,
        )
    return redirect(url_for("Login_admin"))


@app.route("/admin/company_verification/<int:company_id>", methods=["POST"])
def company_verification(company_id):
    return jsonify(verify_company(company_id))


@app.route("/Company/dashboard", methods=["GET"])
def company_dashboard():
    if "comp_name" in session and session["role"] == "company" and "Comp_id" in session:
        total_jobs,Appl_Detail = get_company_job_count(session["Comp_id"])
        total_appl = sum([job['Appl_C'] for job in Appl_Detail])
        Appl_Detail.append(total_appl)
        AD = get_weekly_applications_by_company(session["Comp_id"])  # <== new logic
        return render_template("company_dash.html", jobs=total_jobs, AD=AD)
    return redirect(url_for("Login_company"))


@app.route("/Company/postings", methods=["GET", "POST"])
def company_postings():
    if "comp_name" in session and session["role"] == "company":
        id = session.get("Comp_id")
        if request.method == "POST":
            data = request.form.to_dict()
            if id is not None:
               add_job_to_db(data,id)     #job is listed in database
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


# this route is for filter the job
@app.route("/filter", methods=["POST"])
def filter_job():
    data = request.form.get("search")
    if data:
        filter_list = Extract_filter(data)
    else:
        filter_list = request.form.to_dict()

    jobs = load_filter_jobs_from_db(**filter_list)
    if jobs:
        return render_template("applicant_dash.html", jobs=jobs)
    else:
        # flash("No jobs found with the given filter!")
        jobs = []
        return render_template("applicant_dash.html", jobs=jobs)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("Start"))


# API Endpoints for fetching jobs and job details Via react or flutter apps
@app.route("/api/jobs")
def api_jobs():
    jobs = load_jobs_from_db()
    return jsonify(jobs)

@app.route("/api/jobs/<int:id>")
def api_job(id):
    job = load_job_from_db(id)
    if job:
        return jsonify(job)
    return jsonify({"error": "Job not found"}), 404


if __name__ == "__main__":
    print(__name__)
    app.run(host="0.0.0.0", debug=True)
# This is the main entry point of the application.
