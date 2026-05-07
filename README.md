# Software Testing Project 3 - Group 15

Python Selenium data-driven automation and non-functional testing skeletons for Moodle Sandbox.

## Project Context

- Course: Software Testing
- Project: Project #3 - Data-driven Automation Testing and Non-functional Testing
- Application under test: Moodle Sandbox
- Continuation from: Project #2
- Main deliverables: Python code files and CSV data files

Do not commit real Moodle credentials. Keep only `.env.example` in Git.

## Repository Structure

- `config/`: environment settings and locator strategy notes
- `common/`: shared browser, CSV, result, screenshot, wait, and assertion utilities
- `level1/`: feature scripts for Level 1 data-driven testing
- `level2/`: generic Level 2 runner and feature entry points
- `non_functional/`: final non-functional test modules plus deprecated wrapper modules
- `data/`: CSV inputs for Level 1, Level 2, and non-functional tests
- `results/`: generated CSV result files
- `screenshots/`: failed test evidence
- `logs/`: optional execution logs
- `docs/`: allocation, implementation guide, and report notes

## Setup

Use Python 3.10+.

```bash
pip install -r requirements.txt
copy .env.example .env
```

Update `.env` locally only:

- `BASE_URL`
- `MOODLE_USERNAME`
- `MOODLE_PASSWORD`
- `HEADLESS`

## Level 1 vs Level 2

Level 1 is data-driven by test inputs and expected results. Each feature has a Python script in `level1/` and a CSV file in `data/level1/`. The Python code contains the workflow logic, while the CSV controls values such as names, dates, roles, passwords, and expected messages.

Level 2 is more generic. CSV rows in `data/level2/` provide the URL, locator type, locator value, action type, input value, and expected result. The common runner reads those rows and performs the actions in order. This separates the test flow definition from the Python code.

## Google Sheets Workflow

The working version of test data should be maintained in Google Sheets so the team can collaborate and review rows together. The submission version must be exported from Google Sheets as CSV and placed in the matching `data/` folder.

Recommended shared tabs:

- `level1_f001` to `level1_f008`
- `level2_f001` to `level2_f008`
- `nfr_f003_quiz_performance`
- `nfr_f008_event_reliability`
- `nfr_f001_f007_security`
- `nfr_f001_account_usability`
- `nfr_f002_f005_usability`
- `nfr_f002_f005_data_integrity`
- `nfr_f004_assignment_usability`
- `nfr_f006_upload_performance`

## Running Tests

Run all commands from the repository root.

Level 1 example:

```bash
python -m level1.f001_add_user_level1
```

Level 2 example:

```bash
python -m level2.f001_add_user_level2
```

## Running Non-Functional Scripts

Final Project 3 entry points:

```bash
python -m non_functional.f003_quiz_performance_test
python -m non_functional.f008_event_reliability_test
python -m non_functional.f001_f007_security_test
python -m non_functional.f001_account_usability_test
python -m non_functional.f002_f005_usability_test
python -m non_functional.f002_f005_data_integrity_test
python -m non_functional.f004_assignment_usability_test
python -m non_functional.f006_upload_performance_test
```

Deprecated generic wrapper modules are kept only for backward compatibility:

- `python -m non_functional.performance_test`
- `python -m non_functional.security_test`
- `python -m non_functional.usability_test`
- `python -m non_functional.reliability_test`
- `python -m non_functional.data_integrity_test`

## Final Allocation

| Member | Feature ownership | Integration role |
| --- | --- | --- |
| Nguyen Van Viet | F003 Create Quiz, F008 Create Calendar Event | Lead integration and Level 2 framework |
| Nguyen Gia Hoang | F001 Add New User, F007 Change Password | Feature automation and NFR execution |
| Do Thanh Dat | F002 Create Course, F005 Enroll Users | Feature automation and NFR execution |
| Vo Cao Nhat Minh | F004 Create Assignment, F006 Submit Assignment | Feature automation and NFR execution |

## Non-Functional Allocation

| Member | Script | Feature | Type | Requirement |
| --- | --- | --- | --- | --- |
| Nguyen Van Viet | `f003_quiz_performance_test.py` | F003 | Performance | Quiz creation workflow response time |
| Nguyen Van Viet | `f008_event_reliability_test.py` | F008 | Reliability | Calendar event creation repeated-run stability |
| Nguyen Gia Hoang | `f001_f007_security_test.py` | F001/F007 | Security | Password field masking and password policy enforcement |
| Nguyen Gia Hoang | `f001_account_usability_test.py` | F001 | Usability | Account form validation feedback |
| Do Thanh Dat | `f002_f005_usability_test.py` | F002/F005 | Usability | Form validation feedback and input preservation |
| Do Thanh Dat | `f002_f005_data_integrity_test.py` | F002/F005 | Data integrity | Workflow state consistency |
| Vo Cao Nhat Minh | `f004_assignment_usability_test.py` | F004 | Usability | Assignment validation and recovery |
| Vo Cao Nhat Minh | `f006_upload_performance_test.py` | F006 | Performance | File upload response time |

## Results and Evidence

Each non-functional script writes CSV rows to `results/non_functional/` with these columns:

```text
run_id, run_date, member, feature_id, tc_id, non_functional_type, requirement, metric, expected_result, actual_result, status, screenshot_path, error_message
```

Failed or error test cases save screenshots under `screenshots/non_functional/`.

## Final Submission Checklist

- Python scripts are runnable from the repository root.
- Level 1 and Level 2 are grouped separately.
- Level 1 CSV files contain input data and expected results.
- Level 2 CSV files contain URLs, locators, action types, input values, and expected results.
- Each member has at least two non-functional requirement tests.
- Non-functional CSV files are exported from Google Sheets.
- Result CSV files are generated after execution.
- Failed tests include screenshot evidence.
- Real credentials are not committed.
- Katalon Recorder files are not used as the main output.
