import os

class Config:
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security
    SESSION_COOKIE_SECURE = True

    # Secret Key
    SECRET_KEY = os.getenv("SECRET_KEY")