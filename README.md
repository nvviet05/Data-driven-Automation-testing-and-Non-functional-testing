# Software Testing Project 3 - Group 15

## Project purpose
This repository contains Python-based data-driven automation tests and non-functional test skeletons for Moodle Sandbox. The project supports both Level 1 and Level 2 data-driven testing and produces CSV results with screenshot evidence on failures.

## Repository structure
- config/: Environment settings and locator mapping
- common/: Shared utilities (browser, CSV, results, screenshots, waits)
- level1/: Level 1 scripts (CSV-driven inputs per feature)
- level2/: Level 2 scripts using a generic data-driven runner
- non_functional/: Non-functional test scripts
- data/: CSV inputs for Level 1, Level 2, and non-functional tests
- results/: CSV outputs (ignored by git)
- screenshots/: Evidence images (ignored by git)
- logs/: Log output placeholder
- docs/: Team allocation and report notes

## Setup
1. Install Python 3.10+.
2. (Optional) Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Configure environment
Copy the example file and update values. Do not commit real credentials.

```bash
copy .env.example .env
```

Set:
- BASE_URL
- MOODLE_USERNAME
- MOODLE_PASSWORD
- HEADLESS

## Running tests
Run commands from the repository root.

### Level 1
```bash
python -m level1.f001_add_user_level1
```

### Level 2
```bash
python -m level2.f001_add_user_level2
```

### Non-functional
```bash
python -m non_functional.performance_test
```

## Data-driven inputs
- Level 1 CSVs: data/level1
- Level 2 CSVs: data/level2
- Non-functional CSVs: data/non_functional

For Level 2, update the CSV columns `page_url`, `locator_type`, `locator_value`, `action_type`, `input_value`, and `expected_result` with real Moodle data.

## Results and evidence
- CSV results are written to results/ by level.
- Failed steps save screenshots to screenshots/ by level.

## Submission notes
- Python scripts and CSV data only (no Katalon files).
- Do not hard-code credentials.
- Each member implements assigned features from Project #2.
- Each member completes at least two non-functional tests.

## Team allocation
| Member | Features | Notes |
| --- | --- | --- |
| Nguyen Van Viet | F003 Create Quiz, F008 Create Event | Lead integration and Level 2 framework |
| Nguyen Gia Hoang | F001 Add New User, F007 Change Password |  |
| Do Thanh Dat | F002 Create Course, F005 Enroll Users |  |
| Vo Cao Nhat Minh | F004 Create Assignment, F006 Submit Assignment |  |
