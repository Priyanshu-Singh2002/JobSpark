from sqlalchemy import text, and_, or_
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta

db = SQLAlchemy()

from models import Application,Job,User,Admin,Company  # Import AFTER initializing `db`

def init_db(app):
    with app.app_context():
        db.init_app(app)    #Flask-SQLAlchemy method to bind app
        db.create_all()


# Function to load all jobs from the database
def load_jobs_from_db():
    with db.engine.connect() as conn:
        result = conn.execute(text("select * from jobs"))
        jobs = [dict(row) for row in result.mappings()]
    return jobs


# Function to load a single job from the database
def load_job_from_db(job_id):
    with db.engine.connect() as conn:
        result = conn.execute(
            text("select * from jobs where id = :val"), {"val": job_id}
        )
        job = [dict(row) for row in result.mappings()]
    if len(job) == 0:
        return None
    return job[0]


# function to add applicant data to the database
def Add_Applicant(Job_id, Applicant):
    new_applicant = Application(
        job_id=Job_id,
        full_name=Applicant["full_name"],
        email=Applicant["email"],
        phone=Applicant["phone"],
        linkedin=Applicant["linkedin"],
        education=Applicant["education"],
        work_experience=Applicant["work_experience"],
        resume=Applicant["resume"],
    )
    db.session.add(new_applicant)
    db.session.commit()
    return new_applicant


# funtion to enter and make user in the database
def add_user_to_db(user_data):
    new_user = User(
        username=user_data["username"],
        password=user_data["password"],
        name=user_data["name"],
        email=user_data["email"],
        phone=user_data["phone"],
        skills=user_data["skills"],
        experience=user_data["experience"],
        profile_pic=user_data["profile_pic"],
        resume=user_data["resume"],
    )
    db.session.add(new_user)
    db.session.commit()


# function to add company data to the database
def  add_company_to_db(company_data):
    new_company = Company(
        company_name=company_data["comp_name"],
        contact_email=company_data["email"],
        password=company_data["password"],
        website=company_data["website"]
    )
    
    db.session.add(new_company)
    db.session.commit()

def add_job_to_db(job_data,id):
    new_job = Job(
        title=job_data["title"],
        location=job_data["location"],  
        salary=job_data["salary"],
        currency=job_data["currency"],
        descriptions=job_data["descriptions"],
        requirements=job_data["requirements"],
        status=job_data["status"],
        posted_time=job_data["posted_time"],
        comp_id= id
    )

    db.session.add(new_job)
    db.session.commit()

# function to get user as per there role
def get_applicant_user(username, password):
    with db.engine.connect() as conn:
        result = conn.execute(
            text("select * from user where username = :user and password = :pass"),
            {"user": username, "pass": password}
        )
        A_user = result.mappings().fetchone()        
    return dict(A_user) if A_user else None

# function to get admin user
def get_admin_user(username, password):
    admin_user = db.session.query(Admin).filter_by(username = username, password = password).first()
    if admin_user:
      return admin_user.to_dict()
    return None

#function to get company data
def get_company_data(name, password):
    company = db.session.query(Company).filter_by(company_name = name, password = password).first()
    if company:
        return company.to_dict()
    return None


#function to verify the company
def verify_company(company_id: int):
    company = Company.query.get(company_id)
    if not company:
            return {"success": False, "message": "Company not found"}
    company.status = "verified"
    db.session.commit()
    return {"success": True}


#function to get all unverified company
def get_Unverified_companies():
    unverified_company = db.session.query(Company).filter(or_(Company.status == "pending" , Company.status == "inactive")).all()
    if unverified_company:
        return [company.to_dict() for company in unverified_company]
    return []
    
# Function to get count of total job of a company
def get_company_job_count(company_id):
    count = db.session.query(Job).filter_by(comp_id=company_id).count()  # it will gove total jobs from this company
    sql = text('''select J.title, count(*) as Appl_C from application 
               A INNER JOIN jobs J on A.job_id = J.id where J.comp_id = :C_ID
                group by A.job_id,J.title;''')
    result = db.session.execute(sql,{"C_ID":company_id})
    rows = result.mappings().all()
    return count,rows

        
#function to get Number of applicants for all job
def get_applicants_count():
    sql = text('select J.title, count(*) as Applicant_count from application A INNER JOIN jobs J on A.job_id = J.id group by A.job_id;')
    result = db.session.execute(sql)
    rows = result.mappings().all()
    return rows


#function to calculate the number of user using the JobSpark Application
def get_user_count():
    total_users = db.session.query(User).count()
    return total_users


def get_all_user_emails():
    emails = db.session.query(User.email).all()
    return [e[0] for e in emails if e and e[0]]


def get_all_company_emails(include_unverified: bool = False):
    q = db.session.query(Company.contact_email)
    if not include_unverified:
        q = q.filter(Company.status == "verified")
    emails = q.all()
    return [e[0] for e in emails if e and e[0]]


def get_all_applicant_emails():
    emails = db.session.query(Application.email).distinct().all()
    return [e[0] for e in emails if e and e[0]]


def _job_row_with_company(job):
    d = job.to_dict()
    co = getattr(job, "company", None)
    d["company_name"] = co.company_name if co else ""
    return d


def load_filter_jobs_from_db(**kwargs):
    """Filter jobs with AND semantics. Salary slider is minimum LPA (0–10); stored salary is INR."""
    kwargs = dict(kwargs)
    kwargs.pop("search", None)

    title_f = (kwargs.get("title") or "").strip()
    location_f = (kwargs.get("location") or "").strip()

    loc_lower = location_f.lower()
    if loc_lower in ("remote", "wfh", "work from home"):
        kwargs["remote"] = "on"
        location_f = ""

    salary_slider = kwargs.get("salary", "")
    try:
        min_lakhs_slider = float(str(salary_slider).strip() or 0)
    except ValueError:
        min_lakhs_slider = 0.0

    nlp_lakhs = kwargs.get("min_salary_lakhs")
    try:
        min_lakhs_nlp = float(nlp_lakhs) if nlp_lakhs not in (None, "") else None
    except (TypeError, ValueError):
        min_lakhs_nlp = None

    min_lakhs = max(min_lakhs_slider, min_lakhs_nlp or 0.0)

    experience_f = (kwargs.get("experience") or "").strip()
    if experience_f.lower().startswith("select"):
        experience_f = ""

    def _checkbox_on(v):
        if v is True:
            return True
        if v in (None, "", False):
            return False
        return str(v).lower().strip() in ("on", "true", "1", "yes")

    want_remote = _checkbox_on(kwargs.get("remote"))
    want_parttime = _checkbox_on(kwargs.get("parttime"))

    q = db.session.query(Job).join(Company, Job.comp_id == Company.company_id)

    preds = []

    if title_f:
        t = f"%{title_f}%"
        preds.append(
            or_(
                Job.title.ilike(t),
                Job.descriptions.ilike(t),
                Job.requirements.ilike(t),
            )
        )

    if location_f:
        preds.append(Job.location.ilike(f"%{location_f}%"))

    if min_lakhs > 0:
        min_inr = min_lakhs * 100000.0
        preds.append(Job.salary >= min_inr)

    if want_remote:
        preds.append(
            or_(
                Job.location.ilike("%remote%"),
                Job.location.ilike("%work from home%"),
                Job.location.ilike("%wfh%"),
                Job.descriptions.ilike("%remote%"),
                Job.descriptions.ilike("%work from home%"),
                Job.requirements.ilike("%remote%"),
                Job.requirements.ilike("%work from home%"),
            )
        )

    if want_parttime:
        preds.append(
            or_(
                Job.descriptions.ilike("%part-time%"),
                Job.descriptions.ilike("%part time%"),
                Job.requirements.ilike("%part-time%"),
                Job.requirements.ilike("%part time%"),
                Job.title.ilike("%part-time%"),
                Job.title.ilike("%part time%"),
            )
        )

    if experience_f == "fresher":
        preds.append(
            or_(
                Job.requirements.ilike("%fresher%"),
                Job.requirements.ilike("%fresh graduate%"),
                Job.requirements.ilike("%entry level%"),
                Job.requirements.ilike("%0 year%"),
                Job.requirements.ilike("%no experience%"),
                Job.descriptions.ilike("%fresher%"),
            )
        )
    elif experience_f == "1":
        preds.append(
            or_(
                Job.requirements.ilike("%1 year%"),
                Job.requirements.ilike("%1+ year%"),
                Job.requirements.ilike("%one year%"),
            )
        )
    elif experience_f == "2":
        preds.append(
            or_(
                Job.requirements.ilike("%2 year%"),
                Job.requirements.ilike("%2+ year%"),
                Job.requirements.ilike("%3 year%"),
                Job.requirements.ilike("%4 year%"),
                Job.requirements.ilike("%5 year%"),
                Job.requirements.ilike("%senior%"),
                Job.requirements.ilike("%experienced%"),
            )
        )

    if preds:
        q = q.filter(and_(*preds))

    jobs = q.all()
    if not jobs:
        return None
    return [_job_row_with_company(job) for job in jobs]


def get_weekly_applications_by_company(company_id):
    query = text("""
        SELECT 
            YEARWEEK(applied_on, 1) AS year_week,
            COUNT(*) AS count
        FROM application
        JOIN jobs ON application.job_id = jobs.id
        WHERE jobs.comp_id = :company_id
        GROUP BY year_week
        ORDER BY year_week DESC
        LIMIT 6;
    """)
    result = db.session.execute(query, {'company_id': company_id}).fetchall()

    # Reverse for chronological order (oldest to newest)
    result = result[::-1]

    weekly_counts = [row['count'] for row in result]

    # Fill missing weeks if needed (e.g., always return 6 weeks)
    while len(weekly_counts) < 6:
        weekly_counts.insert(0, 0)

    return weekly_counts


# Save Job in DB or Book Mark Job

from models import SavedJob, Job, User

def save_job(user_id, job_id):

    # check if already saved
    existing = SavedJob.query.filter_by(
        user_id=user_id,
        job_id=job_id
    ).first()

    if existing:
        return False

    saved = SavedJob(
        user_id=user_id,
        job_id=job_id
    )

    db.session.add(saved)
    db.session.commit()

    return True

def get_saved_jobs(user_id):

    saved_jobs = (
        db.session.query(Job)
        .join(SavedJob, Job.id == SavedJob.job_id)
        .filter(SavedJob.user_id == user_id)
        .all()
    )

    return saved_jobs

def remove_saved_job(user_id, job_id):

    saved = SavedJob.query.filter_by(
        user_id=user_id,
        job_id=job_id
    ).first()

    if saved:
        db.session.delete(saved)
        db.session.commit()

        return True

    return False