import subprocess
import os
import time
import tempfile
import re
from enum import Enum
from typing import Tuple
from app.models import TestCase

class Verdict(Enum):
    ACCEPTED = "Accepted"
    WRONG_ANSWER = "Wrong Answer"
    TIME_LIMIT_EXCEEDED = "Time Limit Exceeded"
    RUNTIME_ERROR = "Runtime Error"
    COMPILATION_ERROR = "Compilation Error"

def run_code(code: str, language: str, input_data: str, time_limit: int) -> Tuple[Verdict, str, float]:
    import shutil

    with tempfile.TemporaryDirectory() as temp_dir:
        filename_map = {
            'python': 'solution.py',
            'cpp': 'solution.cpp',
            'java': 'Solution.java',
            'javascript': 'solution.js'
        }

        if language not in filename_map:
            return Verdict.COMPILATION_ERROR, f"Unsupported language: {language}", 0

        filename = filename_map[language]
        code_path = os.path.join(temp_dir, filename)

        # Write user code
        with open(code_path, 'w') as f:
            f.write(code)

        # === Compilation ===
        if language == 'cpp':
            executable = os.path.join(temp_dir, 'solution')
            compile_result = subprocess.run(
                ['g++', code_path, '-o', executable],
                capture_output=True,
                text=True
            )
            if compile_result.returncode != 0:
                return Verdict.COMPILATION_ERROR, compile_result.stderr, 0

        elif language == 'java':
            compile_result = subprocess.run(
                ['javac', code_path],
                cwd=temp_dir,
                capture_output=True,
                text=True
            )
            if compile_result.returncode != 0:
                return Verdict.COMPILATION_ERROR, compile_result.stderr, 0
            executable = ['java', '-cp', temp_dir, 'Solution']

        elif language == 'javascript':
            if not shutil.which("node"):
                return Verdict.COMPILATION_ERROR, "Node.js not installed.", 0
            executable = ['node', code_path]

        else:  # Python
            executable = ['/usr/bin/python3', code_path]

        # === Execution ===
        try:
            start_time = time.time()
            process = subprocess.run(
                executable,
                input=input_data,  # feed test case input directly
                capture_output=True,
                text=True,
                timeout=time_limit,
                cwd=temp_dir
            )
            exec_time = time.time() - start_time

            if process.returncode != 0:
                return Verdict.RUNTIME_ERROR, process.stderr.strip(), exec_time

            return Verdict.ACCEPTED, process.stdout, exec_time

        except subprocess.TimeoutExpired:
            return Verdict.TIME_LIMIT_EXCEEDED, f"Time Limit Exceeded (>{time_limit}s)", time_limit

def judge_submission(submission_id: int):
    """Judge a submission against all test cases"""
    from app import create_app, db
    from app.models import Submission, TestCase

    app = create_app()
    with app.app_context():
        submission = Submission.query.get(submission_id)
        if not submission:
            print(f"[Judge] Submission {submission_id} not found")
            return None

        problem = submission.problem
        test_cases = TestCase.query.filter_by(problem_id=problem.id).all()
        
        print(f"[Judge] Judging submission {submission_id} for problem {problem.id}")
        print(f"[Judge] Found {len(test_cases)} test cases")
        
        if not test_cases:
            submission.status = Verdict.ACCEPTED.value
            submission.execution_time = 0
            db.session.commit()
            print(f"[Judge] No test cases found, marked as Accepted")
            return True
            
        submission.status = Verdict.ACCEPTED.value
        submission.execution_time = 0
        submission.error_message = None

        def normalize_output(text: str) -> str:
            return '\n'.join(
                line.strip()
                for line in text.strip().splitlines()
                if line.strip() != ''
            )

        print(f"[Judge] Starting test case evaluation...")
        for i, test_case in enumerate(test_cases, 1):
            print(f"[Judge] Testing case {i}/{len(test_cases)}: input='{test_case.expected_input}', expected='{test_case.expected_output}'")
            
            time_limit_seconds = max(1, problem.time_limit / 1000)
            
            verdict, output, exec_time = run_code(
                submission.code,
                submission.language,
                test_case.expected_input,
                time_limit_seconds
            )

            submission.execution_time = max(submission.execution_time, exec_time)

            if verdict != Verdict.ACCEPTED:
                # e.g. Runtime Error, Time Limit Exceeded, etc.
                submission.status = verdict.value
                submission.error_message = f"Error in test case {i}: {verdict.value}"
                print(f"[Judge] {submission.error_message} -> {output}")
                db.session.commit()
                return False

            expected_normalized = normalize_output(test_case.expected_output)
            actual_normalized = normalize_output(output)
            
            if actual_normalized != expected_normalized:
                submission.status = Verdict.WRONG_ANSWER.value
                submission.error_message = f"Error in test case {i}: Wrong Answer"
                print(f"[Judge] {submission.error_message}: expected '{expected_normalized}', got '{actual_normalized}'")
                db.session.commit()
                return False
            else:
                print(f"[Judge] Test case {i} passed")

        db.session.commit()
        print(f"[Judge] Final result: {submission.status}")
        return True
