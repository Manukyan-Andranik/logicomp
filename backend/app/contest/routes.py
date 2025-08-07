from flask import render_template, redirect, url_for, flash, abort, request, current_app
from flask_login import login_required, current_user
from app import db
from app.contest import bp
from app.models import Contest, Problem, Submission, User
from datetime import datetime

@bp.route('/')
def index():
    now = datetime.utcnow()
    
    active_contests = Contest.query.filter(
        Contest.start_time <= now,
        Contest.end_time >= now
    ).order_by(Contest.start_time.asc()).all()
    
    upcoming_contests = Contest.query.filter(
        Contest.start_time > now
    ).order_by(Contest.start_time.asc()).all()
    
    past_contests = Contest.query.filter(
        Contest.end_time < now
    ).order_by(Contest.end_time.desc()).limit(5).all()
    
    return render_template('contest/index.html',
                         active_contests=active_contests,
                         upcoming_contests=upcoming_contests,
                         past_contests=past_contests)

@bp.route('/<int:contest_id>')
@login_required
def contest_view(contest_id):
    contest = Contest.query.get_or_404(contest_id)

    if not current_user.role == 'admin':
        if not contest.is_public or current_user not in contest.participants or not contest.is_active():
            flash("This contest is not active", "danger")
            return redirect(request.referrer or '/')
        
    problems = contest.problems.order_by(Problem.id.asc()).all()
    return render_template('contest/view.html', contest=contest, problems=problems)

@bp.route('/<int:contest_id>/problem/<int:problem_id>')
@login_required
def problem_view(contest_id, problem_id):
    contest = Contest.query.get_or_404(contest_id)
    problem = Problem.query.get_or_404(problem_id)
    
    if problem.contest_id != contest.id:
        abort(404)
    
    if not contest.is_public and current_user not in contest.participants:
        abort(403)
    
    submissions = current_user.submissions.filter_by(
        problem_id=problem.id
    ).order_by(Submission.timestamp.desc()).limit(10).all()
    
    return render_template('contest/problem.html', 
                         contest=contest, 
                         problem=problem, 
                         submissions=submissions)

@bp.route('/<int:contest_id>/leaderboard')
@login_required
def leaderboard(contest_id):
    contest = Contest.query.get_or_404(contest_id)

    # Access control: only public contests or registered participants
    if not contest.is_public and current_user not in contest.participants:
        abort(403)

    participants = contest.participants.all()
    problems = contest.problems.order_by(Problem.id.asc()).all()

    leaderboard_data = []

    for user in participants:
        user_data = {
            'user': user,
            'problems': {},
            'timestamp': None,
            'total_score': 0,
            'total_time': 0,
            'submissions_count': 0
        }

        latest_timestamp = None

        for problem in problems:
            submissions = Submission.query.filter_by(
                user_id=user.id,
                problem_id=problem.id
            ).order_by(Submission.timestamp.asc()).all()

            submission_count = len(submissions)
            user_data['submissions_count'] += submission_count

            accepted_submission = next((s for s in submissions if s.status == 'Accepted'), None)

            if accepted_submission:
                user_data['problems'][problem.id] = {
                    'is_accepted': True,
                    'time': accepted_submission.execution_time,
                    'attempts': submission_count,
                    'status': accepted_submission.status
                }
                user_data['total_score'] += 1
                user_data['total_time'] += accepted_submission.execution_time

                if not latest_timestamp or accepted_submission.timestamp > latest_timestamp:
                    latest_timestamp = accepted_submission.timestamp
            elif submission_count > 0:
                user_data['problems'][problem.id] = {
                    'is_accepted': False,
                    'attempts': submission_count
                }
            else:
                # No submission
                user_data['problems'][problem.id] = None

        user_data['timestamp'] = latest_timestamp
        leaderboard_data.append(user_data)

    # Sort: highest score first, then earliest timestamp, then lowest total_time
    leaderboard_data.sort(key=lambda x: (-x['total_score'], x['timestamp'] or datetime.max, x['total_time']))

    return render_template(
        'contest/leaderboard.html',
        contest=contest,
        problems=problems,
        leaderboard=leaderboard_data
    )
