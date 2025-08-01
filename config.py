# config.py
import os, pathlib

BASE_DIR = pathlib.Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "you‑should‑override‑this")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)

class DevelopmentConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{(DATA_DIR/'volunteer.db').as_posix()}"
    )
    DEBUG = True

class TestingConfig(BaseConfig):
    # in‑memory DB or a throwaway file
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    TESTING = True
    
class ProductionConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:////data/volunteer.db"
    )
    DEBUG = False