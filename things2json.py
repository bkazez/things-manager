import re
import json
import argparse
import subprocess
from dataclasses import dataclass

DRY_RUN = False

MAX_TODAY_TODOS = 5
KIT_TAG = "KIT"

DELIM = '|___|'

def run_things2text():
    try:
        result = subprocess.run(['osascript', 'things2text.scpt'], capture_output=True, text=True, check=True)
        return result.stderr.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running things2text: {e}")
        return None

def parse_things_output(output):
    headers = []
    todos = []
    for line in output.split('\n'):
        if line.strip():
            values = line.strip().split(DELIM)
            if headers == []:
                headers = values
            else:
                todo_dict = dict(zip(headers, values))

                # Convert tags to an array
                tags = todo_dict.get('tagNames', '').split(',') if todo_dict.get('tagNames') else []
                todo_dict['tags'] = [tag.strip() for tag in tags if tag.strip()]

                todos.append(todo_dict)

    return todos

def run_applescript(script):
    try:
        # Run the AppleScript using osascript
        process = subprocess.Popen(['osascript', '-e', script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        return_code = process.returncode

        return (return_code, stdout, stderr)

    except Exception as e:
        print(f"An error occurred: {e}")
        return (1, "", str(e))

def print_todos(todos):
    print(json.dumps(todos, indent=2))

def main():
    output = run_things2text()
    if output:
        todos = parse_things_output(output)
        print_todos(todos)

    else:
        print("No output from things2text")

if __name__ == "__main__":
    main()
