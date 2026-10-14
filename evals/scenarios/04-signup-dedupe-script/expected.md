# What a good final output contains

A Python script in the project's `outputs/`.

Must contain:
- Python 3 using only the standard library.
- Duplicates found by email, ignoring case and surrounding spaces.
- Of duplicates, the row with the earliest `signed_up` date is kept.
- The result is written to a new file; the input file is not modified.
- Rows whose email has no `@` are written to a separate rejects file.
- On the six sample rows the result has 3 rows (anna with 2026-01-15, bo, dan) and the
  rejects file has 1 (cecilia.example.com).

Good to have:
- The input path is a command-line argument.
- The script was run on the sample and the counts are reported.

Must not contain:
- pandas or any other package that needs installing.
- Code that overwrites the export.
