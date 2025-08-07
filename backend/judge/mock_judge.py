# judge/mock_judge.py
import subprocess
import os
import time
import tempfile
from enum import Enum, auto
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
            msg = f"Unsupported language: {language}"
            print(f"[run_code] {msg}")
            return Verdict.COMPILATION_ERROR, msg, 0

        filename = filename_map[language]
        code_path = os.path.join(temp_dir, filename)

        # === Auto-wrap for minimal code submission ===
        if language == 'python' and 'def res' in code and 'print' not in code:
            code += "\n\nif __name__ == '__main__':\n    a, b = map(int, input().split())\n    print(res(a, b))\n"

        elif language == 'java' and 'public static int res' in code and 'Scanner' not in code:
            code += (
                "\n\npublic class Solution {\n"
                "    public static int res(int a, int b) {\n"
                "        // your logic here\n"
                "        return a + b;\n"
                "    }\n"
                "    public static void main(String[] args) {\n"
                "        java.util.Scanner sc = new java.util.Scanner(System.in);\n"
                "        int a = sc.nextInt();\n"
                "        int b = sc.nextInt();\n"
                "        System.out.println(res(a, b));\n"
                "    }\n"
                "}\n"
            )

        elif language == 'javascript' and 'function res' in code and 'console.log' not in code:
            code += (
                "\n\nconst fs = require('fs');\n"
                "const input = fs.readFileSync(0, 'utf8').trim().split(' ').map(Number);\n"
                "console.log(res(input[0], input[1]));\n"
            )

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
                msg = f"Compilation Error (C++):\n{compile_result.stderr}"
                print(f"[run_code] {msg}")
                return Verdict.COMPILATION_ERROR, msg, 0

        elif language == 'java':
            compile_result = subprocess.run(
                ['javac', code_path],
                cwd=temp_dir,
                capture_output=True,
                text=True
            )
            if compile_result.returncode != 0:
                msg = f"Compilation Error (Java):\n{compile_result.stderr}"
                print(f"[run_code] {msg}")
                return Verdict.COMPILATION_ERROR, msg, 0
            executable = ['java', '-cp', temp_dir, 'Solution']

        elif language == 'javascript':
            if not shutil.which("node"):
                msg = "Node.js not installed."
                print(f"[run_code] {msg}")
                return Verdict.COMPILATION_ERROR, msg, 0
            executable = ['node', code_path]

        else:  # Python
            executable = ['python3', code_path]

        # === Execution ===
        try:
            start_time = time.time()
            process = subprocess.run(
                executable,
                input=input_data,
                capture_output=True,
                text=True,
                timeout=time_limit,
                cwd=temp_dir
            )
            exec_time = time.time() - start_time

            if process.returncode != 0:
                msg = (
                    f"Runtime Error\n"
                    f"Return code: {process.returncode}\n"
                    f"Stderr:\n{process.stderr.strip()}"
                )
                print(f"[run_code] {msg}")
                return Verdict.RUNTIME_ERROR, msg, exec_time

            msg = (
                f"Output:\n{process.stdout.strip()}\n"
                f"(Execution time: {exec_time:.4f}s)"
            )
            print(f"[run_code] Language: {language}")
            print(f"[run_code] Verdict: {Verdict.ACCEPTED.value}")
            print(f"[run_code] {msg}")
            return Verdict.ACCEPTED, process.stdout, exec_time

        except subprocess.TimeoutExpired:
            msg = f"Time Limit Exceeded (>{time_limit}s)"
            print(f"[run_code] {msg}")
            return Verdict.TIME_LIMIT_EXCEEDED, msg, time_limit

        except Exception as e:
            msg = f"Unexpected Exception: {str(e)}"
            print(f"[run_code] {msg}")
            return Verdict.RUNTIME_ERROR, msg, 0


def judge_submission(submission_id: int):
    # Add this function at the top or near run_code
    def normalize_output(text: str) -> str:
        """Normalize output by stripping extra whitespace and newlines."""
        return '\n'.join(
            line.strip()
            for line in text.strip().splitlines()
            if line.strip() != ''
        )

    """Judge a submission against all test cases"""
    from app import create_app, db
    from app.models import Submission, TestCase
    
    app = create_app()
    with app.app_context():
        submission = Submission.query.get(submission_id)
        if not submission:
            return
        
        problem = submission.problem
        test_cases = TestCase.query.filter_by(problem_id=problem.id).all()
        submission.status = Verdict.ACCEPTED.value
        submission.execution_time = 0
        
        for test_case in test_cases:
            verdict, output, exec_time = run_code(
                submission.code,
                submission.language,
                test_case.expected_input,
                problem.time_limit
            )
            
            submission.execution_time = max(submission.execution_time, exec_time)
            
            if verdict != Verdict.ACCEPTED:
                submission.status = verdict.value
                submission.error_message = output
                break

            if normalize_output(output) != normalize_output(test_case.expected_output):
                submission.status = Verdict.WRONG_ANSWER.value
                submission.error_message = (
                    "Output doesn't match expected result\n"
                    f"Expected: {normalize_output(test_case.expected_output)}\n"
                    f"Got: {normalize_output(output)}"
                )
                break

        
        db.session.commit()