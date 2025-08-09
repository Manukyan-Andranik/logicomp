import json, os
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse

from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm
from app.models import User, Contest

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'error')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    contest_id = request.args.get('contest_id', type=int)
    if not contest_id:
        flash("Contest ID is missing.", "danger")
        return redirect(url_for('main.index'))  # or your default route

    contest = Contest.query.get_or_404(contest_id)
    form = RegistrationForm()

    if form.validate_on_submit():
        participants_file_path = os.path.join(contest.participants_folder, 'participants.json')

        # Ensure directory exists
        os.makedirs(contest.participants_folder, exist_ok=True)

        # Load existing participants
        if os.path.exists(participants_file_path):
            with open(participants_file_path, 'r') as f:
                participants = json.load(f)
        else:
            participants = []

        # Add new participant
        if any(p['username'] == form.username.data for p in participants):
            flash('Username already exists. Please choose a different username.', 'error')
            return redirect(url_for('auth.register', contest_id=contest_id))
        
        participants.append({
            'username': form.username.data,
            'email': form.email.data,
            'contest_id': contest_id
        })

        # Write back
        with open(participants_file_path, 'w') as f:
            json.dump(participants, f, indent=4)

        flash('Congratulations, you are now a registered user! Please wait for an admin to approve your account and send you a verification email with your special credentials.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form, contest=contest)