# Report Notes

## Final Report Structure

1. Introduction
2. Application under test
3. Team workload
4. Level 1 data-driven automation
5. Level 2 data-driven automation
6. Non-functional testing
7. Execution results
8. Discussion and limitations
9. Conclusion

## Section Notes

### 1. Introduction

Briefly describe Project #3, the goal of applying data-driven automation and non-functional testing, and how this project continues from Project #2.

### 2. Application Under Test

Describe Moodle Sandbox, the tested roles, the selected features, and any setup assumptions such as test accounts, course data, and browser environment.

### 3. Team Workload

Use the final allocation table from `docs/work_allocation.md`. Mention each member's two functional features and two non-functional tests.

### 4. Level 1 Data-Driven Automation

Explain that Level 1 keeps workflow logic in Python while input values and expected results are stored in CSV files under `data/level1/`.

### 5. Level 2 Data-Driven Automation

Explain that Level 2 reads URL, locator, action type, input value, and expected result from CSV files under `data/level2/`.

### 6. Non-Functional Testing

Describe the eight assigned NFR tests, their metrics, thresholds, and result CSV outputs.

### 7. Execution Results

Summarize pass/fail/error counts, attach or reference generated CSV files, and include screenshot evidence for failed cases.

### 8. Discussion and Limitations

Discuss Moodle Sandbox instability, locator changes, account permissions, timing variation, and any tests that still need stronger real-data validation.

### 9. Conclusion

Summarize what the team implemented, what was verified, and what could be improved in future work.

## Member Paragraph Templates

Nguyen Van Viet: I was responsible for F003 Create Quiz and F008 Create Calendar Event. For Project #3, I prepared data-driven test data and scripts for these workflows, led integration of the Level 2 framework, and implemented non-functional tests for quiz creation performance and calendar event reliability. My result evidence includes CSV output files and screenshots for failed or error cases.

Nguyen Gia Hoang: I was responsible for F001 Add New User and F007 Change Password. For Project #3, I prepared the related Level 1 and Level 2 CSV data, updated the automation scripts, and implemented non-functional tests for password security and account form usability. My result evidence includes CSV output files and screenshots for failed or error cases.

Do Thanh Dat: I was responsible for F002 Create Course and F005 Enroll Users. For Project #3, I prepared the related data-driven CSV files, updated the automation scripts, and implemented non-functional tests for form usability and workflow data integrity. My result evidence includes CSV output files and screenshots for failed or error cases.

Vo Cao Nhat Minh: I was responsible for F004 Create Assignment and F006 Submit Assignment. For Project #3, I prepared the related Level 1 and Level 2 automation data, updated the scripts, and implemented non-functional tests for assignment usability and upload performance. My result evidence includes CSV output files and screenshots for failed or error cases.

## Evidence Checklist

- Level 1 CSV data and result CSV files
- Level 2 CSV data and result CSV files
- Non-functional CSV data and result CSV files
- Screenshots for failed or error cases
- Short execution summary table
- Known limitations and remaining TODOs
