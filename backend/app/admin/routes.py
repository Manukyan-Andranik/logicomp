import os
import shutil
import json
from pathlib import Path
from datetime import datetime

from flask_login import login_required, current_user
from flask import render_template, redirect, url_for, flash, request, current_app, abort, jsonify

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
from app.models import User, Contest, Problem, Submission, TestCase, ParticipantsHistory, contest_participants
from app.email import send_credentials_email
from app.utils import generate_leaderboard_pdf, generate_leaderboard_excel



@bp.route('/')
@login_required
def index():
    if not current_user.role == 'admin':
        flash('You do not have permission to access this page.', 'danger')
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
    if current_user.role != 'admin':
        abort(403)
    
    form = CreateContestForm()
    if form.validate_on_submit():
        try:
            # Step 1: Temporarily create the contest to get an ID
            temp_contest = Contest(
                title=form.title.data,
                description=form.description.data,
                start_time=form.start_time.data,
                end_time=form.end_time.data,
                is_public=form.is_public.data
            )
            db.session.add(temp_contest)
            db.session.flush()  # Get ID without committing yet

            # Step 2: Prepare folder and file path
            root_dir = os.path.dirname(os.path.abspath(__file__))
            participants_folder = Path(os.path.join(root_dir, f'../static/contest_{temp_contest.id}')).resolve()
            participants_file_path = participants_folder / 'participants.json'

            # Create folder and file
            participants_folder.mkdir(parents=True, exist_ok=True)
            if not participants_file_path.exists() or participants_file_path.stat().st_size == 0:
                with open(participants_file_path, 'w', encoding='utf-8') as f:
                    json.dump([], f, indent=2)
            

            # Step 3: Save the folder path in the contest
            temp_contest.participants_folder = str(participants_folder)
            db.session.commit()

            flash('Contest created successfully!', 'success')
            return redirect(url_for('admin.index'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error creating contest: {str(e)}", "danger")

    elif form.errors:
        flash(f"Cannot create contest: {form.errors}", "danger")

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


@bp.route('/contest/<int:contest_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_contest(contest_id):
    contest = Contest.query.get_or_404(contest_id)

    if not current_user.role == 'admin':
        return redirect(url_for('admin.contest_details', contest_id=contest.id))

    # Delete folder if exists
    participants_folder = contest.participants_folder
    if participants_folder and os.path.exists(participants_folder):
        shutil.rmtree(participants_folder)

    try:
        # Process each participant
        participants = contest.participants.all()
        for participant in participants:
            # Submissions by this participant in this contest
            submissions = Submission.query.filter_by(user_id=participant.id, contest_id=contest.id).all()

            # Save to history
            history = ParticipantsHistory(
                username=participant.username,
                email=participant.email,
                contest_id=contest.id
            )
            db.session.add(history)

            # Delete all their submissions in this contest
            for sub in submissions:
                db.session.delete(sub)

            # Remove from association table
            contest.participants.remove(participant)

            # Check if participant is in any other contest
            other_contests = db.session.query(contest_participants).filter(
                contest_participants.c.user_id == participant.id
            ).count()

            if other_contests == 0:
                db.session.delete(participant)

        # Delete contest (cascades will delete problems, test_cases, etc.)
        db.session.delete(contest)
        db.session.commit()

        flash('Contest and related data deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting contest: {str(e)}', 'danger')

    return redirect(url_for('admin.index'))

@bp.route('/contest/<int:contest_id>/add_problem', methods=['GET', 'POST'])
@login_required
def add_problem(contest_id):
    form = CreateProblemForm()
    contest = Contest.query.get_or_404(contest_id)
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
    base_url = request.url.replace(request.path, '', 1)
    contest_url = f"{base_url}/contest/{contest.id}"
    participants_file = f"{contest.participants_folder}/participants.json" 

    if not os.path.exists(participants_file):    
        flash("The contest does not have any participants yet.", "info")
        return render_template('admin/contest_details.html', contest=contest, datetime=datetime)
    with open(participants_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)    
    if not json_data:
        flash("The contest does not have any participants yet.", "info")
        return render_template('admin/contest_details.html', contest=contest, datetime=datetime)

    participants = []
    try:
        for idx, participant in enumerate(json_data):
            username = participant.get('username')
            email = participant.get('email')
            if not username or not email:
                flash(f"Skipping invalid entry at index {idx}: missing username or email.", "warning")
                continue
            
            password = User.generate_random_password()
            
            user = User.query.filter_by(username=username).first()
            if not user:
                user = User(username=username, email=email, role='participant')
                user.set_password(password)
                db.session.add(user)

            else:
                User.update_password(user, password)
            
            if user not in contest.participants:
                contest.participants.append(user)
            
            participants.append({'username': username, 'password': password, 'email': email, 'username': username})
        
        db.session.commit()
        
        # Send emails
        for participant in participants:
            print(f"Sending credentials to {participant['email']}",
                    f"Username: {participant['username']},",
                    f"Password: {participant['password']}")
            
            # TODO: Send email with credentials
            send_credentials_email(
                participant['email'],
                participant['username'],
                participant['password'],
                contest,
                contest_url=contest_url
            )
        
        flash(f'Generated credentials for {len(participants)} participants from JSON file.', 'success')
        return redirect(url_for('admin.contest_details', contest_id=contest.id))
        
    except Exception as e:
        flash(f"Failed to process JSON file: {str(e)}", 'danger')
        return render_template('admin/contest_details.html', contest=contest, datetime=datetime)

@bp.route('/submissions')
@login_required
def view_submissions():
    page = request.args.get('page', 1, type=int)
    contest_id = request.args.get('contest_id', type=int)
    
    # Query-ն սկզբնականացնում ենք՝ բոլոր հանձնումները ստանալու համար
    query = Submission.query

    contest = None
    if contest_id:
        # Եթե կոնկրետ contest_id է տրված, ֆիլտրում ենք
        contest = Contest.query.get_or_404(contest_id)
        query = query.filter_by(contest_id=contest_id)
    
    submissions_pagination = query.order_by(Submission.timestamp.desc()).paginate(
        page=page, per_page=10, error_out=False
    )

    # Բոլոր մրցույթները ստանում ենք dropdown-ի համար
    all_contests = Contest.query.order_by(Contest.title).all()

    return render_template(
        'admin/submissions.html', 
        submissions=submissions_pagination,
        contest=contest, # Սա կլինի None, եթե contest_id չկա
        all_contests=all_contests, # Փոխանցում ենք dropdown-ի համար
        title="Submissions"
    )

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
    reports_dir = os.path.join(current_app.root_path, 'static')
    os.makedirs(reports_dir, exist_ok=True)

    # Generate PDF and Excel
    pdf_path = os.path.join(reports_dir, f"contest_{contest.id}/leaderboard.pdf")
    excel_path = os.path.join(reports_dir, f"contest_{contest.id}/leaderboard.xlsx")

    generate_leaderboard_pdf(pdf_path, contest, problems, leaderboard_data)
    generate_leaderboard_excel(excel_path, contest, problems, leaderboard_data)

    flash("PDF and Excel reports generated successfully.", "success")
    return redirect(url_for('admin.contest_details', contest_id=contest.id))



