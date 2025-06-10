import os
#configure the mysql db connection
SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI")
SQLALCHEMY_TRACK_MODIFICATIONS = False
SESSION_COOKIE_SECURE = True  
