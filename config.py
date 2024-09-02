# config.py
import os

class Config:
    # General Config
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')
    DEBUG = os.getenv('DEBUG', True)
    
    # Database Config for SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql+pymysql://username:password@localhost/your_database')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Optionally add other configurations
