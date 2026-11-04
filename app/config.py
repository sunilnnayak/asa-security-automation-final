"""Runtime configuration. Secrets are supplied through the environment/secret manager."""
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vulntracker.db")
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise RuntimeError("SECRET_KEY must be set to a random value of at least 32 characters")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
NOTIFY_SERVICE_URL = os.getenv("NOTIFY_SERVICE_URL", "http://localhost:3001")
# Prototype default is deliberately fixed to avoid trusting an unvalidated Host header.
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")
