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
            flash('Invalid username or password', 'danger') # Փոխում ենք error-ը danger-ի՝ Bootstrap-ի համար
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    # Եթե օգտատերը արդեն մուտք է գործել, ուղարկում ենք գլխավոր էջ
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    contest_id = request.args.get('contest_id', type=int)
    contest = Contest.query.get(contest_id) if contest_id else None

    form = RegistrationForm()
    if form.validate_on_submit():
        # 1. Ստեղծում ենք User օբյեկտ և հեշավորում գաղտնաբառը
        user = User(username=form.username.data, email=form.email.data, role='participant')
        user.set_password(form.password.data)
        
        # 2. Եթե օգտատերը գրանցվում է կոնկրետ մրցույթի համար, կցում ենք նրան
        if contest:
            # `contest_participants` աղյուսակին ավելացնում ենք կապը
            contest.participants.append(user)
        
        # 3. Պահպանում ենք տվյալները բազայում
        db.session.add(user)
        # Եթե contest-ը փոփոխվել է (նոր participant է ավելացել), commit-ը կպահպանի նաև դա
        db.session.commit()
        
        flash('Congratulations, you are now registered!', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html', title='Register', form=form, contest=contest)