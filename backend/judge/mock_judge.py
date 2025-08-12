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
            msg = f"Unsupported language: {language}"
            print(f"[run_code] {msg}")
            return Verdict.COMPILATION_ERROR, msg, 0

        filename = filename_map[language]
        code_path = os.path.join(temp_dir, filename)

        # === Detect function name ===
        func_name = None

        if language == 'python':
            # Match function def: def func_name(
            m = re.search(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', code)
            if m:
                func_name = m.group(1)

            # Auto-wrap minimal code submissions
            if func_name and 'print' not in code:
                code += (
                    "\n\nif __name__ == '__main__':\n"
                    "    a, b = map(int, input().split())\n"
                    f"    print({func_name}(a, b))\n"
                )

        elif language == 'java':
            # Match function signature e.g. public static int funcName(
            m = re.search(r'public static (?:int|void|String|double|float|long|boolean) ([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', code)
            if m:
                func_name = m.group(1)

            # If function found but no Scanner/input handling, auto-wrap
            if func_name and 'Scanner' not in code:
                code = (
                    "public class Solution {\n"
                    f"    public static int {func_name}(int a, int b) {{\n"
                    "        // your logic here\n"
                    "        return a + b;\n"
                    "    }\n"
                    "    public static void main(String[] args) {\n"
                    "        java.util.Scanner sc = new java.util.Scanner(System.in);\n"
                    "        int a = sc.nextInt();\n"
                    "        int b = sc.nextInt();\n"
                    f"        System.out.println({func_name}(a, b));\n"
                    "    }\n"
                    "}\n"
                )

        elif language == 'javascript':
            # Match function definition: function funcName(
            m = re.search(r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', code)
            if m:
                func_name = m.group(1)

            if func_name and 'console.log' not in code:
                code += (
                    "\n\nconst fs = require('fs');\n"
                    "const input = fs.readFileSync(0, 'utf8').trim().split(' ').map(Number);\n"
                    f"console.log({func_name}(input[0], input[1]));\n"
                )

        # Write code to file
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
            # If no test cases, mark as accepted (legacy support)
            submission.status = Verdict.ACCEPTED.value
            submission.execution_time = 0
            db.session.commit()
            print(f"[Judge] No test cases found, marked as Accepted")
            return True
            
        # Initialize submission status
        submission.status = Verdict.ACCEPTED.value
        submission.execution_time = 0
        submission.error_message = None

        def normalize_output(text: str) -> str:
            """Normalize output by stripping extra whitespace and newlines."""
            return '\n'.join(
                line.strip()
                for line in text.strip().splitlines()
                if line.strip() != ''
            )

        print(f"[Judge] Starting test case evaluation...")
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"[Judge] Testing case {i}/{len(test_cases)}: input='{test_case.expected_input}', expected='{test_case.expected_output}'")
            
            # Convert time limit from milliseconds to seconds
            time_limit_seconds = max(1, problem.time_limit / 1000)  # Minimum 1 second
            
            verdict, output, exec_time = run_code(
                submission.code,
                submission.language,
                test_case.expected_input,
                time_limit_seconds
            )

            submission.execution_time = max(submission.execution_time, exec_time)

            if verdict != Verdict.ACCEPTED:
                submission.status = verdict.value
                submission.error_message = output
                print(f"[Judge] Test case {i} failed with {verdict.value}: {output}")
                break

            # Normalize outputs for comparison
            expected_normalized = normalize_output(test_case.expected_output)
            actual_normalized = normalize_output(output)
            
            if actual_normalized != expected_normalized:
                submission.status = Verdict.WRONG_ANSWER.value
                submission.error_message = (
                    f"Test case {i} failed: Output doesn't match expected result\n"
                    f"Expected: '{expected_normalized}'\n"
                    f"Got: '{actual_normalized}'"
                )
                print(f"[Judge] Test case {i} failed: expected '{expected_normalized}', got '{actual_normalized}'")
                break
            else:
                print(f"[Judge] Test case {i} passed")

        # Commit the final result
        db.session.commit()
        
        print(f"[Judge] Final result: {submission.status}")
        if submission.error_message:
            print(f"[Judge] Error message: {submission.error_message}")
        
        return True
