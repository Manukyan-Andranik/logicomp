from flask import Blueprint

bp = Blueprint('contest', __name__, url_prefix='/contest')

from app.contest import routes