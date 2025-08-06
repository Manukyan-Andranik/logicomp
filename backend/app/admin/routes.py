# backend/app/admin/routes.py
import os
import json
from datetime import datetime
from flask_login import login_required, current_user
from flask import render_template, redirect, url_for, flash, request, current_app, abort

from app import db, mail
from app.admin import bp
from app.admin.forms import (
    CreateContestForm, 
    CreateProblemForm, 
    GenerateCredentialsForm,
    EditContestForm,
    TestCaseForm,
    EditProblemForm
)
from app.models import User, Contest, Problem, Submission, TestCase
from app.email import send_credentials_email
from app.utils import generate_leaderboard_pdf, generate_leaderboard_excel

@bp.route('/')
@login_required
def index():
    if not current_user.role == 'admin':
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    contests = Contest.query.order_by(Contest.start_time.desc()).paginate(
        page=page, per_page=current_app.config['CONTESTS_PER_PAGE'], error_out=False)

    
    active_contests = Contest.query.filter(
        Contest.start_time <= datetime.utcnow(),
        Contest.end_time >= datetime.utcnow()
    ).count()
    
    participants = User.query.filter_by(role='participant').count()
    
    submissions_today = Submission.query.filter(
        Submission.timestamp >= datetime.utcnow().date()
    ).count()
    
    return render_template('admin/index.html', 
                         contests=contests,
                         active_contests=active_contests,
                         participants=participants,
                         submissions_today=submissions_today,
                        datetime=datetime)

@bp.route('/create_contest', methods=['GET', 'POST'])
@login_required
def create_contest():
    if not current_user.role == 'admin':
        abort(403)
    
    form = CreateContestForm()
    if form.validate_on_submit():
        print("created")
        contest = Contest(
            title=form.title.data,
            description=form.description.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            is_public=form.is_public.data
        )
        db.session.add(contest)
        db.session.commit()
        flash('Contest created successfully!')
        return redirect(url_for('admin.index'))
    flash(f"Cant create contest: {form.errors}", "danger")
    return render_template('admin/create_contest.html', form=form)

@bp.route('/contest/<int:contest_id>')
@login_required
def contest_details(contest_id):
    contest = Contest.query.get_or_404(contest_id)
    return render_template('admin/contest_details.html', contest=contest, datetime=datetime)

@bp.route('/contest/<int:contest_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_contest(contest_id):
    contest = Contest.query.get_or_404(contest_id)
    form = EditContestForm(obj=contest)
    
    if form.validate_on_submit():
        contest.title = form.title.data
        contest.description = form.description.data
        contest.start_time = form.start_time.data
        contest.end_time = form.end_time.data
        contest.is_public = form.is_public.data
        db.session.commit()
        flash('Contest updated successfully!', 'success')
        return redirect(url_for('admin.contest_details', contest_id=contest.id))
    
    return render_template('admin/edit_contest.html', form=form, contest=contest)

@bp.route('/contest/<int:contest_id>/add_problem', methods=['GET', 'POST'])
@login_required
def add_problem(contest_id):
    form = CreateProblemForm()
    contest = Contest.query.get_or_404(contest_id)
    print(form.expected_input.data,
    form.expected_output.data)
    if form.validate_on_submit():
        # Create Problem (optional expected_input/output — legacy fallback)
        problem = Problem(
            contest_id=contest_id,
            title=form.title.data,
            description=form.description.data,
            expected_input=form.expected_input.data or "",  # optional now
            expected_output=form.expected_output.data or "",
            time_limit=form.time_limit.data
        )
        db.session.add(problem)
        db.session.flush()  # Get problem.id before adding test cases

        # ✅ JSON upload processing
        if form.test_case_upload.json_file.data:
            json_file = form.test_case_upload.json_file.data
            try:
                json_data = json.load(json_file)
                if not form.test_case_upload.keep_existing.data:
                    form.test_cases.entries = []  # Clear manual inputs

                for tc in json_data:
                    test_case = TestCase(
                        problem_id=problem.id,
                        expected_input=tc.get('expected_input', ''),
                        expected_output=tc.get('expected_output', ''),
                        is_sample=tc.get('is_sample', False)
                    )
                    db.session.add(test_case)

            except Exception as e:
                db.session.rollback()
                flash(f"Error processing JSON file: {str(e)}", 'danger')
                return redirect(url_for('admin.add_problem', contest_id=contest_id))
            finally:
                json_file.close()


        db.session.commit()
        flash("Problem added successfully!", "success")
        return redirect(url_for('admin.contest_details', contest_id=contest_id))


    return render_template("admin/add_problem.html", form=form, contest=contest)


@bp.route('/problem/<int:problem_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_problem(problem_id):
    problem = Problem.query.get_or_404(problem_id)
    form = EditProblemForm(obj=problem)

    if form.validate_on_submit():
        # Update problem base fields
        problem.title = form.title.data
        problem.description = form.description.data
        problem.expected_input = form.expected_input.data
        problem.expected_output = form.expected_output.data
        problem.time_limit = form.time_limit.data

        json_file = form.test_case_upload.json_file.data

        if json_file:
            # User uploaded a JSON file - replace test cases completely
            try:
                # Delete all existing test cases for this problem
                TestCase.query.filter_by(problem_id=problem.id).delete()

                json_data = json.load(json_file)
                for tc in json_data:
                    test_case = TestCase(
                        problem_id=problem.id,
                        expected_input=tc.get('expected_input', ''),
                        expected_output=tc.get('expected_output', ''),
                        is_sample=tc.get('is_sample', False)
                    )
                    db.session.add(test_case)
            except Exception as e:
                flash(f'Error processing JSON file: {str(e)}', 'danger')
                db.session.rollback()
                return redirect(url_for('admin.edit_problem', problem_id=problem.id))
            finally:
                json_file.close()
        else:
            # No JSON uploaded — keep existing test cases unchanged
            pass

        db.session.commit()
        flash('Problem updated successfully!', 'success')
        return redirect(url_for('admin.contest_details', contest_id=problem.contest_id))

    # On GET: Load existing test cases into form.test_cases if you want to show manual test cases
    if request.method == 'GET':
        existing_cases = TestCase.query.filter_by(problem_id=problem.id).all()
        for tc in existing_cases:
            tc_form = TestCaseForm()
            tc_form.expected_input.data = tc.expected_input
            tc_form.expected_output.data = tc.expected_output
            tc_form.is_sample.data = tc.is_sample


    return render_template('admin/edit_problem.html', form=form, problem=problem)

@bp.route('/contest/<int:contest_id>/generate_credentials', methods=['GET', 'POST'])
@login_required
def generate_credentials(contest_id):
    contest = Contest.query.get_or_404(contest_id)
    form = GenerateCredentialsForm()
    
    if form.validate_on_submit():
        participants = []
        
        # If JSON file uploaded, parse it and generate credentials for those

        if form.json_file.data:
            try:
                data = form.json_file.data.read().decode('utf-8')
                json_data = json.loads(data)
                
                for idx, participant in enumerate(json_data):
                    full_name = participant.get('full_name')
                    email = participant.get('email')
                    if not full_name or not email:
                        flash(f"Skipping invalid entry at index {idx}: missing full_name or email.", "warning")
                        continue
                    
                    username = email.split('@')[0]  # Or build username differently if needed
                    password = User.generate_random_password()
                    
                    user = User.query.filter_by(username=username).first()
                    if not user:
                        user = User(username=username, email=email, role='participant')
                        user.set_password(password)
                        print(user.check_password(password))  # Debugging line
                        print(f"Creating new user: {username}, {email}, {full_name}")
                        db.session.add(user)
                    
                    if user not in contest.participants:
                        contest.participants.append(user)
                    
                    participants.append({'username': username, 'password': password, 'email': email, 'full_name': full_name})
                
                db.session.commit()
                
                # Send emails
                for participant in participants:
                    print(f"Sending credentials to {participant['email']}",
                          f"Username: {participant['username']},",
                          f"Password: {participant['password']}")
                    
                    # TODO: Send email with credentials
                    # send_credentials_email(
                    #     participant['email'],
                    #     participant['username'],
                    #     participant['password'],
                    #     contest
                    # )
                
                flash(f'Generated credentials for {len(participants)} participants from JSON file.', 'success')
                return redirect(url_for('admin.contest_details', contest_id=contest.id))
            
            except Exception as e:
                flash(f"Failed to process JSON file: {str(e)}", 'danger')
                return render_template('admin/generate_credentials.html', form=form, contest=contest)
        
        else:
            flash("Please provide either a JSON file.", "warning")

    return render_template('admin/generate_credentials.html', form=form, contest=contest)

@bp.route('/submissions')
@login_required
def view_submissions():
    page = request.args.get('page', 1, type=int)
    contest_id = request.args.get('contest_id', type=int) 
    contest = Contest.query.get_or_404(contest_id)
    submissions = Submission.query.filter_by(contest_id=contest_id).order_by(Submission.timestamp.desc()).paginate(
        page=page, per_page=current_app.config['SUBMISSIONS_PER_PAGE'], error_out=False)
    print(contest.id)
    return render_template('admin/submissions.html', submissions=submissions, contest=contest)





@bp.route('/contest/<int:contest_id>/export_reports', methods=['GET'])
@login_required
def export_reports(contest_id):
    contest = Contest.query.get_or_404(contest_id)

    if current_user.role != 'admin':
        abort(403)
    print(contest.end_time , datetime.utcnow())
    # if contest.end_time > datetime.utcnow():
    #     flash("Contest has not ended yet.", "warning")
    #     return redirect(url_for('admin.contest_details', contest_id=contest_id))

    participants = contest.participants.all()
    problems = contest.problems.order_by(Problem.id.asc()).all()

    leaderboard_data = []
    for user in participants:
        user_data = {
            'user': user,
            'problems': {},
            'total_score': 0,
            'total_time': 0
        }

        for problem in problems:
            best_submission = Submission.query.filter_by(
                user_id=user.id,
                problem_id=problem.id,
                status='Accepted'
            ).order_by(
                Submission.timestamp.asc(),
                Submission.execution_time.asc()
            ).first()

            if best_submission:
                user_data['problems'][problem.id] = {
                    'time': best_submission.execution_time,
                    'attempts': Submission.query.filter_by(
                        user_id=user.id,
                        problem_id=problem.id
                    ).count()
                }
                user_data['total_score'] += 1
                user_data['total_time'] += best_submission.execution_time
            else:
                user_data['problems'][problem.id] = None

        leaderboard_data.append(user_data)

    leaderboard_data.sort(key=lambda x: (-x['total_score'], x['total_time']))

    # Output folder
    reports_dir = os.path.join(current_app.root_path, 'static', 'reports')
    os.makedirs(reports_dir, exist_ok=True)

    # Generate PDF and Excel
    pdf_path = os.path.join(reports_dir, f"contest_{contest.id}_leaderboard.pdf")
    excel_path = os.path.join(reports_dir, f"contest_{contest.id}_leaderboard.xlsx")

    generate_leaderboard_pdf(pdf_path, contest, problems, leaderboard_data)
    generate_leaderboard_excel(excel_path, contest, problems, leaderboard_data)

    flash("PDF and Excel reports generated successfully.", "success")
    return redirect(url_for('admin.contest_details', contest_id=contest.id))
