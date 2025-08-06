# backend/app/contest/__init__.py
from flask import Blueprint

bp = Blueprint('contest', __name__, url_prefix='/contest')

from app.contest import routes