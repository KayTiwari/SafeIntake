import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("SAFEINTAKE_DATA_DIR", BASE_DIR / "data"))
UPLOAD_DIR = DATA_DIR / "uploads"
REDACTED_DIR = DATA_DIR / "redacted"

for d in (DATA_DIR, UPLOAD_DIR, REDACTED_DIR):
    d.mkdir(parents=True, exist_ok=True)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{DATA_DIR / 'safeintake.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB
    UPLOAD_DIR = str(UPLOAD_DIR)
    REDACTED_DIR = str(REDACTED_DIR)
