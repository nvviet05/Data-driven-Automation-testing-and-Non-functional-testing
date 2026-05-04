import csv
import os

RESULT_COLUMNS = [
    "run_id",
    "run_date",
    "feature_id",
    "tc_id",
    "level",
    "expected_result",
    "actual_result",
    "status",
    "screenshot_path",
    "error_message",
]


def write_results(file_path: str, rows: list[dict]) -> None:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    file_exists = os.path.exists(file_path)

    with open(file_path, "a", newline="", encoding="utf-8") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=RESULT_COLUMNS)
        if not file_exists:
            writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in RESULT_COLUMNS})
