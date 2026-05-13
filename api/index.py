"""Vercel Python serverless entrypoint for the Flask app.

Vercel discovers files in `api/` as serverless functions. We expose the
existing Flask app as a WSGI handler.

Storage notes for Vercel: /tmp is the only writable path and is ephemeral
per cold-start. Each function instance gets its own DB and uploaded files,
which is fine for a single-session portfolio demo but not for production.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

os.environ.setdefault("SAFEINTAKE_DATA_DIR", "/tmp/safeintake")

from app.main import app  # noqa: E402
