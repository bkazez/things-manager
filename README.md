Python script to manage Things3 "Today" list.

To run:
```
python manage.py
```

Use `--dry-run` to test.

It runs an AppleScript that outputs Things tasks as text, turns that into a hash, and then generates AppleScript code needed to re-prioritize tasks.

At the moment it ensures that "Today" has a certain number of tasks in it, chosen from all tasks in order of priority tags (P1-P3), plus one "Keep In Touch" task (labelled KIT).
