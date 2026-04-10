import os

class Config:
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security
    SESSION_COOKIE_SECURE = True

    # Secret Key
    SECRET_KEY = os.getenv("SECRET_KEY")

    # Email (SMTP) configuration for bulk email
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes", "on")
    MAIL_FROM = os.getenv("MAIL_FROM") or SMTP_USERNAME