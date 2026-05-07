from non_functional.nfr_runner import run_non_functional_cases


def run() -> None:
    # TODO: Add real Moodle locators for opening calendar, creating an event,
    # saving it, and verifying the same event after repeated safe runs.
    run_non_functional_cases(
        data_filename="f008_event_reliability_data.csv",
        result_filename="f008_event_reliability_results.csv",
        screenshot_prefix="F008_event_reliability",
        planned_check="Repeat calendar event creation and verify pass rate/failure count.",
    )


if __name__ == "__main__":
    run()
