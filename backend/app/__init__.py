import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from config import Config
from datetime import datetime

db = SQLAlchemy()
login = LoginManager()
login.login_view = 'auth.login'
migrate = Migrate()
mail = Mail()
bootstrap = Bootstrap()

def create_app(config_class=Config):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_path = os.path.join(base_dir, '../../frontend/templates')
    static_path = os.path.join(base_dir, '../../frontend/static')
    
    app = Flask(__name__,
                template_folder=template_path,
                static_folder=static_path)
    
    app.config.from_object(config_class)

    db.init_app(app)
    login.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    bootstrap.init_app(app)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.contest import bp as contest_bp
    app.register_blueprint(contest_bp, url_prefix='/contest')

    from app.submission import bp as submission_bp
    app.register_blueprint(submission_bp, url_prefix='/submission')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}

    return app

from app import models