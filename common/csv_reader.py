import csv


def read_csv(file_path: str) -> list[dict]:
    with open(file_path, newline="", encoding="utf-8") as file_handle:
        return list(csv.DictReader(file_handle))
