# backend/app/main/routes.py
from flask import render_template, redirect, url_for
from flask_login import current_user
from datetime import datetime
from app.main import bp
from app.models import Contest

@bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.index'))
        
        now = datetime.utcnow()
        active_contests = Contest.query.filter(
            Contest.start_time <= now,
            Contest.end_time >= now,
            Contest.is_public | Contest.participants.any(id=current_user.id)
        ).order_by(Contest.start_time.asc()).limit(3).all()
        
        return render_template('main/index.html', 
                            active_contests=active_contests,
                            now=now)
    
    return render_template('main/landing.html')

@bp.route('/about')
def about():
    return render_template('main/about.html')