from flask import render_template, redirect, url_for, flash, abort, request, current_app
from flask_login import login_required, current_user
from app import db
from app.submission import bp
from app.submission.forms import SubmitSolutionForm
from app.models import Submission, Problem, Contest
from judge.mock_judge import judge_submission
from datetime import datetime
from threading import Thread




def process_submission(app, submission):
    with app.app_context():
        problem = Problem.query.get(submission.problem_id)
        result = judge_submission(
            code=submission.code,
            language=submission.language,
            problem_id=submission.problem_id,
            time_limit=problem.time_limit
        )
        
        submission.status = result['verdict']
        submission.execution_time = result['execution_time']
        db.session.commit()

@bp.route('/submit/<int:problem_id>', methods=['GET', 'POST'])
@login_required
def submit(problem_id):
    problem = Problem.query.get_or_404(problem_id)
    contest = Contest.query.get_or_404(problem.contest_id)
    
    if not contest.is_active():
        flash('Contest is not currently active.', 'info')
        return redirect(url_for('contest.problem_view', contest_id=contest.id, problem_id=problem.id))
    
    form = SubmitSolutionForm()
    if form.validate_on_submit():
        source_code = form.code.data
        if not source_code:
            source_code = form.source_file.data.read().decode('utf-8', errors='ignore')


        submission = Submission(
            user_id=current_user.id,
            problem_id=problem.id,
            contest_id=contest.id,
            code=source_code,
            language=form.language.data,
            status='Pending'
        )

        db.session.add(submission)
        db.session.commit()
        
        # Start background judging
        Thread(target=judge_submission, args=(submission.id,)).start()
        
        flash('Solution submitted and is being judged!', 'info')
        return redirect(url_for('submission.view', submission_id=submission.id))
    
    return render_template('submission/submit.html', form=form, problem=problem, contest=contest)


@bp.route('/submission/<int:submission_id>')
@login_required
def view(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    if submission.user_id != current_user.id and current_user.role != 'admin':
        abort(403)
    
    return render_template('submission/view.html', 
                         submission=submission,
                         problem=submission.problem,
                         contest=submission.problem.contest)

@bp.route('/my_submissions', methods=['GET'])
@login_required
def my_submissions():
    page = request.args.get('page', 1, type=int)
    contest_id = request.args.get('contest_id', type=int) 

    contest = None  # Initialize to None so it’s always defined

    if contest_id:
        contest = Contest.query.get_or_404(contest_id)
        submissions = Submission.query.filter_by(contest_id=contest.id).order_by(
            Submission.timestamp.desc()
        ).paginate(
            page=page,
            per_page=current_app.config['SUBMISSIONS_PER_PAGE'],
            error_out=False
        )
    else:
        submissions = Submission.query.order_by(
            Submission.timestamp.desc()
        ).paginate(
            page=page,
            per_page=current_app.config['SUBMISSIONS_PER_PAGE'],
            error_out=False
        )

    return render_template(
        'submission/list.html', 
        submissions=submissions,
        contest=contest,
        title='My Submissions'
    )
