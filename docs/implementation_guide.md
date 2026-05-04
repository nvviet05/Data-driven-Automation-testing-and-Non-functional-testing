# Implementation Guide

## Fill CSV files using Google Sheets
1. Create a new sheet with the same headers as the sample CSV files.
2. Enter one test case per row for Level 1 or one step per row for Level 2.
3. Keep columns consistent and avoid merged cells.
4. Use placeholder values until locators are confirmed.

## Export to CSV
1. In Google Sheets, select File > Download > Comma-separated values (.csv).
2. Save the file in the matching folder under data/.
3. Keep UTF-8 encoding and avoid formulas that export as blanks.

## Tips
- Always include `tc_id` and `expected_result`.
- For Level 2, ensure `action_type` uses supported values: open, type, click, select, upload, wait, verify_text, verify_visible.
