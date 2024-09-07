import re
import json
import argparse
import subprocess
from datetime import datetime
from dataclasses import dataclass

DRY_RUN = False
PRINT_ONLY = False

MAX_TODAY_TODOS = 5
KIT_TAG = "KIT"

# Things3 list IDs
THINGS_TODAY_LIST = "TMTodayListSource"
THINGS_LOGBOOK_LIST = "TMLogbookListSource"
THINGS_UPCOMING_LIST = "TMCalendarListSource"

HELPERS_APPLESCRIPT = 'helpers.applescript'

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

                tags = todo_dict.get('tagNames', '').split(',') if todo_dict.get('tagNames') else []
                todo_dict['tags'] = [tag.strip() for tag in tags if tag.strip()]

                if 'completionDate' in todo_dict:
                    try:
                        todo_dict['completionDate'] = datetime.fromisoformat(todo_dict['completionDate'])
                    except ValueError:
                        todo_dict['completionDate'] = None

                todos.append(todo_dict)

    return todos

def todos_from_list(todos, list_id):
    return [todo for todo in todos if todo.get('listID') == list_id]

def is_kit(todo):
    #print("tags: " + ', '.join(todo['tags']))
    return KIT_TAG in todo['tags']

def ensure_kit_in_today(todos):
    scpt = ""

    # This depends on the prioritization step moving everything away, first.
    # Then, in addition to that, we add one remaining KIT.

    # Search remaining todos
    print("Search remaining todos")
    for todo in todos:
        if is_kit(todo):
            scpt += f"move my todoWithID(\"{todo['id']}\") to list \"Today\" -- {todo['name']}\n"
            break

    return scpt

def get_priority(todo):
    priorities = [int(match.group(1)) for tag in todo['tags']
                  for match in [re.search(r'P(\d)', tag)] if match]
    return min(priorities) if priorities else float('inf')

def sort_by_priority(todos):
    return sorted(todos, key=get_priority)

def prioritize_today(todos, max_today_todos):
    scpt = ""

    today_todos = todos_from_list(todos, THINGS_TODAY_LIST)

    # Move all "Today" todos to "Anytime"
    for todo in today_todos:
        scpt += f"move my todoWithID(\"{todo['id']}\") to list \"Anytime\" -- {todo['name']}\n"

    scpt += "\n"

    # Sort todos by priority, excluding ones with marked follow-up dates (i.e., "Upcoming")
    todos = [todo for todo in todos if todo.get('listID') not in (THINGS_UPCOMING_LIST, THINGS_LOGBOOK_LIST)]
    todos = list({todo['id']: todo for todo in todos}.values()) # unique it here, since earlier we needed to know what was in Today vs Anytime
    todos_by_priority = sort_by_priority(todos)

    print("\n\n\nNot in upcoming, sorted by prio:")
    #print_todos(todos_by_priority)

    # Select max_today_todos to move into Today.
    todos_to_move = todos_by_priority[0:max_today_todos]

    # Move them into Today, starting with the lowest-priority items
    for todo in todos_to_move[::-1]:
        scpt += f"move my todoWithID(\"{todo['id']}\") to list \"Today\" -- {todo['name']}\n"

    return scpt


def indent(text, indent_str="\t"):
    lines = text.split('\n')
    indented_lines = [indent_str + line for line in lines]
    indented_text = '\n'.join(indented_lines)

    return indented_text

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


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def print_todos(todos):
    print(json.dumps(todos, indent=2, cls=DateTimeEncoder))

def main():
    output = run_things2text()
    if output:
        todos = parse_things_output(output)
        if PRINT_ONLY:
            print_todos(todos)
            return

        scpt = ""

        scpt += prioritize_today(todos, MAX_TODAY_TODOS-1) + "\n"
        scpt += ensure_kit_in_today(todos) + "\n"

        # Import helpers
        with open(HELPERS_APPLESCRIPT) as f: helpers = f.read()

        scpt = helpers + "\n\n-----\ntell application \"Things3\"\n" + indent(scpt) + "\nend tell"

        print(scpt)
        if not DRY_RUN:
            print(run_applescript(scpt))

    else:
        print("No output from things2text")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process dry-run argument")
    parser.add_argument('--dry-run', action='store_true', help="Run in dry-run mode")
    parser.add_argument('--print-only', action='store_true', help="Print the todos, and nothing more")

    args = parser.parse_args()
    DRY_RUN = args.dry_run
    PRINT_ONLY = args.print_only

    main()
