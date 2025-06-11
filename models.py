from sqlalchemy import text
from DB import db
from datetime import datetime


class Admin(db.Model):
    __tablename__ = 'admins'
    __table_args__ = {'schema': 'priyanshu_career'}

    id = db.Column(db.Integer, primary_key = True , autoincrement=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    phone = db.Column(db.String(100), nullable=False, unique=True)
    profile_pic = db.Column(db.String(50), nullable=False)
    about = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(5),nullable = False, server_default = text("'admin'"))

    def __init__(self, username, password, name, email, phone, profile_pic, about):
        self.username = username
        self.password = password
        self.name = name
        self.email = email
        self.phone = phone
        self.profile_pic = profile_pic
        self.about = about


    def to_dict(self):
        return{
            "id": self.id,
            "username": self.username,
            "password": self.password,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "profile_pic": self.profile_pic,
            "about": self.about,
            "role" : self.role
        }


class User(db.Model):
    __tablename__ = 'user'
    __table_args__ = {'schema': 'priyanshu_career'}

    id = db.Column(db.Integer ,primary_key = True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    phone = db.Column(db.String(100), nullable=False, unique=True)
    skills = db.Column(db.String(100), nullable=False)
    experience = db.Column(db.String(100), nullable=False)
    profile_pic = db.Column(db.String(50), nullable=False)
    resume = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(10), nullable=False, server_default=text("'applicant'"))

    def __init__(self, username, password, name, email, phone, skills, experience, profile_pic, resume):
        self.username = username
        self.password = password
        self.name = name
        self.email = email
        self.phone = phone
        self.skills = skills
        self.experience = experience
        self.profile_pic = profile_pic
        self.resume = resume

    def __repr__(self):
        return self.username   
    


class Job(db.Model):
    __tablename__ = 'jobs'  # You can rename this to your preferred table name
    __table_args__ = {'schema': 'priyanshu_career'}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(50), nullable=False)
    salary = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(5), nullable=False)
    descriptions = db.Column(db.String(1000), nullable=False)
    requirements = db.Column(db.String(1000), nullable=False)
    status = db.Column(db.String(30), nullable=False)
    posted_time = db.Column(db.Date, nullable=False)

    comp_id = db.Column(db.Integer, db.ForeignKey('priyanshu_career.company.company_id'), nullable=False)

    # Define the relationship with the Company model
    company = db.relationship('Company', backref='jobs', lazy=True)

    # Define the relationship with the Application model
    applications = db.relationship('Application', backref='jobs', lazy=True)
    
    def __init__(self, title, location, salary, currency, descriptions, requirements,status, posted_time, comp_id):
        self.title = title
        self.location = location
        self.salary = salary
        self.currency = currency
        self.descriptions = descriptions
        self.requirements = requirements
        self.status = status
        self.posted_time = posted_time
        self.comp_id = comp_id

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "location": self.location,
            "salary": self.salary,
            "currency": self.currency,
            "descriptions": self.descriptions,
            "requirements": self.requirements,
            "comp_id": self.comp_id,
            "status": self.status,
            "posted_time": self.posted_time
        }

    def __repr__(self):
        return f"<Job {self.title} at {self.company_name}>"   



class Application(db.Model):
    __tablename__ = 'application'
    __table_args__ = {'schema': 'priyanshu_career'}

    id = db.Column(db.Integer, primary_key=True,autoincrement=True)

    # Foreign key to link to the Job model
    job_id = db.Column(db.Integer, db.ForeignKey('priyanshu_career.jobs.id'), nullable=False)

    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.BigInteger, nullable=False)
    linkedin = db.Column(db.String(100), nullable=False)
    education = db.Column(db.String(100), nullable=False)
    work_experience = db.Column(db.String(100), nullable=False)
    resume = db.Column(db.String(100), nullable=False)
    applied_on = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, job_id, full_name, email, phone, linkedin, education, work_experience, resume):
        self.job_id = job_id
        self.full_name = full_name
        self.email = email
        self.phone = phone 
        self.linkedin = linkedin
        self.education = education
        self.work_experience = work_experience
        self.resume = resume

    def __repr__(self):
        return f"<Application {self.id}>"



class Company(db.Model):
    __tablename__ = 'company'
    __table_args__ = {'schema': 'priyanshu_career'}

    company_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_name = db.Column(db.String(100), nullable=False)
    contact_email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False,unique=True)
    website = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20),nullable=False, default='pending')   # code-side default 
    role = db.Column(db.String(10), nullable=False, server_default=text("'company'"))   # DataBase-level default 


    def __init__(self, company_name, contact_email, password, website):
        self.company_name = company_name
        self.contact_email = contact_email
        self.password = password
        self.website = website
    
    def to_dict(self):
        return {
            "company_id": self.company_id,
            "company_name": self.company_name,
            "contact_email": self.contact_email,
            "password": self.password,
            "website": self.website,
            "status": self.status,
            "role" : self.role
        }


    def __repr__(self):
        return f"<Company {self.name}>"
    