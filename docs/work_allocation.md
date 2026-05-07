# Work Allocation

## Project Target

Group 15 tests Moodle Sandbox for Project #3 using Python Selenium. The target is to demonstrate Level 1 data-driven automation, Level 2 CSV-driven automation, and non-functional testing with repeatable CSV inputs, result CSV outputs, and screenshot evidence for failures.

## Feature Ownership

| Member | Owned features | Main responsibility |
| --- | --- | --- |
| Nguyen Van Viet | F003 Create Quiz, F008 Create Calendar Event | Implement feature scripts, lead integration, maintain Level 2 framework |
| Nguyen Gia Hoang | F001 Add New User, F007 Change Password | Implement feature scripts and account/password test data |
| Do Thanh Dat | F002 Create Course, F005 Enroll Users | Implement feature scripts and course/enrolment test data |
| Vo Cao Nhat Minh | F004 Create Assignment, F006 Submit Assignment | Implement feature scripts and assignment/submission test data |

## Non-Functional Testing Allocation

| Member | Feature | NFR type | Requirement | Data file | Script |
| --- | --- | --- | --- | --- | --- |
| Nguyen Van Viet | F003 | Performance | Quiz creation workflow should complete within an acceptable response time. | `data/non_functional/f003_quiz_performance_data.csv` | `non_functional/f003_quiz_performance_test.py` |
| Nguyen Van Viet | F008 | Reliability | Calendar event creation should remain stable across repeated automation runs. | `data/non_functional/f008_event_reliability_data.csv` | `non_functional/f008_event_reliability_test.py` |
| Nguyen Gia Hoang | F001/F007 | Security | Password field masking and password policy enforcement. | `data/non_functional/f001_f007_security_data.csv` | `non_functional/f001_f007_security_test.py` |
| Nguyen Gia Hoang | F001 | Usability | Account form validation feedback. | `data/non_functional/f001_account_usability_data.csv` | `non_functional/f001_account_usability_test.py` |
| Do Thanh Dat | F002/F005 | Usability | Form validation feedback and input preservation. | `data/non_functional/f002_f005_usability_data.csv` | `non_functional/f002_f005_usability_test.py` |
| Do Thanh Dat | F002/F005 | Data integrity | Workflow state consistency. | `data/non_functional/f002_f005_data_integrity_data.csv` | `non_functional/f002_f005_data_integrity_test.py` |
| Vo Cao Nhat Minh | F004 | Usability | Assignment validation and recovery. | `data/non_functional/f004_assignment_usability_data.csv` | `non_functional/f004_assignment_usability_test.py` |
| Vo Cao Nhat Minh | F006 | Performance | File upload response time. | `data/non_functional/f006_upload_performance_data.csv` | `non_functional/f006_upload_performance_test.py` |

## Per-Member Deliverables

| Member | Deliverables |
| --- | --- |
| Nguyen Van Viet | F003 and F008 Level 1 CSV/script updates, F003 and F008 Level 2 CSV/script updates, quiz performance NFR, event reliability NFR, integration review |
| Nguyen Gia Hoang | F001 and F007 Level 1 CSV/script updates, F001 and F007 Level 2 CSV/script updates, password security NFR, account usability NFR |
| Do Thanh Dat | F002 and F005 Level 1 CSV/script updates, F002 and F005 Level 2 CSV/script updates, course/enrol usability NFR, course/enrol data integrity NFR |
| Vo Cao Nhat Minh | F004 and F006 Level 1 CSV/script updates, F004 and F006 Level 2 CSV/script updates, assignment usability NFR, upload performance NFR |

## Shared Google Sheets Tabs

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
- `execution_summary`

## Team Handoff Checklist

- Confirm each CSV tab has the same headers as the exported file.
- Replace `TODO_LOCATOR` and `TODO_TEST_DATA` placeholders before final execution.
- Confirm `.env` exists locally but is not committed.
- Run one Level 1 and one Level 2 script per owned feature.
- Run both assigned non-functional scripts per member.
- Collect result CSV files from `results/`.
- Collect failed-test screenshots from `screenshots/`.
- Add execution summary and limitations to the final report.
