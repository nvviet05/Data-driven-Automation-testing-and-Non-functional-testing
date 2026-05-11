# Implementation Guide

Run scripts from the repository root so relative paths resolve correctly.

## Google Sheets Source of Truth

The shared Google Sheets workbook has five working tabs:

- `TC_Inventory`
- `Level1_Data`
- `Level2_Locators_Data`
- `Execution_Results`
- `Non_Functional_Testing`

Use Google Sheets during team collaboration. Before submission, export the relevant rows into CSV files under `data/`.

## Level 1 CSV Files

Location: `data/level1/*.csv`

Level 1 uses one CSV row per test case. The Python script owns the workflow logic; the CSV owns test data, expected messages, and expected pass/fail behavior.

Minimum guidance:

- Keep `tc_id` unique.
- Use safe demo data only.
- Put the expected UI message or expected final state in `expected_result`.
- Do not place real credentials in any CSV file.

## Level 2 CSV Files

Location: `data/level2/*.csv`

Level 2 uses one CSV row per action step. Supported `action_type` values include `open`, `type`, `click`, `select`, `upload`, `wait`, `verify_text`, and `verify_visible`.

The shared Level 2 runner supports:

- CSS fallback selectors separated with `;`.
- Any locator fallback separated with `;;`.
- XPath union expressions with `|`, with fallback to each side if the full union fails.
- `ENV_MOODLE_USERNAME` and `ENV_MOODLE_PASSWORD` input tokens.
- `UNIQUE:<prefix>` input tokens for timestamped test data.
- Select input prefixes `value=` and `label=`.

Keep Level 2 steps in execution order for each `tc_id`.

## Non-Functional CSV Files

Location: `data/non_functional/*.csv`

Non-functional result rows use:

```text
run_id, run_date, member, feature_id, tc_id, non_functional_type, requirement, metric, expected_result, actual_result, status, screenshot_path, error_message
```

Rules:

- Create one `run_id` per script execution with `uuid.uuid4()`.
- Create `run_date` with `datetime.now().isoformat(timespec="seconds")`.
- Write `PASS`, `FAIL`, `ERROR`, or `SKIPPED` where a script intentionally blocks on role capability.
- Put exception text in `error_message` for `ERROR`.

## Screenshot Evidence

Failed or error cases should call `common.screenshot.save_screenshot`.

Screenshots are saved under:

```text
screenshots/level1/
screenshots/level2/
screenshots/non_functional/
```

Screenshots should only appear for `FAIL` or `ERROR` evidence unless a report explicitly references them.

## Nguyen Van Viet End-to-End Workflow

### Features

- **F003** - Create Quiz
- **F008** - Create Calendar Event

### Automation Notes

F003 opens Moodle's quiz creation form directly at:

```text
/course/modedit.php?add=quiz&course=3&section=1&return=0&sr=0
```

This is an automation shortcut derived from the Project 2 Katalon logs. It avoids the activity chooser while still testing the actual Moodle quiz form, submission, validation messages, and verification in `/mod/quiz/index.php?id=3`.

F008 uses the Moodle calendar modal form from the Project 2 Katalon logs. The script opens `/calendar/view.php?view=month`, clicks `New event`, fills `id=id_name`, `id=id_eventtype`, start time, and duration controls, then saves through the visible modal. Successful events are verified in `/calendar/view.php?view=upcoming`; negative cases require a visible validation selector.

### Running Commands

Run all scripts from the repository root:

```bash
python -m level1.f003_create_quiz_level1
python -m level1.f008_create_event_level1
python -m non_functional.f003_quiz_performance_test
python -m non_functional.f008_event_reliability_test
python -m level2.f003_create_quiz_level2
python -m level2.f008_create_event_level2
```

Final validation command:

```bash
python -m compileall common config level1 level2 non_functional
```

### Expected Output Files

```text
results/level1/f003_level1_results.csv
results/level1/f008_level1_results.csv
results/non_functional/f003_quiz_performance_results.csv
results/non_functional/f008_event_reliability_results.csv
results/level2/f003_level2_results.csv
results/level2/f008_level2_results.csv
```

### Repository Hygiene

Confirm `.env` exists locally with Moodle credentials, but do not commit it. Result CSVs and screenshots are generated evidence only; keep `.gitkeep` placeholders in source control and attach final generated evidence only when the report references it.
