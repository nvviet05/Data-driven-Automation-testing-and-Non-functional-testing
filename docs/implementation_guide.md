# Implementation Guide

Run scripts from the repository root so relative paths resolve correctly.

## Google Sheets Source of Truth

The shared Google Sheets workbook has only five tabs, not one tab per feature:

- `TC_Inventory`
- `Level1_Data`
- `Level2_Locators_Data`
- `Execution_Results`
- `Non_Functional_Testing`

Use Google Sheets as the working source of truth during team collaboration. Before submission, export the relevant rows into CSV files under the `data/` folder.

## Level 1 CSV Files

Location: `data/level1/*.csv`

Level 1 uses one CSV row per test case. Fill input values and expected results for the feature script. The Python script keeps the workflow logic, so the CSV should focus on data such as names, dates, roles, file names, passwords, and expected messages. Export the relevant `Level1_Data` rows into the matching `data/level1/*.csv` file for each feature.

Minimum guidance:

- Keep `tc_id` unique.
- Use safe demo data only.
- Put the expected UI message or expected final state in `expected_result`.
- Do not place real credentials in any CSV file.

## Level 2 CSV Files

Location: `data/level2/*.csv`

Level 2 uses one CSV row per action step. Export the relevant `Level2_Locators_Data` rows into the matching `data/level2/*.csv` file for each feature. Fill:

- `page_url`: page to open, either relative to `BASE_URL` or a full Moodle URL.
- `locator_type`: Selenium locator strategy such as `id`, `name`, `css`, or `xpath`.
- `locator_value`: real Moodle locator.
- `action_type`: supported action such as `open`, `type`, `click`, `select`, `upload`, `wait`, `verify_text`, or `verify_visible`.
- `input_value`: value used by the step.
- `expected_result`: expected text, visibility, or state for verification steps.

Keep Level 2 steps in execution order for each `tc_id`.

## Non-Functional CSV Files

Location: `data/non_functional/*.csv`

Export the relevant rows from `Non_Functional_Testing` into the matching script-specific CSV file under `data/non_functional/`.

Required columns:

```text
tc_id,member,feature_id,non_functional_type,requirement,page_url,input_1,input_2,input_3,metric,threshold,expected_result,notes
```

Use `input_1`, `input_2`, and `input_3` for locator names, safe test values, repeat counts, role names, or small file names. Placeholder values such as `TODO_LOCATOR` and `TODO_TEST_DATA` are allowed during planning, but they must be replaced before final execution.

## Result CSV Generation

All scripts should call `common.result_writer.write_results`. Non-functional result rows use:

```text
run_id, run_date, member, feature_id, tc_id, non_functional_type, requirement, metric, expected_result, actual_result, status, screenshot_path, error_message
```

Rules:

- Create one `run_id` per script execution with `uuid.uuid4()`.
- Create `run_date` with `datetime.now().isoformat(timespec="seconds")`.
- Append result rows to `results/non_functional/<script_specific_name>_results.csv`.
- Use `PASS`, `FAIL`, or `ERROR` for `status`.
- Put exception text in `error_message` for `ERROR`.

## Screenshot Evidence

Failed or error cases should call `common.screenshot.save_screenshot`.

Recommended naming pattern:

```text
<FEATURE_ID>_<short_requirement>_<tc_id>_<timestamp>.png
```

Examples:

- `F003_quiz_performance_NF-F003-001_20260507_103000.png`
- `F006_upload_performance_NF-F006-001_20260507_103000.png`

Save screenshots under `screenshots/non_functional/`.

## Running Scripts

Examples from repository root:

```bash
python -m level1.f003_create_quiz_level1
python -m level2.f003_create_quiz_level2
python -m non_functional.f003_quiz_performance_test
```

Before final demo:

- Install dependencies with `pip install -r requirements.txt`.
- Create local `.env` from `.env.example`.
- Confirm Chrome and ChromeDriver are available for Selenium.
- Replace placeholder Moodle locators and test data.

## Nguyen Van Viet End-to-End Workflow

### Features

- **F003** — Create Quiz
- **F008** — Create Calendar Event

### Running Commands

Run all scripts from the repository root:

```bash
# Level 1 — Data-driven automation
python -m level1.f008_create_event_level1
python -m level1.f003_create_quiz_level1

# Non-functional tests
python -m non_functional.f008_event_reliability_test
python -m non_functional.f003_quiz_performance_test

# Level 2 — Generic step-driven automation
python -m level2.f008_create_event_level2
python -m level2.f003_create_quiz_level2
```

### Expected Output Files

```text
results/level1/f008_level1_results.csv
results/level1/f003_level1_results.csv
results/non_functional/f008_event_reliability_results.csv
results/non_functional/f003_quiz_performance_results.csv
results/level2/f008_level2_results.csv
results/level2/f003_level2_results.csv
```

### Screenshot Evidence

Screenshots on FAIL or ERROR are saved under:

```text
screenshots/level1/
screenshots/non_functional/
screenshots/level2/
```

### Before Final Run

Replace `TODO_LOCATOR` and `TODO_TEST_DATA` with verified Moodle Sandbox locators and safe test data before final execution. Check all CSV files under `data/` for placeholder values.
