# Implementation Guide

Run scripts from the repository root so relative paths resolve correctly.

## Level 1 CSV Files

Location: `data/level1/*.csv`

Level 1 uses one CSV row per test case. Fill input values and expected results for the feature script. The Python script keeps the workflow logic, so the CSV should focus on data such as names, dates, roles, file names, passwords, and expected messages.

Minimum guidance:

- Keep `tc_id` unique.
- Use safe demo data only.
- Put the expected UI message or expected final state in `expected_result`.
- Do not place real credentials in any CSV file.

## Level 2 CSV Files

Location: `data/level2/*.csv`

Level 2 uses one CSV row per action step. Fill:

- `page_url`: page to open, either relative to `BASE_URL` or a full Moodle URL.
- `locator_type`: Selenium locator strategy such as `id`, `name`, `css`, or `xpath`.
- `locator_value`: real Moodle locator.
- `action_type`: supported action such as `open`, `type`, `click`, `select`, `upload`, `wait`, `verify_text`, or `verify_visible`.
- `input_value`: value used by the step.
- `expected_result`: expected text, visibility, or state for verification steps.

Keep Level 2 steps in execution order for each `tc_id`.

## Non-Functional CSV Files

Location: `data/non_functional/*.csv`

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
- Append result rows to `results/non_functional/*.csv`.
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
