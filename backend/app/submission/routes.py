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
    """Process a submission in the background"""
    try:
        with app.app_context():
            print(f"[Judge] Starting to judge submission {submission.id}")
            
            # Get the problem and test cases
            problem = Problem.query.get(submission.problem_id)
            if not problem:
                print(f"[Judge] Error: Problem {submission.problem_id} not found")
                submission.status = "Runtime Error"
                submission.error_message = "Problem not found"
                db.session.commit()
                return
            
            # Check if there are test cases
            test_cases = problem.test_cases.all()
            if not test_cases:
                print(f"[Judge] No test cases found, marking as accepted")
                submission.status = "Accepted"
                submission.execution_time = 0
                db.session.commit()
                return
            
            print(f"[Judge] Found {len(test_cases)} test cases")
            
            # Import judge function
            from judge.mock_judge import judge_submission
            
            # Call the judge with the correct parameters
            result = judge_submission(submission.id)
            
            if result:
                print(f"[Judge] Judging completed for submission {submission.id}")
            else:
                print(f"[Judge] Judging failed for submission {submission.id}")
                submission.status = "Runtime Error"
                submission.error_message = "Judging process failed"
                db.session.commit()
                
    except Exception as e:
        print(f"[Judge] Error processing submission {submission.id}: {str(e)}")
        try:
            with app.app_context():
                submission.status = "Runtime Error"
                submission.error_message = f"Judge error: {str(e)}"
                db.session.commit()
        except Exception as commit_error:
            print(f"[Judge] Failed to update submission status: {str(commit_error)}")

@bp.route('/submit/<int:problem_id>', methods=['GET', 'POST'])
@login_required
def submit(problem_id):
    problem = Problem.query.get_or_404(problem_id)
    contest = Contest.query.get_or_404(problem.contest_id)
    
    # Get the user's last submission for this problem
    my_submissions = Submission.query.filter_by(
        user_id=current_user.id, 
        problem_id=problem.id
    ).order_by(Submission.timestamp.desc()).all()
    
    # Set initial code - either from last submission or None for default
    initial_code = None
    initial_language = None
    if my_submissions:
        initial_code = my_submissions[0].code
        initial_language = my_submissions[0].language
        print(f"Last submission code found: {initial_code[:50]}...")  # Print first 50 characters for debugging
    
    if not contest.is_active():
        flash('Contest is not currently active.', 'info')
        return redirect(url_for('contest.problem_view', contest_id=contest.id, problem_id=problem.id))
    
    form = SubmitSolutionForm()
    if form.validate_on_submit():
        source_code = form.code.data
        
        # If no code in textarea, try to read from uploaded file
        if not source_code and form.source_file.data:
            try:
                source_code = form.source_file.data.read().decode('utf-8', errors='ignore')
            except Exception as e:
                flash('Error reading uploaded file.', 'error')
                return redirect(url_for('submission.submit', problem_id=problem_id))
        
        # Validate that we have source code
        if not source_code or not source_code.strip():
            flash('Please provide source code either in the text area or upload a file.', 'error')
            return redirect(url_for('submission.submit', problem_id=problem_id))

        submission = Submission(
            user_id=current_user.id,
            problem_id=problem.id,
            contest_id=contest.id,
            code=source_code,
            language=form.language.data,
            status='Pending'
        )

        try:
            db.session.add(submission)
            db.session.commit()
            
            # Start background judging
            try:
                Thread(target=process_submission, args=(current_app._get_current_object(), submission)).start()
            except Exception as e:
                flash('Error starting judge process. Please try again.', 'error')
                return redirect(url_for('submission.submit', problem_id=problem_id))
            
            flash('Solution submitted and is being judged!', 'info')
            return redirect(url_for('submission.view', submission_id=submission.id))
        except Exception as e:
            db.session.rollback()
            flash('Error submitting solution. Please try again.', 'error')
            return redirect(url_for('submission.submit', problem_id=problem_id))
    
    return render_template(
        'submission/submit.html',
        form=form,
        problem=problem,
        contest=contest,
        initial_code=initial_code,  # This will be None if no previous submissions
        initial_language=initial_language  # This will be None if no previous submissions
    )


@bp.route('/submission/<int:submission_id>')
@login_required
def view(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    if submission.user_id != current_user.id and current_user.role != 'admin':
        abort(403)
    recent_submissions = Submission.query.filter_by(user_id=current_user.id).order_by(Submission.timestamp.desc()).limit(10).all()
    return render_template('submission/view.html', 
                         submission=submission,
                         problem=submission.problem,
                         contest=submission.problem.contest,
                         recent_submissions=recent_submissions)

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
