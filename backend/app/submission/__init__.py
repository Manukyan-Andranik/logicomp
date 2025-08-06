# backend/app/submission/__init__.py
from flask import Blueprint

bp = Blueprint('submission', __name__, url_prefix='/submission')

from app.submission import routes